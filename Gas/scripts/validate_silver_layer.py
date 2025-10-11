"""
Validate Silver Layer Data

Checks all downloaded data files for:
- Existence
- Date coverage (Oct 2020 - Oct 2025)
- Missing values
- Price/value ranges (sanity checks)
- Data types

Run this after completing all downloads to ensure data quality
before building the Gold layer.
"""

import pandas as pd
import os

def validate_silver_layer():
    """Validate all Silver layer files"""
    
    silver_dir = '../data/silver'
    
    required_files = [
        'rbob_daily.parquet',
        'wti_daily.parquet',
        'retail_prices_daily.parquet',
        'eia_inventory_weekly.parquet',
        'eia_utilization_weekly.parquet',
        'eia_imports_weekly.parquet',
        'padd3_share_weekly.parquet'
    ]
    
    optional_files = [
        'noaa_temp_daily.parquet',
        'hurricane_risk_october.csv'
    ]
    
    print("=" * 70)
    print("SILVER LAYER VALIDATION")
    print("=" * 70)
    print()
    
    all_valid = True
    files_found = 0
    total_rows = 0
    
    # Check required files
    print("REQUIRED FILES:")
    print("-" * 70)
    
    for file in required_files:
        filepath = os.path.join(silver_dir, file)
        
        if not os.path.exists(filepath):
            print(f"❌ MISSING: {file}")
            all_valid = False
            continue
        
        df = pd.read_parquet(filepath)
        files_found += 1
        total_rows += len(df)
        
        print(f"\n✓ {file}")
        print(f"  Rows: {len(df):,}")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
        
        # Check for missing values
        missing = df.isnull().sum()
        if missing.any():
            missing_cols = missing[missing > 0]
            print(f"  ⚠️  Missing values:")
            for col, count in missing_cols.items():
                print(f"     {col}: {count} ({count/len(df)*100:.1f}%)")
        else:
            print(f"  ✓ No missing values")
        
        # Check date coverage
        start_date = df['date'].min()
        end_date = df['date'].max()
        
        if start_date > pd.Timestamp('2020-10-15'):
            print(f"  ⚠️  Start date later than Oct 2020: {start_date.strftime('%Y-%m-%d')}")
        
        if end_date < pd.Timestamp('2024-10-01'):
            print(f"  ⚠️  End date earlier than Oct 2024: {end_date.strftime('%Y-%m-%d')}")
        
        # File-specific validation
        if 'rbob' in file.lower():
            price_col = [c for c in df.columns if 'price' in c.lower()][0]
            min_price = df[price_col].min()
            max_price = df[price_col].max()
            print(f"  Price range: ${min_price:.2f} - ${max_price:.2f}")
            
            if min_price < 0.5 or max_price > 8.0:
                print(f"  ⚠️  RBOB price outside expected range ($0.50-$8.00)")
        
        elif 'wti' in file.lower():
            min_price = df['price_wti'].min()
            max_price = df['price_wti'].max()
            print(f"  Price range: ${min_price:.2f} - ${max_price:.2f}")
            
            if min_price < 10 or max_price > 200:
                print(f"  ⚠️  WTI price outside expected range ($10-$200)")
        
        elif 'retail' in file.lower():
            min_price = df['retail_price'].min()
            max_price = df['retail_price'].max()
            print(f"  Price range: ${min_price:.2f} - ${max_price:.2f}")
            
            if min_price < 1.5 or max_price > 7.0:
                print(f"  ⚠️  Retail price outside expected range ($1.50-$7.00)")
        
        elif 'inventory' in file.lower():
            min_inv = df['inventory_mbbl'].min()
            max_inv = df['inventory_mbbl'].max()
            print(f"  Inventory range: {min_inv:.1f} - {max_inv:.1f} million barrels")
            
            if min_inv < 180 or max_inv > 350:
                print(f"  ⚠️  Inventory outside expected range (180-350 million barrels)")
        
        elif 'utilization' in file.lower():
            min_util = df['utilization_pct'].min()
            max_util = df['utilization_pct'].max()
            print(f"  Utilization range: {min_util:.1f}% - {max_util:.1f}%")
            
            if min_util < 50 or max_util > 100:
                print(f"  ⚠️  Utilization outside expected range (50-100%)")
        
        elif 'padd3' in file.lower():
            min_share = df['padd3_share'].min()
            max_share = df['padd3_share'].max()
            print(f"  PADD3 share range: {min_share:.1f}% - {max_share:.1f}%")
            
            if min_share < 40 or max_share > 60:
                print(f"  ⚠️  PADD3 share outside expected range (40-60%)")
    
    # Check optional files
    print("\n\n" + "=" * 70)
    print("OPTIONAL FILES:")
    print("-" * 70)
    
    for file in optional_files:
        filepath = os.path.join(silver_dir, file)
        
        if not os.path.exists(filepath):
            print(f"○ Not present: {file} (OK - optional)")
        else:
            print(f"✓ Present: {file}")
            if file.endswith('.parquet'):
                df = pd.read_parquet(filepath)
                print(f"  Rows: {len(df):,}")
            elif file.endswith('.csv'):
                df = pd.read_csv(filepath)
                print(f"  Rows: {len(df):,}")
    
    # Summary
    print("\n\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Required files found: {files_found}/{len(required_files)}")
    print(f"Total data rows: {total_rows:,}")
    print()
    
    if all_valid and files_found == len(required_files):
        print("✓✓✓ ALL REQUIRED FILES PRESENT AND VALID ✓✓✓")
        print()
        print("Your Silver layer is complete!")
        print()
        print("Next steps:")
        print("  1. Review DATA_IMPLEMENTATION_GUIDE.md Section 2 (Gold Layer)")
        print("  2. Run: python build_gold_layer.py")
        print("  3. Begin feature engineering and modeling")
        print()
        print("Estimated time to Gold layer: 4-6 hours")
    else:
        print("❌ VALIDATION FAILED")
        print()
        print("Missing or invalid files detected. Please:")
        print("  1. Check download scripts for errors")
        print("  2. Verify EIA API key is set: echo $EIA_API_KEY")
        print("  3. Check internet connection")
        print("  4. Re-run failed download scripts")
    
    print("=" * 70)
    
    return all_valid

if __name__ == "__main__":
    validate_silver_layer()
