"""Train quantile regression models and save metrics/predictions."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import sys
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.quantile_regression import load_dataset, train_quantile_models


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train quantile regression models.")
    parser.add_argument(
        "--data-path",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "gold" / "master_model_ready.parquet",
        help="Path to model-ready dataset",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "quantile_regression",
        help="Directory to save quantile regression artefacts",
    )
    parser.add_argument(
        "--test-start",
        type=str,
        default="2024-10-01",
        help="Date to start test split",
    )
    parser.add_argument(
        "--quantiles",
        nargs="*",
        type=float,
        default=[0.1, 0.5, 0.9],
        help="Quantiles to fit (default 0.1 0.5 0.9)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset = load_dataset(args.data_path)
    results = train_quantile_models(dataset, output_dir=args.output_dir, quantiles=args.quantiles, test_start=args.test_start)

    for q, res in results.items():
        print(f"Quantile {q}: train pinball {res.metrics['train']['pinball_loss']:.4f}, test pinball {res.metrics['test']['pinball_loss']:.4f}")
    print(f"\nArtefacts saved to {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
