"""
Download PADD3 (Gulf Coast) Refinery Capacity Data from EIA

PADD3 is the Gulf Coast region, which accounts for ~50% of U.S. refining capacity.
This feature captures regional concentration risk and capacity utilization.

Used for feature:
- PADD3_Share (% of U.S. capacity in Gulf Coast)

Time: ~20 minutes
Cost: FREE (requires EIA API key)
"""

import pandas as pd
import requests
import os

def download_padd3_capacity():
    """
    Download PADD3 (Gulf Coast) refinery capacity data
    Used to calculate PADD3_Share feature
    """
    
    print("=" * 70)
    print("DOWNLOADING PADD3 REFINERY CAPACITY DATA FROM EIA")
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
        return None
    
    print(f"Using API key: {API_KEY[:10]}...")
    print()
    
    # PADD3 refinery capacity (operable capacity)
    # Note: These series IDs may need adjustment based on EIA's current API structure
    # If these don't work, check: https://www.eia.gov/opendata/browser/petroleum/sum/sndw
    
    padd3_series = "PET.8_NA_8C0_NUS_6.W"  # Weekly operable capacity, PADD3
    total_series = "PET.8_NA_8C0_NUS_1.W"  # Total U.S. operable capacity
    
    print("Fetching PADD3 capacity...")
    print(f"Series: {padd3_series}")
    
    # Download PADD3
    url_padd3 = f"https://api.eia.gov/v2/petroleum/sum/sndw/data/?api_key={API_KEY}&data[0]=value&facets[series][]={padd3_series}&frequency=weekly&start=2020-10-01"
    
    try:
        response_padd3 = requests.get(url_padd3)
        response_padd3.raise_for_status()
        padd3_data = response_padd3.json()
    except Exception as e:
        print(f"❌ ERROR fetching PADD3 data: {e}")
        return None
    
    if 'response' not in padd3_data or 'data' not in padd3_data['response']:
        print(f"❌ ERROR: Unexpected PADD3 response format")
        print(f"Response: {padd3_data}")
        return None
    
    df_padd3 = pd.DataFrame(padd3_data['response']['data'])
    print(f"✓ PADD3 data: {len(df_padd3)} weeks")
    
    # Download Total U.S.
    print("Fetching Total U.S. capacity...")
    print(f"Series: {total_series}")
    
    url_total = f"https://api.eia.gov/v2/petroleum/sum/sndw/data/?api_key={API_KEY}&data[0]=value&facets[series][]={total_series}&frequency=weekly&start=2020-10-01"
    
    try:
        response_total = requests.get(url_total)
        response_total.raise_for_status()
        total_data = response_total.json()
    except Exception as e:
        print(f"❌ ERROR fetching Total capacity data: {e}")
        return None
    
    if 'response' not in total_data or 'data' not in total_data['response']:
        print(f"❌ ERROR: Unexpected Total capacity response format")
        return None
    
    df_total = pd.DataFrame(total_data['response']['data'])
    print(f"✓ Total U.S. data: {len(df_total)} weeks")
    print()
    
    # Merge
    df_padd3['date'] = pd.to_datetime(df_padd3['period'])
    df_padd3['padd3_capacity'] = df_padd3['value'].astype(float)
    
    df_total['date'] = pd.to_datetime(df_total['period'])
    df_total['total_capacity'] = df_total['value'].astype(float)
    
    df = df_padd3[['date', 'padd3_capacity']].merge(
        df_total[['date', 'total_capacity']], 
        on='date'
    )
    
    # Calculate share
    df['padd3_share'] = df['padd3_capacity'] / df['total_capacity'] * 100
    df = df[['date', 'padd3_share']].sort_values('date')
    
    # Sanity checks (PADD3 is typically ~45-55% of U.S. capacity)
    min_share = df['padd3_share'].min()
    max_share = df['padd3_share'].max()
    
    assert min_share > 40, f"PADD3 share too low: {min_share:.1f}% (expected >40%)"
    assert max_share < 60, f"PADD3 share too high: {max_share:.1f}% (expected <60%)"
    
    # Save
    output_path = '../data/silver/padd3_share_weekly.parquet'
    os.makedirs('../data/silver', exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    print("✓ PADD3 data merged and calculated")
    print()
    print(f"Records: {len(df)}")
    print(f"Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"PADD3 share range: {min_share:.1f}% - {max_share:.1f}%")
    print(f"Current PADD3 share: {df.iloc[-1]['padd3_share']:.1f}%")
    print(f"Saved to: {output_path}")
    print()
    
    print("=" * 70)
    print("✓ PADD3 DATA DOWNLOADED SUCCESSFULLY")
    print()
    print("Next step:")
    print("  Run: python validate_silver_layer.py")
    print("=" * 70)
    
    return df

if __name__ == "__main__":
    download_padd3_capacity()
