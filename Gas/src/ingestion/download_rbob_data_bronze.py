"""
Download RBOB Gasoline and WTI Crude Futures from Yahoo Finance to Bronze Layer

This script downloads raw daily futures prices with NO transformations:
- RBOB Gasoline (RB=F) - wholesale gasoline benchmark
- WTI Crude Oil (CL=F) - crude oil benchmark

Bronze layer = Raw API responses, exactly as received from Yahoo Finance
Cleaning and standardization happens in the Silver layer processing script.

Time: ~15 minutes
Cost: FREE
"""

from pathlib import Path
import pandas as pd
import yfinance as yf

BRONZE_DIR = Path(__file__).resolve().parents[1] / "data" / "bronze"


def download_rbob_futures_bronze():
    """Download raw RBOB gasoline futures from Yahoo Finance - NO TRANSFORMATIONS"""
    
    print("Downloading RBOB futures (RB=F) to Bronze layer...")
    
    # RB=F is the front-month RBOB futures contract
    ticker = yf.Ticker("RB=F")
    
    # Download from Oct 2020 to present
    df = ticker.history(start="2020-10-01", end=pd.Timestamp.today())
    
    if len(df) == 0:
        print("❌ ERROR: No data returned from Yahoo Finance")
        print("   Check your internet connection or try again later")
        return None
    
    # Save RAW data - keep ALL columns from Yahoo Finance, NO renaming
    df = df.reset_index()
    
    # Save to bronze
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = BRONZE_DIR / 'rbob_daily_raw.parquet'
    df.to_parquet(output_path, index=False)
    
    print(f"✓ Downloaded {len(df)} days of raw RBOB data")
    print(f"  Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"  Columns: {list(df.columns)}")
    print(f"  Saved to: {output_path}")
    
    return df


def download_wti_futures_bronze():
    """Download raw WTI crude futures from Yahoo Finance - NO TRANSFORMATIONS"""
    
    print("\nDownloading WTI crude futures (CL=F) to Bronze layer...")
    
    ticker = yf.Ticker("CL=F")
    df = ticker.history(start="2020-10-01", end=pd.Timestamp.today())
    
    if len(df) == 0:
        print("❌ ERROR: No data returned from Yahoo Finance")
        return None
    
    # Save RAW data - keep ALL columns
    df = df.reset_index()
    
    output_path = BRONZE_DIR / 'wti_daily_raw.parquet'
    df.to_parquet(output_path, index=False)
    
    print(f"✓ Downloaded {len(df)} days of raw WTI data")
    print(f"  Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"  Columns: {list(df.columns)}")
    print(f"  Saved to: {output_path}")
    
    return df


def main():
    print("=" * 70)
    print("DOWNLOADING RAW FUTURES DATA TO BRONZE LAYER")
    print("=" * 70)
    print()
    
    # Check if output directory exists
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)

    # Download both datasets
    rbob_df = download_rbob_futures_bronze()
    wti_df = download_wti_futures_bronze()
    
    print("\n" + "=" * 70)
    if rbob_df is not None and wti_df is not None:
        print("✓ ALL RAW FUTURES DATA DOWNLOADED TO BRONZE LAYER")
        print()
        print("Next steps:")
        print("  1. Run: python clean_rbob_to_silver.py  (to clean Bronze → Silver)")
        print("  2. Run: python download_retail_prices_bronze.py")
        print("  3. Run: python download_eia_data_bronze.py")
    else:
        print("❌ DOWNLOAD FAILED - Please check errors above")
    print("=" * 70)


if __name__ == "__main__":
    main()
