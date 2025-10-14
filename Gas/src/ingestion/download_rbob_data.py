"""
Download RBOB Gasoline and WTI Crude Futures from Yahoo Finance

This script downloads daily futures prices for:
- RBOB Gasoline (RB=F) - wholesale gasoline benchmark
- WTI Crude Oil (CL=F) - crude oil benchmark

Used for features:
- RBOB_t-3, RBOB_t-7, RBOB_t-14 (lagged prices)
- CrackSpread (RBOB - WTI)
- Vol_RBOB_10d (rolling volatility)
- RBOB_Momentum_7d (7-day price change)
- Asymmetric_Δ (up vs down days)

Time: ~15 minutes
Cost: FREE
"""

from pathlib import Path
import sys
import time

import pandas as pd
import yfinance as yf

SILVER_DIR = Path(__file__).resolve().parents[1] / "data" / "silver"

def download_rbob_futures():
    """Download daily RBOB gasoline futures from Yahoo Finance with retry logic"""
    
    print("Downloading RBOB futures (RB=F)...")
    
    # RB=F is the front-month RBOB futures contract
    ticker = yf.Ticker("RB=F")
    
    # Download from Oct 2020 to present with retry logic
    df = None
    max_retries = 3
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
        print("❌ ERROR: Failed to download data after all retries")
        print("   Check your internet connection or try again later")
        return None
    
    # Clean and format
    df = df.reset_index()
    df = df.rename(columns={
        'Date': 'date',
        'Close': 'price_rbob',
        'Volume': 'volume_rbob'
    })
    
    # Keep only needed columns
    df = df[['date', 'price_rbob', 'volume_rbob']]
    df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
    
    # Convert to $/gallon (Yahoo gives $/gallon already for RB=F)
    # Sanity checks
    assert df['price_rbob'].min() > 0.5, f"RBOB price too low: ${df['price_rbob'].min():.2f}"
    assert df['price_rbob'].max() < 8.0, f"RBOB price too high: ${df['price_rbob'].max():.2f}"
    assert len(df) > 1000, f"Too few observations: {len(df)} (expected >1000)"
    
    # Save
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    output_path = SILVER_DIR / 'rbob_daily.parquet'
    df.to_parquet(output_path, index=False)
    
    print(f"✓ Downloaded {len(df)} days of RBOB data")
    print(f"  Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"  Price range: ${df['price_rbob'].min():.2f} - ${df['price_rbob'].max():.2f}")
    print(f"  Saved to: {output_path}")
    
    return df

def download_wti_futures():
    """Download daily WTI crude futures from Yahoo Finance with retry logic"""
    
    print("\nDownloading WTI crude futures (CL=F)...")
    
    ticker = yf.Ticker("CL=F")
    
    # Download with retry logic
    df = None
    max_retries = 3
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
        print("❌ ERROR: Failed to download data after all retries")
        print("   Check your internet connection or try again later")
        return None
    
    df = df.reset_index()
    df = df.rename(columns={
        'Date': 'date',
        'Close': 'price_wti'
    })
    
    df = df[['date', 'price_wti']]
    df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
    
    # Sanity checks
    assert df['price_wti'].min() > 10, f"WTI price too low: ${df['price_wti'].min():.2f}"
    assert df['price_wti'].max() < 200, f"WTI price too high: ${df['price_wti'].max():.2f}"
    assert len(df) > 1000, f"Too few observations: {len(df)}"
    
    output_path = SILVER_DIR / 'wti_daily.parquet'
    df.to_parquet(output_path, index=False)
    
    print(f"✓ Downloaded {len(df)} days of WTI data")
    print(f"  Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"  Price range: ${df['price_wti'].min():.2f} - ${df['price_wti'].max():.2f}")
    print(f"  Saved to: {output_path}")
    
    return df

def main():
    print("=" * 70)
    print("DOWNLOADING FUTURES DATA FROM YAHOO FINANCE")
    print("=" * 70)
    print()
    
    # Check if output directory exists
    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    # Download both datasets
    rbob_df = download_rbob_futures()
    wti_df = download_wti_futures()
    
    print("\n" + "=" * 70)
    if rbob_df is not None and wti_df is not None:
        print("✓ ALL FUTURES DATA DOWNLOADED SUCCESSFULLY")
        print()
        print("Next steps:")
        print("  1. Run: python download_retail_prices.py")
        print("  2. Run: python download_eia_data.py")
        print("  3. Run: python validate_silver_layer.py")
    else:
        print("❌ DOWNLOAD FAILED - Please check errors above")
    print("=" * 70)

if __name__ == "__main__":
    main()
