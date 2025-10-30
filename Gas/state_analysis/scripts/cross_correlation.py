"""
Cross-Correlation Analysis: Do States Lead or Lag National Average?

Goal: Identify if any states systematically lead/lag the national average
      even with our limited 4-point dataset

Method: Compute cross-correlation at different lags for each state
        Note: With only 4 points, we can test lags -2 to +2 at most

Author: Research Team
Date: October 29, 2025
"""

import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_style('whitegrid')


def load_data():
    """Load historical state data and consumption weights"""
    data_file = Path('state_analysis/data/historical_state_snapshot.csv')
    df = pd.read_csv(data_file)
    return df


def compute_cross_correlation(x: np.ndarray, y: np.ndarray, max_lag: int = 2):
    """
    Compute cross-correlation between two time series at different lags
    
    Args:
        x: State time series
        y: National time series
        max_lag: Maximum lag to test (positive and negative)
    
    Returns:
        dict: {lag: correlation} for lags from -max_lag to +max_lag
    """
    n = len(x)
    correlations = {}
    
    for lag in range(-max_lag, max_lag + 1):
        if lag == 0:
            # Zero lag - standard correlation
            r = np.corrcoef(x, y)[0, 1]
        elif lag > 0:
            # Positive lag: y leads x (national leads state)
            # Compare x[lag:] with y[:-lag]
            if n - lag >= 2:  # Need at least 2 points
                r = np.corrcoef(x[lag:], y[:-lag])[0, 1]
            else:
                r = np.nan
        else:
            # Negative lag: x leads y (state leads national)
            # Compare x[:lag] with y[-lag:]
            lag_abs = abs(lag)
            if n - lag_abs >= 2:
                r = np.corrcoef(x[:-lag_abs], y[lag_abs:])[0, 1]
            else:
                r = np.nan
        
        correlations[lag] = r
    
    return correlations


def analyze_all_states():
    """
    Analyze cross-correlation for all states
    """
    print("\n" + "="*60)
    print("🔍 CROSS-CORRELATION ANALYSIS: State vs National")
    print("="*60 + "\n")
    print("Goal: Identify if states lead/lag national average")
    print("Note: Limited to ±2 day lags due to small sample (n=4)\n")
    
    # Load data
    df = load_data()
    
    # Get national average (volume-weighted)
    # We'll compute it from state data
    states = df['state'].unique()
    time_labels = sorted(df['time_label'].unique(), reverse=True)  # Most recent first
    
    # Map time labels to numeric indices
    time_to_idx = {label: idx for idx, label in enumerate(time_labels)}
    
    # For each time point, compute national average
    national_prices = []
    for time_label in time_labels:
        time_df = df[df['time_label'] == time_label]
        weighted_avg = (time_df['price'] * time_df['consumption_weight']).sum() / time_df['consumption_weight'].sum()
        national_prices.append(weighted_avg)
    
    national_prices = np.array(national_prices)
    
    print(f"Time points: {time_labels}")
    print(f"National prices: {national_prices}")
    print(f"\n{'='*60}\n")
    
    # Analyze each state
    results = []
    
    for state in states:
        state_df = df[df['state'] == state].copy()
        state_df['time_idx'] = state_df['time_label'].map(time_to_idx)
        state_df = state_df.sort_values('time_idx')
        
        state_prices = state_df['price'].values
        state_name = state_df['state_name'].iloc[0]
        weight = state_df['consumption_weight'].iloc[0]
        
        # Compute cross-correlation
        cross_corr = compute_cross_correlation(state_prices, national_prices, max_lag=2)
        
        # Find lag with maximum absolute correlation
        best_lag = max(cross_corr.keys(), key=lambda k: abs(cross_corr[k]) if not np.isnan(cross_corr[k]) else -1)
        best_r = cross_corr[best_lag]
        
        results.append({
            'state': state,
            'state_name': state_name,
            'weight': weight,
            'r_lag_neg2': cross_corr.get(-2, np.nan),
            'r_lag_neg1': cross_corr.get(-1, np.nan),
            'r_lag_0': cross_corr.get(0, np.nan),
            'r_lag_pos1': cross_corr.get(1, np.nan),
            'r_lag_pos2': cross_corr.get(2, np.nan),
            'best_lag': best_lag,
            'best_r': best_r,
        })
    
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('best_r', ascending=False)
    
    # Save results
    output_file = Path('state_analysis/outputs/cross_correlation_results.csv')
    results_df.to_csv(output_file, index=False)
    print(f"✅ Saved results: {output_file}\n")
    
    # Print summary
    print("="*80)
    print("TOP 10 STATES: Best Correlation (Any Lag)")
    print("="*80)
    print(f"{'State':<6} {'Name':<20} {'Weight':<8} {'Best Lag':<10} {'Best r':<10} {'Interpretation'}")
    print("-"*80)
    
    for _, row in results_df.head(10).iterrows():
        if row['best_lag'] < 0:
            interp = f"State leads by {abs(row['best_lag'])} day(s)"
        elif row['best_lag'] > 0:
            interp = f"National leads by {row['best_lag']} day(s)"
        else:
            interp = "Synchronous"
        
        print(f"{row['state']:<6} {row['state_name']:<20} {row['weight']:<8.3f} {row['best_lag']:<10} {row['best_r']:<10.3f} {interp}")
    
    # Leading states (negative lag)
    print(f"\n{'='*80}")
    print("LEADING STATES: State Leads National (lag < 0)")
    print(f"{'='*80}")
    
    leading = results_df[results_df['best_lag'] < 0].sort_values('best_r', ascending=False)
    
    if len(leading) > 0:
        print(f"{'State':<6} {'Name':<20} {'Weight':<8} {'Lead':<10} {'r':<10}")
        print("-"*60)
        for _, row in leading.head(10).iterrows():
            print(f"{row['state']:<6} {row['state_name']:<20} {row['weight']:<8.3f} {abs(row['best_lag'])} day(s)  {row['best_r']:<10.3f}")
    else:
        print("No states show leading patterns with this limited data.")
    
    # Lagging states (positive lag)
    print(f"\n{'='*80}")
    print("LAGGING STATES: National Leads State (lag > 0)")
    print(f"{'='*80}")
    
    lagging = results_df[results_df['best_lag'] > 0].sort_values('best_r', ascending=False)
    
    if len(lagging) > 0:
        print(f"{'State':<6} {'Name':<20} {'Weight':<8} {'Lag':<10} {'r':<10}")
        print("-"*60)
        for _, row in lagging.head(10).iterrows():
            print(f"{row['state']:<6} {row['state_name']:<20} {row['weight']:<8.3f} {row['best_lag']} day(s)  {row['best_r']:<10.3f}")
    else:
        print("No states show lagging patterns with this limited data.")
    
    # High-weight states
    print(f"\n{'='*80}")
    print("HIGH-WEIGHT STATES: Top 5 Consumption")
    print(f"{'='*80}")
    
    top_weight = results_df.nlargest(5, 'weight')
    print(f"{'State':<6} {'Name':<20} {'Weight':<8} {'Best Lag':<10} {'Best r':<10}")
    print("-"*60)
    for _, row in top_weight.iterrows():
        print(f"{row['state']:<6} {row['state_name']:<20} {row['weight']:<8.3f} {row['best_lag']:<10} {row['best_r']:<10.3f}")
    
    return results_df


def create_heatmap(results_df: pd.DataFrame):
    """
    Create heatmap of cross-correlations
    """
    print(f"\n{'='*60}")
    print("📊 CREATING CROSS-CORRELATION HEATMAP")
    print(f"{'='*60}\n")
    
    # Prepare data for heatmap
    lag_cols = ['r_lag_neg2', 'r_lag_neg1', 'r_lag_0', 'r_lag_pos1', 'r_lag_pos2']
    lag_labels = ['-2 days', '-1 day', '0 days', '+1 day', '+2 days']
    
    # Get top 20 states by consumption weight
    top_states = results_df.nlargest(20, 'weight')
    
    # Build matrix
    heatmap_data = top_states[lag_cols].values
    state_labels = top_states['state'].values
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 12))
    
    # Create heatmap
    im = ax.imshow(heatmap_data, cmap='RdBu_r', aspect='auto', vmin=-1, vmax=1)
    
    # Set ticks
    ax.set_xticks(np.arange(len(lag_labels)))
    ax.set_yticks(np.arange(len(state_labels)))
    ax.set_xticklabels(lag_labels)
    ax.set_yticklabels(state_labels)
    
    # Rotate x labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    # Add colorbar
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Correlation", rotation=-90, va="bottom")
    
    # Add values to cells
    for i in range(len(state_labels)):
        for j in range(len(lag_labels)):
            value = heatmap_data[i, j]
            if not np.isnan(value):
                text = ax.text(j, i, f'{value:.2f}',
                             ha="center", va="center", color="black", fontsize=8)
    
    ax.set_title("Cross-Correlation Heatmap: State vs National (Top 20 States)", 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel("Lag (negative = state leads national)", fontsize=12)
    ax.set_ylabel("State", fontsize=12)
    
    plt.tight_layout()
    
    # Save
    output_file = Path('state_analysis/outputs/cross_correlation_heatmap.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_file}")
    
    plt.close()


def create_lag_profile_plots(results_df: pd.DataFrame):
    """
    Create line plots showing correlation vs lag for interesting states
    """
    print(f"\n{'='*60}")
    print("📈 CREATING LAG PROFILE PLOTS")
    print(f"{'='*60}\n")
    
    # Select interesting states
    # Top 5 by weight + top 5 by best correlation
    top_weight = results_df.nlargest(5, 'weight')['state'].values
    top_corr = results_df.nlargest(5, 'best_r')['state'].values
    interesting = list(set(list(top_weight) + list(top_corr)))
    
    fig, axes = plt.subplots(2, 5, figsize=(16, 8))
    axes = axes.flatten()
    
    lag_cols = ['r_lag_neg2', 'r_lag_neg1', 'r_lag_0', 'r_lag_pos1', 'r_lag_pos2']
    lags = [-2, -1, 0, 1, 2]
    
    for idx, state in enumerate(interesting[:10]):
        ax = axes[idx]
        
        row = results_df[results_df['state'] == state].iloc[0]
        correlations = [row[col] for col in lag_cols]
        
        ax.plot(lags, correlations, 'o-', linewidth=2, markersize=8)
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
        ax.axvline(x=row['best_lag'], color='r', linestyle=':', alpha=0.7, label='Best lag')
        
        ax.set_title(f"{row['state']} ({row['weight']:.1%})", fontsize=10, fontweight='bold')
        ax.set_xlabel('Lag (days)', fontsize=9)
        ax.set_ylabel('Correlation', fontsize=9)
        ax.set_ylim([-1, 1])
        ax.grid(True, alpha=0.3)
        
        if idx == 0:
            ax.legend(fontsize=8)
    
    # Hide unused subplots
    for idx in range(len(interesting), 10):
        axes[idx].axis('off')
    
    plt.suptitle('Cross-Correlation Profiles: Correlation vs Lag', 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    # Save
    output_file = Path('state_analysis/outputs/lag_profiles.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_file}")
    
    plt.close()


def create_summary_report(results_df: pd.DataFrame):
    """
    Create markdown summary report
    """
    output_file = Path('state_analysis/outputs/CROSS_CORRELATION_REPORT.md')
    
    with open(output_file, 'w') as f:
        f.write("# 🔍 Cross-Correlation Analysis Report\n\n")
        f.write("**Date:** October 29, 2025  \n")
        f.write("**Sample Size:** n = 4 time points  \n")
        f.write("**Lags Tested:** -2 to +2 days  \n\n")
        
        f.write("---\n\n")
        f.write("## 🎯 PURPOSE\n\n")
        f.write("Determine if any states systematically **lead** or **lag** the national average, ")
        f.write("which could indicate:\n")
        f.write("- Regional price discovery (some markets lead others)\n")
        f.write("- Supply chain effects (upstream states influence downstream)\n")
        f.write("- Predictive value (leading states could improve forecasts)\n\n")
        
        f.write("---\n\n")
        f.write("## 📊 KEY FINDINGS\n\n")
        
        # Leading states
        leading = results_df[results_df['best_lag'] < 0].sort_values('best_r', ascending=False)
        
        if len(leading) > 0:
            f.write("### States That Lead National Average\n\n")
            f.write("| State | Name | Weight | Lead | Best r |\n")
            f.write("|-------|------|--------|------|--------|\n")
            for _, row in leading.head(10).iterrows():
                f.write(f"| {row['state']} | {row['state_name']} | {row['weight']:.3f} | ")
                f.write(f"{abs(row['best_lag'])} day(s) | {row['best_r']:.3f} |\n")
            f.write("\n")
        else:
            f.write("### States That Lead National Average\n\n")
            f.write("❌ No clear leading patterns identified with current data (n=4).\n\n")
        
        # High-weight states
        f.write("### Top 5 Consumption States\n\n")
        f.write("| State | Name | Weight | Best Lag | Best r |\n")
        f.write("|-------|------|--------|----------|--------|\n")
        top5 = results_df.nlargest(5, 'weight')
        for _, row in top5.iterrows():
            f.write(f"| {row['state']} | {row['state_name']} | {row['weight']:.3f} | ")
            f.write(f"{row['best_lag']} | {row['best_r']:.3f} |\n")
        f.write("\n")
        
        f.write("---\n\n")
        f.write("## ⚠️ LIMITATIONS\n\n")
        f.write("1. **Sample size:** Only 4 time points severely limits statistical power\n")
        f.write("2. **Lag range:** Can only test ±2 days (need ≥3 overlapping points)\n")
        f.write("3. **Noise:** With n=4, random variation dominates signal\n")
        f.write("4. **Confidence:** Cannot establish statistical significance\n\n")
        
        f.write("---\n\n")
        f.write("## 🔬 NEXT STEPS\n\n")
        f.write("1. ✅ Continue daily data collection (target: 30 days)\n")
        f.write("2. ✅ Re-run cross-correlation with larger sample\n")
        f.write("3. ✅ Test lags up to ±7 days with sufficient data\n")
        f.write("4. ✅ Granger causality tests (requires 30+ observations)\n")
        f.write("5. ❌ Do NOT add lag features to model yet (premature)\n\n")
        
        f.write("---\n\n")
        f.write("## 💡 INTERPRETATION\n\n")
        f.write("While these results are **suggestive**, they are **not conclusive** due to small sample size. ")
        f.write("The observed lag patterns could easily be due to random chance. ")
        f.write("We need 30+ daily observations before making definitive statements about leading/lagging relationships.\n\n")
    
    print(f"✅ Saved: {output_file}")


if __name__ == '__main__':
    # Run analysis
    results_df = analyze_all_states()
    
    # Create visualizations
    create_heatmap(results_df)
    create_lag_profile_plots(results_df)
    
    # Create report
    create_summary_report(results_df)
    
    print(f"\n{'='*60}")
    print("✅ CROSS-CORRELATION ANALYSIS COMPLETE!")
    print(f"{'='*60}\n")
    print("Files created:")
    print("  1. state_analysis/outputs/cross_correlation_results.csv")
    print("  2. state_analysis/outputs/cross_correlation_heatmap.png")
    print("  3. state_analysis/outputs/lag_profiles.png")
    print("  4. state_analysis/outputs/CROSS_CORRELATION_REPORT.md")
    print("\n" + "="*60)
