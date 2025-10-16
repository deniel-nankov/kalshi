"""
Evaluate model robustness across multiple October holdout periods.

Usage:
    python multi_period_validation.py --horizon 21 --years 2021 2022 2023 2024
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Dict, List

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.baseline_models import DEFAULT_DATA_PATH, load_model_ready_dataset, train_all_models  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run multi-period October validation.")
    parser.add_argument(
        "--data-path",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help="Path to master_model_ready.parquet",
    )
    parser.add_argument(
        "--years",
        type=int,
        nargs="+",
        default=[2021, 2022, 2023, 2024],
        help="October years to evaluate",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=21,
        help="Forecast horizon in days (default: 21)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "multi_period_validation",
        help="Directory to store artefacts (default: outputs/multi_period_validation)",
    )
    return parser.parse_args()


def collect_metrics_summary(records: List[Dict[str, float]]) -> pd.DataFrame:
    summary = (
        pd.DataFrame(records)
        .groupby("model")
        .agg(
            test_r2_mean=("test_r2", "mean"),
            test_r2_std=("test_r2", "std"),
            test_rmse_mean=("test_rmse", "mean"),
            test_rmse_std=("test_rmse", "std"),
            horizon_days=("horizon_days", "max"),
            n_periods=("year", "nunique"),
        )
        .reset_index()
    )
    return summary


def main() -> None:
    args = parse_args()
    df = load_model_ready_dataset(args.data_path)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    records: List[Dict[str, float]] = []

    for year in args.years:
        year_dir = args.output_dir / f"year_{year}"
        year_dir.mkdir(parents=True, exist_ok=True)

        test_start = f"{year}-10-01"
        cutoff = pd.Timestamp(f"{year}-11-01")
        subset = df[df["date"] < cutoff].copy()
        if subset.empty:
            print(f"[WARN] No observations before {cutoff.date()} – skipping {year}.")
            continue

        results = train_all_models(
            subset,
            output_dir=year_dir,
            test_start=test_start,
            horizon=args.horizon,
        )

        for name, output in results.items():
            records.append(
                {
                    "model": name,
                    "year": year,
                    "test_r2": output.metrics["test"]["r2"],
                    "test_rmse": output.metrics["test"]["rmse"],
                    "horizon_days": args.horizon,
                }
            )

    if not records:
        raise RuntimeError("No validation records produced. Check dataset coverage and year arguments.")

    detailed_df = pd.DataFrame(records)
    detailed_path = args.output_dir / "detailed_metrics.csv"
    detailed_df.to_csv(detailed_path, index=False)

    summary_df = collect_metrics_summary(records)
    summary_path = args.output_dir / "summary_metrics.csv"
    summary_df.to_csv(summary_path, index=False)

    print("Multi-period validation complete.")
    print(f"Detailed metrics saved to: {detailed_path}")
    print(f"Summary metrics saved to: {summary_path}")
    print("\n📊 Summary:")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
