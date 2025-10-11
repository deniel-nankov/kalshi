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
    - master_daily.parquet       # Daily panel with engineered features
    - master_october.parquet     # Filtered October observations (2020 onward)

The feature engineering mirrors the architecture blueprint:
    * Align daily and weekly series on a common calendar
    * Forward-fill weekly fundamentals
    * Create pass-through lags, spreads, and seasonal markers
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
SILVER_DIR = REPO_ROOT / "data" / "silver"
GOLD_DIR = REPO_ROOT / "data" / "gold"


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


def _winter_blend_curve(dates: pd.Series, decay: float = 0.2) -> pd.Series:
    """
    Smooth transition function for the October blend switch.
    Returns zeros before Oct 1 of each year and decays thereafter.
    """
    october_start = pd.to_datetime(dates.dt.year.astype(str) + "-10-01")
    days_since = (dates - october_start).dt.days.clip(lower=0)
    return -0.12 * (1 - np.exp(-decay * days_since))


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

    gold["crack_spread"] = gold["price_rbob"] - gold["price_wti"]
    gold["retail_margin"] = gold["retail_price"] - gold["price_rbob"]
    gold["rbob_lag3"] = gold["price_rbob"].shift(3)
    gold["rbob_lag7"] = gold["price_rbob"].shift(7)
    gold["rbob_lag14"] = gold["price_rbob"].shift(14)
    gold["delta_rbob_1w"] = gold["price_rbob"] - gold["price_rbob"].shift(7)
    gold["rbob_return_1d"] = gold["price_rbob"].pct_change()
    gold["vol_rbob_10d"] = gold["rbob_return_1d"].rolling(10).std()

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
    model_ready = gold.dropna(
        subset=[
            "price_rbob",
            "price_wti",
            "retail_price",
            "crack_spread",
            "retail_margin",
            "rbob_lag3",
            "rbob_lag7",
            "rbob_lag14",
            "delta_rbob_1w",
            "vol_rbob_10d",
        ]
    ).copy()
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
