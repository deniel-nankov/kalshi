#!/usr/bin/env python3
"""
Fetch Latest EIA Data and Make Predictions

This script:
1. Checks EIA API for latest available data (tries multiple dates)
2. Retries API calls multiple times (EIA can be flaky)
3. Updates the gold layer with new data
4. Makes predictions for all new dates
5. Tracks everything in real_time_tracking.csv

Author: Deniel Nankov
Date: October 28, 2025
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/denielnankov/Documents/kalshi/.env')

print("=" * 80)
print("🔄 FETCH LATEST EIA DATA & MAKE PREDICTIONS")
print("=" * 80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# ============================================================================
# 1. CHECK LATEST EIA DATA AVAILABILITY
# ============================================================================

def fetch_eia_with_retry(start_date, end_date, max_retries=5):
    """Fetch EIA data with retries (API can be flaky)"""
    eia_key = os.getenv('EIA_API_KEY')
    
    for attempt in range(1, max_retries + 1):
        try:
            # EIA API for daily retail gas prices
            url = f'https://api.eia.gov/v2/petroleum/pri/gnd/data/?api_key={eia_key}&frequency=daily&data[0]=value&facets[product][]=EPM0_EPD2D_PTE_NUS_DPG&start={start_date}&end={end_date}'
            
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'response' in data and 'data' in data['response']:
                    return data['response']['data']
                else:
                    print(f"   ⚠️ Attempt {attempt}/{max_retries}: No data in response")
            else:
                print(f"   ⚠️ Attempt {attempt}/{max_retries}: Status {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ Attempt {attempt}/{max_retries}: Error - {str(e)[:50]}")
        
        if attempt < max_retries:
            wait_time = 2 ** attempt  # Exponential backoff
            print(f"      Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
    
    return None


def check_latest_available_date():
    """Check what's the latest date with EIA data"""
    print("\n🔍 Checking latest EIA data availability...")
    print("-" * 80)
    
    # Start from today and go backwards
    today = datetime.now().date()
    
    # EIA typically publishes with 1-3 day lag
    # Check last 10 days to find latest
    for days_back in range(0, 10):
        check_date = today - timedelta(days=days_back)
        check_str = check_date.strftime('%Y-%m-%d')
        
        print(f"\n📅 Checking {check_str}...")
        
        # Fetch data for this date (check a 3-day window)
        start_str = (check_date - timedelta(days=2)).strftime('%Y-%m-%d')
        end_str = check_str
        
        data = fetch_eia_with_retry(start_str, end_str)
        
        if data and len(data) > 0:
            # Parse dates
            dates = [pd.to_datetime(d['period']).date() for d in data]
            latest = max(dates)
            
            print(f"   ✅ Found data! Latest date: {latest}")
            print(f"   📊 Records in window: {len(data)}")
            
            # Show what we got
            for d in sorted(data, key=lambda x: x['period'], reverse=True)[:3]:
                print(f"      - {d['period']}: ${float(d['value']):.3f}/gal")
            
            return latest, data
    
    print(f"   ❌ No data found in last 10 days!")
    return None, None


# ============================================================================
# 2. CHECK WHAT WE ALREADY HAVE
# ============================================================================

print("\n📂 Checking existing data...")

# Check gold layer
gold_path = Path('data/gold/master_model_ready.parquet')
if gold_path.exists():
    df_gold = pd.read_parquet(gold_path)
    gold_latest = pd.to_datetime(df_gold['date']).max().date()
    print(f"   Gold layer latest date: {gold_latest}")
else:
    print(f"   ⚠️ Gold layer not found!")
    gold_latest = None

# Check tracking file
tracking_path = Path('data/real_time_tracking.csv')
if tracking_path.exists():
    df_tracking = pd.read_csv(tracking_path)
    df_tracking['target_date'] = pd.to_datetime(df_tracking['target_date']).dt.date
    tracking_latest = df_tracking['target_date'].max()
    print(f"   Tracking latest target: {tracking_latest}")
    print(f"   Predictions made: {len(df_tracking)}")
else:
    print(f"   ⚠️ Tracking file not found!")
    tracking_latest = None

# ============================================================================
# 3. FETCH LATEST EIA DATA
# ============================================================================

latest_eia_date, eia_data = check_latest_available_date()

if not latest_eia_date:
    print("\n❌ Could not fetch EIA data. Exiting.")
    sys.exit(1)

print(f"\n" + "=" * 80)
print(f"📊 DATA STATUS SUMMARY")
print("=" * 80)
print(f"   EIA Latest Available:  {latest_eia_date}")
print(f"   Gold Layer Latest:     {gold_latest}")
print(f"   Tracking Latest:       {tracking_latest}")

# ============================================================================
# 4. DETERMINE WHAT DATES NEED PREDICTIONS
# ============================================================================

print(f"\n🎯 Determining prediction targets...")

# We need predictions for dates AFTER the gold layer
# Gold layer is frozen at Oct 18, 2024 based on previous context
# We want to predict Oct 19, 20, 21, ... up to latest EIA date

if gold_latest:
    # Predict from day after gold layer up to latest EIA
    start_predict = gold_latest + timedelta(days=1)
else:
    # If no gold layer, start from tracking latest
    start_predict = tracking_latest + timedelta(days=1) if tracking_latest else latest_eia_date

# Generate list of dates to predict
dates_to_predict = []
current = start_predict
while current <= latest_eia_date:
    dates_to_predict.append(current)
    current += timedelta(days=1)

print(f"   Start prediction from: {start_predict}")
print(f"   End prediction at:     {latest_eia_date}")
print(f"   Dates to predict:      {len(dates_to_predict)}")

if len(dates_to_predict) == 0:
    print(f"\n✅ No new predictions needed! Already up to date.")
    sys.exit(0)

print(f"\n📅 Will predict for dates:")
for date in dates_to_predict[:10]:  # Show first 10
    print(f"      - {date}")
if len(dates_to_predict) > 10:
    print(f"      ... and {len(dates_to_predict) - 10} more")

# ============================================================================
# 5. MAKE PREDICTIONS FOR EACH DATE
# ============================================================================

print(f"\n" + "=" * 80)
print(f"🤖 MAKING PREDICTIONS")
print("=" * 80)

# Import prediction modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    # Run daily prediction script for each date
    for i, target_date in enumerate(dates_to_predict, 1):
        print(f"\n[{i}/{len(dates_to_predict)}] Predicting for {target_date}...")
        print("-" * 80)
        
        # Set environment variable for target date
        os.environ['TARGET_DATE'] = target_date.strftime('%Y-%m-%d')
        
        # Run prediction script
        result = os.system('cd /Users/denielnankov/Documents/kalshi/Gas && /Users/denielnankov/Documents/kalshi/.venv/bin/python scripts/daily_prediction.py')
        
        if result == 0:
            print(f"   ✅ Prediction for {target_date} completed!")
        else:
            print(f"   ⚠️ Prediction for {target_date} failed (exit code {result})")
        
        # Small delay between predictions
        time.sleep(1)

except Exception as e:
    print(f"\n❌ Error during predictions: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# 6. SUMMARY
# ============================================================================

print(f"\n" + "=" * 80)
print(f"✅ PREDICTION RUN COMPLETE")
print("=" * 80)

# Reload tracking file to show results
if tracking_path.exists():
    df_final = pd.read_csv(tracking_path)
    print(f"\n📊 Final Tracking Status:")
    print(f"   Total predictions: {len(df_final)}")
    print(f"   Latest target: {df_final['target_date'].max()}")
    
    # Show last 5 predictions
    print(f"\n📅 Last 5 Predictions:")
    print(df_final[['prediction_date', 'target_date', 'ridge_prediction', 'fused_prediction']].tail().to_string(index=False))

print(f"\n🎯 NEXT STEPS:")
print(f"   1. Wait for EIA to publish actual prices")
print(f"   2. Run: python scripts/track_actuals.py")
print(f"   3. Run: python scripts/create_submission_graphs.py")
print(f"   4. Check outputs/submission_graphs/")

print("\n" + "=" * 80)
