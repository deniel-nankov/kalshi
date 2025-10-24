import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load results
df = pd.read_csv('outputs/walk_forward/walk_forward_metrics.csv')

# Extract data
data_1d = df[df['horizon'] == 1].sort_values('year')
data_3d = df[df['horizon'] == 3].sort_values('year')
years = data_1d['year'].values

# Create figure
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('1-Day vs 3-Day Gas Price Forecast Comparison', fontsize=20, fontweight='bold')

# 1. R² Comparison
ax1 = axes[0, 0]
x = np.arange(len(years))
width = 0.35

ax1.bar(x - width/2, data_1d['r2'].values, width, label='1-day', 
        color='#2ecc71', alpha=0.8, edgecolor='black')
ax1.bar(x + width/2, data_3d['r2'].values, width, label='3-day',
        color='#e74c3c', alpha=0.8, edgecolor='black')

ax1.axhline(y=0, color='black', linestyle='--', linewidth=1)
ax1.set_xlabel('Year', fontsize=12, fontweight='bold')
ax1.set_ylabel('R² Score', fontsize=12, fontweight='bold')
ax1.set_title('R² Score by Year', fontsize=14, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(years)
ax1.legend(fontsize=11)
ax1.grid(axis='y', alpha=0.3)

# 2. MAE Comparison
ax2 = axes[0, 1]
ax2.bar(x - width/2, data_1d['mae'].values*100, width, label='1-day',
        color='#2ecc71', alpha=0.8, edgecolor='black')
ax2.bar(x + width/2, data_3d['mae'].values*100, width, label='3-day',
        color='#e74c3c', alpha=0.8, edgecolor='black')

ax2.set_xlabel('Year', fontsize=12, fontweight='bold')
ax2.set_ylabel('Mean Absolute Error (cents)', fontsize=12, fontweight='bold')
ax2.set_title('Average Error by Year', fontsize=14, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(years)
ax2.legend(fontsize=11)
ax2.grid(axis='y', alpha=0.3)

# 3. Average Performance
ax3 = axes[1, 0]
metrics = ['R²', 'MAE (cents)', 'MAPE (%)']
avg_1d = [data_1d['r2'].mean(), data_1d['mae'].mean()*100, data_1d['mape_pct'].mean()]
avg_3d = [data_3d['r2'].mean(), data_3d['mae'].mean()*100, data_3d['mape_pct'].mean()]

x_avg = np.arange(len(metrics))
ax3.bar(x_avg - width/2, avg_1d, width, label='1-day',
        color='#2ecc71', alpha=0.8, edgecolor='black')
ax3.bar(x_avg + width/2, avg_3d, width, label='3-day',
        color='#e74c3c', alpha=0.8, edgecolor='black')

ax3.axhline(y=0, color='black', linestyle='--', linewidth=1)
ax3.set_ylabel('Value', fontsize=12, fontweight='bold')
ax3.set_title('Average Performance (2021-2024)', fontsize=14, fontweight='bold')
ax3.set_xticks(x_avg)
ax3.set_xticklabels(metrics)
ax3.legend(fontsize=11)
ax3.grid(axis='y', alpha=0.3)

# 4. Summary Text
ax4 = axes[1, 1]
ax4.axis('off')
summary_text = f"""
SUMMARY STATISTICS

1-Day Forecasts:
  Average R²:    {data_1d['r2'].mean():>7.3f} ✅
  Best R² (2023): {data_1d['r2'].max():>6.3f}
  Average MAE:    {data_1d['mae'].mean()*100:>6.2f}¢
  Average MAPE:   {data_1d['mape_pct'].mean():>6.2f}%

3-Day Forecasts:
  Average R²:    {data_3d['r2'].mean():>7.3f} ❌
  Best R² (2021): {data_3d['r2'].max():>6.3f}
  Average MAE:    {data_3d['mae'].mean()*100:>6.2f}¢
  Average MAPE:   {data_3d['mape_pct'].mean():>6.2f}%

WINNER: 1-Day Forecasts!
  Better by {data_1d['r2'].mean() - data_3d['r2'].mean():>6.3f} R² points

RECOMMENDATION:
✅ Focus on 1-day forecasts for your paper
   (Positive R², reliable, practical)

⚠️ De-emphasize 3-day forecasts
   (Negative R², unreliable)
"""
ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes,
         fontsize=12, verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('outputs/walk_forward/1day_vs_3day_comparison.png', dpi=300, bbox_inches='tight')
print('✅ Saved: outputs/walk_forward/1day_vs_3day_comparison.png')
print()
print('='*80)
print('1-DAY vs 3-DAY FORECAST COMPARISON')
print('='*80)
print(f'1-day average R²: {data_1d["r2"].mean():>7.3f} ✅ RELIABLE')
print(f'3-day average R²: {data_3d["r2"].mean():>7.3f} ❌ UNRELIABLE')
print(f'Difference:       {data_1d["r2"].mean() - data_3d["r2"].mean():>7.3f} R² points')
print()
print('🏆 RECOMMENDATION: Focus on 1-day forecasts for your paper!')
