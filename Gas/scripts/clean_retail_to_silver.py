"""
Clean Retail Prices data from Bronze → Silver Layer

This script performs data cleaning and standardization:
- Parse dates correctly
- Convert to consistent units
- Forward-fill weekly data to daily frequency
- Apply sanity checks and validation
- Standardize column names

Bronze → Silver transformation
"""

from pathlib import Path
import pandas as pd

BRONZE_DIR = Path(__file__).resolve().parents[1] / "data" / "bronze"
SILVER_DIR = Path(__file__).resolve().parents[1] / "data" / "silver"


def clean_retail_to_silver():
    """Clean raw retail price data from Bronze → Silver"""
    
    print("Cleaning Retail Prices: Bronze → Silver...")
    
    # Load raw bronze data
    bronze_path = BRONZE_DIR / 'retail_prices_raw.parquet'
    if not bronze_path.exists():
        print(f"❌ ERROR: Bronze file not found: {bronze_path}")
        print("   Run: python download_retail_prices_bronze.py first")
        return None
    
    weekly = pd.read_parquet(bronze_path)
    
    print(f"  Loaded {len(weekly)} rows from Bronze")
    print(f"  Raw columns: {list(weekly.columns)}")
    
    # CLEANING TRANSFORMATIONS
    # 1. Parse dates and rename columns
    weekly = weekly.assign(
        date=pd.to_datetime(weekly["period"]),
        retail_price=weekly["value"].astype(float),
    )[["date", "retail_price"]].sort_values("date")
    
    # 2. Forward-fill weekly data to daily frequency for modeling
    full_range = pd.date_range(
        weekly["date"].min(), 
        pd.Timestamp.today().normalize(), 
        freq="D"
    )
    
    daily = (
        weekly.set_index("date")
        .reindex(full_range)
        .rename_axis("date")
        .ffill()
        .bfill()
        .reset_index()
    )
    
    # 3. Sanity checks (validation)
    min_price = daily["retail_price"].min()
    max_price = daily["retail_price"].max()
    
    assert min_price >= 1.5, f"Retail price too low: ${min_price:.2f}"
    assert max_price <= 7.0, f"Retail price too high: ${max_price:.2f}"
    assert len(daily) > 1000, f"Too few observations: {len(daily)}"
    
    # Save to Silver
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    output_path = SILVER_DIR / 'retail_prices_daily.parquet'
    daily.to_parquet(output_path, index=False)
    
    print(f"✓ Cleaned retail prices saved to Silver")
    print(f"  Weekly records: {len(weekly)}")
    print(f"  Daily records (forward-filled): {len(daily)}")
    print(f"  Date range: {daily['date'].min().strftime('%Y-%m-%d')} to {daily['date'].max().strftime('%Y-%m-%d')}")
    print(f"  Price range: ${min_price:.2f} - ${max_price:.2f}")
    print(f"  Saved to: {output_path}")
    
    return daily


def main():
    print("=" * 70)
    print("CLEANING RETAIL PRICES: BRONZE → SILVER")
    print("=" * 70)
    print()
    
    # Check if bronze directory exists
    if not BRONZE_DIR.exists():
        print(f"❌ ERROR: Bronze directory not found: {BRONZE_DIR}")
        print("   Run download scripts first to populate Bronze layer")
        return
    
    # Clean dataset
    df = clean_retail_to_silver()
    
    print("\n" + "=" * 70)
    if df is not None:
        print("✓ RETAIL PRICES CLEANED TO SILVER LAYER")
        print()
        print("Next steps:")
        print("  1. Run: python clean_eia_to_silver.py")
        print("  2. Run: python validate_silver_layer.py")
    else:
        print("❌ CLEANING FAILED - Please check errors above")
    print("=" * 70)


if __name__ == "__main__":
    main()
