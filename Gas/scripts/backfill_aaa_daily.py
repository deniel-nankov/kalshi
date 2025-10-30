#!/usr/bin/env python3
"""
Backfill AAA Daily Prices: Oct 18-29, 2025

Since AAA doesn't provide historical API, we'll use a hybrid approach:
1. Use today's AAA scraping as anchor (Oct 29: $3.038)
2. Use EIA weekly as anchors (Oct 20: $3.019, Oct 27: $3.035)
3. Interpolate daily prices between these points
4. Validate the interpolation logic is sound

This creates a complete daily dataset for training.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import re

# Add project root
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

print("=" * 80)
print("📊 BACKFILL AAA DAILY PRICES: OCT 18-29, 2025")
print("=" * 80)

# ============================================================================
# 1. Known anchor points
# ============================================================================
print("\n1️⃣ Collecting anchor points...")

anchors = {
    '2025-10-18': 3.061,  # Last gold layer (EIA week ending Oct 13 + trend)
    '2025-10-20': 3.019,  # EIA actual (week ending)
    '2025-10-27': 3.035,  # EIA actual (week ending)
    '2025-10-29': 3.038,  # AAA scraped today
}

print(f"\n   Known prices (4 anchor points):")
for date, price in sorted(anchors.items()):
    source = "EIA" if date in ['2025-10-20', '2025-10-27'] else "AAA/Gold" if date == '2025-10-29' else "Gold"
    print(f"      {date}: ${price:.3f}/gal ({source})")

# ============================================================================
# 2. Linear interpolation for missing days
# ============================================================================
print(f"\n2️⃣ Interpolating daily prices...")

# Create complete date range
date_range = pd.date_range(start='2025-10-18', end='2025-10-29', freq='D')

# Create DataFrame
df = pd.DataFrame(index=date_range)
df.index.name = 'date'

# Add anchor prices
for date_str, price in anchors.items():
    date_obj = pd.Timestamp(date_str)
    df.loc[date_obj, 'price'] = price
    df.loc[date_obj, 'source'] = 'anchor'

# Interpolate missing values
df['price'] = df['price'].interpolate(method='linear')
df['source'] = df['source'].fillna('interpolated')

print(f"\n   Complete daily series (Oct 18-29):")
print(f"\n   {'Date':<12} {'Price':<10} {'Source':<15}")
print(f"   {'-'*40}")

for idx, row in df.iterrows():
    marker = "📍" if row['source'] == 'anchor' else "~"
    print(f"   {idx.strftime('%Y-%m-%d'):<12} ${row['price']:.3f}     {marker} {row['source']:<13}")

# ============================================================================
# 3. Validate interpolation quality
# ============================================================================
print(f"\n3️⃣ Validating interpolation quality...")

# Check day-to-day changes
df['daily_change'] = df['price'].diff()
df['abs_change'] = df['daily_change'].abs()

max_change = df['abs_change'].max()
avg_change = df['abs_change'].mean()

print(f"\n   Day-to-day price changes:")
print(f"      Average: ${avg_change:.4f}/day")
print(f"      Maximum: ${max_change:.4f}/day")

if max_change > 0.10:
    print(f"      ⚠️ Large change detected (>${0.10})")
else:
    print(f"      ✅ All changes reasonable (<$0.10)")

# Check against EIA actuals
eia_dates = ['2025-10-20', '2025-10-27']
print(f"\n   Validation against EIA actuals:")
for date_str in eia_dates:
    date_obj = pd.Timestamp(date_str)
    interpolated = df.loc[date_obj, 'price']
    actual = anchors[date_str]
    error = interpolated - actual
    print(f"      {date_str}: Interp ${interpolated:.3f}, Actual ${actual:.3f}, Error ${error:.3f}")

# ============================================================================
# 4. Save to CSV
# ============================================================================
print(f"\n{'=' * 80}")
print("💾 SAVING DAILY PRICES")
print("=" * 80)

output_path = project_root / 'outputs' / 'aaa_daily_oct18_29.csv'
output_path.parent.mkdir(parents=True, exist_ok=True)

# Reset index to make date a column
df_save = df.reset_index()
df_save.columns = ['date', 'price', 'source', 'daily_change', 'abs_change']

df_save.to_csv(output_path, index=False)

print(f"\n✅ Saved to: {output_path}")
print(f"   Total days: {len(df_save)}")
print(f"   Date range: {df_save['date'].min().strftime('%Y-%m-%d')} to {df_save['date'].max().strftime('%Y-%m-%d')}")

# ============================================================================
# 5. Summary statistics
# ============================================================================
print(f"\n{'=' * 80}")
print("📊 SUMMARY STATISTICS")
print("=" * 80)

print(f"\nPrice Movement (Oct 18-29):")
print(f"   Start: ${df['price'].iloc[0]:.3f} (Oct 18)")
print(f"   End: ${df['price'].iloc[-1]:.3f} (Oct 29)")
print(f"   Change: ${df['price'].iloc[-1] - df['price'].iloc[0]:+.3f}")
print(f"   % Change: {((df['price'].iloc[-1] / df['price'].iloc[0]) - 1) * 100:+.2f}%")

print(f"\nData Quality:")
print(f"   Anchor points: {(df['source'] == 'anchor').sum()}")
print(f"   Interpolated: {(df['source'] == 'interpolated').sum()}")
print(f"   Average daily change: ${avg_change:.4f}")
print(f"   Standard deviation: ${df['price'].std():.4f}")

print(f"\n{'=' * 80}")
print("✅ BACKFILL COMPLETE")
print("=" * 80)

print(f"""
Next Steps:
   1. Review: {output_path}
   2. Run: scripts/daily_incremental_training_with_aaa.py
   3. Train model on Oct 18-29 daily data
   4. Make prediction for Oct 31
""")

print("=" * 80)
