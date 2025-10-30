#!/usr/bin/env python3
"""
Quick visualization of today's state price collection
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
STATE_PROJECT = PROJECT_ROOT / 'state_analysis'
DATA_FILE = STATE_PROJECT / 'data' / 'daily_snapshots' / 'state_prices_2025-10-29.csv'
OUTPUT_DIR = STATE_PROJECT / 'outputs'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load data
df = pd.read_csv(DATA_FILE)
df = df.sort_values('price', ascending=False)

print("=" * 80)
print("📊 STATE GAS PRICE VISUALIZATION")
print("=" * 80)
print(f"\nData: {DATA_FILE}")
print(f"Date: 2025-10-29")
print(f"States: {len(df)}")

# Calculate national average
simple_avg = df['price'].mean()
weighted_avg = (df['price'] * df['consumption_weight']).sum() / df['consumption_weight'].sum()

print(f"\nNational Average:")
print(f"  Simple: ${simple_avg:.3f}")
print(f"  Volume-weighted: ${weighted_avg:.3f}")

# Create visualization
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))

# Top: Bar chart of all states
colors = ['#e74c3c' if p > weighted_avg else '#3498db' for p in df['price']]
ax1.barh(range(len(df)), df['price'], color=colors, edgecolor='black', linewidth=0.5)
ax1.set_yticks(range(len(df)))
ax1.set_yticklabels(df['state'], fontsize=7)
ax1.axvline(x=weighted_avg, color='green', linestyle='--', linewidth=2, label=f'National Avg (weighted): ${weighted_avg:.3f}')
ax1.axvline(x=simple_avg, color='orange', linestyle='--', linewidth=2, label=f'National Avg (simple): ${simple_avg:.3f}')
ax1.set_xlabel('Price ($/gallon)', fontsize=12, fontweight='bold')
ax1.set_title('Gas Prices by State (October 29, 2025)', fontsize=14, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(axis='x', alpha=0.3)

# Add price labels on bars
for i, (idx, row) in enumerate(df.iterrows()):
    ax1.text(row['price'] + 0.05, i, f"${row['price']:.3f}", va='center', fontsize=6)

# Bottom: Top 10 and bottom 10
top_bottom = pd.concat([df.head(10), df.tail(10)])
colors_tb = ['#e74c3c'] * 10 + ['#27ae60'] * 10
ax2.barh(range(len(top_bottom)), top_bottom['price'], color=colors_tb, edgecolor='black', linewidth=1)
ax2.set_yticks(range(len(top_bottom)))
ax2.set_yticklabels([f"{row['state']} ({row['state_name']})" for _, row in top_bottom.iterrows()], fontsize=10)
ax2.axvline(x=weighted_avg, color='green', linestyle='--', linewidth=2, label=f'National Avg: ${weighted_avg:.3f}')
ax2.set_xlabel('Price ($/gallon)', fontsize=12, fontweight='bold')
ax2.set_title('Top 10 Most Expensive vs Bottom 10 Cheapest States', fontsize=14, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(axis='x', alpha=0.3)

# Add price labels
for i, (idx, row) in enumerate(top_bottom.iterrows()):
    ax2.text(row['price'] + 0.05, i, f"${row['price']:.3f}", va='center', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'state_prices_oct29.png', dpi=300, bbox_inches='tight')
print(f"\n✅ Saved visualization: {OUTPUT_DIR / 'state_prices_oct29.png'}")

# Print statistics
print(f"\n📊 Statistics:")
print(f"  Highest: {df.iloc[0]['state']} ({df.iloc[0]['state_name']}) = ${df.iloc[0]['price']:.3f}")
print(f"  Lowest: {df.iloc[-1]['state']} ({df.iloc[-1]['state_name']}) = ${df.iloc[-1]['price']:.3f}")
print(f"  Spread: ${df['price'].max() - df['price'].min():.3f}")
print(f"  Std Dev: ${df['price'].std():.3f}")

# Top impact states
df['contribution'] = df['price'] * df['consumption_weight'] / df['consumption_weight'].sum()
df = df.sort_values('contribution', ascending=False)

print(f"\n🎯 Top 5 States by Impact on National Average:")
for i, row in df.head(5).iterrows():
    impact_pct = (row['consumption_weight'] / df['consumption_weight'].sum()) * 100
    print(f"  {row['state']} ({row['state_name']}): ${row['price']:.3f} × {impact_pct:.1f}% = ${row['contribution']:.4f} contribution")

print("\n" + "=" * 80)
