"""
Train baseline models using October-only data to assess seasonal sensitivity.

Usage:
    python train_models_october_only.py --horizon 21
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.baseline_models import (  # noqa: E402
    DEFAULT_DATA_PATH,
    load_model_ready_dataset,
    train_all_models,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train models using October-only historical data.")
    parser.add_argument(
        "--data-path",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help="Path to master_model_ready.parquet (default: data/gold/master_model_ready.parquet)",
    )
    parser.add_argument(
        "--test-start",
        type=str,
        default="2024-10-01",
        help="Date to begin the test period (default: 2024-10-01).",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=21,
        help="Forecast horizon in days (default: 21).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "models_october_only",
        help="Directory to save artefacts (default: outputs/models_october_only).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_model_ready_dataset(args.data_path)
    df["date"] = pd.to_datetime(df["date"])
    october_data = df[df["date"].dt.month == 10].copy()

    if october_data.empty:
        raise RuntimeError("No October observations found in dataset.")

    args.output_dir = args.output_dir / f"horizon_{args.horizon}"
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"October rows available: {len(october_data):,}")
    print(f"Training horizon: {args.horizon} day(s) ahead")

    results = train_all_models(
        october_data,
        output_dir=args.output_dir,
        test_start=args.test_start,
        horizon=args.horizon,
    )

    summary_records = []
    for name, output in results.items():
        row = {
            "model": name,
            "train_rmse": output.metrics["train"]["rmse"],
            "test_rmse": output.metrics["test"]["rmse"],
            "train_mae": output.metrics["train"]["mae"],
            "test_mae": output.metrics["test"]["mae"],
            "train_r2": output.metrics["train"]["r2"],
            "test_r2": output.metrics["test"]["r2"],
            "train_mape_pct": output.metrics["train"]["mape_pct"],
            "test_mape_pct": output.metrics["test"]["mape_pct"],
            "horizon_days": args.horizon,
        }
        if "best_alpha" in output.metrics:
            row["best_alpha"] = output.metrics["best_alpha"]
        summary_records.append(row)

    summary_df = pd.DataFrame(summary_records)
    summary_path = args.output_dir / "october_only_metrics.csv"
    summary_df.to_csv(summary_path, index=False)

    print("\nOctober-only model evaluation complete.")
    print(f"Summary saved to: {summary_path}")
    print("\n📊 Metrics:")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
