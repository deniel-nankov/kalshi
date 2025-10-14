"""
Build the Gold (modeling-ready) dataset from Silver layer inputs.

Usage:
    python build_gold_layer.py

Expected inputs (Silver layer):
    - rbob_daily.parquet
    - wti_daily.parquet
    - retail_prices_daily.parquet
    - eia_inventory_weekly.parquet
    - eia_utilization_weekly.parquet
    - eia_imports_weekly.parquet             (optional but recommended)
    - padd3_share_weekly.parquet             (optional)
    - noaa_temp_daily.parquet                (optional)
    - hurricane_risk_october.csv             (optional)

Outputs (Gold layer):
    - master_daily.parquet       # Daily panel with engineered features (21+ features)
    - master_october.parquet     # Filtered October observations (2020 onward)
    - master_model_ready.parquet # Complete cases for training

Feature Engineering (18+ features):
    Price & Market:
        - price_rbob, price_wti, retail_price
        - rbob_lag3, rbob_lag7, rbob_lag14
        - crack_spread, retail_margin
        - delta_rbob_1w, rbob_return_1d, vol_rbob_10d
        - rbob_momentum_7d (NEW: percentage momentum)
    
    Supply & Refining:
        - inventory_mbbl, utilization_pct, net_imports_kbd
        - days_supply (NEW: normalized inventory)
        - util_inv_interaction (NEW: compound stress)
        - padd3_share (optional)
    
    Seasonal & Timing:
        - winter_blend_effect, days_since_oct1
        - weekday, is_weekend
        - temperature anomalies (optional)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# Add src directory to path for feature modules
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

SILVER_DIR = REPO_ROOT / "data" / "silver"
GOLD_DIR = REPO_ROOT / "data" / "gold"

# Feature engineering constants
HURRICANE_PROB_OCTOBER = 0.15  # Default hurricane probability for October (source: historical NOAA data)
DAILY_CONSUMPTION_MBBL = 8.5  # US average gasoline consumption (million barrels per day)
WINTER_BLEND_EFFECT_MAGNITUDE = -0.12  # Price impact of winter blend transition ($/gallon)
WINTER_BLEND_DECAY_RATE = 0.2  # Exponential decay rate for winter blend transition
MIN_OCTOBER_SAMPLES_FOR_COPULA = 50  # Minimum observations needed for reliable copula estimation

# Import copula feature (will be optional if module doesn't exist)
try:
    from features.copula_supply_stress import compute_copula_stress, validate_copula_feature
    COPULA_AVAILABLE = True
except ImportError:
    COPULA_AVAILABLE = False
    print("⚪ Copula feature module not available (optional)")


def _load_parquet(filename: str, *, required: bool = True) -> Optional[pd.DataFrame]:
    """Read a parquet file from the Silver directory with helpful messaging."""
    path = SILVER_DIR / filename
    if not path.exists():
        msg = f"Missing required Silver file: {path}" if required else f"Optional Silver file not found: {path}"
        print(f"⚠ {msg}")
        if required:
            raise FileNotFoundError(msg)
        return None

    df = pd.read_parquet(path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df


def _prepare_calendar(*frames: pd.DataFrame) -> pd.DataFrame:
    """Create a continuous daily calendar covering the union of provided dates."""
    frames_filtered = [f for f in frames if f is not None and not f.empty and "date" in f.columns]
    if not frames_filtered:
        # Return empty DataFrame with 'date' column as DatetimeIndex
        return pd.DataFrame({"date": pd.to_datetime([])})
    # Ensure all dates are datetime
    min_date = min(pd.to_datetime(f["date"]).min() for f in frames_filtered)
    max_date = max(pd.to_datetime(f["date"]).max() for f in frames_filtered)
    calendar = pd.DataFrame({"date": pd.date_range(min_date, max_date, freq="D")})
    return calendar


def _winter_blend_curve(dates: pd.Series, decay: float = WINTER_BLEND_DECAY_RATE) -> pd.Series:
    """
    Smooth transition function for the October blend switch.
    Returns zeros before Oct 1 of each year and decays thereafter.
    
    The winter blend transition typically causes a price decrease due to:
    - Lower production costs (winter formulation is less expensive)
    - Reduced volatility specifications
    
    Uses exponential decay to model the gradual market adjustment.
    """
    october_start = pd.to_datetime(dates.dt.year.astype(str) + "-10-01")
    days_since = (dates - october_start).dt.days.clip(lower=0)
    return WINTER_BLEND_EFFECT_MAGNITUDE * (1 - np.exp(-decay * days_since))


def build_gold_dataset() -> pd.DataFrame:
    """Construct the master daily dataset with engineered features."""
    print("=" * 80)
    print("BUILDING GOLD LAYER")
    print("=" * 80)

    rbob = _load_parquet("rbob_daily.parquet")
    wti = _load_parquet("wti_daily.parquet")
    retail = _load_parquet("retail_prices_daily.parquet")
    inventory = _load_parquet("eia_inventory_weekly.parquet")
    utilization = _load_parquet("eia_utilization_weekly.parquet")

    net_imports = _load_parquet("eia_imports_weekly.parquet", required=False)
    padd3 = _load_parquet("padd3_share_weekly.parquet", required=False)
    temps = _load_parquet("noaa_temp_daily.parquet", required=False)

    hurricane_path = SILVER_DIR / "hurricane_risk_october.csv"
    hurricanes = None
    if hurricane_path.exists():
        hurricanes = pd.read_csv(hurricane_path)
        hurricanes["date"] = pd.to_datetime(hurricanes["date"])
    else:
        print(f"⚪ Optional hurricane file not found: {hurricane_path}")

    calendar = _prepare_calendar(rbob, retail)

    gold = calendar.merge(rbob, on="date", how="left")
    gold = gold.merge(wti, on="date", how="left")
    gold = gold.merge(retail, on="date", how="left")

    for weekly_df, suffix in [
        (inventory, "inventory_mbbl"),
        (utilization, "utilization_pct"),
        (net_imports, "net_imports_kbd"),
        (padd3, "padd3_share"),
    ]:
        if weekly_df is None:
            continue
        gold = gold.merge(weekly_df, on="date", how="left", suffixes=("", ""))
        gold[suffix] = gold[suffix].ffill()

    if temps is not None:
        gold = gold.merge(temps, on="date", how="left", suffixes=("", ""))

    if hurricanes is not None:
        gold = gold.merge(hurricanes, on="date", how="left", suffixes=("", ""))

    gold = gold.sort_values("date").set_index("date")

    # Forward-fill daily market data to cover weekends/holidays
    gold[["price_rbob", "volume_rbob"]] = gold[["price_rbob", "volume_rbob"]].ffill()
    gold["price_wti"] = gold["price_wti"].ffill()

    # === PRICE & MARKET STRUCTURE FEATURES ===
    gold["crack_spread"] = gold["price_rbob"] - gold["price_wti"]
    gold["retail_margin"] = gold["retail_price"] - gold["price_rbob"]
    
    # Lagged retail margin (SAFE - uses past values only, no leakage)
    gold["retail_margin_lag7"] = gold["retail_margin"].shift(7)
    gold["retail_margin_lag14"] = gold["retail_margin"].shift(14)
    
    gold["rbob_lag3"] = gold["price_rbob"].shift(3)
    gold["rbob_lag7"] = gold["price_rbob"].shift(7)
    gold["rbob_lag14"] = gold["price_rbob"].shift(14)
    gold["delta_rbob_1w"] = gold["price_rbob"] - gold["price_rbob"].shift(7)
    gold["rbob_return_1d"] = gold["price_rbob"].pct_change()
    gold["vol_rbob_10d"] = gold["rbob_return_1d"].rolling(10).std()
    
    # NEW: RBOB Momentum (percentage change over 7 days)
    # Captures velocity of price changes, not just position
    # Guard against division by zero with np.where
    gold["rbob_momentum_7d"] = np.where(
        (gold["rbob_lag7"] == 0) | gold["rbob_lag7"].isna(),
        np.nan,
        (gold["price_rbob"] - gold["rbob_lag7"]) / gold["rbob_lag7"]
    )

    # === SUPPLY & REFINING BALANCE FEATURES ===
    # NEW: Days Supply (normalized inventory relative to daily consumption)
    # US average gasoline consumption is approximately 8.5 million barrels/day
    if "inventory_mbbl" in gold.columns:
        # Guard against negative or zero values
        gold["days_supply"] = np.where(
            gold["inventory_mbbl"] > 0,
            gold["inventory_mbbl"] / DAILY_CONSUMPTION_MBBL,
            np.nan
        )
    
    # NEW: Utilization × Inventory Interaction (compound stress indicator)
    # High utilization + low inventory = severe supply constraint
    if "utilization_pct" in gold.columns and "days_supply" in gold.columns:
        gold["util_inv_interaction"] = gold["utilization_pct"] * gold["days_supply"]
    
    # NEW: Copula Supply Stress (joint tail risk modeling)
    # Captures non-linear dependencies: low inventory + high utilization + hurricane risk
    # Academic foundation: Patton (2006), Cherubini et al. (2004)
    if COPULA_AVAILABLE and "days_supply" in gold.columns and "utilization_pct" in gold.columns:
        print("\n🎯 Computing copula supply stress feature...")
        try:
            # Extract October data for historical calibration (more stable estimates)
            # Simplified date handling: extract date column regardless of index/column status
            date_col = pd.to_datetime(gold['date'] if 'date' in gold.columns else gold.index)
            october_hist = gold.loc[date_col.dt.month == 10].copy()
            
            if len(october_hist) >= MIN_OCTOBER_SAMPLES_FOR_COPULA:  # Need minimum observations for copula
                # Compute copula stress using historical October data
                gold["copula_supply_stress"] = compute_copula_stress(
                    inventory_days=gold["days_supply"],
                    utilization_pct=gold["utilization_pct"],
                    hurricane_prob=HURRICANE_PROB_OCTOBER,
                    historical_data=october_hist[["days_supply", "utilization_pct"]].dropna()
                )
                print("   ✓ Copula stress feature added successfully")
            else:
                print(f"   ⚠️  Insufficient October data ({len(october_hist)} obs) - skipping copula")
        except Exception as e:
            print(f"   ⚠️  Copula computation failed: {e}")
            print("   → Proceeding without copula feature")

    # === SEASONAL & TIMING FEATURES ===
    gold["weekday"] = gold.index.dayofweek
    gold["is_weekend"] = gold["weekday"].isin([5, 6]).astype(int)

    gold["winter_blend_effect"] = _winter_blend_curve(gold.index.to_series())
    oct1_dates = pd.to_datetime(gold.index.year.astype(str) + "-10-01")
    delta_days = pd.Series((gold.index - oct1_dates).days, index=gold.index)
    gold["days_since_oct1"] = delta_days.clip(lower=0)

    gold["target"] = gold["retail_price"]

    gold = gold.reset_index()

    # Drop rows without the target; these occur before retail data begins
    gold = gold.dropna(subset=["retail_price"])

    return gold


def save_outputs(gold: pd.DataFrame) -> None:
    """Persist the Gold layer datasets."""
    os.makedirs(GOLD_DIR, exist_ok=True)

    master_daily_path = GOLD_DIR / "master_daily.parquet"
    gold.to_parquet(master_daily_path, index=False)
    print(f"✓ Saved full daily panel: {master_daily_path}")

    gold_october = gold[gold["date"].dt.month == 10].copy()
    gold_october = gold_october[gold_october["date"] >= pd.Timestamp("2020-10-01")]
    master_october_path = GOLD_DIR / "master_october.parquet"
    gold_october.to_parquet(master_october_path, index=False)
    print(f"✓ Saved October subset: {master_october_path}")

    # Additional model-ready dataset with key features present
    required_features = [
        "price_rbob",
        "price_wti",
        "retail_price",
        "crack_spread",
        "retail_margin",
        "retail_margin_lag7",   # NEW: lagged retail margin (safe)
        "retail_margin_lag14",  # NEW: lagged retail margin (safe)
        "rbob_lag3",
        "rbob_lag7",
        "rbob_lag14",
        "delta_rbob_1w",
        "vol_rbob_10d",
        "rbob_momentum_7d",
    ]
    
    # Add optional features if they exist
    if "days_supply" in gold.columns:
        required_features.append("days_supply")
    if "util_inv_interaction" in gold.columns:
        required_features.append("util_inv_interaction")
    if "copula_supply_stress" in gold.columns:
        required_features.append("copula_supply_stress")
    
    model_ready = gold.dropna(subset=required_features).copy()
    
    # Validate copula feature if present
    if "copula_supply_stress" in model_ready.columns and COPULA_AVAILABLE:
        print("\n" + "=" * 80)
        print("VALIDATING COPULA FEATURE")
        print("=" * 80)
        try:
            from features.copula_supply_stress import validate_copula_feature, print_validation_report
            metrics = validate_copula_feature(model_ready, target="retail_price")
            print_validation_report(metrics)
        except Exception as e:
            print(f"⚠️  Copula validation failed: {e}")
    model_ready_path = GOLD_DIR / "master_model_ready.parquet"
    model_ready.to_parquet(model_ready_path, index=False)
    print(f"✓ Saved model-ready subset: {model_ready_path}")

    print("\nRows saved:")
    print(f"  Full panel: {len(gold):,}")
    print(f"  October only: {len(gold_october):,}")
    print(f"  Model-ready: {len(model_ready):,}")


def main() -> None:
    gold = build_gold_dataset()
    missing_core_cols = [col for col in ["price_rbob", "price_wti", "retail_price"] if col not in gold.columns]
    if missing_core_cols:
        raise RuntimeError(f"Gold dataset missing core columns: {missing_core_cols}")

    save_outputs(gold)

    print("\nNext steps:")
    print("  1. Run: python validate_gold_layer.py")
    print("  2. Begin feature selection / modeling notebooks\n")


if __name__ == "__main__":
    main()
