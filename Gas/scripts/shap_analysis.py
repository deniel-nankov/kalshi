"""
Generate SHAP explanations for the baseline Ridge model.

This script loads the trained ridge pipeline, computes SHAP values on a sample
of the Gold model-ready dataset, and saves a suite of interpretability plots.

Outputs (default): Gas/outputs/interpretability/shap_*.png
"""

from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
try:
    import shap
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "shap package is required for shap_analysis.py. Install with `pip install shap`."
    ) from exc

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.baseline_models import COMMON_FEATURES, load_model_ready_dataset  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate SHAP explanations for Ridge baseline.")
    parser.add_argument(
        "--data-path",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "gold" / "master_model_ready.parquet",
        help="Path to Gold model-ready dataset.",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "models" / "ridge_model.pkl",
        help="Path to trained ridge model.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "interpretability",
        help="Directory to store SHAP figures.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=1500,
        help="Number of rows to sample for SHAP analysis (to limit compute).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_model_ready_dataset(args.data_path)
    if not COMMON_FEATURES:
        raise RuntimeError("COMMON_FEATURES list is empty.")

    X = df[COMMON_FEATURES]
    sample_n = min(args.sample_size, len(X))
    X_sample = X.sample(n=sample_n, random_state=42)

    if not args.model_path.exists():
        raise FileNotFoundError(f"Model file not found: {args.model_path}")
    
    with open(args.model_path, 'rb') as f:
        model = pickle.load(f)

    print(f"Creating SHAP explainer on {sample_n:,} samples …")
    explainer = shap.Explainer(model.predict, X_sample, algorithm="auto")
    shap_values = explainer(X_sample)

    print("Saving SHAP plots …")
    plt.figure(figsize=(10, 6))
    shap.plots.bar(shap_values, show=False)
    plt.title("SHAP Feature Importance (Mean |SHAP|)")
    plt.tight_layout()
    plt.savefig(output_dir / "shap_feature_importance_bar.png", dpi=160)
    plt.close()

    plt.figure(figsize=(10, 6))
    shap.plots.beeswarm(shap_values, show=False, max_display=20)
    plt.title("SHAP Beeswarm Plot")
    plt.tight_layout()
    plt.savefig(output_dir / "shap_beeswarm.png", dpi=160)
    plt.close()

    top_feature = COMMON_FEATURES[np.argmax(np.abs(shap_values.values).mean(axis=0))]
    plt.figure(figsize=(8, 6))
    shap.plots.scatter(shap_values[:, top_feature], color=shap_values, show=False)
    plt.title(f"SHAP Dependence Plot – {top_feature}")
    plt.tight_layout()
    plt.savefig(output_dir / f"shap_dependence_{top_feature}.png", dpi=160)
    plt.close()

    print(f"✓ SHAP analysis complete. Figures saved to {output_dir.resolve()}")


if __name__ == "__main__":
    main()
