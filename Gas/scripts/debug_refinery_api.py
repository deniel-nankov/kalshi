"""
Debug refinery API to understand data format.
"""

import os
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Load API key
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)
EIA_API_KEY = os.getenv("EIA_API_KEY", "")

# Test refinery utilization series
url = "https://api.eia.gov/v2/petroleum/sum/sndw/data/"

params = {
    "api_key": EIA_API_KEY,
    "frequency": "weekly",
    "data[0]": "value",
    "facets[series][]": "WCRFPUS2",  # Percent utilization
    "start": "2024-01-01",
    "length": 5,
}

print("Testing WCRFPUS2 (Refinery Utilization %)...")
print(f"URL: {url}")
print(f"Params: {params}\n")

response = requests.get(url, params=params, timeout=10)
data = response.json()

print("Response structure:")
print(f"Keys: {list(data.keys())}\n")

if 'response' in data and 'data' in data['response']:
    records = data['response']['data']
    print(f"Records returned: {len(records)}\n")
    
    print("First record:")
    for key, value in records[0].items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*80)
    print("All records:")
    df = pd.DataFrame(records)
    print(df[['period', 'series', 'series-description', 'value', 'units']].to_string(index=False))
    
    # Check if value needs conversion
    df['value_num'] = pd.to_numeric(df['value'], errors='coerce')
    print(f"\n  Min value: {df['value_num'].min()}")
    print(f"  Max value: {df['value_num'].max()}")
    print(f"  Mean value: {df['value_num'].mean():.1f}")
    print(f"  Units field: {df['units'].unique()}")
