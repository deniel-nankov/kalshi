"""
Convenience orchestrator for the core research pipeline.

Runs (in order):
    1. Build Gold layer
    2. Validate Gold layer
    3. Train baseline models
    4. Walk-forward validation
    5. Data freshness dashboard (PNG & GIF)

Usage:
    python run_pipeline.py [--skip-walkforward] [--skip-freshness]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def run_step(name: str, command: list[str]) -> None:
    print(f"\n=== {name} ===")
    result = subprocess.run(command, check=True)
    if result.returncode == 0:
        print(f"✓ {name} completed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run full gasoline forecasting pipeline")
    parser.add_argument("--skip-walkforward", action="store_true", help="Skip walk-forward validation step")
    parser.add_argument("--skip-freshness", action="store_true", help="Skip data freshness dashboard")
    parser.add_argument(
        "--horizon",
        type=int,
        default=0,
        help="Forecast horizon (in days) passed to train_models.py (default: 0).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    python = sys.executable

    steps = [
        ("Build Gold Layer", [python, str(SCRIPT_DIR / "build_gold_layer.py")]),
        ("Validate Gold Layer", [python, str(SCRIPT_DIR / "validate_gold_layer.py")]),
        (
            "Train Baseline Models",
            [
                python,
                str(SCRIPT_DIR / "train_models.py"),
                "--horizon",
                str(args.horizon),
            ],
        ),
    ]

    if not args.skip_walkforward:
        steps.append(
            ("Walk-Forward Validation", [python, str(SCRIPT_DIR / "walk_forward_validation.py")])
        )

    if not args.skip_freshness:
        steps.append(
            ("Data Freshness Dashboard", [python, str(SCRIPT_DIR / "report_data_freshness.py")])
        )

    for name, cmd in steps:
        run_step(name, cmd)

    print("\nPipeline complete. Check the outputs/ directory for artefacts.")


if __name__ == "__main__":
    main()
