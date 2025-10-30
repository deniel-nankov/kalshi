"""
Test EIA API to understand response structure
"""

import requests
import json

api_key = open('state_analysis/.eia_api_key').read().strip()

# Try different endpoint formats
tests = [
    # Test 1: Petroleum prices endpoint
    {
        'name': 'Petroleum Prices - Weekly Gas',
        'url': 'https://api.eia.gov/v2/petroleum/pri/gnd/data/',
        'params': {
            'api_key': api_key,
            'frequency': 'weekly',
            'data[0]': 'value',
            'facets[product][]': 'EPM0',  # All grades
            'facets[duoarea][]': 'SCA',  # California
            'start': '2024-01',
            'length': 50
        }
    },
    # Test 2: Try without facets
    {
        'name': 'Simple query',
        'url': 'https://api.eia.gov/v2/petroleum/pri/gnd/data/',
        'params': {
            'api_key': api_key,
            'length': 10
        }
    }
]

for test in tests:
    print(f"\n{'='*80}")
    print(f"TEST: {test['name']}")
    print(f"{'='*80}\n")
    print(f"URL: {test['url']}")
    print(f"Params: {json.dumps(test['params'], indent=2)}\n")
    
    try:
        response = requests.get(test['url'], params=test['params'], timeout=10)
        print(f"Status: {response.status_code}\n")
        
        if response.status_code == 200:
            data = response.json()
            print("Response structure:")
            print(json.dumps(data, indent=2)[:2000])  # First 2000 chars
            
            if 'response' in data:
                resp = data['response']
                print(f"\nResponse keys: {list(resp.keys())}")
                if 'data' in resp:
                    print(f"Data length: {len(resp['data'])}")
                    if len(resp['data']) > 0:
                        print(f"First record: {json.dumps(resp['data'][0], indent=2)}")
        else:
            print(f"Error: {response.text[:500]}")
    
    except Exception as e:
        print(f"Exception: {e}")
