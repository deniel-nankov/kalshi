"""Generate visualizations for asymmetric pass-through analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualize asymmetric pass-through results")
    parser.add_argument(
        "--data-path",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "gold" / "master_model_ready.parquet",
        help="Path to model-ready dataset",
    )
    parser.add_argument(
        "--asym-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "asym_pass_through",
        help="Directory containing asymmetrics outputs",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "asym_pass_through",
        help="Directory to save plots",
    )
    return parser.parse_args()


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["rbob_change"] = df["price_rbob"].diff()
    df["rbob_up"] = df["rbob_change"].clip(lower=0)
    df["rbob_down"] = df["rbob_change"].clip(upper=0)
    df["retail_change"] = df["retail_price"].diff()
    df = df.dropna().reset_index(drop=True)
    return df


def scatter_plot(df: pd.DataFrame, output_path: Path) -> None:
    plt.figure(figsize=(8, 5))
    plt.scatter(df["rbob_up"], df["retail_change"], color="#E74C3C", alpha=0.6, label="Wholesale up", edgecolors="white", linewidths=0.3)
    plt.scatter(np.abs(df["rbob_down"]), df["retail_change"], color="#3498DB", alpha=0.6, label="Wholesale down", edgecolors="white", linewidths=0.3)
    plt.xlabel("Wholesale change ($/gal)")
    plt.ylabel("Retail change ($/gal)")
    plt.title("Retail response to positive vs. negative wholesale moves")
    plt.grid(alpha=0.2)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def bar_plot(metrics_json: Path, output_path: Path) -> None:
    import json
    metrics = json.loads(metrics_json.read_text())
    coef_up = metrics.get("coef_up", np.nan)
    coef_down = metrics.get("coef_down", np.nan)
    errors = [metrics.get("p_up", np.nan), metrics.get("p_down", np.nan)]

    plt.figure(figsize=(6, 4))
    bars = plt.bar(["Wholesale up", "Wholesale down"], [coef_up, coef_down], color=["#E74C3C", "#3498DB"])
    plt.ylabel("Estimated pass-through coefficient")
    plt.title("Asymmetric pass-through coefficients")
    for bar, pval in zip(bars, errors):
        label = f"p={pval:.3f}" if isinstance(pval, (float, int)) else ""
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), label, ha="center", va="bottom")
    plt.grid(axis="y", alpha=0.2)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def time_series_heatmap(df: pd.DataFrame, output_path: Path) -> None:
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M")
    grouped = df.groupby("month").agg({"rbob_up": "mean", "rbob_down": "mean", "retail_change": "mean"}).reset_index()
    grouped["month"] = grouped["month"].astype(str)
    pivot = grouped.pivot_table(index="month", values=["rbob_up", "rbob_down", "retail_change"])

    plt.figure(figsize=(8, 6))
    plt.imshow(pivot.T, aspect="auto", cmap="coolwarm")
    plt.yticks(range(len(pivot.columns)), ["Wholesale up", "Wholesale down", "Retail change"])
    plt.xticks(range(len(pivot.index)), pivot.index, rotation=90)
    plt.colorbar(label="Average change ($/gal)")
    plt.title("Monthly average pass-through dynamics")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.data_path)
    df["date"] = pd.to_datetime(df["date"])
    engineered = engineer_features(df)

    scatter_plot(engineered, output_dir / "asym_scatter.png")
    time_series_heatmap(engineered, output_dir / "asym_heatmap.png")

    metrics_json = args.asym_dir / "asym_metrics.json"
    if metrics_json.exists():
        bar_plot(metrics_json, output_dir / "asym_coef_bar.png")

    print(f"✓ Asymmetric pass-through visuals saved to {output_dir.resolve()}")


if __name__ == "__main__":
    main()
