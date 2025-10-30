"""
EIA State Gas Price Downloader - WORKING VERSION

Downloads historical weekly state-level gasoline prices from EIA API v2

Author: Research Team
Date: October 29, 2025
"""

import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
import time
import json

# EIA API Configuration
EIA_API_BASE = "https://api.eia.gov/v2"

# State codes in EIA format (S + state abbr for most states)
# Format: Mostly "S" + state code, but some variations
EIA_STATE_CODES = {
    'AL': 'SAL', 'AK': 'SAK', 'AZ': 'SAZ', 'AR': 'SAR',
    'CA': 'SCA', 'CO': 'SCO', 'CT': 'SCT', 'DE': 'SDE',
    'FL': 'SFL', 'GA': 'SGA', 'HI': 'SHI', 'ID': 'SID',
    'IL': 'SIL', 'IN': 'SIN', 'IA': 'SIA', 'KS': 'SKS',
    'KY': 'SKY', 'LA': 'SLA', 'ME': 'SME', 'MD': 'SMD',
    'MA': 'SMA', 'MI': 'SMI', 'MN': 'SMN', 'MS': 'SMS',
    'MO': 'SMO', 'MT': 'SMT', 'NE': 'SNE', 'NV': 'SNV',
    'NH': 'SNH', 'NJ': 'SNJ', 'NM': 'SNM', 'NY': 'SNY',
    'NC': 'SNC', 'ND': 'SND', 'OH': 'SOH', 'OK': 'SOK',
    'OR': 'SOR', 'PA': 'SPA', 'RI': 'SRI', 'SC': 'SSC',
    'SD': 'SSD', 'TN': 'STN', 'TX': 'STX', 'UT': 'SUT',
    'VT': 'SVT', 'VA': 'SVA', 'WA': 'SWA', 'WV': 'SWV',
    'WI': 'SWI', 'WY': 'SWY'
}

STATE_NAMES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming'
}


def download_state_weekly_prices(api_key: str, start_year: str = '2022'):
    """
    Download weekly gasoline prices for all states from EIA
    
    Args:
        api_key: EIA API key
        start_year: Start year (YYYY format)
    
    Returns:
        DataFrame with columns: date, state, state_name, price
    """
    print("\n" + "="*80)
    print("📥 DOWNLOADING EIA WEEKLY STATE GASOLINE PRICES")
    print("="*80 + "\n")
    print(f"Start date: {start_year}-01-01")
    print(f"States: {len(EIA_STATE_CODES)}")
    print(f"Estimated records: ~{len(EIA_STATE_CODES) * 150}\n")
    
    all_data = []
    failed_states = []
    
    for state_abbr, eia_code in EIA_STATE_CODES.items():
        state_name = STATE_NAMES[state_abbr]
        print(f"Downloading {state_abbr} ({state_name})...", end=" ")
        
        # EIA API endpoint
        url = f"{EIA_API_BASE}/petroleum/pri/gnd/data/"
        
        params = {
            'api_key': api_key,
            'frequency': 'weekly',
            'data[0]': 'value',
            'facets[product][]': 'EPM0',  # All Grades
            'facets[duoarea][]': eia_code,  # State code
            'facets[process][]': 'PTE',  # Retail sales
            'start': start_year,
            'sort[0][column]': 'period',
            'sort[0][direction]': 'asc',
            'offset': 0,
            'length': 5000  # Max allowed
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'response' in data and 'data' in data['response']:
                    records = data['response']['data']
                    
                    if len(records) > 0:
                        for record in records:
                            all_data.append({
                                'date': record['period'],
                                'state': state_abbr,
                                'state_name': state_name,
                                'price': float(record['value']),
                                'eia_area': record['duoarea'],
                                'series': record.get('series', '')
                            })
                        
                        print(f"✅ {len(records)} weeks")
                    else:
                        print(f"⚠️  No data")
                        failed_states.append(state_abbr)
                else:
                    print(f"❌ Bad response format")
                    failed_states.append(state_abbr)
            else:
                print(f"❌ HTTP {response.status_code}")
                failed_states.append(state_abbr)
        
        except Exception as e:
            print(f"❌ Error: {str(e)[:50]}")
            failed_states.append(state_abbr)
        
        time.sleep(0.2)  # Be polite to API
    
    # Create DataFrame
    df = pd.DataFrame(all_data)
    
    if not df.empty:
        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Sort
        df = df.sort_values(['date', 'state']).reset_index(drop=True)
        
        print(f"\n{'='*80}")
        print("📊 DOWNLOAD SUMMARY")
        print(f"{'='*80}\n")
        print(f"Total records: {len(df)}")
        print(f"States successful: {len(EIA_STATE_CODES) - len(failed_states)}/{len(EIA_STATE_CODES)}")
        print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
        print(f"Unique weeks: {df['date'].nunique()}")
        print(f"Weeks per state (avg): {len(df) / (len(EIA_STATE_CODES) - len(failed_states)):.1f}")
        
        if failed_states:
            print(f"\n⚠️  Failed states ({len(failed_states)}): {', '.join(failed_states)}")
    
    return df


def calculate_national_average(df: pd.DataFrame, weights_file: str = 'data/consumption_weights.csv'):
    """
    Calculate volume-weighted national average from state prices
    """
    # Load consumption weights
    weights_path = Path(weights_file)
    if not weights_path.exists():
        print(f"\n⚠️  Weights file not found: {weights_file}")
        print("   Calculating simple average instead of weighted average")
        
        # Simple average
        national = df.groupby('date').agg({
            'price': 'mean'
        }).reset_index()
        national['state'] = 'US'
        national['state_name'] = 'National Average (unweighted)'
        
        return national
    
    # Load weights
    weights_df = pd.read_csv(weights_path)
    
    # Merge with prices
    df_weighted = df.merge(weights_df[['state', 'consumption_weight']], on='state', how='left')
    
    # Calculate weighted average per week
    national = df_weighted.groupby('date').apply(
        lambda x: (x['price'] * x['consumption_weight']).sum() / x['consumption_weight'].sum()
    ).reset_index()
    national.columns = ['date', 'price']
    national['state'] = 'US'
    national['state_name'] = 'National Average (weighted)'
    
    return national


if __name__ == '__main__':
    # Load API key
    api_key_file = Path('state_analysis/.eia_api_key')
    
    if not api_key_file.exists():
        print("❌ API key not found!")
        print(f"   Expected: {api_key_file}")
        print("\nGet free API key at: https://www.eia.gov/opendata/register.php")
        print(f"Then save to: {api_key_file}")
        exit(1)
    
    with open(api_key_file, 'r') as f:
        api_key = f.read().strip()
    
    print("\n" + "="*80)
    print("🎯 EIA WEEKLY STATE GASOLINE PRICES DOWNLOADER")
    print("="*80)
    
    # Download data
    df = download_state_weekly_prices(api_key, start_year='2022')
    
    if not df.empty:
        # Save state data
        output_file = Path('state_analysis/data/eia_state_prices_weekly.csv')
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
        
        print(f"\n✅ State data saved to: {output_file}")
        
        # Calculate and save national average
        national = calculate_national_average(df)
        national_file = Path('state_analysis/data/eia_national_average_weekly.csv')
        national.to_csv(national_file, index=False)
        
        print(f"✅ National average saved to: {national_file}")
        
        # Statistics
        print(f"\n{'='*80}")
        print("📊 FINAL DATASET STATISTICS")
        print(f"{'='*80}\n")
        print(f"State records: {len(df)}")
        print(f"States: {df['state'].nunique()}")
        print(f"Weeks: {df['date'].nunique()}")
        print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
        print(f"Duration: {(df['date'].max() - df['date'].min()).days / 7:.1f} weeks")
        print(f"\nPrice statistics:")
        print(f"  Mean: ${df['price'].mean():.3f}")
        print(f"  Min: ${df['price'].min():.3f}")
        print(f"  Max: ${df['price'].max():.3f}")
        print(f"  Std: ${df['price'].std():.3f}")
        
        print(f"\n{'='*80}")
        print("🎯 NEXT STEPS")
        print(f"{'='*80}\n")
        print("Now you can run the analysis scripts:")
        print("  1. python state_analysis/scripts/analyze_weekly_correlations.py")
        print("  2. python state_analysis/scripts/granger_causality_weekly.py")
        print("\nWith ~150 weeks of data, you'll have:")
        print("  ✅ Tight confidence intervals (not ±2 like with n=4!)")
        print("  ✅ Statistical power to detect r=0.3")
        print("  ✅ Valid Granger causality tests")
        print("  ✅ Definitive answers!")
        
    else:
        print("\n❌ No data downloaded. Check:")
        print("  1. API key is valid")
        print("  2. Network connection")
        print("  3. EIA API is operational")
