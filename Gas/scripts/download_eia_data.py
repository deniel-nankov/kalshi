"""
Download EIA weekly petroleum data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from eia_client import EIAClient, EIAClientError, default_params

SILVER_DIR = Path(__file__).resolve().parents[1] / "data" / "silver"


def _save(df: pd.DataFrame, filename: str) -> Path:
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    path = SILVER_DIR / filename
    df.to_parquet(path, index=False)
    return path


def fetch_inventory(client: Optional[EIAClient] = None) -> pd.DataFrame:
    client = client or EIAClient()
    params = default_params("WGTSTUS1", frequency="weekly", start="2020-10-01")
    df = client.fetch("petroleum/stoc/wstk/data", params)
    if df.empty:
        raise EIAClientError("Fetched inventory data is empty. No data returned from EIA API.")
    df = df.assign(
        date=pd.to_datetime(df["period"]),
        inventory_mbbl=df["value"].astype(float) / 1000.0,
    )[["date", "inventory_mbbl"]].sort_values("date")

    if df["inventory_mbbl"].min() <= 180 or df["inventory_mbbl"].max() >= 350:
        raise EIAClientError("Inventory values outside expected range (180-350 million barrels).")
    return df


def fetch_utilization(client: Optional[EIAClient] = None) -> pd.DataFrame:
    client = client or EIAClient()
    params = default_params("WPULEUS3", frequency="weekly", start="2020-10-01")
    df = client.fetch("petroleum/pnp/wiup/data", params)
    if df.empty:
        raise EIAClientError("Fetched utilization data is empty. No data returned from EIA API.")
    df = df.assign(
        date=pd.to_datetime(df["period"]),
        utilization_pct=df["value"].astype(float),
    )[["date", "utilization_pct"]].sort_values("date")

    if df["utilization_pct"].min() <= 50 or df["utilization_pct"].max() >= 100:
        raise EIAClientError("Utilization percentage outside expected range (50-100%).")
    return df


def fetch_net_imports(client: Optional[EIAClient] = None) -> pd.DataFrame:
    client = client or EIAClient()
    imports_params = default_params("WGTIMUS2", frequency="weekly", start="2020-10-01")
    exports_params = default_params("W_EPM0F_EEX_NUS-Z00_MBBLD", frequency="weekly", start="2020-10-01")

    imports_df = client.fetch("petroleum/move/wkly/data", imports_params)
    exports_df = client.fetch("petroleum/move/wkly/data", exports_params)
    if imports_df.empty:
        raise EIAClientError("Fetched imports data is empty. No data returned from EIA API.")
    if exports_df.empty:
        raise EIAClientError("Fetched exports data is empty. No data returned from EIA API.")

    imports = imports_df.assign(
        date=pd.to_datetime(imports_df["period"]), imports=imports_df["value"].astype(float)
    )[["date", "imports"]]
    exports = exports_df.assign(
        date=pd.to_datetime(exports_df["period"]), exports=exports_df["value"].astype(float)
    )[["date", "exports"]]

    df = (
        imports.merge(exports, on="date", how="inner")
        .assign(net_imports_kbd=lambda x: x["imports"] - x["exports"])
        [["date", "net_imports_kbd"]]
        .sort_values("date")
    )
    if df.empty:
        raise EIAClientError("Merged net imports DataFrame is empty. No overlapping dates between imports and exports.")
    return df


def main() -> None:
    print("=" * 60)
    print("EIA DATA DOWNLOAD")
    print("=" * 60)

    try:
        inventory_df = fetch_inventory()
        inv_path = _save(inventory_df, "eia_inventory_weekly.parquet")
        print(f"✓ Inventory data saved to {inv_path}")

        util_df = fetch_utilization()
        util_path = _save(util_df, "eia_utilization_weekly.parquet")
        print(f"✓ Utilization data saved to {util_path}")

        imports_df = fetch_net_imports()
        imports_path = _save(imports_df, "eia_imports_weekly.parquet")
        print(f"✓ Net imports data saved to {imports_path}")

    except EIAClientError as err:
        print(f"✗ EIA download failed: {err}")
        return

    print("\n✅ EIA data download complete!")
    print(f"Files saved in: {SILVER_DIR}")


if __name__ == "__main__":
    main()
