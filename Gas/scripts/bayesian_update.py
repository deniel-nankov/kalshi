"""Bayesian updating of the Oct 31, 2025 forecast as new observation days arrive."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import sys
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.bayesian_update import load_dataset, produce_forecast  # noqa: E402

DEFAULT_UPDATES = [10, 16, 23, 30]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bayesian forecast updates for October 31, 2025")
    parser.add_argument(
        "--data-path",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "gold" / "master_model_ready.parquet",
        help="Path to Gold model-ready dataset",
    )
    parser.add_argument(
        "--updates",
        nargs="*",
        type=int,
        default=DEFAULT_UPDATES,
        help="Day-of-month observation dates (default: 10 16 23 30)",
    )
    parser.add_argument(
        "--tau2",
        type=float,
        default=5.0,
        help="Prior variance scale for coefficients (default 5.0)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "bayesian_updates",
        help="Directory to save update summaries",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_dataset(args.data_path)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    results_json = []
    for day in sorted(set(args.updates)):
        try:
            forecast = produce_forecast(df, observation_day=day, tau2=args.tau2)
        except Exception as exc:  # pragma: no cover
            print(f"Warning: could not compute forecast for day {day}: {exc}")
            continue

        record = {
            "update_date": forecast.update_date,
            "point_forecast": forecast.mean,
            "variance": forecast.variance,
            "lower_80": forecast.lower_80,
            "upper_80": forecast.upper_80,
            "lower_95": forecast.lower_95,
            "upper_95": forecast.upper_95,
            "sigma2": forecast.sigma2,
            "training_years": forecast.training_years,
        }
        results_json.append(record)

        individual_path = output_dir / f"bayesian_update_{forecast.update_date}.json"
        individual_path.write_text(json.dumps(record, indent=2))
        print(json.dumps(record, indent=2))

    all_path = output_dir / "bayesian_updates_summary.json"
    all_path.write_text(json.dumps(results_json, indent=2))
    print(f"\n✓ Bayesian update summaries saved to {output_dir.resolve()}")


if __name__ == "__main__":
    main()
