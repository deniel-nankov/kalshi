"""
Debug EIA API to find correct SPR data endpoint.
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load API key
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)
EIA_API_KEY = os.getenv("EIA_API_KEY", "")

print("="*80)
print("EIA API Debugging - Strategic Petroleum Reserve")
print("="*80)
print(f"API Key: {EIA_API_KEY[:10]}... (masked)")

# Test different endpoints and series
tests = [
    {
        "name": "SPR Stocks - Weekly (WCSSTUS1)",
        "url": "https://api.eia.gov/v2/petroleum/sum/sndw/data/",
        "params": {
            "api_key": EIA_API_KEY,
            "frequency": "weekly",
            "data[0]": "value",
            "facets[series][]": "WCSSTUS1",
            "start": "2024-01-01",
            "length": 5,
        }
    },
    {
        "name": "SPR Stocks - Alternative endpoint",
        "url": "https://api.eia.gov/v2/petroleum/sum/sndw/data/",
        "params": {
            "api_key": EIA_API_KEY,
            "frequency": "weekly",
            "data[0]": "value",
            "facets[product][]": "EPMR",
            "facets[series][]": "WCSSTUS1",
            "start": "2024-01-01",
            "length": 5,
        }
    },
    {
        "name": "All weekly stocks series",
        "url": "https://api.eia.gov/v2/petroleum/sum/sndw/data/",
        "params": {
            "api_key": EIA_API_KEY,
            "frequency": "weekly",
            "length": 5,
        }
    },
    {
        "name": "Browse petroleum routes",
        "url": "https://api.eia.gov/v2/petroleum/",
        "params": {
            "api_key": EIA_API_KEY,
        }
    },
]

for i, test in enumerate(tests, 1):
    print(f"\n{'='*80}")
    print(f"Test {i}: {test['name']}")
    print(f"{'='*80}")
    print(f"URL: {test['url']}")
    print(f"Params: {test['params']}")
    
    try:
        response = requests.get(test['url'], params=test['params'], timeout=10)
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Valid JSON response")
                
                # Print structure
                if isinstance(data, dict):
                    print(f"Keys: {list(data.keys())}")
                    if 'response' in data:
                        print(f"Response keys: {list(data['response'].keys())}")
                        if 'data' in data['response']:
                            print(f"Data records: {len(data['response']['data'])}")
                            if len(data['response']['data']) > 0:
                                print(f"Sample record: {data['response']['data'][0]}")
                    if 'routes' in data:
                        print(f"Routes available: {data['routes'][:5]}")
                else:
                    print(f"Response type: {type(data)}")
                    print(f"Response preview: {str(data)[:500]}")
                    
            except Exception as e:
                print(f"⚠️ JSON parse error: {e}")
                print(f"Response text: {response.text[:500]}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print(f"❌ Timeout after 10 seconds")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

print(f"\n{'='*80}")
print("Debug Complete")
print(f"{'='*80}")

# Try to find SPR in series list
print("\n" + "="*80)
print("Searching for SPR-related series...")
print("="*80)

try:
    # Get all weekly petroleum series
    response = requests.get(
        "https://api.eia.gov/v2/petroleum/sum/sndw/data/",
        params={
            "api_key": EIA_API_KEY,
            "frequency": "weekly",
            "length": 1,
        },
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        if 'response' in data and 'data' in data['response']:
            series_found = set()
            for record in data['response']['data'][:100]:  # Check first 100
                if 'series' in record:
                    series_found.add(record['series'])
            
            print(f"\nFound {len(series_found)} unique series in first 100 records:")
            spr_series = [s for s in series_found if 'SPR' in s or 'WCSS' in s]
            if spr_series:
                print(f"✅ SPR-related series: {spr_series}")
            else:
                print(f"⚠️ No SPR series found in sample")
                print(f"Sample series: {list(series_found)[:10]}")
except Exception as e:
    print(f"❌ Series search failed: {e}")
