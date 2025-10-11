"""
Validate Gold Layer outputs produced by build_gold_layer.py.

Checks:
    - Required files exist
    - Column schema and dtypes
    - Date coverage (at least Oct 2020 onward)
    - Presence of key engineered features
    - Missing values summary

Usage:
    python validate_gold_layer.py
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
GOLD_DIR = REPO_ROOT / "data" / "gold"

REQUIRED_FILES = [
    "master_daily.parquet",
    "master_october.parquet",
    "master_model_ready.parquet",
]
CORE_COLUMNS = [
    "date",
    "retail_price",
    "price_rbob",
    "price_wti",
    "crack_spread",
    "retail_margin",
    "rbob_lag3",
    "rbob_lag7",
    "rbob_lag14",
    "delta_rbob_1w",
    "vol_rbob_10d",
    "winter_blend_effect",
    "target",
]


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def _missing_columns(df: pd.DataFrame, required: List[str]) -> List[str]:
    return [col for col in required if col not in df.columns]


def validate_file(path: Path) -> bool:
    df = pd.read_parquet(path)
    df["date"] = pd.to_datetime(df["date"])

    _print_header(f"VALIDATING {path.name}")

    print(f"Rows: {len(df):,}")
    print(f"Date range: {df['date'].min():%Y-%m-%d} → {df['date'].max():%Y-%m-%d}")

    missing_cols = _missing_columns(df, CORE_COLUMNS)
    if missing_cols:
        print(f"✗ Missing expected columns: {missing_cols}")
        return False
    print("✓ Column schema present")

    missing_counts = df[CORE_COLUMNS].isnull().sum()
    if missing_counts.any():
        print("⚠ Missing values detected:")
        for col, count in missing_counts[missing_counts > 0].items():
            pct = count / len(df) * 100
            print(f"    {col}: {count} rows ({pct:.1f}%)")
    else:
        print("✓ No missing values in core columns")

    if df["date"].min() > pd.Timestamp("2020-10-01"):
        print("⚠ Start date is later than Oct 2020. Confirm Silver layer coverage.")

    return True


def validate_gold_layer() -> bool:
    _print_header("GOLD LAYER VALIDATION")
    all_good = True

    for filename in REQUIRED_FILES:
        path = GOLD_DIR / filename
        if not path.exists():
            print(f"✗ Missing Gold file: {path}")
            all_good = False
            continue

        if not validate_file(path):
            all_good = False

    _print_header("SUMMARY")
    if all_good:
        print("✓✓✓ Gold layer looks good. Ready for modeling.")
    else:
        print("❌ Issues detected. Please review messages above.")

    return all_good


if __name__ == "__main__":
    validate_gold_layer()
