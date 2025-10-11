"""
Download Daily Retail Gasoline Prices from EIA

This script downloads U.S. national average retail gasoline prices
(regular grade) from the EIA API.

Used for:
- Target variable (October 31, 2025 forecast)
- RetailMargin feature (Retail - RBOB)
- Model calibration and validation

Time: ~15 minutes
Cost: FREE (requires EIA API key)
API Key: https://www.eia.gov/opendata/register.php
"""

import pandas as pd
import requests
import os

def download_aaa_retail_prices():
    """
    Download daily retail gasoline prices from EIA
    (EIA aggregates AAA and other sources)
    """
    
    print("=" * 70)
    print("DOWNLOADING RETAIL GASOLINE PRICES FROM EIA")
    print("=" * 70)
    print()
    
    # Get API key from environment
    API_KEY = os.environ.get('EIA_API_KEY')
    
    if not API_KEY:
        print("❌ ERROR: EIA_API_KEY not set!")
        print()
        print("To fix this:")
        print("  1. Register for free API key: https://www.eia.gov/opendata/register.php")
        print("  2. Set environment variable:")
        print("     export EIA_API_KEY='your_key_here'")
        print()
        print("Then run this script again.")
        return None
    
    print(f"Using API key: {API_KEY[:10]}...")
    print()
    
    # Series ID for U.S. Regular Gasoline Retail Price ($/gal)
    series_id = "PET.EMM_EPM0_PTE_NUS_DPG.D"
    
    print(f"Fetching series: {series_id}")
    print("Description: U.S. Regular All Formulations Retail Gasoline Prices ($/gal)")
    print()
    
    url = f"https://api.eia.gov/v2/petroleum/pri/gnd/data/?api_key={API_KEY}&data[0]=value&facets[series][]={series_id}&frequency=daily&start=2020-10-01"
    
    print("Making API request...")
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"❌ ERROR: API returned status code {response.status_code}")
        print(f"Message: {response.text}")
        print()
        print("Possible causes:")
        print("  - Invalid API key")
        print("  - Rate limit exceeded (5000 calls/day)")
        print("  - EIA server issues")
        return None
    
    data = response.json()
    
    # Check for errors in response
    if 'response' not in data:
        print(f"❌ ERROR: Unexpected response format")
        print(f"Response: {data}")
        return None
    
    if 'data' not in data['response']:
        print(f"❌ ERROR: No data in response")
        print(f"Response: {data['response']}")
        return None
    
    # Parse
    df = pd.DataFrame(data['response']['data'])
    
    if len(df) == 0:
        print("❌ ERROR: No data returned")
        return None
    
    df['date'] = pd.to_datetime(df['period'])
    df['retail_price'] = df['value'].astype(float)
    
    df = df[['date', 'retail_price']].sort_values('date')
    
    # Sanity checks
    min_price = df['retail_price'].min()
    max_price = df['retail_price'].max()
    
    assert min_price > 1.5, f"Retail price too low: ${min_price:.2f} (expected >$1.50)"
    assert max_price < 7.0, f"Retail price too high: ${max_price:.2f} (expected <$7.00)"
    
    missing_count = df['retail_price'].isna().sum()
    if missing_count > 0:
        print(f"⚠️  WARNING: {missing_count} missing values detected")
        print("   These will be forward-filled in the Gold layer")
    
    # Save
    output_path = '../data/silver/retail_prices_daily.parquet'
    os.makedirs('../data/silver', exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    print("✓ Download successful!")
    print()
    print(f"Records: {len(df)}")
    print(f"Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"Price range: ${min_price:.2f} - ${max_price:.2f}")
    print(f"Saved to: {output_path}")
    print()
    
    # Show recent prices
    print("Most recent prices:")
    print(df.tail(10).to_string(index=False))
    print()
    
    print("=" * 70)
    print("✓ RETAIL PRICES DOWNLOADED SUCCESSFULLY")
    print()
    print("Next steps:")
    print("  1. Run: python download_eia_data.py (inventory, utilization)")
    print("  2. Run: python download_padd3_data.py (PADD3 capacity)")
    print("  3. Run: python validate_silver_layer.py (check all files)")
    print("=" * 70)
    
    return df

if __name__ == "__main__":
    download_aaa_retail_prices()
