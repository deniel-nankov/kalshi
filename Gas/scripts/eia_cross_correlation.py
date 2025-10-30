"""
Cross-Correlation Analysis with 200 Weeks of EIA Data
====================================================

Now that we have n=200 weeks with strong correlations (r=0.837-0.985),
test if states LEAD or LAG the national average.

Research Questions:
1. Do any states lead national by 1-4 weeks? (Early indicator?)
2. Do any states lag national by 1-4 weeks? (Late adopter?)
3. What is optimal lag for each state?
4. Is synchronous correlation (lag=0) strongest?

Methodology:
- Cross-correlation at lags -10 to +10 weeks
- Negative lag = state LEADS national
- Positive lag = state LAGS national
- Statistical significance testing

Expected Outcome:
Given r>0.9 at lag=0, likely see:
- Strongest correlation at lag=0 (synchronous)
- Minimal improvement at other lags
- Validates aggregation hypothesis (no lead/lag dynamics)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'state_analysis' / 'data'
RESULTS_DIR = BASE_DIR / 'results'
RESULTS_DIR.mkdir(exist_ok=True)

print("="*80)
print("CROSS-CORRELATION ANALYSIS WITH 200 WEEKS OF EIA DATA")
print("="*80)

# Load data
df_states = pd.read_csv(DATA_DIR / 'eia_state_prices_weekly.csv')
df_national = pd.read_csv(DATA_DIR / 'eia_national_average_weekly.csv')

# Convert dates
df_states['week'] = pd.to_datetime(df_states['date'])
df_national['week'] = pd.to_datetime(df_national['date'])

# Pivot to wide format
pivot = df_states.pivot(index='week', columns='state', values='price')
national_prices = df_national.set_index('week')['price']

# Align dates
common_weeks = pivot.index.intersection(national_prices.index)
pivot = pivot.loc[common_weeks].sort_index()
national_prices = national_prices.loc[common_weeks].sort_index()

states = pivot.columns.tolist()
n = len(common_weeks)

print(f"\n✅ Data loaded:")
print(f"   States: {len(states)}")
print(f"   Weeks: {n}")
print(f"   Date range: {common_weeks[0].date()} to {common_weeks[-1].date()}")

# Consumption weights
consumption_weights = {
    'CA': 0.111, 'TX': 0.094, 'FL': 0.062, 'NY': 0.047,
    'OH': 0.036, 'MA': 0.025, 'MN': 0.020, 'CO': 0.018, 'WA': 0.024
}

# Cross-correlation analysis
max_lag = 10
results = []

print(f"\n🔍 Computing cross-correlations (lags: -{max_lag} to +{max_lag})...")

for state in states:
    state_prices = pivot[state].values
    national = national_prices.values
    
    # Compute cross-correlation at each lag
    lag_corrs = []
    
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            # State leads: correlate state[0:n+lag] with national[-lag:n]
            s = state_prices[:lag]
            n_aligned = national[-lag:]
        elif lag > 0:
            # State lags: correlate state[lag:n] with national[0:n-lag]
            s = state_prices[lag:]
            n_aligned = national[:-lag]
        else:
            # Synchronous
            s = state_prices
            n_aligned = national
        
        # Compute correlation
        if len(s) > 10:
            r, p = stats.pearsonr(s, n_aligned)
            lag_corrs.append({
                'state': state,
                'lag': lag,
                'r': r,
                'p_value': p,
                'n': len(s)
            })
    
    # Find best lag
    best = max(lag_corrs, key=lambda x: abs(x['r']))
    
    # Get lag=0 for comparison
    lag0 = [x for x in lag_corrs if x['lag'] == 0][0]
    
    results.append({
        'state': state,
        'consumption_weight': consumption_weights.get(state, 0.0),
        'best_lag': best['lag'],
        'best_r': best['r'],
        'best_p': best['p_value'],
        'lag0_r': lag0['r'],
        'lag0_p': lag0['p_value'],
        'improvement': best['r'] - lag0['r'],
        'lag_corrs': lag_corrs
    })

df_results = pd.DataFrame(results)
df_results = df_results.sort_values('best_r', ascending=False)

print("\n" + "="*80)
print("CROSS-CORRELATION RESULTS")
print("="*80)

print(f"\n📊 Summary:")
print(f"   Mean best r: {df_results['best_r'].mean():.3f}")
print(f"   Mean lag=0 r: {df_results['lag0_r'].mean():.3f}")
print(f"   Mean improvement: {df_results['improvement'].mean():.4f}")
print(f"   States with |lag| > 0 best: {(df_results['best_lag'] != 0).sum()}/{len(df_results)}")

print(f"\n🔝 Best Correlations (any lag):")
print(df_results[['state', 'best_lag', 'best_r', 'lag0_r', 'improvement', 'consumption_weight']].head(9).to_string(index=False))

# Classify states
leading = df_results[df_results['best_lag'] < 0]
lagging = df_results[df_results['best_lag'] > 0]
synchronous = df_results[df_results['best_lag'] == 0]

print(f"\n📈 Classification:")
print(f"   Leading (lag < 0): {len(leading)} states")
if len(leading) > 0:
    for _, row in leading.iterrows():
        print(f"      {row['state']} ({row['consumption_weight']*100:.1f}%): lag={row['best_lag']}, r={row['best_r']:.3f}, Δr={row['improvement']:.4f}")

print(f"\n   Synchronous (lag = 0): {len(synchronous)} states")
if len(synchronous) > 0:
    for _, row in synchronous.iterrows():
        print(f"      {row['state']} ({row['consumption_weight']*100:.1f}%): r={row['lag0_r']:.3f}")

print(f"\n   Lagging (lag > 0): {len(lagging)} states")
if len(lagging) > 0:
    for _, row in lagging.iterrows():
        print(f"      {row['state']} ({row['consumption_weight']*100:.1f}%): lag={row['best_lag']}, r={row['best_r']:.3f}, Δr={row['improvement']:.4f}")

print(f"\n🏆 High-Consumption States (Top 4):")
for state in ['CA', 'TX', 'FL', 'NY']:
    row = df_results[df_results['state'] == state]
    if len(row) > 0:
        row = row.iloc[0]
        print(f"   {state} ({row['consumption_weight']*100:.1f}%): best_lag={row['best_lag']}, best_r={row['best_r']:.3f}, lag0_r={row['lag0_r']:.3f}, Δr={row['improvement']:.4f}")

# Visualization
fig, axes = plt.subplots(3, 3, figsize=(16, 12))
axes = axes.flatten()

for idx, state in enumerate(states):
    ax = axes[idx]
    
    # Get lag correlations for this state
    row = df_results[df_results['state'] == state].iloc[0]
    lag_data = pd.DataFrame(row['lag_corrs'])
    
    # Plot
    ax.plot(lag_data['lag'], lag_data['r'], marker='o', linewidth=2, markersize=6)
    
    # Highlight best lag
    best_lag = row['best_lag']
    best_r = row['best_r']
    ax.scatter([best_lag], [best_r], color='red', s=200, zorder=5, marker='*', 
               label=f'Best: lag={best_lag}, r={best_r:.3f}')
    
    # Highlight lag=0
    lag0_r = row['lag0_r']
    ax.scatter([0], [lag0_r], color='green', s=150, zorder=4, marker='o',
               label=f'Lag=0: r={lag0_r:.3f}')
    
    ax.axvline(0, color='gray', linestyle='--', alpha=0.5)
    ax.axhline(0, color='gray', linestyle='-', alpha=0.3)
    
    weight = consumption_weights.get(state, 0.0)
    ax.set_title(f'{state} ({weight*100:.1f}%)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Lag (weeks)', fontsize=10)
    ax.set_ylabel('Correlation (r)', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc='lower right')
    ax.set_ylim([0.7, 1.0])

plt.tight_layout()
plt.savefig(RESULTS_DIR / 'eia_cross_correlation_200weeks.png', dpi=300, bbox_inches='tight')
print(f"\n💾 Saved: {RESULTS_DIR / 'eia_cross_correlation_200weeks.png'}")

# Heatmap
fig, ax = plt.subplots(figsize=(12, 8))

# Create matrix of correlations
lag_range = range(-max_lag, max_lag + 1)
corr_matrix = np.zeros((len(states), len(lag_range)))

for i, state in enumerate(states):
    row = df_results[df_results['state'] == state].iloc[0]
    lag_data = pd.DataFrame(row['lag_corrs'])
    for j, lag in enumerate(lag_range):
        r = lag_data[lag_data['lag'] == lag]['r'].values[0]
        corr_matrix[i, j] = r

# Plot heatmap
im = ax.imshow(corr_matrix, cmap='RdYlGn', aspect='auto', vmin=0.7, vmax=1.0)

# Set ticks
ax.set_xticks(range(len(lag_range)))
ax.set_xticklabels(lag_range)
ax.set_yticks(range(len(states)))
ax.set_yticklabels([f"{s} ({consumption_weights.get(s, 0)*100:.1f}%)" for s in states])

ax.set_xlabel('Lag (weeks, negative = state leads)', fontsize=12)
ax.set_ylabel('State (consumption weight)', fontsize=12)
ax.set_title('Cross-Correlation Heatmap: State vs National Prices\n(n=200 weeks)', 
             fontsize=14, fontweight='bold')

# Add colorbar
cbar = plt.colorbar(im, ax=ax)
cbar.set_label('Correlation (r)', fontsize=12)

# Mark best lags
for i, state in enumerate(states):
    row = df_results[df_results['state'] == state].iloc[0]
    best_lag = row['best_lag']
    j = list(lag_range).index(best_lag)
    ax.plot(j, i, marker='*', color='red', markersize=15, markeredgecolor='black', markeredgewidth=1)

plt.tight_layout()
plt.savefig(RESULTS_DIR / 'eia_cross_correlation_heatmap.png', dpi=300, bbox_inches='tight')
print(f"💾 Saved: {RESULTS_DIR / 'eia_cross_correlation_heatmap.png'}")

# Save results
output_file = RESULTS_DIR / 'eia_cross_correlation_results.csv'
df_results[['state', 'consumption_weight', 'best_lag', 'best_r', 'lag0_r', 'improvement']].to_csv(output_file, index=False)
print(f"💾 Saved: {output_file}")

# Create report
report = f"""
EIA CROSS-CORRELATION ANALYSIS - 200 WEEKS
===========================================

Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
Data: {common_weeks[0].date()} to {common_weeks[-1].date()} ({n} weeks)
States: {len(states)}
Lag range: -{max_lag} to +{max_lag} weeks

INTERPRETATION
--------------
- Lag < 0: State LEADS national (potential predictor)
- Lag = 0: Synchronous (moves together)
- Lag > 0: State LAGS national (follower)

SUMMARY STATISTICS
------------------
Mean best correlation:     {df_results['best_r'].mean():.3f}
Mean synchronous (lag=0):  {df_results['lag0_r'].mean():.3f}
Mean improvement:          {df_results['improvement'].mean():.4f}

States with best lag ≠ 0:  {(df_results['best_lag'] != 0).sum()}/{len(df_results)}
Mean absolute best lag:    {abs(df_results['best_lag']).mean():.2f} weeks

CLASSIFICATION
--------------
Leading states (lag < 0):     {len(leading)}
Synchronous states (lag = 0): {len(synchronous)}
Lagging states (lag > 0):     {len(lagging)}

ALL STATES RANKED
-----------------
{df_results[['state', 'consumption_weight', 'best_lag', 'best_r', 'lag0_r', 'improvement']].to_string(index=False)}

HIGH-CONSUMPTION STATES (Top 4 = 31.4%)
----------------------------------------
"""

for state in ['CA', 'TX', 'FL', 'NY']:
    row = df_results[df_results['state'] == state]
    if len(row) > 0:
        row = row.iloc[0]
        classification = "LEADS" if row['best_lag'] < 0 else ("LAGS" if row['best_lag'] > 0 else "SYNCHRONOUS")
        report += f"""
{state} ({row['consumption_weight']*100:.1f}% of national):
  Classification: {classification}
  Best lag: {row['best_lag']} weeks
  Best r: {row['best_r']:.3f}
  Lag=0 r: {row['lag0_r']:.3f}
  Improvement: {row['improvement']:.4f} ({row['improvement']/row['lag0_r']*100:.2f}%)
"""

report += f"""

KEY FINDINGS
------------
1. Mean improvement from optimal lag: {df_results['improvement'].mean():.4f} ({df_results['improvement'].mean()/df_results['lag0_r'].mean()*100:.2f}%)
2. {len(synchronous)} states are synchronous (lag=0 is best)
3. {len(leading)} states lead, {len(lagging)} states lag
4. Maximum improvement: {df_results['improvement'].max():.4f} ({df_results.loc[df_results['improvement'].idxmax(), 'state']})

INTERPRETATION
--------------
"""

if df_results['improvement'].mean() < 0.01:
    report += """
✅ MINIMAL LEAD/LAG STRUCTURE DETECTED

Mean improvement from optimal lag is <1%, indicating:
- States move SYNCHRONOUSLY with national average
- No systematic leading or lagging dynamics
- States aggregate to national without predictive lead
- Validates aggregation hypothesis

CONCLUSION: State prices do NOT provide leading indicators.
They simply compose the national average in real-time.

This is a NEGATIVE but RIGOROUS result suitable for publication:
"200-week analysis shows state gas prices aggregate to national
average without systematic lead/lag structure (mean lag improvement
{df_results['improvement'].mean():.4f}, {df_results['improvement'].mean()/df_results['lag0_r'].mean()*100:.2f}%)."
"""
else:
    report += f"""
⚠️ SOME LEAD/LAG STRUCTURE DETECTED

Mean improvement: {df_results['improvement'].mean():.4f} ({df_results['improvement'].mean()/df_results['lag0_r'].mean()*100:.2f}%)

Proceed to Granger causality tests to determine if improvement is
statistically significant and predictively useful.
"""

report += f"""

NEXT STEPS
----------
1. Granger causality tests (GOLD STANDARD)
   - Test if states Granger-cause national prices
   - Requires p<0.05 for causal claim
   
2. If Granger p>0.05: Document null result (publishable!)
3. If Granger p<0.05: Consider model enhancement

FILES
-----
- Results: {output_file}
- Lag profiles: {RESULTS_DIR / 'eia_cross_correlation_200weeks.png'}
- Heatmap: {RESULTS_DIR / 'eia_cross_correlation_heatmap.png'}
"""

report_file = RESULTS_DIR / 'EIA_CROSS_CORRELATION_REPORT.md'
report_file.write_text(report)
print(f"💾 Saved: {report_file}")

print("\n" + "="*80)
print("✅ CROSS-CORRELATION ANALYSIS COMPLETE!")
print("="*80)

print(f"\nKey Finding:")
print(f"  • Mean improvement from optimal lag: {df_results['improvement'].mean():.4f} ({df_results['improvement'].mean()/df_results['lag0_r'].mean()*100:.2f}%)")
print(f"  • Synchronous states: {len(synchronous)}/{len(df_results)}")

if df_results['improvement'].mean() < 0.01:
    print(f"\n✅ CONCLUSION: MINIMAL LEAD/LAG STRUCTURE")
    print(f"   States move synchronously with national average.")
    print(f"   No systematic leading or lagging dynamics detected.")
    print(f"   Validates aggregation hypothesis!")
else:
    print(f"\n⚠️ CONCLUSION: SOME LEAD/LAG DETECTED")
    print(f"   Proceed to Granger causality for definitive test.")

print(f"\nNext: Run eia_granger_causality.py for gold standard test")
