#!/usr/bin/env python3
"""
Make Predictions for Multiple Days

Since EIA only publishes WEEKLY data (not daily), we make predictions
for multiple target dates using the frozen gold layer data.

Date: October 28, 2025
"""

import pandas as pd
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

print("=" * 80)
print("🔮 MULTI-DAY PREDICTION GENERATOR")
print("=" * 80)
print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Check gold layer
gold_path = Path('data/gold/master_model_ready.parquet')
df_gold = pd.read_parquet(gold_path)
gold_latest = pd.to_datetime(df_gold['date']).max().date()

print(f"\n📊 Gold layer:")
print(f"   Latest date: {gold_latest}")
print(f"   Total records: {len(df_gold):,}")

# Check tracking
tracking_path = Path('data/real_time_tracking.csv')
if tracking_path.exists():
    df_track = pd.read_csv(tracking_path)
    df_track['target_date'] = pd.to_datetime(df_track['target_date']).dt.date
    tracking_dates = set(df_track['target_date'].unique())
    print(f"\n📅 Existing predictions: {len(tracking_dates)}")
    for d in sorted(tracking_dates):
        print(f"   - {d}")
else:
    tracking_dates = set()
    print(f"\n📅 No existing predictions found")

# Determine dates to predict
today = datetime.now().date()
start_date = gold_latest + timedelta(days=1)  # Day after gold layer
end_date = today + timedelta(days=1)  # Tomorrow

# Generate date range
all_dates = []
current = start_date
while current <= end_date:
    all_dates.append(current)
    current += timedelta(days=1)

# Filter out already predicted dates
new_dates = [d for d in all_dates if d not in tracking_dates]

print(f"\n🎯 Target prediction dates:")
print(f"   From: {start_date}")
print(f"   To:   {end_date}")
print(f"   Total possible: {len(all_dates)}")
print(f"   Already predicted: {len(tracking_dates)}")
print(f"   NEW predictions needed: {len(new_dates)}")

if len(new_dates) == 0:
    print(f"\n✅ All dates already predicted! Nothing to do.")
    sys.exit(0)

print(f"\n📋 Will predict for:")
for d in new_dates:
    print(f"   - {d}")

# Confirm
print(f"\n" + "=" * 80)
response = input(f"Proceed with {len(new_dates)} predictions? (y/n): ")
if response.lower() != 'y':
    print("Cancelled.")
    sys.exit(0)

# Make predictions
print(f"\n" + "=" * 80)
print(f"🤖 GENERATING PREDICTIONS")
print("=" * 80)

success_count = 0
fail_count = 0

for i, target_date in enumerate(new_dates, 1):
    print(f"\n[{i}/{len(new_dates)}] Predicting for {target_date}...")
    print("-" * 80)
    
    # Set environment variable for target date (if script supports it)
    os.environ['FORCE_TARGET_DATE'] = target_date.strftime('%Y-%m-%d')
    
    try:
        # Run daily prediction script
        result = os.system('/Users/denielnankov/Documents/kalshi/.venv/bin/python scripts/daily_prediction.py < /dev/null')
        
        if result == 0:
            print(f"   ✅ Success!")
            success_count += 1
        else:
            print(f"   ⚠️ Failed (exit code {result})")
            fail_count += 1
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        fail_count += 1
    
    # Small delay
    import time
    time.sleep(0.5)

# Summary
print(f"\n" + "=" * 80)
print(f"✅ PREDICTION RUN COMPLETE")
print("=" * 80)
print(f"   Successful: {success_count}/{len(new_dates)}")
print(f"   Failed:     {fail_count}/{len(new_dates)}")

# Show final tracking status
if tracking_path.exists():
    df_final = pd.read_csv(tracking_path)
    print(f"\n📊 Final Tracking Status:")
    print(f"   Total predictions: {len(df_final)}")
    
    # Show last 5
    print(f"\n📅 Latest 5 predictions:")
    display_cols = ['prediction_date', 'target_date', 'ridge_pred', 'fused_pred']
    print(df_final[display_cols].tail().to_string(index=False))

print(f"\n🎯 Next: Run track_actuals.py when EIA publishes weekly data")
print("=" * 80)
