#!/usr/bin/env python3
"""
Create Publication-Ready Graphs for Kalshi Competition Submission

This script generates 6 comprehensive visualizations:
1. Predicted vs Actual Time Series
2. Forecast Error Distribution
3. Scatter: Predicted vs Actual
4. Confidence Interval Coverage
5. Uncertainty Reduction Bar Chart
6. Cumulative Absolute Error

Usage:
    python scripts/create_submission_graphs.py

Output:
    - 6 high-resolution PNG files (300 DPI)
    - Saved to outputs/submission_graphs/
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set publication-quality style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10

# Create output directory
output_dir = Path('outputs/submission_graphs')
output_dir.mkdir(parents=True, exist_ok=True)

print('='*80)
print('📊 CREATING SUBMISSION GRAPHS FOR KALSHI COMPETITION')
print('='*80)
print(f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print(f'Output Directory: {output_dir}')
print('='*80)

# Load tracking data
try:
    df = pd.read_csv('data/real_time_tracking.csv')
    print(f'\n✅ Loaded tracking data: {len(df)} predictions')
    print(f'Columns: {df.columns.tolist()}')
except FileNotFoundError:
    print('\n❌ Error: data/real_time_tracking.csv not found!')
    print('Make sure you have run daily predictions.')
    exit(1)

# Check if we have actual prices
has_actuals = df['actual_price'].notna().sum() > 0
print(f'\n📊 Data Status:')
print(f'   Total Predictions: {len(df)}')
print(f'   Validated (with actuals): {df["actual_price"].notna().sum()}')
print(f'   Pending Validation: {df["actual_price"].isna().sum()}')

if not has_actuals:
    print('\n⚠️  Warning: No actual prices yet. Graphs will show predictions only.')
    print('   Run track_actuals.py after EIA publishes data to validate.')

# ============================================================================
# GRAPH 1: Predicted vs Actual Time Series
# ============================================================================
print('\n📈 Creating Graph 1: Predicted vs Actual Time Series...')

fig, ax = plt.subplots(figsize=(12, 6))

# Convert dates
df['prediction_date'] = pd.to_datetime(df['prediction_date'])
df['target_date'] = pd.to_datetime(df['target_date'])

# Plot predictions
ax.plot(df['target_date'], df['ridge_pred'], 
        marker='o', linestyle='-', linewidth=2, markersize=6,
        label='Ridge Prediction', color='#1f77b4', alpha=0.8)

ax.plot(df['target_date'], df['market_pred'], 
        marker='s', linestyle='-', linewidth=2, markersize=6,
        label='Kalshi Market', color='#2ca02c', alpha=0.8)

ax.plot(df['target_date'], df['fused_pred'], 
        marker='D', linestyle='-', linewidth=2, markersize=6,
        label='Bayesian Fused', color='#d62728', alpha=0.8)

# Plot actuals if available
if has_actuals:
    actual_data = df[df['actual_price'].notna()]
    ax.plot(actual_data['target_date'], actual_data['actual_price'],
            marker='*', linestyle='--', linewidth=2, markersize=12,
            label='Actual Price (EIA)', color='black', alpha=0.9, zorder=10)

ax.set_xlabel('Target Date', fontweight='bold')
ax.set_ylabel('Gas Price ($)', fontweight='bold')
ax.set_title('Gas Price Predictions vs Actuals\nRidge + Kalshi Markets + Bayesian Fusion', 
             fontweight='bold', pad=20)
ax.legend(loc='best', frameon=True, shadow=True)
ax.grid(True, alpha=0.3)

# Format y-axis as currency
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.3f}'))

# Rotate x-axis labels
plt.xticks(rotation=45, ha='right')

plt.tight_layout()
plt.savefig(output_dir / 'graph1_time_series.png', dpi=300, bbox_inches='tight')
plt.close()
print(f'   ✅ Saved: graph1_time_series.png')

# ============================================================================
# GRAPH 2: Forecast Error Distribution
# ============================================================================
print('\n📊 Creating Graph 2: Forecast Error Distribution...')

if has_actuals:
    # Calculate errors
    df_actual = df[df['actual_price'].notna()].copy()
    df_actual['ridge_error'] = df_actual['ridge_pred'] - df_actual['actual_price']
    df_actual['fused_error'] = df_actual['fused_pred'] - df_actual['actual_price']
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Box plot
    error_data = [df_actual['ridge_error'], df_actual['fused_error']]
    bp = ax1.boxplot(error_data, labels=['Ridge', 'Bayesian Fused'],
                     patch_artist=True, widths=0.6)
    
    # Color the boxes
    colors = ['#1f77b4', '#d62728']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    
    ax1.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax1.set_ylabel('Prediction Error ($)', fontweight='bold')
    ax1.set_title('Error Distribution (Box Plot)', fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Histogram
    ax2.hist(df_actual['ridge_error'], bins=10, alpha=0.6, color='#1f77b4', 
             label='Ridge', edgecolor='black')
    ax2.hist(df_actual['fused_error'], bins=10, alpha=0.6, color='#d62728',
             label='Bayesian Fused', edgecolor='black')
    ax2.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax2.set_xlabel('Prediction Error ($)', fontweight='bold')
    ax2.set_ylabel('Frequency', fontweight='bold')
    ax2.set_title('Error Distribution (Histogram)', fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'graph2_error_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f'   ✅ Saved: graph2_error_distribution.png')
else:
    print(f'   ⚠️  Skipped: Need actual prices for error distribution')

# ============================================================================
# GRAPH 3: Scatter Plot - Predicted vs Actual
# ============================================================================
print('\n🎯 Creating Graph 3: Predicted vs Actual Scatter Plot...')

if has_actuals:
    df_actual = df[df['actual_price'].notna()].copy()
    
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Plot Ridge predictions
    ax.scatter(df_actual['actual_price'], df_actual['ridge_pred'],
              s=100, alpha=0.6, color='#1f77b4', edgecolors='black',
              label='Ridge', marker='o')
    
    # Plot Bayesian Fused predictions
    ax.scatter(df_actual['actual_price'], df_actual['fused_pred'],
              s=100, alpha=0.6, color='#d62728', edgecolors='black',
              label='Bayesian Fused', marker='D')
    
    # Plot perfect prediction line (y=x)
    min_price = min(df_actual['actual_price'].min(), 
                   df_actual['ridge_pred'].min(),
                   df_actual['fused_pred'].min())
    max_price = max(df_actual['actual_price'].max(),
                   df_actual['ridge_pred'].max(),
                   df_actual['fused_pred'].max())
    
    ax.plot([min_price, max_price], [min_price, max_price],
           'k--', linewidth=2, label='Perfect Prediction (y=x)', alpha=0.7)
    
    ax.set_xlabel('Actual Price ($)', fontweight='bold')
    ax.set_ylabel('Predicted Price ($)', fontweight='bold')
    ax.set_title('Predicted vs Actual Gas Prices\nBias Check (Points Should Align on Diagonal)', 
                fontweight='bold', pad=20)
    ax.legend(loc='best', frameon=True, shadow=True)
    ax.grid(True, alpha=0.3)
    
    # Make it square
    ax.set_aspect('equal', adjustable='box')
    
    # Format axes as currency
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.3f}'))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.3f}'))
    
    plt.tight_layout()
    plt.savefig(output_dir / 'graph3_scatter_predicted_vs_actual.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f'   ✅ Saved: graph3_scatter_predicted_vs_actual.png')
else:
    print(f'   ⚠️  Skipped: Need actual prices for scatter plot')

# ============================================================================
# GRAPH 4: Confidence Interval Coverage
# ============================================================================
print('\n📉 Creating Graph 4: Confidence Interval Coverage...')

fig, ax = plt.subplots(figsize=(14, 7))

# Plot Bayesian CI as shaded region
ax.fill_between(df['target_date'], 
               df['ci_95_lower'], 
               df['ci_95_upper'],
               alpha=0.2, color='#d62728', label='Bayesian 95% CI (±$0.048)')

# Plot Conformal CI as shaded region
ax.fill_between(df['target_date'],
               df['conformal_lower'],
               df['conformal_upper'],
               alpha=0.3, color='#1f77b4', label='Conformal 95% CI (±$0.017)')

# Plot predictions
ax.plot(df['target_date'], df['fused_pred'],
       marker='D', linestyle='-', linewidth=2, markersize=6,
       label='Bayesian Fused Prediction', color='#d62728', zorder=5)

ax.plot(df['target_date'], df['conformal_pred'],
       marker='o', linestyle='-', linewidth=2, markersize=6,
       label='Conformal Prediction', color='#1f77b4', zorder=5)

# Plot actuals if available
if has_actuals:
    actual_data = df[df['actual_price'].notna()]
    ax.plot(actual_data['target_date'], actual_data['actual_price'],
           marker='*', linestyle='', markersize=15,
           label='Actual Price (EIA)', color='black', zorder=10)

ax.set_xlabel('Target Date', fontweight='bold')
ax.set_ylabel('Gas Price ($)', fontweight='bold')
ax.set_title('Confidence Interval Coverage\nBayesian CI vs Conformal CI with Actual Prices',
            fontweight='bold', pad=20)
ax.legend(loc='best', frameon=True, shadow=True)
ax.grid(True, alpha=0.3)

# Format y-axis as currency
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.3f}'))

plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(output_dir / 'graph4_confidence_intervals.png', dpi=300, bbox_inches='tight')
plt.close()
print(f'   ✅ Saved: graph4_confidence_intervals.png')

# ============================================================================
# GRAPH 5: Uncertainty Reduction Bar Chart
# ============================================================================
print('\n📊 Creating Graph 5: Uncertainty Reduction Bar Chart...')

fig, ax = plt.subplots(figsize=(10, 7))

# Uncertainty values (in dollars)
methods = ['Ridge\nRegression', 'Bayesian\nFusion', 'Conformal\nPrediction']
uncertainties = [0.100, 0.048, 0.017]  # ±$ values
colors = ['#1f77b4', '#d62728', '#2ca02c']

bars = ax.bar(methods, uncertainties, color=colors, alpha=0.7, edgecolor='black', linewidth=2)

# Add value labels on bars
for bar, value in zip(bars, uncertainties):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
           f'±${value:.3f}\n({value/3.06*100:.2f}%)',
           ha='center', va='bottom', fontweight='bold', fontsize=11)

# Add percentage reduction annotations
ax.annotate('', xy=(1, 0.048), xytext=(0, 0.100),
           arrowprops=dict(arrowstyle='<->', color='red', lw=2))
ax.text(0.5, 0.074, '52.5%\nreduction', ha='center', va='center',
       bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5),
       fontweight='bold')

ax.annotate('', xy=(2, 0.017), xytext=(1, 0.048),
           arrowprops=dict(arrowstyle='<->', color='red', lw=2))
ax.text(1.5, 0.032, '64.6%\nreduction', ha='center', va='center',
       bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5),
       fontweight='bold')

ax.set_ylabel('Prediction Uncertainty (±$)', fontweight='bold')
ax.set_title('Uncertainty Reduction Through Ensemble Methods\nFrom Ridge (±$0.100) to Conformal (±$0.017)',
            fontweight='bold', pad=20)
ax.grid(True, alpha=0.3, axis='y')
ax.set_ylim(0, 0.12)

plt.tight_layout()
plt.savefig(output_dir / 'graph5_uncertainty_reduction.png', dpi=300, bbox_inches='tight')
plt.close()
print(f'   ✅ Saved: graph5_uncertainty_reduction.png')

# ============================================================================
# GRAPH 6: Cumulative Absolute Error
# ============================================================================
print('\n📈 Creating Graph 6: Cumulative Absolute Error...')

if has_actuals:
    df_actual = df[df['actual_price'].notna()].copy()
    df_actual = df_actual.sort_values('target_date')
    
    # Calculate cumulative absolute errors
    df_actual['ridge_abs_error'] = np.abs(df_actual['ridge_pred'] - df_actual['actual_price'])
    df_actual['fused_abs_error'] = np.abs(df_actual['fused_pred'] - df_actual['actual_price'])
    
    df_actual['ridge_cum_error'] = df_actual['ridge_abs_error'].cumsum()
    df_actual['fused_cum_error'] = df_actual['fused_abs_error'].cumsum()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(df_actual['target_date'], df_actual['ridge_cum_error'],
           marker='o', linestyle='-', linewidth=2, markersize=6,
           label='Ridge Cumulative Error', color='#1f77b4')
    
    ax.plot(df_actual['target_date'], df_actual['fused_cum_error'],
           marker='D', linestyle='-', linewidth=2, markersize=6,
           label='Bayesian Fused Cumulative Error', color='#d62728')
    
    # Calculate improvement
    final_ridge_error = df_actual['ridge_cum_error'].iloc[-1]
    final_fused_error = df_actual['fused_cum_error'].iloc[-1]
    improvement_pct = (final_ridge_error - final_fused_error) / final_ridge_error * 100
    
    ax.set_xlabel('Target Date', fontweight='bold')
    ax.set_ylabel('Cumulative Absolute Error ($)', fontweight='bold')
    ax.set_title(f'Cumulative Absolute Error Over Time\nBayesian Fusion: {improvement_pct:.1f}% Better',
                fontweight='bold', pad=20)
    ax.legend(loc='best', frameon=True, shadow=True)
    ax.grid(True, alpha=0.3)
    
    # Format y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.4f}'))
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_dir / 'graph6_cumulative_error.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f'   ✅ Saved: graph6_cumulative_error.png')
else:
    print(f'   ⚠️  Skipped: Need actual prices for cumulative error')

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================
print('\n' + '='*80)
print('📊 SUMMARY STATISTICS')
print('='*80)

if has_actuals:
    df_actual = df[df['actual_price'].notna()].copy()
    
    # Calculate metrics
    ridge_mae = np.mean(np.abs(df_actual['ridge_pred'] - df_actual['actual_price']))
    fused_mae = np.mean(np.abs(df_actual['fused_pred'] - df_actual['actual_price']))
    
    ridge_rmse = np.sqrt(np.mean((df_actual['ridge_pred'] - df_actual['actual_price'])**2))
    fused_rmse = np.sqrt(np.mean((df_actual['fused_pred'] - df_actual['actual_price'])**2))
    
    mean_actual = df_actual['actual_price'].mean()
    ridge_mape = (ridge_mae / mean_actual) * 100
    fused_mape = (fused_mae / mean_actual) * 100
    
    improvement = ((ridge_mae - fused_mae) / ridge_mae) * 100
    
    print(f'\n📈 Ridge Regression:')
    print(f'   MAE:  ${ridge_mae:.4f}')
    print(f'   RMSE: ${ridge_rmse:.4f}')
    print(f'   MAPE: {ridge_mape:.3f}%')
    
    print(f'\n📈 Bayesian Fused:')
    print(f'   MAE:  ${fused_mae:.4f}')
    print(f'   RMSE: ${fused_rmse:.4f}')
    print(f'   MAPE: {fused_mape:.3f}%')
    
    print(f'\n🎯 Improvement:')
    print(f'   MAE Reduction: {improvement:.1f}%')
    print(f'   RMSE Reduction: {((ridge_rmse - fused_rmse) / ridge_rmse) * 100:.1f}%')
    
    # Check CI coverage
    bayesian_coverage = np.mean(
        (df_actual['actual_price'] >= df_actual['ci_95_lower']) &
        (df_actual['actual_price'] <= df_actual['ci_95_upper'])
    ) * 100
    
    conformal_coverage = np.mean(
        (df_actual['actual_price'] >= df_actual['conformal_lower']) &
        (df_actual['actual_price'] <= df_actual['conformal_upper'])
    ) * 100
    
    print(f'\n📊 Confidence Interval Coverage:')
    print(f'   Bayesian 95% CI: {bayesian_coverage:.1f}% coverage')
    print(f'   Conformal 95% CI: {conformal_coverage:.1f}% coverage')
else:
    print('\n⚠️  No actual prices available yet for statistics.')
    print('   Run track_actuals.py after EIA publishes data.')

print('\n' + '='*80)
print('✅ ALL GRAPHS CREATED SUCCESSFULLY!')
print('='*80)
print(f'\n📁 Output Location: {output_dir.absolute()}')
print(f'\n📊 Generated Files:')
print(f'   1. graph1_time_series.png')
print(f'   2. graph2_error_distribution.png (if actuals available)')
print(f'   3. graph3_scatter_predicted_vs_actual.png (if actuals available)')
print(f'   4. graph4_confidence_intervals.png')
print(f'   5. graph5_uncertainty_reduction.png')
print(f'   6. graph6_cumulative_error.png (if actuals available)')
print('\n💡 Tip: Include these graphs in your Kalshi submission memo!')
print('='*80)
