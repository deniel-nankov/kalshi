"""
Walk-forward validation harness for October gasoline forecasting.

This script evaluates baseline (Ridge) forecasts across multiple horizons and
years, producing metrics, prediction traces, and summary plots.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Dict, Iterable, List

import matplotlib.pyplot as plt
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.baseline_models import (  # noqa: E402
    COMMON_FEATURES,
    compute_metrics,
    load_model_ready_dataset,
    ridge_time_series_cv,
    train_ridge_model,
)


def create_horizon_dataset(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    df_sorted = df.sort_values("date").copy()
    target_col = f"target_h{horizon}"
    df_sorted[target_col] = df_sorted["retail_price"].shift(-horizon)
    df_sorted["target_date"] = df_sorted["date"] + pd.Timedelta(days=horizon)
    df_h = df_sorted.dropna(subset=[target_col]).reset_index(drop=True)
    return df_h


def walk_forward_forecasts(
    df: pd.DataFrame,
    horizons: Iterable[int],
    years: Iterable[int],
    output_dir: Path,
) -> Dict[str, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_records = []
    prediction_records = []

    for horizon in horizons:
        df_h = create_horizon_dataset(df, horizon)
        target_col = f"target_h{horizon}"
        horizon_dir = output_dir / f"horizon_{horizon}"
        horizon_dir.mkdir(parents=True, exist_ok=True)

        for year in years:
            start = pd.Timestamp(f"{year}-10-01")
            end = pd.Timestamp(f"{year}-10-31")

            train_mask = df_h["target_date"] < start
            test_mask = (df_h["target_date"] >= start) & (df_h["target_date"] <= end)

            train_df = df_h.loc[train_mask].copy()
            test_df = df_h.loc[test_mask].copy()

            if len(train_df) < 200 or test_df.empty:
                continue

            cv_results = ridge_time_series_cv(train_df, COMMON_FEATURES, target_col)
            best_alpha = cv_results["best_alpha"]
            if not cv_results["summary"].empty:
                cv_results["summary"].to_csv(
                    horizon_dir / f"ridge_cv_summary_{year}.csv",
                    index=False,
                )

            model = train_ridge_model(train_df, COMMON_FEATURES, target=target_col, alpha=best_alpha)
            preds = model.predict(test_df[COMMON_FEATURES])

            metrics = compute_metrics(test_df[target_col], preds)
            metrics.update(
                {
                    "year": year,
                    "horizon": horizon,
                    "best_alpha": best_alpha,
                    "n_train": len(train_df),
                    "n_test": len(test_df),
                }
            )
            metrics_records.append(metrics)

            for as_of_date, target_date, actual, pred in zip(
                test_df["date"],
                test_df["target_date"],
                test_df[target_col],
                preds,
            ):
                prediction_records.append(
                    {
                        "horizon": horizon,
                        "year": year,
                        "as_of_date": as_of_date,
                        "target_date": target_date,
                        "actual": actual,
                        "prediction": pred,
                    }
                )

    metrics_df = pd.DataFrame(metrics_records)
    predictions_df = pd.DataFrame(prediction_records)
    metrics_df.to_csv(output_dir / "walk_forward_metrics.csv", index=False)
    predictions_df.to_csv(output_dir / "walk_forward_predictions.csv", index=False)

    return {"metrics": metrics_df, "predictions": predictions_df}


def plot_walk_forward(predictions_df: pd.DataFrame, output_dir: Path) -> None:
    if predictions_df.empty or "horizon" not in predictions_df.columns:
        print("[WARN] No predictions to plot: predictions_df is empty or missing 'horizon' column.")
        # Optionally, create a placeholder artifact or just return
        return

    for horizon in sorted(predictions_df["horizon"].unique()):
        subset = predictions_df[predictions_df["horizon"] == horizon]
        if subset.empty:
            continue

        years = sorted(subset["year"].unique())
        n_years = len(years)
        cols = 3
        rows = (n_years + cols - 1) // cols
        fig, axes = plt.subplots(rows, cols, figsize=(cols * 4.5, rows * 3.5), sharey=True)
        axes = axes.flatten()

        for ax in axes:
            ax.set_visible(False)

        for idx, year in enumerate(years):
            ax = axes[idx]
            ax.set_visible(True)
            data = subset[subset["year"] == year].sort_values("target_date")
            ax.plot(data["target_date"], data["actual"], color="#1ABC9C", linewidth=2, label="Actual")
            ax.plot(data["target_date"], data["prediction"], color="#F39C12", linewidth=1.8, linestyle="--", label="Prediction")
            ax.set_title(f"{year}")
            ax.grid(alpha=0.2)
            ax.tick_params(axis="x", rotation=45)

        axes[0].legend(loc="upper left")
        fig.suptitle(f"Walk-Forward Forecasts – Horizon {horizon} days", fontsize=16)
        fig.tight_layout(rect=[0, 0, 1, 0.96])
        fig.savefig(output_dir / f"walk_forward_h{horizon}.png", dpi=160)
        plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Walk-forward validation for gasoline models")
    parser.add_argument(
        "--data-path",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "gold" / "master_model_ready.parquet",
        help="Path to Gold model-ready dataset",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "walk_forward",
        help="Directory to store walk-forward artefacts",
    )
    parser.add_argument(
        "--horizons",
        type=int,
        nargs="*",
        default=[21, 14, 7, 3, 1],
        help="Forecast horizons (days ahead)",
    )
    parser.add_argument(
        "--years",
        type=int,
        nargs="*",
        default=[2021, 2022, 2023, 2024],
        help="Years (October) to evaluate",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_model_ready_dataset(args.data_path)
    artefacts = walk_forward_forecasts(df, args.horizons, args.years, args.output_dir)
    plot_walk_forward(artefacts["predictions"], args.output_dir)
    print(f"✓ Walk-forward metrics saved to {args.output_dir / 'walk_forward_metrics.csv'}")
    print(f"✓ Walk-forward plots available under {args.output_dir}")


if __name__ == "__main__":
    main()
