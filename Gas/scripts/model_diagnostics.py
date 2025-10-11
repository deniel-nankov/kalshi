"""
Generate Yellowbrick diagnostic plots for the Ridge baseline model.

Produces prediction error and residual plots using the train/test split
from the Gold model-ready dataset.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd

# Temporary bridge for Python >=3.12 where distutils is removed.
try:  # pragma: no cover
    import distutils  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover
    import importlib

    distutils_module = importlib.import_module("setuptools._distutils")
    distutils_version_module = importlib.import_module("setuptools._distutils.version")
    sys.modules["distutils"] = distutils_module
    sys.modules["distutils.version"] = distutils_version_module

try:
    from yellowbrick.regressor import PredictionError, ResidualsPlot
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "yellowbrick package is required for model_diagnostics.py. Install with `pip install yellowbrick`."
    ) from exc

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.baseline_models import (  # noqa: E402
    COMMON_FEATURES,
    load_model_ready_dataset,
    train_all_models,
    chronological_split,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Yellowbrick diagnostics for Ridge baseline.")
    parser.add_argument(
        "--data-path",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "gold" / "master_model_ready.parquet",
        help="Path to model-ready dataset.",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "models" / "ridge_baseline_model.joblib",
        help="Path to trained ridge model pipeline.",
    )
    parser.add_argument(
        "--test-start",
        type=str,
        default="2024-10-01",
        help="Date to start test split (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "model_diagnostics",
        help="Directory to save diagnostic figures.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_model_ready_dataset(args.data_path)
    splits = chronological_split(df, test_start=args.test_start)
    train_df, test_df = splits["train"], splits["test"]

    X_train, y_train = train_df[COMMON_FEATURES], train_df["retail_price"]
    X_test, y_test = test_df[COMMON_FEATURES], test_df["retail_price"]

    if not args.model_path.exists():
        print("Model file not found, re-training baseline …")
        train_all_models(df, output_dir=output_dir.parents[0], test_start=args.test_start)

    pipeline = joblib.load(args.model_path)

    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111)
    visualizer = PredictionError(pipeline, ax=ax, random_state=42)
    visualizer.fit(X_train, y_train)
    visualizer.score(X_test, y_test)
    visualizer.finalize()
    fig.savefig(output_dir / "prediction_error.png", dpi=160)
    plt.close(fig)

    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111)
    residual_viz = ResidualsPlot(pipeline, ax=ax, random_state=42)
    residual_viz.fit(X_train, y_train)
    residual_viz.score(X_test, y_test)
    residual_viz.finalize()
    fig.savefig(output_dir / "residuals_plot.png", dpi=160)
    plt.close(fig)

    print(f"✓ Yellowbrick diagnostics saved to {output_dir.resolve()}")


if __name__ == "__main__":
    main()
