#!/usr/bin/env python3
"""
COMPLETE AUTOMATED SYSTEM: Train + Predict + Validate

This is the master script that does everything:
1. Loads daily AAA prices (Oct 18-29)
2. Trains model incrementally day-by-day
3. Makes prediction for Oct 31, 2025
4. Validates against EIA weekly
5. Saves all results

Run this once and get complete analysis!
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import matplotlib.pyplot as plt
import json

# Add project root
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Paths
GOLD_PATH = project_root / 'data' / 'gold' / 'master_model_ready.parquet'
AAA_DAILY_PATH = project_root / 'outputs' / 'aaa_daily_oct18_29.csv'
OUTPUT_DIR = project_root / 'outputs' / 'final_validation'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("🚀 AUTOMATED GAS PRICE FORECASTING SYSTEM")
print("=" * 80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Target: Predict for October 31, 2025")
print("=" * 80)

# ============================================================================
# STEP 1: Load Historical Gold Layer
# ============================================================================
print("\n" + "=" * 80)
print("STEP 1: LOAD HISTORICAL DATA")
print("=" * 80)

print("\n📂 Loading gold layer (historical features)...")
gold_df = pd.read_parquet(GOLD_PATH)
gold_df['date'] = pd.to_datetime(gold_df['date'])
gold_df = gold_df.sort_values('date').reset_index(drop=True)

print(f"   ✅ Loaded {len(gold_df)} samples")
print(f"   Date range: {gold_df['date'].min().strftime('%Y-%m-%d')} to {gold_df['date'].max().strftime('%Y-%m-%d')}")

# Get feature columns (numeric only)
target_col = 'retail_price'
exclude_cols = ['date', 'Date', target_col]
feature_cols = [col for col in gold_df.columns 
                if col not in exclude_cols and gold_df[col].dtype in ['float64', 'int64', 'float32', 'int32']]

print(f"   Features: {len(feature_cols)}")
print(f"   Target: {target_col}")

latest_gold_date = gold_df['date'].max()
latest_gold_price = gold_df[gold_df['date'] == latest_gold_date][target_col].iloc[0]
print(f"   Latest: {latest_gold_date.strftime('%Y-%m-%d')} = ${latest_gold_price:.3f}/gal")

# ============================================================================
# STEP 2: Load AAA Daily Prices
# ============================================================================
print("\n" + "=" * 80)
print("STEP 2: LOAD AAA DAILY PRICES (OCT 18-29)")
print("=" * 80)

print(f"\n📂 Loading AAA daily prices...")
aaa_df = pd.read_csv(AAA_DAILY_PATH)
aaa_df['date'] = pd.to_datetime(aaa_df['date'])

print(f"   ✅ Loaded {len(aaa_df)} daily prices")
print(f"\n   Daily prices:")
for _, row in aaa_df.iterrows():
    marker = "📍" if row['source'] == 'anchor' else "~"
    print(f"      {row['date'].strftime('%Y-%m-%d')}: ${row['price']:.3f} {marker}")

# ============================================================================
# STEP 3: Incremental Training (Day by Day)
# ============================================================================
print("\n" + "=" * 80)
print("STEP 3: INCREMENTAL TRAINING (OCT 19-29)")
print("=" * 80)

print("\n🎯 Training model incrementally with daily data...")

# Start with base gold layer
train_df = gold_df.copy()

# Track results
training_results = []

# For each day from Oct 19-29 (we already have Oct 18 in gold layer)
for _, aaa_row in aaa_df.iterrows():
    current_date = aaa_row['date']
    current_price = aaa_row['price']
    
    # Skip Oct 18 (already in gold layer)
    if current_date <= latest_gold_date:
        continue
    
    day_num = (current_date - latest_gold_date).days
    
    print(f"\n{'-' * 80}")
    print(f"Day {day_num}: {current_date.strftime('%Y-%m-%d')}")
    print(f"{'-' * 80}")
    
    # Train on all data up to yesterday
    print(f"   Training samples: {len(train_df)}")
    print(f"   Training period: {train_df['date'].min().strftime('%Y-%m-%d')} to {train_df['date'].max().strftime('%Y-%m-%d')}")
    
    # Prepare training data
    X_train = train_df[feature_cols].values
    y_train = train_df[target_col].values
    
    # Build pipeline
    imputer = SimpleImputer(strategy='mean')
    scaler = StandardScaler()
    model = Ridge(alpha=1.0)
    
    # Fit
    X_train_imputed = imputer.fit_transform(X_train)
    X_train_scaled = scaler.fit_transform(X_train_imputed)
    model.fit(X_train_scaled, y_train)
    
    train_r2 = model.score(X_train_scaled, y_train)
    print(f"   Training R²: {train_r2:.6f}")
    
    # Make prediction for today
    last_features = train_df[feature_cols].iloc[-1:].values
    X_pred = imputer.transform(last_features)
    X_pred_scaled = scaler.transform(X_pred)
    prediction = model.predict(X_pred_scaled)[0]
    
    # Compare to actual
    error = prediction - current_price
    abs_error = abs(error)
    pct_error = (abs_error / current_price) * 100
    
    print(f"   Prediction: ${prediction:.3f}/gal")
    print(f"   Actual: ${current_price:.3f}/gal ({aaa_row['source']})")
    print(f"   Error: ${error:+.3f} ({pct_error:.2f}%)")
    
    # Record result
    training_results.append({
        'date': current_date,
        'train_samples': len(train_df),
        'train_r2': train_r2,
        'prediction': prediction,
        'actual': current_price,
        'source': aaa_row['source'],
        'error': error,
        'abs_error': abs_error,
        'pct_error': pct_error
    })
    
    # Add today to training set for tomorrow
    new_row = train_df.iloc[-1:].copy()
    new_row['date'] = current_date
    new_row[target_col] = current_price
    train_df = pd.concat([train_df, new_row], ignore_index=True)

# ============================================================================
# STEP 4: Predict for October 31, 2025
# ============================================================================
print("\n" + "=" * 80)
print("STEP 4: PREDICT FOR OCTOBER 31, 2025")
print("=" * 80)

target_date = pd.Timestamp('2025-10-31')
print(f"\n🔮 Making prediction for {target_date.strftime('%Y-%m-%d')}...")

# Final training with all data through Oct 29
print(f"\n   Final training dataset:")
print(f"      Samples: {len(train_df)}")
print(f"      Date range: {train_df['date'].min().strftime('%Y-%m-%d')} to {train_df['date'].max().strftime('%Y-%m-%d')}")

X_final = train_df[feature_cols].values
y_final = train_df[target_col].values

# Build final model
imputer_final = SimpleImputer(strategy='mean')
scaler_final = StandardScaler()
model_final = Ridge(alpha=1.0)

X_final_imputed = imputer_final.fit_transform(X_final)
X_final_scaled = scaler_final.fit_transform(X_final_imputed)
model_final.fit(X_final_scaled, y_final)

final_r2 = model_final.score(X_final_scaled, y_final)
print(f"      Training R²: {final_r2:.6f}")

# Predict Oct 31
last_features_final = train_df[feature_cols].iloc[-1:].values
X_oct31 = imputer_final.transform(last_features_final)
X_oct31_scaled = scaler_final.transform(X_oct31)
oct31_prediction = model_final.predict(X_oct31_scaled)[0]

print(f"\n   {'=' * 60}")
print(f"   🎯 PREDICTION FOR OCTOBER 31, 2025")
print(f"   {'=' * 60}")
print(f"   Price: ${oct31_prediction:.3f}/gal")
print(f"   {'=' * 60}")

# Estimate uncertainty (use recent prediction errors)
results_df = pd.DataFrame(training_results)
recent_mae = results_df.tail(5)['abs_error'].mean()
recent_std = results_df.tail(5)['abs_error'].std()

print(f"\n   Uncertainty estimate (from recent errors):")
print(f"      Recent MAE (last 5 days): ${recent_mae:.4f}")
print(f"      Recent Std Dev: ${recent_std:.4f}")
print(f"      95% CI (approx): ${oct31_prediction:.3f} ± ${1.96 * recent_std:.3f}")
print(f"      Range: ${oct31_prediction - 1.96*recent_std:.3f} - ${oct31_prediction + 1.96*recent_std:.3f}")

# ============================================================================
# STEP 5: Save Results
# ============================================================================
print("\n" + "=" * 80)
print("STEP 5: SAVE RESULTS")
print("=" * 80)

# Save training results
results_df.to_csv(OUTPUT_DIR / 'incremental_training_oct19_29.csv', index=False)
print(f"\n✅ Training results: {OUTPUT_DIR / 'incremental_training_oct19_29.csv'}")

# Save Oct 31 prediction
oct31_record = {
    'prediction_date': datetime.now().strftime('%Y-%m-%d'),
    'target_date': '2025-10-31',
    'prediction': oct31_prediction,
    'lower_95ci': oct31_prediction - 1.96*recent_std,
    'upper_95ci': oct31_prediction + 1.96*recent_std,
    'recent_mae': recent_mae,
    'recent_std': recent_std,
    'training_samples': len(train_df),
    'training_r2': final_r2,
    'model': 'Ridge(alpha=1.0)',
    'features': len(feature_cols)
}

with open(OUTPUT_DIR / 'oct31_prediction.json', 'w') as f:
    json.dump(oct31_record, f, indent=2)

print(f"✅ Oct 31 prediction: {OUTPUT_DIR / 'oct31_prediction.json'}")

# ============================================================================
# STEP 6: Performance Summary
# ============================================================================
print("\n" + "=" * 80)
print("STEP 6: PERFORMANCE SUMMARY")
print("=" * 80)

print(f"\n📊 Incremental Training Performance (Oct 19-29):")
print(f"\n   {'Date':<12} {'Pred':<8} {'Actual':<8} {'Error':<10} {'Source':<12}")
print(f"   {'-'*55}")

for _, row in results_df.iterrows():
    print(f"   {row['date'].strftime('%Y-%m-%d'):<12} "
          f"${row['prediction']:.3f}   "
          f"${row['actual']:.3f}   "
          f"${row['error']:+.3f}     "
          f"{row['source']:<12}")

print(f"\n   Overall Metrics:")
print(f"      Mean Absolute Error: ${results_df['abs_error'].mean():.4f}")
print(f"      Mean % Error: {results_df['pct_error'].mean():.2f}%")
print(f"      Max Error: ${results_df['abs_error'].max():.4f}")
print(f"      Min Error: ${results_df['abs_error'].min():.4f}")

# EIA actual vs all others
eia_only = results_df[results_df['source'] == 'anchor']
interp_only = results_df[results_df['source'] == 'interpolated']

if len(eia_only) > 0:
    print(f"\n   EIA Anchor Points Only ({len(eia_only)} days):")
    print(f"      Mean Absolute Error: ${eia_only['abs_error'].mean():.4f}")
    print(f"      Mean % Error: {eia_only['pct_error'].mean():.2f}%")

if len(interp_only) > 0:
    print(f"\n   Interpolated Points ({len(interp_only)} days):")
    print(f"      Mean Absolute Error: ${interp_only['abs_error'].mean():.4f}")
    print(f"      Mean % Error: {interp_only['pct_error'].mean():.2f}%")

# ============================================================================
# STEP 7: Visualization
# ============================================================================
print("\n" + "=" * 80)
print("STEP 7: CREATE VISUALIZATIONS")
print("=" * 80)

print(f"\n📊 Generating graphs...")

# Graph 1: Predictions vs Actuals
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

# Time series
ax1.plot(results_df['date'], results_df['prediction'], 'o-', 
         label='ML Prediction', color='#2E86AB', linewidth=2, markersize=8)

eia_pts = results_df[results_df['source'] == 'anchor']
interp_pts = results_df[results_df['source'] == 'interpolated']

ax1.plot(eia_pts['date'], eia_pts['actual'], 's', 
         label='AAA/EIA Actual', color='#A23B72', markersize=12,
         markeredgewidth=2, markeredgecolor='white')
ax1.plot(interp_pts['date'], interp_pts['actual'], '^',
         label='Interpolated', color='#F18F01', markersize=8, alpha=0.6)

# Add Oct 31 prediction
ax1.axhline(y=oct31_prediction, color='green', linestyle='--', linewidth=2,
            label=f'Oct 31 Forecast: ${oct31_prediction:.3f}')
ax1.fill_between([results_df['date'].max(), pd.Timestamp('2025-10-31')],
                 oct31_prediction - 1.96*recent_std,
                 oct31_prediction + 1.96*recent_std,
                 color='green', alpha=0.2, label='95% CI')

ax1.set_xlabel('Date', fontsize=12, fontweight='bold')
ax1.set_ylabel('Price ($/gallon)', fontsize=12, fontweight='bold')
ax1.set_title('Daily Incremental Training + Oct 31 Forecast', fontsize=14, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Errors
ax2.bar(results_df['date'], results_df['error'], color=['red' if e > 0 else 'blue' for e in results_df['error']])
ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
ax2.set_ylabel('Prediction Error ($/gal)', fontsize=12, fontweight='bold')
ax2.set_title('Prediction Errors by Day', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='y')
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'final_training_and_forecast.png', dpi=300, bbox_inches='tight')
print(f"   ✅ Saved: final_training_and_forecast.png")
plt.close()

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("✅ AUTOMATION COMPLETE!")
print("=" * 80)

print(f"""
📋 SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Training Data:
   • Base: {len(gold_df)} historical samples (2020-2025)
   • Daily updates: {len(results_df)} days (Oct 19-29)
   • Total: {len(train_df)} samples
   • Final R²: {final_r2:.6f}

Validation Performance (Oct 19-29):
   • Mean Absolute Error: ${results_df['abs_error'].mean():.4f}
   • Mean % Error: {results_df['pct_error'].mean():.2f}%
   • Days tested: {len(results_df)}
   • All errors < $0.05: {(results_df['abs_error'] < 0.05).sum()}/{len(results_df)}

October 31 Forecast:
   • Prediction: ${oct31_prediction:.3f}/gal
   • 95% CI: ${oct31_prediction - 1.96*recent_std:.3f} - ${oct31_prediction + 1.96*recent_std:.3f}
   • Uncertainty: ±${1.96*recent_std:.3f}

Output Files:
   1. {OUTPUT_DIR / 'incremental_training_oct19_29.csv'}
   2. {OUTPUT_DIR / 'oct31_prediction.json'}
   3. {OUTPUT_DIR / 'final_training_and_forecast.png'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Next Steps:
   • Validate Oct 31 prediction when AAA updates (Nov 1)
   • Add to Kalshi submission
   • Continue daily collection for ongoing validation

System is fully automated and ready for production!
""")

print("=" * 80)
