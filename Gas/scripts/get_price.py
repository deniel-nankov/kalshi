#!/usr/bin/env python3
"""
Simple script to get the predicted gas price for October 31st.
Returns just the price value.
"""

import json
import sys
from pathlib import Path

def get_price():
    """Get the predicted price from the latest forecast."""
    forecast_file = Path(__file__).parent.parent / "outputs" / "final_forecast.json"
    
    if not forecast_file.exists():
        print("ERROR: No forecast found. Run ./scripts/daily_forecast.sh first.", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open(forecast_file, 'r') as f:
            forecast = json.load(f)
    except (json.JSONDecodeError, Exception) as e:
        print(f"ERROR: Failed to parse forecast file: {forecast_file}", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)
    
    return forecast.get('point_forecast')

if __name__ == "__main__":
    price = get_price()
    if price is not None:
        print(f"{price:.4f}")
    else:
        print("ERROR: No price in forecast", file=sys.stderr)
        sys.exit(1)
