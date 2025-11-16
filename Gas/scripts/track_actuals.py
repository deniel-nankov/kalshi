"""
Track Actual Prices and Validate Predictions
============================================

Fetches actual EIA prices and compares with predictions.

Author: Gas Price Forecasting System
Date: October 19, 2025
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import requests
from dotenv import load_dotenv
import time

load_dotenv('/Users/denielnankov/Documents/kalshi/.env')

def fetch_eia_prices(start_date, end_date, max_retries=5):
    """
    Fetch actual gas prices from EIA API with retry logic
    
    Parameters:
    -----------
    start_date : str or date
        Start date (YYYY-MM-DD)
    end_date : str or date
        End date (YYYY-MM-DD)
    max_retries : int, default=5
        Maximum number of retry attempts
        
    Returns:
    --------
    pd.DataFrame : Date and price columns
    """
    print(f"\n📡 Fetching EIA prices from {start_date} to {end_date}...")
    
    eia_key = os.getenv('EIA_API_KEY')
    
    # Format dates
    if isinstance(start_date, (pd.Timestamp, datetime)):
        start_date = start_date.strftime('%Y-%m-%d')
    if isinstance(end_date, (pd.Timestamp, datetime)):
        end_date = end_date.strftime('%Y-%m-%d')
    
    # EIA API endpoint
    url = f"https://api.eia.gov/v2/petroleum/pri/gnd/data/"
    params = {
        'api_key': eia_key,
        'frequency': 'daily',
        'data[0]': 'value',
        'facets[product][]': 'EPM0_EPD2D_PTE_NUS_DPG',  # Regular gas, all grades
        'start': start_date,
        'end': end_date,
        'sort[0][column]': 'period',
        'sort[0][direction]': 'asc'
    }
    
    # Retry loop with exponential backoff
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                # Exponential backoff: 2, 4, 8, 16 seconds
                wait_time = 2 ** (attempt - 1)
                print(f"   ⏳ Retry {attempt}/{max_retries} after {wait_time}s...")
                time.sleep(wait_time)
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'response' in data and 'data' in data['response']:
                    records = data['response']['data']
                    
                    if records:
                        # Success! Convert to DataFrame
                        df = pd.DataFrame(records)
                        df['date'] = pd.to_datetime(df['period'])
                        df = df.rename(columns={'value': 'retail_price'})
                        df = df[['date', 'retail_price']].sort_values('date')
                        
                        success_msg = f"   ✅ Fetched {len(df)} price records"
                        if attempt > 1:
                            success_msg += f" (succeeded on attempt {attempt})"
                        print(success_msg)
                        print(f"   Latest: {df['date'].max().date()} = ${df['retail_price'].iloc[-1]:.3f}")
                        
                        return df
                    else:
                        # No data available for date range (not an error, data just not published yet)
                        print(f"   ⚠️ No data available for date range")
                        return None
                else:
                    print(f"   ⚠️ Attempt {attempt}: No data in response")
            else:
                print(f"   ⚠️ Attempt {attempt}: EIA API returned status {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"   ⚠️ Attempt {attempt}: Request timeout")
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️ Attempt {attempt}: Connection error")
        except Exception as e:
            print(f"   ⚠️ Attempt {attempt}: {str(e)[:50]}")
    
    # All retries failed
    print(f"   ❌ Failed after {max_retries} attempts")
    print(f"   This is usually because data hasn't been published yet (1-2 day lag)")
    return None

def validate_predictions():
    """
    Check for pending predictions and validate with actual prices
    
    Returns:
    --------
    int : Number of predictions validated
    """
    print("\n" + "="*80)
    print("✅ VALIDATING PREDICTIONS")
    print("="*80)
    print(f"Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    tracking_file = Path('/Users/denielnankov/Documents/kalshi/Gas/data/real_time_tracking.csv')
    
    if not tracking_file.exists():
        print("\n⚠️ No predictions to validate")
        return 0
    
    # Load predictions
    tracking = pd.read_csv(tracking_file, parse_dates=['prediction_date', 'target_date'])
    
    # Find pending predictions (no actual price yet)
    pending = tracking[tracking['actual_price'].isna()].copy()
    
    if len(pending) == 0:
        print("\n✅ All predictions already validated!")
        return 0
    
    print(f"\n🔍 Found {len(pending)} pending predictions:")
    # Use itertuples() for better performance (5-10x faster than iterrows)
    for row in pending.itertuples(index=False):
        print(f"   {row.target_date.date()}: Predicted ${row.predicted_price:.3f}")
    
    # Fetch actual prices for pending predictions
    start_date = pending['target_date'].min()
    end_date = pending['target_date'].max()
    
    actual_prices = fetch_eia_prices(start_date, end_date)
    
    if actual_prices is None:
        print("\n⚠️ Could not fetch actual prices")
        return 0
    
    # Match predictions with actuals
    validated_count = 0
    
    # Use itertuples() with index=True to get both index and row data
    for row in pending.itertuples():
        idx = row.Index
        target_date = pd.to_datetime(row.target_date).date()
        
        # Find matching actual price
        actual = actual_prices[actual_prices['date'].dt.date == target_date]
        
        if len(actual) == 0:
            print(f"\n   ⏳ {target_date}: No actual price available yet")
            continue
        
        actual_price = actual.iloc[0]['retail_price']
        
        # Calculate errors
        ridge_error = row.predicted_price - actual_price
        baseline_error = row.baseline_prediction - actual_price
        
        # Update tracking
        tracking.loc[idx, 'actual_price'] = actual_price
        tracking.loc[idx, 'ridge_error'] = ridge_error
        tracking.loc[idx, 'baseline_error'] = baseline_error
        
        # Show result
        ridge_abs_err = abs(ridge_error)
        baseline_abs_err = abs(baseline_error)
        better = "✅" if ridge_abs_err < baseline_abs_err else "❌"
        
        improvement = (baseline_abs_err - ridge_abs_err) / baseline_abs_err * 100
        
        print(f"\n   {better} {target_date}:")
        print(f"      Predicted:  ${row['predicted_price']:.3f}")
        print(f"      Actual:     ${actual_price:.3f}")
        print(f"      Ridge err:  ${ridge_error:+.3f} (|{ridge_abs_err:.3f}|)")
        print(f"      Baseline:   ${baseline_error:+.3f} (|{baseline_abs_err:.3f}|)")
        print(f"      Better by:  {improvement:+.1f}%")
        
        validated_count += 1
    
    # Save updated tracking
    tracking.to_csv(tracking_file, index=False)
    
    print(f"\n✅ Validated {validated_count} predictions")
    
    # Show overall statistics if we have validated predictions
    validated = tracking[tracking['actual_price'].notna()]
    
    if len(validated) > 0:
        from sklearn.metrics import r2_score, mean_absolute_error
        
        r2 = r2_score(validated['actual_price'], validated['predicted_price'])
        mae = mean_absolute_error(validated['actual_price'], validated['predicted_price'])
        baseline_mae = mean_absolute_error(validated['actual_price'], validated['baseline_prediction'])
        
        improvement = (1 - mae / baseline_mae) * 100
        
        print("\n" + "="*80)
        print("📊 OVERALL PERFORMANCE")
        print("="*80)
        print(f"\n   Sample size: {len(validated)} predictions")
        print(f"   Date range:  {validated['target_date'].min().date()} to {validated['target_date'].max().date()}")
        print(f"\n   Ridge Model:")
        print(f"      R²:  {r2:.3f}")
        print(f"      MAE: ${mae:.4f} per gallon")
        print(f"\n   Baseline (naive tomorrow=today):")
        print(f"      MAE: ${baseline_mae:.4f} per gallon")
        print(f"\n   Improvement: {improvement:+.1f}%")
        
        if improvement > 0:
            print(f"\n   ✅ Ridge model beats baseline!")
        else:
            print(f"\n   ⚠️ Baseline is better (may need more data)")
    
    return validated_count

def main():
    """Main workflow: Validate pending predictions"""
    try:
        validated = validate_predictions()
        
        if validated > 0:
            print("\n" + "="*80)
            print("✅ VALIDATION COMPLETE!")
            print("="*80)
            print(f"\n   Validated {validated} predictions")
            print(f"\n   Run daily_prediction.py to make tomorrow's prediction")
            print(f"   Run compare_predictions.py for detailed analysis")
        else:
            print("\n" + "="*80)
            print("⏳ WAITING FOR DATA")
            print("="*80)
            print(f"\n   No new actuals available yet")
            print(f"   EIA typically publishes 1-2 days after the date")
            print(f"   Check again tomorrow")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
