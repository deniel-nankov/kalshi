"""Run asymmetric pass-through regression and save outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

import sys
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.asymmetric_pass_through import load_dataset, run_full_analysis


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Behavioral pricing (asymmetric pass-through) regression analysis")
    parser.add_argument(
        "--data-path",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "gold" / "master_model_ready.parquet",
        help="Path to model-ready dataset",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "asym_pass_through",
        help="Directory to save regression outputs",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_dataset(args.data_path)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    result = run_full_analysis(df)

    metrics_path = output_dir / "asym_metrics.json"
    summary_path = output_dir / "asym_summary.txt"
    result.model.save(output_dir / "asym_model.pkl")
    import json
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(result.metrics, f, indent=2)
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(result.summary)

    print(f"✓ Asymmetric pass-through analysis saved to {output_dir.resolve()}")


if __name__ == "__main__":
    main()
