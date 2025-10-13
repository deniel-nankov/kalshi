"""
Download EIA weekly petroleum data to Bronze Layer

Bronze layer = Raw API responses, exactly as received from EIA
Cleaning and standardization happens in the Silver layer processing script.

This script downloads:
- Gasoline inventory (stocks)
- Refinery utilization
- Imports/Exports
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from eia_client import EIAClient, EIAClientError, default_params

BRONZE_DIR = Path(__file__).resolve().parents[1] / "data" / "bronze"


def fetch_inventory_bronze(client: Optional[EIAClient] = None) -> pd.DataFrame:
    """Fetch raw inventory data - NO TRANSFORMATIONS"""
    client = client or EIAClient()
    params = default_params("WGTSTUS1", frequency="weekly", start="2020-10-01")
    df = client.fetch("petroleum/stoc/wstk/data", params)
    if df.empty:
        raise EIAClientError("Fetched inventory data is empty.")
    return df


def fetch_utilization_bronze(client: Optional[EIAClient] = None) -> pd.DataFrame:
    """Fetch raw utilization data - NO TRANSFORMATIONS"""
    client = client or EIAClient()
    params = default_params("WPULEUS3", frequency="weekly", start="2020-10-01")
    df = client.fetch("petroleum/pnp/wiup/data", params)
    if df.empty:
        raise EIAClientError("Fetched utilization data is empty.")
    return df


def fetch_imports_bronze(client: Optional[EIAClient] = None) -> pd.DataFrame:
    """Fetch raw imports data - NO TRANSFORMATIONS"""
    client = client or EIAClient()
    params = default_params("WGTIMUS2", frequency="weekly", start="2020-10-01")
    df = client.fetch("petroleum/move/wkly/data", params)
    if df.empty:
        raise EIAClientError("Fetched imports data is empty.")
    return df


def fetch_exports_bronze(client: Optional[EIAClient] = None) -> pd.DataFrame:
    """Fetch raw exports data - NO TRANSFORMATIONS"""
    client = client or EIAClient()
    params = default_params("W_EPM0F_EEX_NUS-Z00_MBBLD", frequency="weekly", start="2020-10-01")
    df = client.fetch("petroleum/move/wkly/data", params)
    if df.empty:
        raise EIAClientError("Fetched exports data is empty.")
    return df


def main() -> None:
    print("=" * 70)
    print("EIA DATA DOWNLOAD TO BRONZE LAYER")
    print("=" * 70)

    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    client = EIAClient()

    try:
        # Download inventory
        print("\n📦 Downloading gasoline inventory...")
        inventory = fetch_inventory_bronze(client)
        inv_path = BRONZE_DIR / "eia_inventory_raw.parquet"
        inventory.to_parquet(inv_path, index=False)
        print(f"✓ Inventory: {len(inventory)} records → {inv_path}")

        # Download utilization
        print("\n🏭 Downloading refinery utilization...")
        utilization = fetch_utilization_bronze(client)
        util_path = BRONZE_DIR / "eia_utilization_raw.parquet"
        utilization.to_parquet(util_path, index=False)
        print(f"✓ Utilization: {len(utilization)} records → {util_path}")

        # Download imports
        print("\n📥 Downloading imports...")
        imports = fetch_imports_bronze(client)
        imp_path = BRONZE_DIR / "eia_imports_raw.parquet"
        imports.to_parquet(imp_path, index=False)
        print(f"✓ Imports: {len(imports)} records → {imp_path}")

        # Download exports
        print("\n📤 Downloading exports...")
        exports = fetch_exports_bronze(client)
        exp_path = BRONZE_DIR / "eia_exports_raw.parquet"
        exports.to_parquet(exp_path, index=False)
        print(f"✓ Exports: {len(exports)} records → {exp_path}")

    except EIAClientError as err:
        print(f"✗ EIA download failed: {err}")
        return

    print("\n" + "=" * 70)
    print("✅ EIA data download to Bronze complete!")
    print()
    print("Next steps:")
    print("  1. Run: python clean_eia_to_silver.py")
    print("  2. Run: python download_padd3_data_bronze.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
