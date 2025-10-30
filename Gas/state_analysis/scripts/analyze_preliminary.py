#!/usr/bin/env python3
"""
PRELIMINARY STATE-LEVEL ANALYSIS

Analyzes the historical state data we just collected to determine:
1. Which states correlate most with national average?
2. Do any states show leading/lagging patterns?
3. Price change trends (week-over-week, month-over-month)
4. Should we add state features to the model?
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Setup
PROJECT_ROOT = Path(__file__).parent.parent.parent
STATE_PROJECT = PROJECT_ROOT / 'state_analysis'
DATA_FILE = STATE_PROJECT / 'data' / 'historical_state_snapshot.csv'
OUTPUT_DIR = STATE_PROJECT / 'outputs'
OUTPUT_DIR.mkdir(exist_ok=True)

print("="*70)
print("PRELIMINARY STATE-LEVEL ANALYSIS")
print("="*70)

# Load data
df = pd.read_csv(DATA_FILE)
print(f"\nLoaded {len(df)} records")
print(f"  States: {df['state'].nunique()}")
print(f"  Dates: {df['date'].nunique()}")
print(f"  Time points: {df['time_label'].nunique()}")

# Focus on recent data (exclude year_ago for now)
df_recent = df[df['time_label'] != 'year_ago'].copy()
print(f"\nRecent data (excluding year_ago): {len(df_recent)} records")

# Calculate national averages for each time point
print("\n" + "="*70)
print("NATIONAL AVERAGES (VOLUME-WEIGHTED)")
print("="*70)

national_avgs = []
for time_label in ['current', 'yesterday', 'week_ago', 'month_ago']:
    subset = df_recent[df_recent['time_label'] == time_label]
    if len(subset) > 0:
        weighted_avg = (subset['price'] * subset['consumption_weight']).sum() / subset['consumption_weight'].sum()
        national_avgs.append({
            'time_label': time_label,
            'date': subset['date'].iloc[0],
            'national_price': weighted_avg
        })
        print(f"{time_label:12s} ({subset['date'].iloc[0]}): ${weighted_avg:.3f}")

national_df = pd.DataFrame(national_avgs)

# Calculate price changes
print("\n" + "="*70)
print("NATIONAL PRICE CHANGES")
print("="*70)

current_price = national_df[national_df['time_label'] == 'current']['national_price'].values[0]
yesterday_price = national_df[national_df['time_label'] == 'yesterday']['national_price'].values[0]
week_ago_price = national_df[national_df['time_label'] == 'week_ago']['national_price'].values[0]
month_ago_price = national_df[national_df['time_label'] == 'month_ago']['national_price'].values[0]

print(f"Day-over-day: ${current_price - yesterday_price:+.3f} ({(current_price/yesterday_price - 1)*100:+.2f}%)")
print(f"Week-over-week: ${current_price - week_ago_price:+.3f} ({(current_price/week_ago_price - 1)*100:+.2f}%)")
print(f"Month-over-month: ${current_price - month_ago_price:+.3f} ({(current_price/month_ago_price - 1)*100:+.2f}%)")

# State-level analysis
print("\n" + "="*70)
print("STATE-LEVEL CORRELATION WITH NATIONAL")
print("="*70)

# Pivot to get state×time matrix
pivot = df_recent.pivot_table(index='state', columns='time_label', values='price')
pivot = pivot[['month_ago', 'week_ago', 'yesterday', 'current']]  # Chronological order

# For each state, calculate correlation with national trend
correlations = []
for state in pivot.index:
    state_prices = pivot.loc[state].values
    
    # Simple correlation with national prices
    national_prices = national_df.sort_values('time_label')['national_price'].values[:4]  # Match order
    
    if len(state_prices) == len(national_prices) and not np.any(np.isnan(state_prices)):
        corr, p_value = stats.pearsonr(state_prices, national_prices)
        
        # Calculate price changes
        current = pivot.loc[state, 'current']
        week_ago = pivot.loc[state, 'week_ago']
        month_ago = pivot.loc[state, 'month_ago']
        
        weight = df_recent[df_recent['state'] == state]['consumption_weight'].iloc[0]
        
        correlations.append({
            'state': state,
            'correlation': corr,
            'p_value': p_value,
            'current_price': current,
            'week_change': current - week_ago,
            'month_change': current - month_ago,
            'weight': weight,
        })

corr_df = pd.DataFrame(correlations).sort_values('correlation', ascending=False)

print("\nTop 10 states most correlated with national trend:")
print(corr_df.head(10)[['state', 'correlation', 'current_price', 'weight']].to_string(index=False))

print("\nBottom 10 states (least correlated):")
print(corr_df.tail(10)[['state', 'correlation', 'current_price', 'weight']].to_string(index=False))

# Weighted correlation (by consumption weight)
print("\n" + "="*70)
print("HIGH-WEIGHT STATES (Top 10 by consumption)")
print("="*70)

top_weight = corr_df.nlargest(10, 'weight')
print(top_weight[['state', 'correlation', 'weight', 'current_price', 'week_change']].to_string(index=False))

# Check if high-weight states drive national
weighted_corr_sum = (corr_df['correlation'] * corr_df['weight']).sum()
print(f"\nWeighted-average correlation: {weighted_corr_sum:.3f}")
print("(Should be ~1.0 if high-weight states drive national perfectly)")

# Price volatility analysis
print("\n" + "="*70)
print("PRICE VOLATILITY (Week-over-week changes)")
print("="*70)

volatility = corr_df.copy()
volatility['abs_week_change'] = volatility['week_change'].abs()
volatility = volatility.sort_values('abs_week_change', ascending=False)

print("\nMost volatile states (largest week-over-week changes):")
print(volatility.head(10)[['state', 'week_change', 'current_price', 'weight']].to_string(index=False))

print("\nMost stable states (smallest week-over-week changes):")
print(volatility.tail(10)[['state', 'week_change', 'current_price', 'weight']].to_string(index=False))

# Regional patterns
print("\n" + "="*70)
print("REGIONAL PRICE PATTERNS")
print("="*70)

regions = {
    'West Coast': ['CA', 'WA', 'OR'],
    'Southwest': ['AZ', 'NV', 'NM', 'UT'],
    'South': ['TX', 'LA', 'OK', 'AR', 'MS', 'AL', 'GA', 'FL', 'SC', 'NC', 'TN'],
    'Midwest': ['IL', 'IN', 'OH', 'MI', 'WI', 'MN', 'IA', 'MO', 'KS', 'NE', 'SD', 'ND'],
    'Northeast': ['NY', 'PA', 'NJ', 'CT', 'MA', 'RI', 'NH', 'VT', 'ME'],
    'Mountain': ['CO', 'WY', 'MT', 'ID'],
}

region_stats = []
for region_name, states in regions.items():
    region_data = corr_df[corr_df['state'].isin(states)]
    if len(region_data) > 0:
        region_stats.append({
            'region': region_name,
            'avg_price': region_data['current_price'].mean(),
            'avg_corr': region_data['correlation'].mean(),
            'avg_week_change': region_data['week_change'].mean(),
            'n_states': len(region_data),
        })

region_df = pd.DataFrame(region_stats).sort_values('avg_price', ascending=False)
print("\nRegional averages:")
print(region_df.to_string(index=False))

# KEY INSIGHT: Can state features improve model?
print("\n" + "="*70)
print("🎯 KEY QUESTION: SHOULD WE ADD STATE FEATURES?")
print("="*70)

print("\n1. CORRELATION ANALYSIS:")
high_corr_states = corr_df[corr_df['correlation'] > 0.95]
print(f"   States with r > 0.95: {len(high_corr_states)}/51 ({len(high_corr_states)/51*100:.1f}%)")
print(f"   Average correlation: {corr_df['correlation'].mean():.3f}")

print("\n2. HIGH-WEIGHT STATE ANALYSIS:")
top5_weight = corr_df.nlargest(5, 'weight')
print(f"   Top 5 states by weight: {', '.join(top5_weight['state'].values)}")
print(f"   Combined weight: {top5_weight['weight'].sum():.1f}%")
print(f"   Average correlation: {top5_weight['correlation'].mean():.3f}")

print("\n3. PRICE CHANGE CONSISTENCY:")
week_change_std = corr_df['week_change'].std()
print(f"   Std dev of week-over-week changes: ${week_change_std:.3f}")
print(f"   National week-over-week change: ${current_price - week_ago_price:.3f}")
print(f"   Coefficient of variation: {week_change_std / abs(current_price - week_ago_price):.2f}")

# RECOMMENDATION
print("\n" + "="*70)
print("💡 PRELIMINARY RECOMMENDATION")
print("="*70)

avg_corr = corr_df['correlation'].mean()
top5_corr = top5_weight['correlation'].mean()

if avg_corr > 0.95 and top5_corr > 0.98:
    print("\n✅ HYPOTHESIS 1 LIKELY: States are just components of national")
    print(f"   • Average correlation: {avg_corr:.3f} (very high!)")
    print(f"   • Top 5 states: {top5_corr:.3f} (near perfect)")
    print("\n   Implication: State features probably REDUNDANT")
    print("   • National price = Σ(State_i × Weight_i)")
    print("   • Adding state lags unlikely to improve model")
    print("   • Current 108 features already capture national trends")
    
elif avg_corr < 0.90:
    print("\n🔬 HYPOTHESIS 2 POSSIBLE: Some states may lead/lag")
    print(f"   • Average correlation: {avg_corr:.3f} (moderate)")
    print(f"   • Suggests independence or timing differences")
    print("\n   Implication: State features MIGHT help")
    print("   • Test lag features: CA_lag1, TX_lag1, etc.")
    print("   • Run Granger causality when we have daily data")
    print("   • Potential 5-15% improvement")
    
else:
    print("\n⚠️  MIXED RESULTS: Need more data")
    print(f"   • Average correlation: {avg_corr:.3f}")
    print(f"   • Not conclusive with only 4 time points")
    print("\n   Recommendation: Continue daily collection")
    print("   • Collect 30 consecutive days")
    print("   • Re-run analysis with daily data")
    print("   • Then decide on model enhancement")

print("\n4. IMMEDIATE ACTION:")
print("\n   For Oct 31 submission (tomorrow):")
print("   ❌ Do NOT add state features (insufficient data)")
print("   ✅ Keep current model ($3.046/gal, MAE $0.0214)")
print("   ✅ Add this analysis to 'Future Work' section")
print("\n   For next month:")
print("   ✅ Continue daily state collection")
print("   ✅ Re-run analysis with 30+ days")
print("   ✅ If states lead: Add top 3-5 state lag features")
print("   ✅ If states redundant: Document finding (still valuable!)")

# Save correlation results
output_file = OUTPUT_DIR / 'state_correlations_preliminary.csv'
corr_df.to_csv(output_file, index=False)
print(f"\n✅ Saved correlation analysis: {output_file}")

print("\n" + "="*70)
print("ANALYSIS COMPLETE!")
print("="*70)
