"""
Generate animated visualizations that illustrate how the pipeline transforms
raw (silver) data into the forward-filled gold layer.

Outputs:
    - Gas/outputs/silver_gold_prices.gif
    - Gas/outputs/silver_gold_fundamentals.gif

The price animation highlights the smoother daily series produced in the gold
layer. The fundamentals animation shows weekly inventory/utilization data being
forward-filled to a daily calendar for modelling.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.dates as mdates
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
SILVER_DIR = REPO_ROOT / "data" / "silver"
GOLD_DIR = REPO_ROOT / "data" / "gold"
OUTPUT_DIR = REPO_ROOT / "outputs"


def load_price_data() -> pd.DataFrame:
    retail_silver = pd.read_parquet(SILVER_DIR / "retail_prices_daily.parquet")
    rbob_silver = pd.read_parquet(SILVER_DIR / "rbob_daily.parquet")[["date", "price_rbob"]]
    gold = pd.read_parquet(GOLD_DIR / "master_daily.parquet")[["date", "retail_price", "price_rbob"]]

    merged = (
        retail_silver.merge(rbob_silver, on="date", how="left", suffixes=("_retail_silver", "_rbob_silver"))
        .merge(
            gold.rename(columns={"retail_price": "retail_price_gold", "price_rbob": "price_rbob_gold"}),
            on="date",
            how="left",
        )
    )

    merged = merged.sort_values("date").set_index("date")
    recent = merged.iloc[-180:]  # last ~6 months to keep animation crisp
    return recent.reset_index()


def animate_transition(df: pd.DataFrame, output_path: Path) -> None:
    plt.style.use("seaborn-v0_8-darkgrid")
    fig, ax = plt.subplots(figsize=(10, 5))

    line_retail_silver, = ax.plot([], [], color="tab:orange", alpha=0.6, label="Retail (Silver)")
    line_retail_gold, = ax.plot([], [], color="tab:red", linewidth=2.0, label="Retail (Gold)")
    line_rbob_silver, = ax.plot([], [], color="tab:blue", alpha=0.5, label="RBOB (Silver)")
    line_rbob_gold, = ax.plot([], [], color="navy", linewidth=1.5, linestyle="--", label="RBOB (Gold)")

    ax.set_title("Silver → Gold Transition: Retail vs Wholesale Prices")
    ax.set_ylabel("$/gallon")
    ax.set_xlabel("Date")
    ax.legend(loc="upper left")

    dates = df["date"]
    y_min = min(df[["retail_price", "retail_price_gold", "price_rbob", "price_rbob_gold"]].min()) - 0.1
    y_max = max(df[["retail_price", "retail_price_gold", "price_rbob", "price_rbob_gold"]].max()) + 0.1
    ax.set_ylim(y_min, y_max)

    def update(frame: int):
        current = df.iloc[: frame + 1]
        line_retail_silver.set_data(current["date"], current["retail_price"])
        line_retail_gold.set_data(current["date"], current["retail_price_gold"])
        line_rbob_silver.set_data(current["date"], current["price_rbob"])
        line_rbob_gold.set_data(current["date"], current["price_rbob_gold"])
        ax.set_xlim(dates.iloc[0], dates.iloc[-1])
        return (
            line_retail_silver,
            line_retail_gold,
            line_rbob_silver,
            line_rbob_gold,
        )

    frames = len(df)
    animation = FuncAnimation(fig, update, frames=frames, interval=60, blit=True)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    animation.save(output_path, writer="pillow", dpi=120)
    plt.close(fig)


def load_fundamental_data() -> pd.DataFrame:
    inventory_silver = pd.read_parquet(SILVER_DIR / "eia_inventory_weekly.parquet")
    utilization_silver = pd.read_parquet(SILVER_DIR / "eia_utilization_weekly.parquet")

    gold = pd.read_parquet(GOLD_DIR / "master_daily.parquet")[["date", "inventory_mbbl", "utilization_pct"]]
    gold = gold.sort_values("date")

    combined = gold.merge(
        inventory_silver.rename(columns={"inventory_mbbl": "inventory_weekly"}),
        on="date",
        how="left",
    ).merge(
        utilization_silver.rename(columns={"utilization_pct": "utilization_weekly"}),
        on="date",
        how="left",
    )

    recent = combined.iloc[-180:]  # last ~6 months
    return recent.reset_index(drop=True)


def animate_fundamentals(df: pd.DataFrame, output_path: Path) -> None:
    plt.style.use("seaborn-v0_8-darkgrid")
    fig, ax1 = plt.subplots(figsize=(10, 5))

    line_inv_gold, = ax1.plot([], [], color="tab:purple", linewidth=2.0, label="Inventory (Gold)")
    scatter_inv_silver = ax1.scatter([], [], color="tab:purple", marker="o", s=35, alpha=0.7, label="Inventory (Silver)")

    ax2 = ax1.twinx()
    line_util_gold, = ax2.plot([], [], color="tab:green", linewidth=2.0, label="Utilization (Gold)")
    scatter_util_silver = ax2.scatter([], [], color="tab:green", marker="x", s=35, alpha=0.7, label="Utilization (Silver)")

    ax1.set_title("Silver → Gold Transition: Fundamentals Forward-Fill")
    ax1.set_ylabel("Inventory (million bbl)")
    ax2.set_ylabel("Utilization (%)")

    dates = df["date"]
    ax1.set_xlim(dates.iloc[0], dates.iloc[-1])
    ax1.set_ylim(df["inventory_mbbl"].min() - 2, df["inventory_mbbl"].max() + 2)
    ax2.set_ylim(df["utilization_pct"].min() - 2, df["utilization_pct"].max() + 2)

    inv_handles = [line_inv_gold, scatter_inv_silver]
    util_handles = [line_util_gold, scatter_util_silver]
    handles = inv_handles + util_handles
    labels = [h.get_label() for h in handles]
    ax1.legend(handles, labels, loc="upper left")

    def update(frame: int):
        current = df.iloc[: frame + 1]

        line_inv_gold.set_data(current["date"], current["inventory_mbbl"])
        inv_points = current.dropna(subset=["inventory_weekly"])
        if inv_points.empty:
            scatter_inv_silver.set_offsets(np.empty((0, 2)))
        else:
            coords = np.column_stack(
                [mdates.date2num(inv_points["date"]), inv_points["inventory_weekly"]]
            )
            scatter_inv_silver.set_offsets(coords)

        line_util_gold.set_data(current["date"], current["utilization_pct"])
        util_points = current.dropna(subset=["utilization_weekly"])
        if util_points.empty:
            scatter_util_silver.set_offsets(np.empty((0, 2)))
        else:
            coords = np.column_stack(
                [mdates.date2num(util_points["date"]), util_points["utilization_weekly"]]
            )
            scatter_util_silver.set_offsets(coords)

        return line_inv_gold, scatter_inv_silver, line_util_gold, scatter_util_silver

    frames = len(df)
    animation = FuncAnimation(fig, update, frames=frames, interval=60, blit=True)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    animation.save(output_path, writer="pillow", dpi=120)
    plt.close(fig)


def main() -> None:
    price_df = load_price_data()
    if price_df.empty:
        raise RuntimeError("No price data available to animate. Run data downloads first.")
    animate_transition(price_df, OUTPUT_DIR / "silver_gold_prices.gif")
    print(f"✓ Price animation saved to {OUTPUT_DIR / 'silver_gold_prices.gif'}")

    fundamentals_df = load_fundamental_data()
    if fundamentals_df.empty:
        raise RuntimeError("No fundamentals data available to animate. Run data downloads first.")
    animate_fundamentals(fundamentals_df, OUTPUT_DIR / "silver_gold_fundamentals.gif")
    print(f"✓ Fundamentals animation saved to {OUTPUT_DIR / 'silver_gold_fundamentals.gif'}")


if __name__ == "__main__":
    main()
