"""
Clean EIA data from Bronze → Silver Layer

This script performs data cleaning and standardization:
- Parse dates correctly
- Convert to consistent units (thousands → millions for inventory)
- Calculate net imports from imports/exports
- Apply sanity checks and validation
- Standardize column names

Bronze → Silver transformation
"""

from pathlib import Path
import pandas as pd

BRONZE_DIR = Path(__file__).resolve().parents[1] / "data" / "bronze"
SILVER_DIR = Path(__file__).resolve().parents[1] / "data" / "silver"


def clean_inventory_to_silver():
    """Clean raw inventory data from Bronze → Silver"""
    
    print("Cleaning Inventory: Bronze → Silver...")
    
    bronze_path = BRONZE_DIR / 'eia_inventory_raw.parquet'
    if not bronze_path.exists():
        print(f"❌ ERROR: Bronze file not found: {bronze_path}")
        return None
    
    df = pd.read_parquet(bronze_path)
    print(f"  Loaded {len(df)} rows from Bronze")
    
    # CLEANING TRANSFORMATIONS
    # 1. Parse dates and convert units (thousands → millions)
    df = df.assign(
        date=pd.to_datetime(df["period"]),
        inventory_mbbl=df["value"].astype(float) / 1000.0,  # thousands → millions
    )[["date", "inventory_mbbl"]].sort_values("date")
    
    # 2. Sanity checks
    min_val = df["inventory_mbbl"].min()
    max_val = df["inventory_mbbl"].max()
    assert min_val > 180, f"Inventory too low: {min_val:.1f} million barrels"
    assert max_val < 350, f"Inventory too high: {max_val:.1f} million barrels"
    
    # Save to Silver
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    output_path = SILVER_DIR / 'eia_inventory_weekly.parquet'
    df.to_parquet(output_path, index=False)
    
    print(f"✓ Cleaned inventory saved to Silver")
    print(f"  Rows: {len(df)}")
    print(f"  Range: {min_val:.1f} - {max_val:.1f} million barrels")
    print(f"  Saved to: {output_path}")
    
    return df


def clean_utilization_to_silver():
    """Clean raw utilization data from Bronze → Silver"""
    
    print("\nCleaning Utilization: Bronze → Silver...")
    
    bronze_path = BRONZE_DIR / 'eia_utilization_raw.parquet'
    if not bronze_path.exists():
        print(f"❌ ERROR: Bronze file not found: {bronze_path}")
        return None
    
    df = pd.read_parquet(bronze_path)
    print(f"  Loaded {len(df)} rows from Bronze")
    
    # CLEANING TRANSFORMATIONS
    df = df.assign(
        date=pd.to_datetime(df["period"]),
        utilization_pct=df["value"].astype(float),
    )[["date", "utilization_pct"]].sort_values("date")
    
    # Sanity checks
    min_val = df["utilization_pct"].min()
    max_val = df["utilization_pct"].max()
    assert min_val > 50, f"Utilization too low: {min_val:.1f}%"
    assert max_val < 100, f"Utilization too high: {max_val:.1f}%"
    
    # Save to Silver
    output_path = SILVER_DIR / 'eia_utilization_weekly.parquet'
    df.to_parquet(output_path, index=False)
    
    print(f"✓ Cleaned utilization saved to Silver")
    print(f"  Rows: {len(df)}")
    print(f"  Range: {min_val:.1f}% - {max_val:.1f}%")
    print(f"  Saved to: {output_path}")
    
    return df


def clean_imports_to_silver():
    """Clean raw imports/exports data and calculate net imports Bronze → Silver"""
    
    print("\nCleaning Imports/Exports: Bronze → Silver...")
    
    imports_path = BRONZE_DIR / 'eia_imports_raw.parquet'
    exports_path = BRONZE_DIR / 'eia_exports_raw.parquet'
    
    if not imports_path.exists() or not exports_path.exists():
        print(f"❌ ERROR: Bronze files not found")
        return None
    
    imports_df = pd.read_parquet(imports_path)
    exports_df = pd.read_parquet(exports_path)
    
    print(f"  Loaded {len(imports_df)} import records, {len(exports_df)} export records")
    
    # CLEANING TRANSFORMATIONS
    # 1. Parse and clean imports
    imports = imports_df.assign(
        date=pd.to_datetime(imports_df["period"]), 
        imports=imports_df["value"].astype(float)
    )[["date", "imports"]]
    
    # 2. Parse and clean exports
    exports = exports_df.assign(
        date=pd.to_datetime(exports_df["period"]), 
        exports=exports_df["value"].astype(float)
    )[["date", "exports"]]
    
    # 3. Merge and calculate net imports
    df = (
        imports.merge(exports, on="date", how="inner")
        .assign(net_imports_kbd=lambda x: x["imports"] - x["exports"])
        [["date", "net_imports_kbd"]]
        .sort_values("date")
    )
    
    if df.empty:
        print("❌ ERROR: No data after merging imports and exports")
        return None
    
    # Save to Silver
    output_path = SILVER_DIR / 'eia_imports_weekly.parquet'
    df.to_parquet(output_path, index=False)
    
    print(f"✓ Cleaned net imports saved to Silver")
    print(f"  Rows: {len(df)}")
    print(f"  Range: {df['net_imports_kbd'].min():.1f} - {df['net_imports_kbd'].max():.1f} kbd")
    print(f"  Saved to: {output_path}")
    
    return df


def main():
    print("=" * 70)
    print("CLEANING EIA DATA: BRONZE → SILVER")
    print("=" * 70)
    print()
    
    if not BRONZE_DIR.exists():
        print(f"❌ ERROR: Bronze directory not found: {BRONZE_DIR}")
        print("   Run download scripts first to populate Bronze layer")
        return
    
    # Clean all EIA datasets
    inventory = clean_inventory_to_silver()
    utilization = clean_utilization_to_silver()
    imports = clean_imports_to_silver()
    
    print("\n" + "=" * 70)
    if all([inventory is not None, utilization is not None, imports is not None]):
        print("✓ EIA DATA CLEANED TO SILVER LAYER")
        print()
        print("Next steps:")
        print("  1. Run: python clean_padd3_to_silver.py")
        print("  2. Run: python validate_silver_layer.py")
    else:
        print("❌ CLEANING FAILED - Please check errors above")
    print("=" * 70)


if __name__ == "__main__":
    main()
