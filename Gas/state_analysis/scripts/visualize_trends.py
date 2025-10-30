#!/usr/bin/env python3
"""
Create visualization of state vs national price trends
to understand the negative correlations
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Setup
PROJECT_ROOT = Path(__file__).parent.parent.parent
STATE_PROJECT = PROJECT_ROOT / 'state_analysis'
DATA_FILE = STATE_PROJECT / 'data' / 'historical_state_snapshot.csv'
OUTPUT_DIR = STATE_PROJECT / 'outputs'

# Load data
df = pd.read_csv(DATA_FILE)
df_recent = df[df['time_label'] != 'year_ago'].copy()

# Calculate national averages
national_data = []
for time_label in ['month_ago', 'week_ago', 'yesterday', 'current']:
    subset = df_recent[df_recent['time_label'] == time_label]
    weighted_avg = (subset['price'] * subset['consumption_weight']).sum() / subset['consumption_weight'].sum()
    national_data.append({
        'time': time_label,
        'price': weighted_avg
    })

# Plot top 5 weight states vs national
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Left plot: Top 5 consumption states
top_states = ['CA', 'TX', 'FL', 'NY', 'PA']
time_labels = ['month_ago', 'week_ago', 'yesterday', 'current']
x = np.arange(len(time_labels))

for state in top_states:
    state_data = df_recent[df_recent['state'] == state]
    prices = [state_data[state_data['time_label'] == t]['price'].values[0] 
              for t in time_labels]
    weight = state_data['consumption_weight'].iloc[0]
    ax1.plot(x, prices, marker='o', label=f'{state} ({weight*100:.1f}%)', linewidth=2)

national_prices = [d['price'] for d in national_data]
ax1.plot(x, national_prices, 'k--', marker='s', label='National (weighted)', linewidth=3)

ax1.set_xlabel('Time Period', fontsize=12)
ax1.set_ylabel('Price ($/gal)', fontsize=12)
ax1.set_title('Top 5 Consumption States vs National Average', fontsize=14, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(['Month Ago\n(Sep 29)', 'Week Ago\n(Oct 22)', 'Yesterday\n(Oct 28)', 'Today\n(Oct 29)'])
ax1.legend(loc='best', fontsize=10)
ax1.grid(True, alpha=0.3)

# Right plot: Price changes
changes_data = []
for state in top_states:
    state_subset = df_recent[df_recent['state'] == state]
    current = state_subset[state_subset['time_label'] == 'current']['price'].values[0]
    week_ago = state_subset[state_subset['time_label'] == 'week_ago']['price'].values[0]
    month_ago = state_subset[state_subset['time_label'] == 'month_ago']['price'].values[0]
    
    changes_data.append({
        'state': state,
        'week_change': current - week_ago,
        'month_change': current - month_ago
    })

# National changes
national_current = national_prices[3]
national_week = national_prices[1]
national_month = national_prices[0]

changes_data.append({
    'state': 'National',
    'week_change': national_current - national_week,
    'month_change': national_current - national_month
})

changes_df = pd.DataFrame(changes_data)
x2 = np.arange(len(changes_df))
width = 0.35

bars1 = ax2.bar(x2 - width/2, changes_df['week_change'], width, label='Week-over-week', alpha=0.8)
bars2 = ax2.bar(x2 + width/2, changes_df['month_change'], width, label='Month-over-month', alpha=0.8)

# Color code bars (green=decrease, red=increase)
for i, bar in enumerate(bars1):
    if changes_df['week_change'].iloc[i] < 0:
        bar.set_color('green')
    else:
        bar.set_color('red')
        
for i, bar in enumerate(bars2):
    if changes_df['month_change'].iloc[i] < 0:
        bar.set_color('darkgreen')
    else:
        bar.set_color('darkred')

ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax2.set_xlabel('State', fontsize=12)
ax2.set_ylabel('Price Change ($/gal)', fontsize=12)
ax2.set_title('Price Changes by State (Negative = Decrease)', fontsize=14, fontweight='bold')
ax2.set_xticks(x2)
ax2.set_xticklabels(changes_df['state'])
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'state_vs_national_trends.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved visualization: {OUTPUT_DIR / 'state_vs_national_trends.png'}")

# Print summary
print("\n" + "="*70)
print("KEY OBSERVATION")
print("="*70)

print("\nNational price trend:")
print(f"  Month ago → Current: ${national_month:.3f} → ${national_current:.3f} = {(national_current-national_month):.3f} ({(national_current/national_month-1)*100:.1f}%)")
print(f"  Week ago → Current: ${national_week:.3f} → ${national_current:.3f} = {(national_current-national_week):.3f} ({(national_current/national_week-1)*100:.1f}%)")

print("\nTop 5 states price trends:")
for state in top_states:
    state_subset = df_recent[df_recent['state'] == state]
    current = state_subset[state_subset['time_label'] == 'current']['price'].values[0]
    month_ago_val = state_subset[state_subset['time_label'] == 'month_ago']['price'].values[0]
    change = current - month_ago_val
    pct = (current/month_ago_val - 1) * 100
    print(f"  {state}: ${month_ago_val:.3f} → ${current:.3f} = {change:+.3f} ({pct:+.1f}%)")

print("\n💡 INTERPRETATION:")
print("If all states followed national trend perfectly:")
print("  • All correlations would be ~1.0")
print("  • All price changes would be similar")
print("\nWhat we see:")
print("  • Negative/low correlations")
print("  • Different price change magnitudes")
print("\nThis suggests:")
print("  ✅ States have INDEPENDENT dynamics!")
print("  ✅ State features MIGHT improve forecasts")
print("  ⚠️  BUT: Only 4 time points = insufficient for conclusions")
print("\nNext step:")
print("  • Collect daily data for 30 days")
print("  • Re-run correlation with 30 points")
print("  • Test Granger causality")
print("  • Then add state features if validated")

plt.show()
