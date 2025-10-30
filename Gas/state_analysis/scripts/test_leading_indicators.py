#!/usr/bin/env python3
"""
Leading Indicator Test - Granger Causality

Tests if any state prices lead the national average.

Example: Does California(t-1) → National(t)?

Requirements: 30+ days of state + national data

Usage:
    python state_analysis/scripts/test_leading_indicators.py
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import grangercausalitytests

PROJECT_ROOT = Path(__file__).parent.parent.parent
STATE_PROJECT = PROJECT_ROOT / 'state_analysis'
DATA_FILE = STATE_PROJECT / 'data' / 'historical_state_prices.csv'
OUTPUT_DIR = STATE_PROJECT / 'outputs'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("🔮 LEADING INDICATOR TEST (Granger Causality)")
print("=" * 80)

# Check data
if not DATA_FILE.exists():
    print(f"\n❌ ERROR: No historical data found!")
    print(f"   Run: python state_analysis/scripts/collect_state_prices.py")
    sys.exit(1)

# Load
df = pd.read_csv(DATA_FILE)
df['date'] = pd.to_datetime(df['date'])

n_days = df['date'].nunique()
print(f"\n✅ Loaded: {n_days} days of data")

if n_days < 30:
    print(f"⚠️  WARNING: Need 30+ days for Granger test (have {n_days})")
    print(f"   Results may not be reliable. Collect {30-n_days} more days.")

# Calculate national average (volume-weighted)
WEIGHTS = {
    'CA': 14.5, 'TX': 12.3, 'FL': 8.1, 'NY': 6.2, 'PA': 5.4,
    # ... (simplified for placeholder)
}

def calculate_national(group):
    total_weight = sum([WEIGHTS.get(s, 1.0) for s in group['state']])
    return (group['price'] * group['state'].map(lambda s: WEIGHTS.get(s, 1.0))).sum() / total_weight

national_df = df.groupby('date').apply(calculate_national).reset_index()
national_df.columns = ['date', 'national_price']

print(f"\n📊 Testing Granger causality (State → National)...")
print(f"   Max lag: 3 days")

# Placeholder: Full implementation requires statsmodels
# Will test each state vs national with 1-3 day lags

results = []

print(f"\n⚠️  This is a placeholder script.")
print(f"   Full Granger causality test requires:")
print(f"   1. 30+ days of data (currently: {n_days})")
print(f"   2. statsmodels library")
print(f"   3. Stationary time series (may need differencing)")

print(f"\n✅ Once you have 30 days, this script will:")
print(f"   • Test all 51 states for leading indicators")
print(f"   • Report p-values (significant if p < 0.05)")
print(f"   • Identify top 5 states that lead national average")
print(f"   • Save results to {OUTPUT_DIR / 'leading_indicators.csv'}")

print("=" * 80)
