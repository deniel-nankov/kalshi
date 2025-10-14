#!/usr/bin/env python3
"""
Get Latest Forecast

Returns the latest gas price forecast in JSON format.
Use this for trading decisions or integration with other systems.

Usage:
    python scripts/get_latest_forecast.py
    python scripts/get_latest_forecast.py --summary
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

def get_latest_forecast(summary_only=False):
    """Load and return latest forecast"""
    forecast_file = Path(__file__).parent.parent / "outputs" / "final_forecast.json"
    
    if not forecast_file.exists():
        return {
            "error": "No forecast available",
            "status": "missing",
            "suggestion": "Run: python scripts/daily_forecast.sh"
        }
    
    # Check if forecast is recent (< 24 hours old)
    age_hours = (datetime.now().timestamp() - forecast_file.stat().st_mtime) / 3600
    
    try:
        with open(forecast_file, 'r') as f:
            forecast = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"ERROR: Failed to read or parse forecast file: {forecast_file}", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        return {
            "error": "Invalid forecast file",
            "status": "corrupted",
            "details": str(e),
            "suggestion": "Regenerate forecast: python scripts/daily_forecast.sh"
        }
    
    # Add metadata
    forecast['metadata'] = {
        'age_hours': round(age_hours, 2),
        'is_fresh': age_hours < 24,
        'is_stale': age_hours > 48,
        'file_path': str(forecast_file),
        'last_updated': datetime.fromtimestamp(forecast_file.stat().st_mtime).isoformat()
    }
    
    if summary_only:
        # Return just key info
        predictions = forecast.get('predictions', [])
        if predictions:
            first = predictions[0]
            last = predictions[-1]
            
            return {
                'status': 'ok',
                'is_fresh': age_hours < 24,
                'age_hours': round(age_hours, 2),
                'first_prediction': {
                    'date': first.get('date'),
                    'price': first.get('predicted_price')
                },
                'last_prediction': {
                    'date': last.get('date'),
                    'price': last.get('predicted_price')
                },
                'total_predictions': len(predictions)
            }
    
    return forecast


def main():
    parser = argparse.ArgumentParser(
        description='Get latest gas price forecast',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Full forecast
  python scripts/get_latest_forecast.py
  
  # Summary only
  python scripts/get_latest_forecast.py --summary
  
  # Use in script
  FORECAST=$(python scripts/get_latest_forecast.py --summary)
  echo $FORECAST
        '''
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Return summary only (faster)'
    )
    
    args = parser.parse_args()
    
    forecast = get_latest_forecast(summary_only=args.summary)
    print(json.dumps(forecast, indent=2))


if __name__ == "__main__":
    main()
