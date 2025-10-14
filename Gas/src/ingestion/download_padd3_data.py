"""
Download PADD3 (Gulf Coast) refinery capacity share from EIA.
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


def fetch_padd3_share(client: Optional[EIAClient] = None) -> pd.DataFrame:
    client = client or EIAClient()
    padd3_params = default_params("WGTSTP31", frequency="weekly", start="2020-10-01")
    total_params = default_params("WGTSTUS1", frequency="weekly", start="2020-10-01")

    padd3_df = client.fetch("petroleum/stoc/wstk/data", padd3_params)
    total_df = client.fetch("petroleum/stoc/wstk/data", total_params)
    if padd3_df.empty:
        raise EIAClientError("Fetched PADD3 stock data is empty. No data returned from EIA API.")
    if total_df.empty:
        raise EIAClientError("Fetched total stock data is empty. No data returned from EIA API.")

    padd3 = padd3_df.assign(
        date=pd.to_datetime(padd3_df["period"]), padd3_stock=padd3_df["value"].astype(float)
    )[["date", "padd3_stock"]]
    total = total_df.assign(
        date=pd.to_datetime(total_df["period"]), total_stock=total_df["value"].astype(float)
    )[["date", "total_stock"]]

    df = (
        padd3.merge(total, on="date", how="inner")
        .assign(padd3_share=lambda x: x["padd3_stock"] / x["total_stock"] * 100.0)
        [["date", "padd3_share"]]
        .sort_values("date")
    )
    if df.empty:
        raise EIAClientError("Merged PADD3 share DataFrame is empty. No overlapping dates between PADD3 and total stock series.")

    min_share = df["padd3_share"].min()
    max_share = df["padd3_share"].max()
    if min_share < 30 or max_share > 45:
        raise EIAClientError("PADD3 share outside expected 30%-45% band.")
    return df


def main() -> None:
    print("=" * 70)
    print("DOWNLOADING PADD3 REFINERY CAPACITY DATA FROM EIA")
    print("=" * 70)

    try:
        df = fetch_padd3_share()
    except EIAClientError as err:
        print(f"✗ PADD3 download failed: {err}")
        return

    path = _save(df, "padd3_share_weekly.parquet")
    print("✓ PADD3 data merged and saved")
    print(f"Records: {len(df)}")
    print(f"Date range: {df['date'].min():%Y-%m-%d} to {df['date'].max():%Y-%m-%d}")
    print(f"PADD3 share range: {df['padd3_share'].min():.1f}% - {df['padd3_share'].max():.1f}%")
    print(f"Saved to: {path}")
    print("=" * 70)
    print("Next step: python validate_silver_layer.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
