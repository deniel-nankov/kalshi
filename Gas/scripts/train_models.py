"""
Train baseline forecasting models and save evaluation artefacts.

Usage:
    python train_models.py [
        --data-path data/gold/master_model_ready.parquet
        --test-start 2024-10-01
        --output-dir outputs/models
    ]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.baseline_models import DEFAULT_DATA_PATH, load_model_ready_dataset, train_all_models


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train baseline gasoline forecasting models.")
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
        help="Date (YYYY-MM-DD) to start test split (default: 2024-10-01)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "models",
        help="Directory to save model artefacts (default: outputs/models)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_model_ready_dataset(args.data_path)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loaded dataset with {len(df):,} rows spanning {df['date'].min():%Y-%m-%d} → {df['date'].max():%Y-%m-%d}")
    results = train_all_models(df, output_dir=args.output_dir, test_start=args.test_start)

    summary_records = []
    for name, output in results.items():
        metrics_row = {
            "model": name,
            "train_rmse": output.metrics["train"]["rmse"],
            "test_rmse": output.metrics["test"]["rmse"],
            "train_mae": output.metrics["train"]["mae"],
            "test_mae": output.metrics["test"]["mae"],
            "train_r2": output.metrics["train"]["r2"],
            "test_r2": output.metrics["test"]["r2"],
            "train_mape_pct": output.metrics["train"]["mape_pct"],
            "test_mape_pct": output.metrics["test"]["mape_pct"],
        }
        if "best_alpha" in output.metrics:
            metrics_row["best_alpha"] = output.metrics["best_alpha"]
        summary_records.append(metrics_row)

    summary_df = pd.DataFrame(summary_records)
    summary_path = args.output_dir / "model_metrics_summary.csv"
    summary_df.to_csv(summary_path, index=False)

    summary_json_path = args.output_dir / "model_metrics_summary.json"
    summary_df.to_json(summary_json_path, orient="records", indent=2)

    print(f"Model training complete. Metrics saved to {summary_path} and {summary_json_path}")
    print(f"Artefacts available in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
