"""
Download Daily Retail Gasoline Prices from EIA.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from .eia_client import EIAClient, EIAClientError, default_params

SILVER_DIR = Path(__file__).resolve().parents[1] / "data" / "silver"


def _save(df: pd.DataFrame, filename: str) -> Path:
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    path = SILVER_DIR / filename
    df.to_parquet(path, index=False)
    return path


def fetch_retail_prices(client: Optional[EIAClient] = None) -> pd.DataFrame:
    """
    Fetch U.S. regular gasoline retail prices ($/gal) as a daily DataFrame.

    Data source: EIA Weekly Retail Gasoline and Diesel Prices (gnd route).
    Weekly observations are forward-filled to daily frequency for modeling.
    """
    client = client or EIAClient()
    params = default_params("EMM_EPMR_PTE_NUS_DPG", frequency="weekly", start="2020-10-01")
    params.pop("facets[series][]", None)
    params["facets[duoarea][]"] = "NUS"
    params["facets[product][]"] = "EPMR"  # Regular gasoline
    weekly = client.fetch("petroleum/pri/gnd/data", params)
    weekly = weekly.assign(
        date=pd.to_datetime(weekly["period"]),
        retail_price=weekly["value"].astype(float),
    )[["date", "retail_price"]].sort_values("date")

    if weekly.empty:
        raise EIAClientError("No retail gasoline data returned from EIA.")

    full_range = pd.date_range(weekly["date"].min(), pd.Timestamp.today().normalize(), freq="D")
    daily = (
        weekly.set_index("date")
        .reindex(full_range)
        .rename_axis("date")
        .ffill()
        .bfill()
        .reset_index()
    )

    min_price = daily["retail_price"].min()
    max_price = daily["retail_price"].max()
    if min_price < 1.5 or max_price > 7.0:
        raise EIAClientError("Retail prices outside expected range ($1.50-$7.00).")
    return daily


def main() -> None:
    print("=" * 70)
    print("DOWNLOADING RETAIL GASOLINE PRICES FROM EIA")
    print("=" * 70)

    try:
        df = fetch_retail_prices()
    except EIAClientError as err:
        print(f"✗ Retail price download failed: {err}")
        return

    path = _save(df, "retail_prices_daily.parquet")
    print("✓ Download successful!")
    print(f"Records: {len(df)}")
    print(f"Date range: {df['date'].min():%Y-%m-%d} to {df['date'].max():%Y-%m-%d}")
    print(f"Price range: ${df['retail_price'].min():.2f} - ${df['retail_price'].max():.2f}")
    print(f"Saved to: {path}")
    print("=" * 70)
    print("Next steps:")
    print("  1. Run: python download_eia_data.py")
    print("  2. Run: python download_padd3_data.py")
    print("  3. Run: python validate_silver_layer.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
