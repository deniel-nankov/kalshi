"""
Download Daily Retail Gasoline Prices from EIA to Bronze Layer

Bronze layer = Raw API responses, exactly as received from EIA
Cleaning and standardization happens in the Silver layer processing script.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from .eia_client import EIAClient, EIAClientError, default_params

BRONZE_DIR = Path(__file__).resolve().parents[1] / "data" / "bronze"


def fetch_retail_prices_bronze(client: Optional[EIAClient] = None) -> pd.DataFrame:
    """
    Fetch U.S. regular gasoline retail prices from EIA - RAW DATA ONLY
    
    No transformations, just save what comes from the API.
    """
    client = client or EIAClient()
    params = default_params("EMM_EPMR_PTE_NUS_DPG", frequency="weekly", start="2020-10-01")
    params.pop("facets[series][]", None)
    params["facets[duoarea][]"] = "NUS"
    params["facets[product][]"] = "EPMR"  # Regular gasoline
    
    # Fetch raw data
    weekly = client.fetch("petroleum/pri/gnd/data", params)
    
    if weekly.empty:
        raise EIAClientError("No retail gasoline data returned from EIA.")
    
    return weekly


def main() -> None:
    print("=" * 70)
    print("DOWNLOADING RAW RETAIL PRICES TO BRONZE LAYER")
    print("=" * 70)

    try:
        df = fetch_retail_prices_bronze()
    except EIAClientError as err:
        print(f"✗ Retail price download failed: {err}")
        return

    # Save RAW data with ALL columns from API
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    path = BRONZE_DIR / "retail_prices_raw.parquet"
    df.to_parquet(path, index=False)
    
    print("✓ Download successful!")
    print(f"Records: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(f"Saved to: {path}")
    print("=" * 70)
    print("Next steps:")
    print("  1. Run: python clean_retail_to_silver.py")
    print("  2. Run: python download_eia_data_bronze.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
