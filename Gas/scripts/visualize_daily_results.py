#!/usr/bin/env python3
"""
Visualize Daily Incremental Training Results
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Paths
project_root = Path(__file__).parent.parent
results_path = project_root / 'outputs' / 'daily_incremental_results.csv'
output_dir = project_root / 'outputs' / 'daily_validation_graphs'
output_dir.mkdir(parents=True, exist_ok=True)

# Load results
df = pd.read_csv(results_path)
df['date'] = pd.to_datetime(df['date'])

print("=" * 80)
print("📊 CREATING DAILY VALIDATION VISUALIZATIONS")
print("=" * 80)

# ============================================================================
# Graph 1: Predictions vs Actuals Over Time
# ============================================================================
print("\n1️⃣ Creating time series comparison...")

fig, ax = plt.subplots(figsize=(14, 6))

# Plot predictions
ax.plot(df['date'], df['prediction'], 'o-', label='ML Prediction', 
        color='#2E86AB', linewidth=2, markersize=8)

# Plot actuals (separate EIA vs interpolated)
eia_actual = df[df['is_eia_actual'] == True]
interpolated = df[df['is_eia_actual'] == False]

ax.plot(eia_actual['date'], eia_actual['actual'], 's', 
        label='EIA Actual (Weekly)', color='#A23B72', markersize=12, 
        markeredgewidth=2, markeredgecolor='white')

ax.plot(interpolated['date'], interpolated['actual'], '^', 
        label='Interpolated', color='#F18F01', markersize=8, alpha=0.6)

# Formatting
ax.set_xlabel('Date', fontsize=12, fontweight='bold')
ax.set_ylabel('Price ($/gallon)', fontsize=12, fontweight='bold')
ax.set_title('Daily ML Predictions vs Actual Prices (Oct 19-27, 2025)', 
             fontsize=14, fontweight='bold', pad=20)
ax.legend(fontsize=11, loc='best', framealpha=0.95)
ax.grid(True, alpha=0.3, linestyle='--')

# Rotate x-axis labels
plt.xticks(rotation=45, ha='right')

# Add price range
ax.set_ylim(2.98, 3.08)

plt.tight_layout()
plt.savefig(output_dir / 'daily_predictions_vs_actuals.png', dpi=300, bbox_inches='tight')
print(f"   ✅ Saved: daily_predictions_vs_actuals.png")
plt.close()

# ============================================================================
# Graph 2: Error Over Time
# ============================================================================
print("\n2️⃣ Creating error analysis...")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

# Absolute error
ax1.plot(df['date'], df['abs_error'] * 1000, 'o-', color='#E63946', 
         linewidth=2, markersize=8, label='Absolute Error')
ax1.axhline(y=10, color='green', linestyle='--', alpha=0.5, label='$0.01 threshold (excellent)')
ax1.axhline(y=50, color='orange', linestyle='--', alpha=0.5, label='$0.05 threshold (good)')

# Highlight EIA actual days
for _, row in eia_actual.iterrows():
    ax1.plot(row['date'], row['abs_error'] * 1000, 'D', 
            color='#A23B72', markersize=12, markeredgewidth=2, 
            markeredgecolor='white', zorder=5)

ax1.set_ylabel('Absolute Error (cents)', fontsize=12, fontweight='bold')
ax1.set_title('Prediction Error Over Time', fontsize=14, fontweight='bold', pad=20)
ax1.legend(fontsize=10, loc='best')
ax1.grid(True, alpha=0.3)
ax1.set_ylim(0, 45)

# Percentage error
ax2.plot(df['date'], df['pct_error'], 'o-', color='#457B9D', 
         linewidth=2, markersize=8, label='Percentage Error')

# Highlight EIA actual days
for _, row in eia_actual.iterrows():
    ax2.plot(row['date'], row['pct_error'], 'D', 
            color='#A23B72', markersize=12, markeredgewidth=2, 
            markeredgecolor='white', zorder=5)

ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
ax2.set_ylabel('Error (%)', fontsize=12, fontweight='bold')
ax2.legend(fontsize=10, loc='best')
ax2.grid(True, alpha=0.3)
ax2.set_ylim(0, 1.6)

plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.savefig(output_dir / 'daily_error_analysis.png', dpi=300, bbox_inches='tight')
print(f"   ✅ Saved: daily_error_analysis.png")
plt.close()

# ============================================================================
# Graph 3: Training Set Growth
# ============================================================================
print("\n3️⃣ Creating training set growth visualization...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Training samples over time
ax1.plot(df['date'], df['train_samples'], 'o-', color='#06A77D', 
         linewidth=3, markersize=10)
ax1.fill_between(df['date'], df['train_samples'], alpha=0.3, color='#06A77D')
ax1.set_xlabel('Prediction Date', fontsize=12, fontweight='bold')
ax1.set_ylabel('Training Samples', fontsize=12, fontweight='bold')
ax1.set_title('Model Training Set Growth', fontsize=14, fontweight='bold', pad=20)
ax1.grid(True, alpha=0.3)
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Add annotations
start_samples = df['train_samples'].iloc[0]
end_samples = df['train_samples'].iloc[-1]
ax1.annotate(f'Start: {start_samples:,}', 
            xy=(df['date'].iloc[0], start_samples),
            xytext=(10, 20), textcoords='offset points',
            fontsize=10, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7))
ax1.annotate(f'End: {end_samples:,}', 
            xy=(df['date'].iloc[-1], end_samples),
            xytext=(-80, -30), textcoords='offset points',
            fontsize=10, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7))

# Training R² over time
ax2.plot(df['date'], df['train_r2'], 'o-', color='#9C89B8', 
         linewidth=3, markersize=10)
ax2.set_xlabel('Prediction Date', fontsize=12, fontweight='bold')
ax2.set_ylabel('Training R²', fontsize=12, fontweight='bold')
ax2.set_title('Model Fit Quality', fontsize=14, fontweight='bold', pad=20)
ax2.grid(True, alpha=0.3)
ax2.set_ylim(0.999, 1.001)
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.savefig(output_dir / 'daily_training_growth.png', dpi=300, bbox_inches='tight')
print(f"   ✅ Saved: daily_training_growth.png")
plt.close()

# ============================================================================
# Graph 4: Performance Summary
# ============================================================================
print("\n4️⃣ Creating performance summary...")

fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

# Overall stats
ax1 = fig.add_subplot(gs[0, :])
ax1.axis('off')

stats_text = f"""
DAILY INCREMENTAL TRAINING RESULTS (Oct 19-27, 2025)

Training Approach: Model retrained daily with one additional data point (incremental learning)
Total Predictions: {len(df)} days
EIA Actual Validations: {len(eia_actual)} days (Oct 20, 27)
Interpolated Validations: {len(interpolated)} days

Overall Performance:
  • Mean Absolute Error: ${df['abs_error'].mean():.4f} ({df['pct_error'].mean():.2f}%)
  • Max Error: ${df['abs_error'].max():.4f} on {df.loc[df['abs_error'].idxmax(), 'date'].strftime('%Y-%m-%d')}
  • Min Error: ${df['abs_error'].min():.4f} on {df.loc[df['abs_error'].idxmin(), 'date'].strftime('%Y-%m-%d')}

EIA Actual Prices Only:
  • Mean Absolute Error: ${eia_actual['abs_error'].mean():.4f} ({eia_actual['pct_error'].mean():.2f}%)
  • Oct 20: Predicted ${eia_actual.iloc[0]['prediction']:.3f}, Actual ${eia_actual.iloc[0]['actual']:.3f}, Error ${eia_actual.iloc[0]['error']:+.3f}
  • Oct 27: Predicted ${eia_actual.iloc[1]['prediction']:.3f}, Actual ${eia_actual.iloc[1]['actual']:.3f}, Error ${eia_actual.iloc[1]['error']:+.3f}

Training Set Growth: {df['train_samples'].iloc[0]:,} → {df['train_samples'].iloc[-1]:,} samples ({len(df)} new days)
Model Consistency: R² = {df['train_r2'].mean():.6f} (extremely stable)
"""

ax1.text(0.05, 0.95, stats_text, transform=ax1.transAxes,
         fontsize=11, verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# Error distribution
ax2 = fig.add_subplot(gs[1, 0])
errors_cents = df['abs_error'] * 1000
ax2.hist(errors_cents, bins=15, color='#E76F51', alpha=0.7, edgecolor='black')
ax2.axvline(errors_cents.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {errors_cents.mean():.1f}¢')
ax2.set_xlabel('Absolute Error (cents)', fontsize=11, fontweight='bold')
ax2.set_ylabel('Frequency', fontsize=11, fontweight='bold')
ax2.set_title('Error Distribution', fontsize=12, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Prediction vs Actual scatter
ax3 = fig.add_subplot(gs[1, 1])
ax3.scatter(df['actual'], df['prediction'], s=100, alpha=0.6, color='#2A9D8F')
ax3.scatter(eia_actual['actual'], eia_actual['prediction'], s=200, 
           marker='D', edgecolors='red', linewidths=2, color='#2A9D8F',
           label='EIA Actual', zorder=5)

# Perfect prediction line
min_val = min(df['actual'].min(), df['prediction'].min())
max_val = max(df['actual'].max(), df['prediction'].max())
ax3.plot([min_val, max_val], [min_val, max_val], 'k--', linewidth=2, alpha=0.5, label='Perfect Prediction')

ax3.set_xlabel('Actual Price ($/gal)', fontsize=11, fontweight='bold')
ax3.set_ylabel('Predicted Price ($/gal)', fontsize=11, fontweight='bold')
ax3.set_title('Predictions vs Actuals', fontsize=12, fontweight='bold')
ax3.legend()
ax3.grid(True, alpha=0.3)
ax3.set_aspect('equal')

# Day-by-day comparison
ax4 = fig.add_subplot(gs[2, :])
x = np.arange(len(df))
width = 0.35

bars1 = ax4.bar(x - width/2, df['prediction'], width, label='Prediction', 
               color='#2E86AB', alpha=0.8)
bars2 = ax4.bar(x + width/2, df['actual'], width, label='Actual', 
               color='#A23B72', alpha=0.8)

# Highlight EIA actual days
for idx, row in df.iterrows():
    if row['is_eia_actual']:
        bars2[idx].set_edgecolor('gold')
        bars2[idx].set_linewidth(3)

ax4.set_xlabel('Date', fontsize=11, fontweight='bold')
ax4.set_ylabel('Price ($/gal)', fontsize=11, fontweight='bold')
ax4.set_title('Day-by-Day Comparison (Gold border = EIA Actual)', fontsize=12, fontweight='bold')
ax4.set_xticks(x)
ax4.set_xticklabels(df['date'].dt.strftime('%m/%d'), rotation=45, ha='right')
ax4.legend()
ax4.grid(True, alpha=0.3, axis='y')

plt.savefig(output_dir / 'daily_performance_summary.png', dpi=300, bbox_inches='tight')
print(f"   ✅ Saved: daily_performance_summary.png")
plt.close()

# ============================================================================
# Summary
# ============================================================================
print(f"\n{'=' * 80}")
print("✅ ALL VISUALIZATIONS CREATED")
print("=" * 80)
print(f"\nOutput directory: {output_dir}")
print(f"\nFiles created:")
print(f"   1. daily_predictions_vs_actuals.png - Time series comparison")
print(f"   2. daily_error_analysis.png - Error metrics over time")
print(f"   3. daily_training_growth.png - Model evolution")
print(f"   4. daily_performance_summary.png - Complete analysis dashboard")
print("=" * 80)
