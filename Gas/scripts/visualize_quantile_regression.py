"""Generate visualizations to showcase quantile regression outputs."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualize quantile regression artefacts.")
    parser.add_argument(
        "--data-path",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "gold" / "master_model_ready.parquet",
        help="Path to model-ready dataset (for actual targets).",
    )
    parser.add_argument(
        "--qr-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "quantile_regression",
        help="Directory where quantile regression outputs were saved.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "quantile_regression",
        help="Directory to save figures (defaults to QR output directory).",
    )
    parser.add_argument(
        "--fan-chart-days",
        type=int,
        default=120,
        help="Number of most recent days to display in the fan chart.",
    )
    return parser.parse_args()


def load_quantile_predictions(qr_dir: Path) -> Dict[float, pd.DataFrame]:
    prediction_files = list(qr_dir.glob("quantile_*_predictions.csv"))
    if not prediction_files:
        raise FileNotFoundError(
            f"No quantile prediction files found in {qr_dir}. Run train_quantile_models.py first."
        )

    quantile_frames: Dict[float, pd.DataFrame] = {}
    for csv_file in prediction_files:
        quantile = int(csv_file.stem.split("_")[1]) / 100
        df = pd.read_csv(csv_file, parse_dates=["date"])
        quantile_frames[quantile] = df
    return quantile_frames


def plot_fan_chart(actual_df: pd.DataFrame, quantiles: Dict[float, pd.DataFrame], output_path: Path, window_days: int) -> None:
    merged = actual_df[["date", "retail_price"]].copy()
    for q, df in quantiles.items():
        pivot = df[df["split"] == "test"]["date"].to_frame()
        pivot[f"q{int(q*100)}"] = df[df["split"] == "test"]["prediction"].values
        merged = merged.merge(pivot, on="date", how="left")

    merged = merged.dropna(subset=[col for col in merged.columns if col.startswith("q")])
    merged = merged.sort_values("date")
    if window_days and len(merged) > window_days:
        merged = merged.iloc[-window_days:]

    plt.figure(figsize=(12, 6))
    plt.plot(merged["date"], merged["retail_price"], color="#1ABC9C", linewidth=2.5, label="Actual Retail")

    quantile_cols = sorted([col for col in merged.columns if col.startswith("q")])
    if len(quantile_cols) >= 2:
        lower = merged[quantile_cols[0]]
        upper = merged[quantile_cols[-1]]
        plt.fill_between(merged["date"], lower, upper, color="#F39C12", alpha=0.2, label=f"{quantile_cols[0][-2:]}–{quantile_cols[-1][-2:]} band")
    if "q50" in quantile_cols:
        plt.plot(merged["date"], merged["q50"], color="#D35400", linestyle="--", linewidth=2, label="Median Forecast")
    for col in quantile_cols:
        if col not in {"q50", quantile_cols[0], quantile_cols[-1]}:
            plt.plot(merged["date"], merged[col], linestyle=":", linewidth=1, alpha=0.7, label=f"{col.upper()}")

    plt.title("Quantile Regression Fan Chart (Test Period)")
    plt.xlabel("Date")
    plt.ylabel("$/gal")
    plt.grid(alpha=0.2)
    plt.legend(loc="upper left", ncol=2, fontsize=9)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def plot_pinball_bar(summary_csv: Path, output_path: Path) -> None:
    summary_df = pd.read_csv(summary_csv)
    summary_df = summary_df.sort_values("quantile")
    x = [f"{int(q*100)}" for q in summary_df["quantile"]]
    width = 0.35

    plt.figure(figsize=(8, 5))
    plt.bar(np.arange(len(x)) - width/2, summary_df["train_pinball"], width, color="#2980B9", label="Train")
    plt.bar(np.arange(len(x)) + width/2, summary_df["test_pinball"], width, color="#E74C3C", label="Test")
    plt.title("Pinball Loss by Quantile")
    plt.xlabel("Quantile (%)")
    plt.ylabel("Pinball Loss ($)")
    plt.xticks(np.arange(len(x)), x)
    plt.legend()
    plt.grid(alpha=0.2, axis="y")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def plot_quantile_residuals(actual_df: pd.DataFrame, quantiles: Dict[float, pd.DataFrame], output_path: Path) -> None:
    median_df = quantiles.get(0.5)
    if median_df is None:
        return
    median_test = median_df[median_df["split"] == "test"]
    merged = actual_df.merge(median_test[["date", "prediction"]], on="date", how="inner")
    merged["residual"] = merged["retail_price"] - merged["prediction"]

    plt.figure(figsize=(10, 5))
    plt.scatter(merged["prediction"], merged["residual"], alpha=0.5, color="#8E44AD", edgecolors="white", linewidths=0.3)
    plt.axhline(0, color="black", linestyle="--", linewidth=1)
    plt.title("Median Quantile Residuals (Actual - Q50)")
    plt.xlabel("Median Forecast ($/gal)")
    plt.ylabel("Residual ($/gal)")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def main() -> None:
    args = parse_args()
    actual_df = pd.read_parquet(args.data_path)[["date", "retail_price"]]
    actual_df["date"] = pd.to_datetime(actual_df["date"])

    quantiles = load_quantile_predictions(args.qr_dir)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    fan_chart_path = output_dir / "quantile_fan_chart.png"
    plot_fan_chart(actual_df, quantiles, fan_chart_path, window_days=args.fan_chart_days)

    summary_csv = args.qr_dir / "quantile_metrics_summary.csv"
    if summary_csv.exists():
        plot_pinball_bar(summary_csv, output_dir / "quantile_pinball_loss.png")

    plot_quantile_residuals(actual_df, quantiles, output_dir / "quantile_median_residuals.png")

    print(f"✓ Quantile regression visualizations saved to {output_dir.resolve()}")


if __name__ == "__main__":
    main()
