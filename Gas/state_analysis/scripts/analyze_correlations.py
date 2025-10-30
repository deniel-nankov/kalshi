#!/usr/bin/env python3
"""
State-Level Correlation Analysis

Analyzes which states move together and which states drive national average.

Requirements: 30+ days of state price data

Usage:
    python state_analysis/scripts/analyze_correlations.py
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

PROJECT_ROOT = Path(__file__).parent.parent.parent
STATE_PROJECT = PROJECT_ROOT / 'state_analysis'
DATA_FILE = STATE_PROJECT / 'data' / 'historical_state_prices.csv'
OUTPUT_DIR = STATE_PROJECT / 'outputs'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("📊 STATE-LEVEL CORRELATION ANALYSIS")
print("=" * 80)

# Check if data exists
if not DATA_FILE.exists():
    print(f"\n❌ ERROR: No historical data found!")
    print(f"   Expected: {DATA_FILE}")
    print(f"\n   Run data collection first:")
    print(f"   python state_analysis/scripts/collect_state_prices.py")
    sys.exit(1)

# Load data
df = pd.read_csv(DATA_FILE)
df['date'] = pd.to_datetime(df['date'])

print(f"\n✅ Loaded: {len(df)} records")
print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
print(f"   Days: {df['date'].nunique()}")
print(f"   States: {df['state'].nunique()}")

# Check if enough data
n_days = df['date'].nunique()
if n_days < 30:
    print(f"\n⚠️  WARNING: Only {n_days} days of data")
    print(f"   Recommended: 30+ days for reliable correlation analysis")
    print(f"   Need {30 - n_days} more days")
    print(f"\n   Continue anyway? Results may not be statistically significant.")

# Pivot to wide format (dates as rows, states as columns)
price_matrix = df.pivot(index='date', columns='state', values='price')

print(f"\n📊 Creating correlation matrix...")

# Calculate correlation matrix
corr_matrix = price_matrix.corr()

# Save
corr_matrix.to_csv(OUTPUT_DIR / 'state_correlation_matrix.csv')
print(f"   ✅ Saved: {OUTPUT_DIR / 'state_correlation_matrix.csv'}")

# Visualize
fig, ax = plt.subplots(figsize=(16, 14))
sns.heatmap(corr_matrix, cmap='RdYlGn', center=0.95, vmin=0.8, vmax=1.0,
            square=True, linewidths=0.5, cbar_kws={"shrink": 0.8},
            annot=False, fmt='.2f', ax=ax)
ax.set_title(f'State Gas Price Correlations ({n_days} days)', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'correlation_heatmap.png', dpi=300, bbox_inches='tight')
print(f"   ✅ Saved: {OUTPUT_DIR / 'correlation_heatmap.png'}")

print(f"\n📊 Top 10 Most Correlated State Pairs:")
# Get upper triangle (avoid duplicates)
corr_upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
corr_pairs = corr_upper.stack().sort_values(ascending=False).head(10)

for (state1, state2), corr in corr_pairs.items():
    print(f"   {state1} <-> {state2}: {corr:.4f}")

print(f"\n✅ Analysis complete! Check {OUTPUT_DIR} for results.")
print("=" * 80)
