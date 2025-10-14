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
import sys
import time
from typing import Optional

import pandas as pd
import yfinance as yf

BRONZE_DIR = Path(__file__).resolve().parents[1] / "data" / "bronze"


def _download_futures_bronze(
    symbol: str,
    name: str,
    output_filename: str,
    max_retries: int = 3
) -> Optional[pd.DataFrame]:
    """
    Shared logic for downloading futures data to Bronze layer with retry logic.
    
    Args:
        symbol: Yahoo Finance ticker symbol (e.g., 'RB=F', 'CL=F')
        name: Human-readable name for logging (e.g., 'RBOB', 'WTI crude')
        output_filename: Filename to save in Bronze directory
        max_retries: Number of retry attempts for transient failures
        
    Returns:
        DataFrame with raw data, or None if all retries failed
    """
    print(f"Downloading {name} futures ({symbol}) to Bronze layer...")
    
    ticker = yf.Ticker(symbol)
    
    # Download with retry logic and exponential backoff
    df = None
    for attempt in range(1, max_retries + 1):
        try:
            df = ticker.history(start="2020-10-01", end=pd.Timestamp.today())
            if len(df) > 0:
                break  # Success!
            else:
                print(f"   Attempt {attempt}/{max_retries}: No data returned")
        except Exception as e:
            print(f"   Attempt {attempt}/{max_retries} failed: {e}", file=sys.stderr)
        
        if attempt < max_retries:
            wait_time = 2 ** attempt  # Exponential backoff: 2s, 4s, 8s
            print(f"   Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    
    if df is None or len(df) == 0:
        print(f"❌ ERROR: Failed to download {name} data after all retries")
        print("   Check your internet connection or try again later")
        return None
    
    # Save RAW data - keep ALL columns from Yahoo Finance, NO transformations
    df = df.reset_index()
    
    # Save to bronze
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = BRONZE_DIR / output_filename
    df.to_parquet(output_path, index=False)
    
    print(f"✓ Downloaded {len(df)} days of raw {name} data")
    print(f"  Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"  Columns: {list(df.columns)}")
    print(f"  Saved to: {output_path}")
    
    return df


def download_rbob_futures_bronze():
    """Download raw RBOB gasoline futures from Yahoo Finance - NO TRANSFORMATIONS"""
    return _download_futures_bronze(
        symbol="RB=F",
        name="RBOB",
        output_filename="rbob_daily_raw.parquet"
    )


def download_wti_futures_bronze():
    """Download raw WTI crude futures from Yahoo Finance - NO TRANSFORMATIONS"""
    print()  # Add blank line for formatting
    return _download_futures_bronze(
        symbol="CL=F",
        name="WTI crude",
        output_filename="wti_daily_raw.parquet"
    )


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
