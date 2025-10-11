"""
Generate a high-impact dashboard that showcases data recency across all Silver
layer inputs. The report blends spotlight charts, recency gauges, and a
color-coded scoreboard so stakeholders can instantly verify that the latest
feeds are flowing into the ML pipeline.

Outputs:
    Gas/outputs/data_freshness_report.png
    Gas/outputs/data_freshness_report.gif
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
from matplotlib import gridspec
import pandas as pd
from PIL import Image

plt.style.use("dark_background")


REPO_ROOT = Path(__file__).resolve().parents[1]
SILVER_DIR = REPO_ROOT / "data" / "silver"
OUTPUT_DIR = REPO_ROOT / "outputs"


DATASETS: List[Dict[str, str]] = [
    {"label": "Retail Price ($/gal)", "file": "retail_prices_daily.parquet", "column": "retail_price", "freq": "D"},
    {"label": "RBOB Futures ($/gal)", "file": "rbob_daily.parquet", "column": "price_rbob", "freq": "D"},
    {"label": "WTI Futures ($/bbl)", "file": "wti_daily.parquet", "column": "price_wti", "freq": "D"},
    {"label": "Gasoline Inventory (M bbl)", "file": "eia_inventory_weekly.parquet", "column": "inventory_mbbl", "freq": "W"},
    {"label": "Refinery Utilization (%)", "file": "eia_utilization_weekly.parquet", "column": "utilization_pct", "freq": "W"},
    {"label": "Net Imports (kbd)", "file": "eia_imports_weekly.parquet", "column": "net_imports_kbd", "freq": "W"},
    {"label": "PADD3 Share (%)", "file": "padd3_share_weekly.parquet", "column": "padd3_share", "freq": "W"},
]


def load_dataset(meta: Dict[str, str]) -> pd.DataFrame:
    path = SILVER_DIR / meta["file"]
    if not path.exists():
        raise FileNotFoundError(f"Silver file missing: {path}")

    df = pd.read_parquet(path)
    df = df[["date", meta["column"]]].dropna()
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date")


def status_color(freq: str, recency_days: int) -> str:
    if freq == "D":
        if recency_days <= 2:
            return "#1ABC9C"
        if recency_days <= 4:
            return "#F1C40F"
        return "#E74C3C"
    if recency_days <= 8:
        return "#1ABC9C"
    if recency_days <= 15:
        return "#F1C40F"
    return "#E74C3C"


def collect_dataset_info():
    dataset_info = []
    for meta in DATASETS:
        try:
            df = load_dataset(meta)
        except FileNotFoundError:
            dataset_info.append(
                {
                    "meta": meta,
                    "df": None,
                    "recent": None,
                    "latest_date": None,
                    "latest_value": None,
                    "rows": 0,
                    "recency_days": float("inf"),
                    "status": "#E74C3C",
                }
            )
            continue

        latest_date = df["date"].max()
        latest_value = df[meta["column"]].iloc[-1]
        rows = len(df)
        recency_days = (pd.Timestamp.today().normalize() - latest_date.normalize()).days
        status = status_color(meta["freq"], recency_days)
        lookback = "45D" if meta["freq"] == "D" else "150D"
        recent = df[df["date"] >= latest_date - pd.Timedelta(lookback)]

        dataset_info.append(
            {
                "meta": meta,
                "df": df,
                "recent": recent,
                "latest_date": latest_date,
                "latest_value": latest_value,
                "rows": rows,
                "recency_days": recency_days,
                "status": status,
            }
        )
    return dataset_info


def render_dashboard(dataset_info, highlight_idx: int | None = None) -> plt.Figure:
    fig = plt.figure(figsize=(14, 12))
    fig.patch.set_facecolor("#06080F")
    gs = gridspec.GridSpec(5, 2, figure=fig, height_ratios=[1, 1, 1, 1, 1.5], hspace=0.55, wspace=0.28)
    chart_axes = [fig.add_subplot(gs[r, c]) for r in range(4) for c in range(2)]
    scoreboard_ax = fig.add_subplot(gs[4, :])

    summary_rows = []

    for idx, info in enumerate(dataset_info):
        ax = chart_axes[idx]
        ax.set_facecolor("#0F1A25")
        meta = info["meta"]

        if info["df"] is None:
            ax.axis("off")
            ax.text(0.5, 0.5, "Missing data", ha="center", va="center", fontsize=12, color="#E74C3C")
            summary_rows.append(
                {
                    "Dataset": meta["label"],
                    "Latest Date": "Missing",
                    "Recency (days)": "∞",
                    "Rows": 0,
                    "Frequency": meta["freq"],
                    "Status": "#E74C3C",
                }
            )
            continue

        df = info["df"]
        recent = info["recent"]
        latest_date = info["latest_date"]
        latest_value = info["latest_value"]
        rows = info["rows"]
        recency_days = info["recency_days"]
        status = info["status"]

        summary_rows.append(
            {
                "Dataset": meta["label"],
                "Latest Date": latest_date.strftime("%Y-%m-%d"),
                "Recency (days)": recency_days,
                "Rows": rows,
                "Frequency": meta["freq"],
                "Status": status,
            }
        )

        is_highlight = idx == highlight_idx
        base_color = "#58D68D" if is_highlight else ("#3498DB" if meta["freq"] == "D" else "#9B59B6")
        fill_alpha = 0.32 if is_highlight else 0.18

        ax.plot(df["date"], df[meta["column"]], color="#2C3E50", linewidth=1.1, alpha=0.6)
        ax.fill_between(df["date"], df[meta["column"]], color="#17202A", alpha=0.2)
        ax.plot(recent["date"], recent[meta["column"]], color=base_color, linewidth=3 if is_highlight else 2.5, alpha=0.95)
        ax.fill_between(recent["date"], recent[meta["column"]], color=base_color, alpha=fill_alpha)
        ax.scatter(latest_date, latest_value, s=150 if is_highlight else 110, color=status, edgecolor="white", linewidth=1.3, zorder=5)

        ax.annotate(
            f"{latest_value:,.2f}",
            xy=(latest_date, latest_value),
            xytext=(12, 18 if is_highlight else 12),
            textcoords="offset points",
            fontsize=12 if is_highlight else 10,
            color="#FDFEFE",
            bbox=dict(
                boxstyle="round,pad=0.35",
                fc="#0E6655" if status == "#1ABC9C" else "#7D6608",
                ec="none",
                alpha=0.92,
            ),
        )

        title_color = "#FDFEFE" if is_highlight else "#ECF0F1"
        ax.set_title(meta["label"], fontsize=13 if is_highlight else 12, color=title_color, pad=12)
        ax.set_ylabel(meta["column"], color="#AAB7B8")
        ax.set_xlim(df["date"].min(), df["date"].max())
        ax.grid(alpha=0.12)
        ax.tick_params(colors="#AAB7B8")

    for j in range(len(dataset_info), len(chart_axes)):
        chart_axes[j].axis("off")

    scoreboard_ax.axis("off")
    summary_df = pd.DataFrame(summary_rows)
    summary_df = summary_df.sort_values("Dataset")
    display_df = summary_df.copy()
    display_df["Recency (days)"] = display_df["Recency (days)"].astype(str)
    columns = ["Dataset", "Latest Date", "Recency (days)", "Rows", "Frequency"]

    table = scoreboard_ax.table(
        cellText=display_df[columns].values,
        colLabels=columns,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.15, 1.35)

    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#102A43")
            cell.set_text_props(color="white", weight="bold")
        else:
            color = summary_df.iloc[row - 1]["Status"]
            cell.set_facecolor(color)
            cell.set_text_props(color="white" if color != "#F1C40F" else "black", weight="bold")
            if highlight_idx is not None and summary_df.iloc[row - 1]["Dataset"] == dataset_info[highlight_idx]["meta"]["label"]:
                cell.set_edgecolor("#FDFEFE")
                cell.set_linewidth(2.0)

    scoreboard_ax.set_title(
        f"Freshness Summary — generated {pd.Timestamp.today().strftime('%Y-%m-%d %H:%M')}",
        fontsize=14,
        color="#ECF0F1",
        pad=20,
    )

    fig.suptitle(
        "Silver Layer Recency Dashboard",
        fontsize=20,
        fontweight="bold",
        color="#FDFEFE",
        y=0.99,
    )
    fig.text(
        0.5,
        0.965,
        "Green = fresh; Yellow = monitor; Red = refresh required",
        ha="center",
        fontsize=12,
        color="#F7F9F9",
    )
    return fig


def save_animation(dataset_info):
    frames: List[Image.Image] = []
    highlight_sequence = list(range(len(dataset_info))) + [None]

    for highlight in highlight_sequence:
        fig = render_dashboard(dataset_info, highlight)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        frame = Image.open(buf).convert("RGB")
        frames.append(frame)

    gif_path = OUTPUT_DIR / "data_freshness_report.gif"
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=900, loop=0)
    return gif_path


def generate_report() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset_info = collect_dataset_info()

    final_fig = render_dashboard(dataset_info, highlight_idx=None)
    png_path = OUTPUT_DIR / "data_freshness_report.png"
    final_fig.savefig(png_path, dpi=170, bbox_inches="tight")
    plt.close(final_fig)

    gif_path = save_animation(dataset_info)
    print(f"✓ Animated dashboard saved to {gif_path}")

    return png_path


def main() -> None:
    report_path = generate_report()
    print(f"✓ Data freshness report saved to {report_path}")


if __name__ == "__main__":
    main()
