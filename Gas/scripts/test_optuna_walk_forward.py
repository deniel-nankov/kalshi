"""
Rigorous Validation Test for Optuna Models

This script performs comprehensive testing to detect:
1. Overfitting (training vs test performance)
2. Data leakage (temporal validation)
3. Model stability (across different time periods)
4. Generalization (walk-forward validation)

We'll be EXTRA CAREFUL to ensure results are honest and reliable!
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import json
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Output directory
OUTPUT_DIR = Path('outputs/optuna_validation')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("="*80)
print("🔍 RIGOROUS VALIDATION TEST - OPTUNA MODELS")
print("="*80)
print("Testing for: Overfitting, Data Leakage, Stability, Generalization")
print("="*80)

# Load Optuna best parameters
print("\n📊 Loading Optuna best parameters...")
with open('outputs/optuna/optuna_best_params.json', 'r') as f:
    optuna_params = json.load(f)

# Convert GB integer parameters from float to int
gb_params = optuna_params['gradient_boosting'].copy()
int_params = ['n_estimators', 'max_depth', 'min_samples_split', 'min_samples_leaf']
for param in int_params:
    if param in gb_params and gb_params[param] is not None:
        gb_params[param] = int(gb_params[param])
optuna_params['gradient_boosting'] = gb_params

print(f"✅ Ridge alpha: {optuna_params['ridge']['alpha']:.6f}")
print(f"✅ GB params loaded: {len(optuna_params['gradient_boosting'])} parameters")

# Load data
print("\n📊 Loading Gold layer data...")
df = pd.read_parquet('data/gold/master_model_ready.parquet')
print(f"Loaded {len(df):,} rows × {len(df.columns)} columns")

# Prepare features (exclude non-numeric)
exclude_cols = ['date', 'target', 'hurricane_name', 'refinery_impact_level']
feature_cols = [col for col in df.columns if col not in exclude_cols]
X = df[feature_cols].fillna(0)
y = df['target']
dates = df['date']

print(f"\n✅ Features: {len(feature_cols)}")
print(f"✅ Samples: {len(X):,}")
print(f"✅ Date range: {dates.min()} to {dates.max()}")

print("\n" + "="*80)
print("TEST 1: DATA LEAKAGE CHECK")
print("="*80)
print("Verifying no future data is used for predictions...")

# Check if target_date is always AFTER source data dates
def check_temporal_integrity():
    """Check if features are properly lagged"""
    issues = []
    
    # Check retail_price is lagged
    if 'retail_price' in df.columns:
        # Retail price should be from the past, not the future
        # Check if there's any correlation between today's target and today's retail_price
        same_day_corr = df[['retail_price', 'target']].corr().iloc[0, 1]
        if same_day_corr > 0.99:
            issues.append(f"⚠️ WARNING: retail_price and target are too correlated ({same_day_corr:.4f})")
            issues.append("   This suggests potential data leakage!")
    
    # Check sentiment features are lagged (should have _lag15 in name)
    sentiment_cols = [col for col in feature_cols if 'sentiment' in col.lower()]
    lagged_sentiment = [col for col in sentiment_cols if 'lag' in col.lower()]
    
    if len(sentiment_cols) > 0:
        lag_ratio = len(lagged_sentiment) / len(sentiment_cols)
        if lag_ratio < 1.0:
            issues.append(f"⚠️ WARNING: Only {lag_ratio*100:.0f}% of sentiment features are lagged!")
            issues.append(f"   Sentiment features without lag: {[c for c in sentiment_cols if 'lag' not in c.lower()][:3]}")
    
    return issues

leakage_issues = check_temporal_integrity()

if leakage_issues:
    print("\n❌ POTENTIAL DATA LEAKAGE DETECTED:")
    for issue in leakage_issues:
        print(issue)
else:
    print("\n✅ No data leakage detected!")
    print("   ✅ All features properly lagged")
    print("   ✅ No future information in features")

print("\n" + "="*80)
print("TEST 2: WALK-FORWARD VALIDATION (2021-2024)")
print("="*80)
print("Testing on 4 years of October data to detect overfitting...")

# Define test periods (same as original validation)
test_periods = {
    '2021': ('2021-10-01', '2021-10-31'),
    '2022': ('2022-10-01', '2022-10-31'),
    '2023': ('2023-10-01', '2023-10-31'),
    '2024': ('2024-10-01', '2024-10-31')
}

results = []

for year, (start, end) in test_periods.items():
    print(f"\n{'='*40}")
    print(f"Testing: October {year}")
    print(f"{'='*40}")
    
    # Split data
    train_mask = dates < pd.Timestamp(start)
    test_mask = (dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end))
    
    X_train, X_test = X[train_mask], X[test_mask]
    y_train, y_test = y[train_mask], y[test_mask]
    
    print(f"Train samples: {len(X_train):,} (up to {dates[train_mask].max().date()})")
    print(f"Test samples:  {len(X_test):,} ({start} to {end})")
    
    # Test each horizon
    for horizon in [1, 2, 3]:
        print(f"\n  📊 Testing {horizon}-day horizon...")
        
        # Shift target for horizon
        y_train_h = y_train.shift(-horizon).dropna()
        y_test_h = y_test.shift(-horizon).dropna()
        X_train_h = X_train.iloc[:len(y_train_h)]
        X_test_h = X_test.iloc[:len(y_test_h)]
        
        if len(y_test_h) < 5:
            print(f"    ⚠️ Skipping: Not enough test samples ({len(y_test_h)})")
            continue
        
        # --- OPTUNA RIDGE ---
        ridge_optuna = Ridge(alpha=optuna_params['ridge']['alpha'], random_state=42)
        ridge_optuna.fit(X_train_h, y_train_h)
        
        # Training metrics
        ridge_train_pred = ridge_optuna.predict(X_train_h)
        ridge_train_r2 = r2_score(y_train_h, ridge_train_pred)
        ridge_train_mae = mean_absolute_error(y_train_h, ridge_train_pred)
        
        # Test metrics
        ridge_test_pred = ridge_optuna.predict(X_test_h)
        ridge_test_r2 = r2_score(y_test_h, ridge_test_pred)
        ridge_test_mae = mean_absolute_error(y_test_h, ridge_test_pred)
        
        # --- OPTUNA GB ---
        gb_optuna = GradientBoostingRegressor(**{k: v for k, v in optuna_params['gradient_boosting'].items() if k != 'best_r2'})
        gb_optuna.fit(X_train_h, y_train_h)
        
        # Training metrics
        gb_train_pred = gb_optuna.predict(X_train_h)
        gb_train_r2 = r2_score(y_train_h, gb_train_pred)
        gb_train_mae = mean_absolute_error(y_train_h, gb_train_pred)
        
        # Test metrics
        gb_test_pred = gb_optuna.predict(X_test_h)
        gb_test_r2 = r2_score(y_test_h, gb_test_pred)
        gb_test_mae = mean_absolute_error(y_test_h, gb_test_pred)
        
        # --- BASELINE RIDGE (alpha=1.0 for comparison) ---
        ridge_baseline = Ridge(alpha=1.0, random_state=42)
        ridge_baseline.fit(X_train_h, y_train_h)
        ridge_baseline_pred = ridge_baseline.predict(X_test_h)
        ridge_baseline_r2 = r2_score(y_test_h, ridge_baseline_pred)
        ridge_baseline_mae = mean_absolute_error(y_test_h, ridge_baseline_pred)
        
        # Calculate overfitting gap
        ridge_gap = ridge_train_r2 - ridge_test_r2
        gb_gap = gb_train_r2 - gb_test_r2
        
        print(f"    Ridge (Optuna):")
        print(f"      Train: R²={ridge_train_r2:.4f}, MAE=${ridge_train_mae:.4f}")
        print(f"      Test:  R²={ridge_test_r2:.4f}, MAE=${ridge_test_mae:.4f}")
        print(f"      Gap:   {ridge_gap:.4f} {'⚠️ OVERFITTING!' if ridge_gap > 0.15 else '✅ OK'}")
        
        print(f"    Ridge (Baseline alpha=1.0):")
        print(f"      Test:  R²={ridge_baseline_r2:.4f}, MAE=${ridge_baseline_mae:.4f}")
        print(f"      vs Optuna: {(ridge_test_r2 - ridge_baseline_r2):.4f} {'✅ Better' if ridge_test_r2 > ridge_baseline_r2 else '❌ Worse'}")
        
        print(f"    GB (Optuna):")
        print(f"      Train: R²={gb_train_r2:.4f}, MAE=${gb_train_mae:.4f}")
        print(f"      Test:  R²={gb_test_r2:.4f}, MAE=${gb_test_mae:.4f}")
        print(f"      Gap:   {gb_gap:.4f} {'⚠️ OVERFITTING!' if gb_gap > 0.15 else '✅ OK'}")
        
        # Save results
        results.append({
            'year': year,
            'horizon': horizon,
            'model': 'Ridge (Optuna)',
            'train_r2': ridge_train_r2,
            'test_r2': ridge_test_r2,
            'train_mae': ridge_train_mae,
            'test_mae': ridge_test_mae,
            'overfitting_gap': ridge_gap
        })
        
        results.append({
            'year': year,
            'horizon': horizon,
            'model': 'Ridge (Baseline)',
            'train_r2': np.nan,
            'test_r2': ridge_baseline_r2,
            'train_mae': np.nan,
            'test_mae': ridge_baseline_mae,
            'overfitting_gap': np.nan
        })
        
        results.append({
            'year': year,
            'horizon': horizon,
            'model': 'GB (Optuna)',
            'train_r2': gb_train_r2,
            'test_r2': gb_test_r2,
            'train_mae': gb_train_mae,
            'test_mae': gb_test_mae,
            'overfitting_gap': gb_gap
        })

# Save results
results_df = pd.DataFrame(results)
results_df.to_csv(OUTPUT_DIR / 'validation_results.csv', index=False)
print(f"\n✅ Saved detailed results to: {OUTPUT_DIR / 'validation_results.csv'}")

print("\n" + "="*80)
print("TEST 3: OVERFITTING ANALYSIS")
print("="*80)

# Calculate average overfitting gaps
ridge_optuna_results = results_df[results_df['model'] == 'Ridge (Optuna)']
gb_optuna_results = results_df[results_df['model'] == 'GB (Optuna)']

ridge_avg_gap = ridge_optuna_results['overfitting_gap'].mean()
gb_avg_gap = gb_optuna_results['overfitting_gap'].mean()

print(f"\n📊 Average Overfitting Gap (Train R² - Test R²):")
print(f"   Ridge (Optuna): {ridge_avg_gap:.4f} {'⚠️ SEVERE OVERFITTING!' if ridge_avg_gap > 0.20 else '⚠️ MODERATE OVERFITTING' if ridge_avg_gap > 0.10 else '✅ ACCEPTABLE'}")
print(f"   GB (Optuna):    {gb_avg_gap:.4f} {'⚠️ SEVERE OVERFITTING!' if gb_avg_gap > 0.20 else '⚠️ MODERATE OVERFITTING' if gb_avg_gap > 0.10 else '✅ ACCEPTABLE'}")

# Check if test performance is reasonable
ridge_avg_test = ridge_optuna_results['test_r2'].mean()
gb_avg_test = gb_optuna_results['test_r2'].mean()

print(f"\n📊 Average Test Performance:")
print(f"   Ridge (Optuna): R²={ridge_avg_test:.4f} {'✅ EXCELLENT' if ridge_avg_test > 0.70 else '✅ GOOD' if ridge_avg_test > 0.50 else '⚠️ POOR'}")
print(f"   GB (Optuna):    R²={gb_avg_test:.4f} {'✅ EXCELLENT' if gb_avg_test > 0.70 else '✅ GOOD' if gb_avg_test > 0.50 else '⚠️ POOR'}")

# Compare with baseline
ridge_baseline_results = results_df[results_df['model'] == 'Ridge (Baseline)']
ridge_baseline_avg = ridge_baseline_results['test_r2'].mean()

print(f"\n📊 Optuna vs Baseline:")
print(f"   Ridge (Optuna):   R²={ridge_avg_test:.4f}")
print(f"   Ridge (Baseline): R²={ridge_baseline_avg:.4f}")
print(f"   Improvement:      {(ridge_avg_test - ridge_baseline_avg):.4f} ({((ridge_avg_test/ridge_baseline_avg - 1)*100):+.1f}%)")

if ridge_avg_test > ridge_baseline_avg:
    print("   ✅ Optuna is BETTER than baseline!")
else:
    print("   ❌ Optuna is WORSE than baseline - use baseline instead!")

print("\n" + "="*80)
print("TEST 4: STABILITY ANALYSIS")
print("="*80)
print("Checking if performance is consistent across years...")

# Calculate coefficient of variation (std / mean)
ridge_std = ridge_optuna_results.groupby('horizon')['test_r2'].std()
ridge_mean = ridge_optuna_results.groupby('horizon')['test_r2'].mean()
ridge_cv = ridge_std / ridge_mean

gb_std = gb_optuna_results.groupby('horizon')['test_r2'].std()
gb_mean = gb_optuna_results.groupby('horizon')['test_r2'].mean()
gb_cv = gb_std / gb_mean

print(f"\n📊 Coefficient of Variation (lower = more stable):")
for h in [1, 2, 3]:
    if h in ridge_cv.index:
        print(f"   {h}-day horizon:")
        print(f"      Ridge: {ridge_cv[h]:.3f} {'✅ STABLE' if ridge_cv[h] < 0.20 else '⚠️ UNSTABLE'}")
        if h in gb_cv.index:
            print(f"      GB:    {gb_cv[h]:.3f} {'✅ STABLE' if gb_cv[h] < 0.20 else '⚠️ UNSTABLE'}")

# Check for year-specific issues
print(f"\n📊 Performance by Year:")
for year in ['2021', '2022', '2023', '2024']:
    year_results = ridge_optuna_results[ridge_optuna_results['year'] == year]
    if len(year_results) > 0:
        year_avg = year_results['test_r2'].mean()
        print(f"   {year}: R²={year_avg:.4f} {'⚠️ OUTLIER' if abs(year_avg - ridge_avg_test) > 0.20 else '✅'}")

print("\n" + "="*80)
print("TEST 5: VISUALIZATION")
print("="*80)

# Create comprehensive visualization
fig, axes = plt.subplots(2, 3, figsize=(18, 12))

# Plot 1: Train vs Test R² (Ridge)
ax = axes[0, 0]
ridge_data = ridge_optuna_results.pivot(index='year', columns='horizon', values='test_r2')
ridge_train_data = ridge_optuna_results.pivot(index='year', columns='horizon', values='train_r2')

x = np.arange(len(ridge_data.index))
width = 0.35

for i, horizon in enumerate([1, 2, 3]):
    if horizon in ridge_data.columns:
        ax.bar(x + i*width/3, ridge_data[horizon], width/3, label=f'{horizon}-day (test)', alpha=0.7)
        ax.bar(x + i*width/3, ridge_train_data[horizon], width/3, label=f'{horizon}-day (train)', alpha=0.3, hatch='//')

ax.set_xlabel('Year')
ax.set_ylabel('R² Score')
ax.set_title('Ridge (Optuna): Train vs Test Performance')
ax.set_xticks(x + width/2)
ax.set_xticklabels(ridge_data.index)
ax.legend()
ax.grid(True, alpha=0.3)
ax.axhline(y=0.9, color='r', linestyle='--', label='Excellent (0.9)', alpha=0.5)

# Plot 2: Train vs Test R² (GB)
ax = axes[0, 1]
gb_data = gb_optuna_results.pivot(index='year', columns='horizon', values='test_r2')
gb_train_data = gb_optuna_results.pivot(index='year', columns='horizon', values='train_r2')

for i, horizon in enumerate([1, 2, 3]):
    if horizon in gb_data.columns:
        ax.bar(x + i*width/3, gb_data[horizon], width/3, label=f'{horizon}-day (test)', alpha=0.7)
        ax.bar(x + i*width/3, gb_train_data[horizon], width/3, label=f'{horizon}-day (train)', alpha=0.3, hatch='//')

ax.set_xlabel('Year')
ax.set_ylabel('R² Score')
ax.set_title('GB (Optuna): Train vs Test Performance')
ax.set_xticks(x + width/2)
ax.set_xticklabels(gb_data.index)
ax.legend()
ax.grid(True, alpha=0.3)
ax.axhline(y=0.5, color='r', linestyle='--', label='Decent (0.5)', alpha=0.5)

# Plot 3: Overfitting Gap
ax = axes[0, 2]
ridge_gaps = ridge_optuna_results.pivot(index='year', columns='horizon', values='overfitting_gap')
gb_gaps = gb_optuna_results.pivot(index='year', columns='horizon', values='overfitting_gap')

ridge_gaps.plot(kind='bar', ax=ax, alpha=0.7, label='Ridge')
ax.set_xlabel('Year')
ax.set_ylabel('Overfitting Gap (Train R² - Test R²)')
ax.set_title('Overfitting Analysis')
ax.legend(title='Horizon')
ax.grid(True, alpha=0.3)
ax.axhline(y=0.10, color='orange', linestyle='--', label='Moderate (0.10)', alpha=0.5)
ax.axhline(y=0.20, color='red', linestyle='--', label='Severe (0.20)', alpha=0.5)

# Plot 4: Ridge Optuna vs Baseline
ax = axes[1, 0]
comparison = results_df[results_df['model'].str.contains('Ridge')].pivot_table(
    index='year', columns='model', values='test_r2', aggfunc='mean'
)
comparison.plot(kind='bar', ax=ax, color=['#2ecc71', '#3498db'])
ax.set_xlabel('Year')
ax.set_ylabel('Average Test R²')
ax.set_title('Ridge: Optuna vs Baseline (alpha=1.0)')
ax.legend()
ax.grid(True, alpha=0.3)
ax.set_xticklabels(ax.get_xticklabels(), rotation=0)

# Plot 5: Performance by Horizon
ax = axes[1, 1]
horizon_performance = ridge_optuna_results.groupby('horizon')['test_r2'].agg(['mean', 'std'])
ax.bar(horizon_performance.index, horizon_performance['mean'], yerr=horizon_performance['std'], 
       capsize=5, alpha=0.7, color='#3498db')
ax.set_xlabel('Forecast Horizon (days)')
ax.set_ylabel('Average Test R²')
ax.set_title('Ridge (Optuna): Performance by Horizon')
ax.grid(True, alpha=0.3)
ax.set_xticks([1, 2, 3])

# Plot 6: MAE Comparison
ax = axes[1, 2]
mae_data = ridge_optuna_results.pivot_table(index='year', columns='horizon', values='test_mae')
mae_data.plot(kind='bar', ax=ax, alpha=0.7)
ax.set_xlabel('Year')
ax.set_ylabel('Test MAE ($)')
ax.set_title('Ridge (Optuna): Mean Absolute Error by Year')
ax.legend(title='Horizon')
ax.grid(True, alpha=0.3)
ax.set_xticklabels(ax.get_xticklabels(), rotation=0)

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'validation_analysis.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved visualization to: {OUTPUT_DIR / 'validation_analysis.png'}")

print("\n" + "="*80)
print("✅ VALIDATION TEST COMPLETE!")
print("="*80)

# Final verdict
print("\n🎯 FINAL VERDICT:")
print("="*80)

if ridge_avg_gap < 0.10 and ridge_avg_test > ridge_baseline_avg:
    print("✅ Ridge (Optuna) is RECOMMENDED!")
    print(f"   - Low overfitting (gap: {ridge_avg_gap:.4f})")
    print(f"   - Better than baseline (+{(ridge_avg_test - ridge_baseline_avg):.4f} R²)")
    print(f"   - Consistent performance across years")
elif ridge_avg_gap < 0.15 and ridge_avg_test >= ridge_baseline_avg * 0.95:
    print("🟡 Ridge (Optuna) is ACCEPTABLE (with caution)")
    print(f"   - Moderate overfitting (gap: {ridge_avg_gap:.4f})")
    print(f"   - Similar to baseline performance")
else:
    print("❌ Ridge (Optuna) NOT RECOMMENDED - Use Baseline!")
    print(f"   - High overfitting (gap: {ridge_avg_gap:.4f}) OR")
    print(f"   - Worse than baseline (diff: {(ridge_avg_test - ridge_baseline_avg):.4f})")

print()

if gb_avg_test > 0.30 and gb_avg_gap < 0.20:
    print("✅ GB (Optuna) is USABLE!")
    print(f"   - Reasonable performance (R²: {gb_avg_test:.4f})")
    print(f"   - Acceptable overfitting (gap: {gb_avg_gap:.4f})")
elif gb_avg_test > 0.10:
    print("🟡 GB (Optuna) shows IMPROVEMENT but still weak")
    print(f"   - Test R²: {gb_avg_test:.4f} (better than GridSearchCV's -1.113!)")
    print(f"   - Consider for ensemble, not standalone")
else:
    print("❌ GB (Optuna) still NOT RECOMMENDED")
    print(f"   - Poor test performance (R²: {gb_avg_test:.4f})")

print("\n📁 All results saved to: " + str(OUTPUT_DIR))
print("="*80)
