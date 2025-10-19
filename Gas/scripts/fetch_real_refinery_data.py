"""
Fetch real refinery utilization data from EIA API.

This script replaces synthetic refinery outage data with real:
- Refinery operable capacity
- Refinery utilization %  
- Calculate offline capacity = operable_capacity * (1 - utilization/100)
"""

import os
import pandas as pd
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load API key
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)
EIA_API_KEY = os.getenv("EIA_API_KEY", "")

print("="*80)
print("Fetching REAL Refinery Utilization Data from EIA")
print("="*80)

# EIA Series for refinery data:
# WCRFPUS2: Weekly U.S. percent utilization of refinery operable capacity
# WOCLEUS2: Weekly U.S. operable refinery capacity (thousand barrels per day)

def fetch_refinery_utilization(start_date="2020-01-01", end_date="2025-10-18"):
    """Fetch refinery utilization % from EIA."""
    
    url = "https://api.eia.gov/v2/petroleum/sum/sndw/data/"
    
    params = {
        "api_key": EIA_API_KEY,
        "frequency": "weekly",
        "data[0]": "value",
        "facets[series][]": "WCRFPUS2",  # Percent utilization
        "start": start_date,
        "end": end_date,
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "length": 5000,
    }
    
    print("\n1. Fetching refinery utilization %...")
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    records = data["response"]["data"]
    df = pd.DataFrame(records)
    df['date'] = pd.to_datetime(df['period'])
    df['utilization_pct'] = pd.to_numeric(df['value'], errors='coerce')
    df = df[['date', 'utilization_pct']].sort_values('date')
    
    print(f"   ✅ {len(df)} records")
    print(f"   Range: {df['utilization_pct'].min():.1f}% to {df['utilization_pct'].max():.1f}%")
    print(f"   Latest: {df['utilization_pct'].iloc[-1]:.1f}% ({df['date'].iloc[-1].date()})")
    
    return df


def fetch_refinery_capacity(start_date="2020-01-01", end_date="2025-10-18"):
    """Fetch refinery operable capacity from EIA."""
    
    url = "https://api.eia.gov/v2/petroleum/sum/sndw/data/"
    
    params = {
        "api_key": EIA_API_KEY,
        "frequency": "weekly",
        "data[0]": "value",
        "facets[series][]": "WOCLEUS2",  # Operable capacity
        "start": start_date,
        "end": end_date,
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "length": 5000,
    }
    
    print("\n2. Fetching refinery operable capacity...")
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    records = data["response"]["data"]
    df = pd.DataFrame(records)
    df['date'] = pd.to_datetime(df['period'])
    df['operable_capacity_kbd'] = pd.to_numeric(df['value'], errors='coerce')
    df = df[['date', 'operable_capacity_kbd']].sort_values('date')
    
    print(f"   ✅ {len(df)} records")
    print(f"   Range: {df['operable_capacity_kbd'].min():.0f} to {df['operable_capacity_kbd'].max():.0f} kbd")
    print(f"   Latest: {df['operable_capacity_kbd'].iloc[-1]:.0f} kbd ({df['date'].iloc[-1].date()})")
    
    return df


def calculate_refinery_outages(utilization_df, capacity_df):
    """Calculate offline capacity from utilization and operable capacity."""
    
    print("\n3. Calculating refinery offline capacity...")
    
    # Merge utilization and capacity
    df = pd.merge(utilization_df, capacity_df, on='date', how='outer')
    df = df.sort_values('date')
    
    # Forward fill missing values (weekly data)
    df['utilization_pct'] = df['utilization_pct'].fillna(method='ffill')
    df['operable_capacity_kbd'] = df['operable_capacity_kbd'].fillna(method='ffill')
    
    # Calculate offline capacity
    # Offline = Total Operable * (1 - Utilization/100)
    df['total_offline_capacity_bpd'] = df['operable_capacity_kbd'] * 1000 * (1 - df['utilization_pct'] / 100)
    
    # For compatibility with existing features, split into scheduled vs unplanned
    # Assume typical scheduled maintenance is ~5-8% of capacity
    # Anything above baseline is "unplanned"
    baseline_idle_pct = 8.0  # Typical baseline idle capacity
    df['scheduled_maintenance_capacity_bpd'] = df['operable_capacity_kbd'] * 1000 * (baseline_idle_pct / 100)
    df['refinery_outage_capacity_bpd'] = df['total_offline_capacity_bpd'] - df['scheduled_maintenance_capacity_bpd']
    df['refinery_outage_capacity_bpd'] = df['refinery_outage_capacity_bpd'].clip(lower=0)  # No negative outages
    
    print(f"   ✅ Calculated offline capacity for {len(df)} weeks")
    print(f"\n   Statistics:")
    print(f"   - Average utilization: {df['utilization_pct'].mean():.1f}%")
    print(f"   - Average offline: {df['total_offline_capacity_bpd'].mean():.0f} bpd ({df['total_offline_capacity_bpd'].mean()/1000:.0f} kbd)")
    print(f"   - Min offline: {df['total_offline_capacity_bpd'].min():.0f} bpd (peak utilization)")
    print(f"   - Max offline: {df['total_offline_capacity_bpd'].max():.0f} bpd (maintenance season)")
    
    # Select final columns
    result = df[['date', 'refinery_outage_capacity_bpd', 'scheduled_maintenance_capacity_bpd', 'total_offline_capacity_bpd']].copy()
    
    return result


if __name__ == "__main__":
    try:
        # Fetch data
        utilization_df = fetch_refinery_utilization()
        capacity_df = fetch_refinery_capacity()
        
        # Calculate outages
        refinery_df = calculate_refinery_outages(utilization_df, capacity_df)
        
        # Save to file
        output_path = Path(__file__).resolve().parents[1] / "data" / "external" / "refinery_outage_data.csv"
        refinery_df.to_csv(output_path, index=False)
        
        print(f"\n{'='*80}")
        print(f"✅ SUCCESS: Real refinery data saved!")
        print(f"{'='*80}")
        print(f"Output: {output_path}")
        print(f"Records: {len(refinery_df)}")
        print(f"Date range: {refinery_df['date'].min().date()} to {refinery_df['date'].max().date()}")
        
        # Show sample
        print(f"\nSample data (first 5 records):")
        print(refinery_df.head().to_string(index=False))
        
        print(f"\nSample data (last 5 records):")
        print(refinery_df.tail().to_string(index=False))
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
