"""
Clean RBOB and WTI data from Bronze → Silver Layer

This script performs data cleaning and standardization:
- Rename columns to consistent naming convention
- Convert data types (dates, prices)
- Select only needed columns
- Apply sanity checks and validation
- Standardize units

Bronze → Silver transformation
"""

from pathlib import Path
import pandas as pd

BRONZE_DIR = Path(__file__).resolve().parents[1] / "data" / "bronze"
SILVER_DIR = Path(__file__).resolve().parents[1] / "data" / "silver"


def clean_rbob_to_silver():
    """Clean raw RBOB data from Bronze → Silver"""
    
    print("Cleaning RBOB data: Bronze → Silver...")
    
    # Load raw bronze data
    bronze_path = BRONZE_DIR / 'rbob_daily_raw.parquet'
    if not bronze_path.exists():
        print(f"❌ ERROR: Bronze file not found: {bronze_path}")
        print("   Run: python download_rbob_data_bronze.py first")
        return None
    
    df = pd.read_parquet(bronze_path)
    
    print(f"  Loaded {len(df)} rows from Bronze")
    print(f"  Raw columns: {list(df.columns)}")
    
    # CLEANING TRANSFORMATIONS
    # 1. Rename columns to consistent convention
    df = df.rename(columns={
        'Date': 'date',
        'Close': 'price_rbob',
        'Volume': 'volume_rbob'
    })
    
    # 2. Select only needed columns
    df = df[['date', 'price_rbob', 'volume_rbob']]
    
    # 3. Convert data types
    df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
    df['price_rbob'] = df['price_rbob'].astype(float)
    df['volume_rbob'] = df['volume_rbob'].astype(float)
    
    # 4. Sanity checks (validation)
    assert df['price_rbob'].min() > 0.5, f"RBOB price too low: ${df['price_rbob'].min():.2f}"
    assert df['price_rbob'].max() < 8.0, f"RBOB price too high: ${df['price_rbob'].max():.2f}"
    assert len(df) > 1000, f"Too few observations: {len(df)} (expected >1000)"
    assert df['date'].is_monotonic_increasing or df['date'].is_monotonic_decreasing, "Dates not ordered"
    
    # 5. Remove duplicates if any
    original_len = len(df)
    df = df.drop_duplicates(subset=['date'])
    if len(df) < original_len:
        print(f"  ⚠️  Removed {original_len - len(df)} duplicate dates")
    
    # 6. Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    # Save to Silver
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    output_path = SILVER_DIR / 'rbob_daily.parquet'
    df.to_parquet(output_path, index=False)
    
    print(f"✓ Cleaned RBOB data saved to Silver")
    print(f"  Rows: {len(df)}")
    print(f"  Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"  Price range: ${df['price_rbob'].min():.2f} - ${df['price_rbob'].max():.2f}")
    print(f"  Saved to: {output_path}")
    
    return df


def clean_wti_to_silver():
    """Clean raw WTI data from Bronze → Silver"""
    
    print("\nCleaning WTI data: Bronze → Silver...")
    
    # Load raw bronze data
    bronze_path = BRONZE_DIR / 'wti_daily_raw.parquet'
    if not bronze_path.exists():
        print(f"❌ ERROR: Bronze file not found: {bronze_path}")
        print("   Run: python download_rbob_data_bronze.py first")
        return None
    
    df = pd.read_parquet(bronze_path)
    
    print(f"  Loaded {len(df)} rows from Bronze")
    
    # CLEANING TRANSFORMATIONS
    # 1. Rename columns
    df = df.rename(columns={
        'Date': 'date',
        'Close': 'price_wti'
    })
    
    # 2. Select only needed columns
    df = df[['date', 'price_wti']]
    
    # 3. Convert data types
    df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
    df['price_wti'] = df['price_wti'].astype(float)
    
    # 4. Sanity checks
    assert df['price_wti'].min() > 10, f"WTI price too low: ${df['price_wti'].min():.2f}"
    assert df['price_wti'].max() < 200, f"WTI price too high: ${df['price_wti'].max():.2f}"
    assert len(df) > 1000, f"Too few observations: {len(df)}"
    
    # 5. Remove duplicates
    original_len = len(df)
    df = df.drop_duplicates(subset=['date'])
    if len(df) < original_len:
        print(f"  ⚠️  Removed {original_len - len(df)} duplicate dates")
    
    # 6. Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    # Save to Silver
    output_path = SILVER_DIR / 'wti_daily.parquet'
    df.to_parquet(output_path, index=False)
    
    print(f"✓ Cleaned WTI data saved to Silver")
    print(f"  Rows: {len(df)}")
    print(f"  Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"  Price range: ${df['price_wti'].min():.2f} - ${df['price_wti'].max():.2f}")
    print(f"  Saved to: {output_path}")
    
    return df


def main():
    print("=" * 70)
    print("CLEANING FUTURES DATA: BRONZE → SILVER")
    print("=" * 70)
    print()
    
    # Check if bronze directory exists
    if not BRONZE_DIR.exists():
        print(f"❌ ERROR: Bronze directory not found: {BRONZE_DIR}")
        print("   Run download scripts first to populate Bronze layer")
        return
    
    # Clean both datasets
    rbob_df = clean_rbob_to_silver()
    wti_df = clean_wti_to_silver()
    
    print("\n" + "=" * 70)
    if rbob_df is not None and wti_df is not None:
        print("✓ FUTURES DATA CLEANED TO SILVER LAYER")
        print()
        print("Next steps:")
        print("  1. Run: python clean_retail_to_silver.py")
        print("  2. Run: python clean_eia_to_silver.py")
        print("  3. Run: python validate_silver_layer.py")
    else:
        print("❌ CLEANING FAILED - Please check errors above")
    print("=" * 70)


if __name__ == "__main__":
    main()
