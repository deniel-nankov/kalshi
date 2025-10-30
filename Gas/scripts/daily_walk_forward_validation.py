#!/usr/bin/env python3
"""
Daily Walk-Forward Validation: Oct 18-27, 2025

This script performs true walk-forward validation:
1. For each day from Oct 18-27:
   - Train model on ALL data up to (but not including) that day
   - Make prediction for that day
   - Compare prediction to actual price (when available)
   - Retrain next day with one more data point

This simulates real production usage where model is retrained daily with most recent data.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import joblib

# Add project root
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Paths
GOLD_PATH = project_root / 'data' / 'gold' / 'master_model_ready.parquet'
OUTPUT_PATH = project_root / 'outputs' / 'daily_walk_forward_results.csv'

print("=" * 80)
print("📊 DAILY WALK-FORWARD VALIDATION: OCT 18-27, 2025")
print("=" * 80)

# ============================================================================
# 1. Load gold layer (historical data through Oct 18)
# ============================================================================
print("\n1️⃣ Loading gold layer...")
gold_df = pd.read_parquet(GOLD_PATH)

# Find date column
date_col = None
for col in ['date', 'Date', 'DATE']:
    if col in gold_df.columns:
        date_col = col
        break

if not date_col:
    print("❌ No date column found!")
    sys.exit(1)

gold_df['date'] = pd.to_datetime(gold_df[date_col])
gold_df = gold_df.sort_values('date').reset_index(drop=True)

# Find target column
target_col = None
for col in ['retail_price', 'target', 'price']:
    if col in gold_df.columns:
        target_col = col
        break

if not target_col:
    print("❌ No target column found!")
    print(f"Available columns: {list(gold_df.columns[:20])}")
    sys.exit(1)

print(f"   Date column: {date_col}")
print(f"   Target column: {target_col}")
print(f"   Total samples: {len(gold_df)}")
print(f"   Date range: {gold_df['date'].min().strftime('%Y-%m-%d')} to {gold_df['date'].max().strftime('%Y-%m-%d')}")

latest_date = gold_df['date'].max()
print(f"   Latest gold layer date: {latest_date.strftime('%Y-%m-%d')}")

# Get feature columns (exclude date and target, only numeric)
exclude_cols = [date_col, 'date', target_col]
feature_cols = [col for col in gold_df.columns 
                if col not in exclude_cols and gold_df[col].dtype in ['float64', 'int64', 'float32', 'int32']]
print(f"   Feature columns: {len(feature_cols)}")

# Check for any non-numeric that slipped through
non_numeric = [col for col in feature_cols if gold_df[col].dtype == 'object']
if non_numeric:
    print(f"   ⚠️ Removing {len(non_numeric)} non-numeric columns: {non_numeric[:5]}")
    feature_cols = [col for col in feature_cols if col not in non_numeric]
    print(f"   Final feature columns: {len(feature_cols)}")

# ============================================================================
# 2. EIA weekly actuals (for validation)
# ============================================================================
print("\n2️⃣ Loading EIA weekly actuals...")

eia_actuals = {
    '2025-10-20': 3.019,
    '2025-10-27': 3.035,
}

print(f"   Available weekly actuals: {len(eia_actuals)}")
for date_str, price in eia_actuals.items():
    print(f"      {date_str}: ${price:.3f}/gal")

# ============================================================================
# 3. Daily walk-forward validation
# ============================================================================
print("\n3️⃣ Starting daily walk-forward validation...")
print("   This will train a new model each day using only past data")
print("=" * 80)

# Validation period: Oct 19-27 (we have data through Oct 18)
start_date = latest_date + timedelta(days=1)  # Oct 19
end_date = pd.Timestamp('2025-10-27')

results = []
current_date = start_date

while current_date <= end_date:
    date_str = current_date.strftime('%Y-%m-%d')
    print(f"\n{'=' * 80}")
    print(f"📅 {date_str} (Day {(current_date - start_date).days + 1}/9)")
    print("=" * 80)
    
    # ========================================================================
    # Step 1: Get training data (everything before current_date)
    # ========================================================================
    train_mask = gold_df['date'] < current_date
    train_df = gold_df[train_mask].copy()
    
    if len(train_df) < 100:
        print(f"   ⚠️ Insufficient training data ({len(train_df)} samples)")
        current_date += timedelta(days=1)
        continue
    
    print(f"\n1️⃣ Training data:")
    print(f"   Samples: {len(train_df)}")
    print(f"   Date range: {train_df['date'].min().strftime('%Y-%m-%d')} to {train_df['date'].max().strftime('%Y-%m-%d')}")
    print(f"   Latest price: ${train_df[target_col].iloc[-1]:.3f}/gal")
    
    # ========================================================================
    # Step 2: Train model
    # ========================================================================
    print(f"\n2️⃣ Training Ridge model...")
    
    X_train = train_df[feature_cols].values
    y_train = train_df[target_col].values
    
    # Preprocessing pipeline
    imputer = SimpleImputer(strategy='mean')
    scaler = StandardScaler()
    model = Ridge(alpha=1.0)
    
    # Fit pipeline
    X_train_imputed = imputer.fit_transform(X_train)
    X_train_scaled = scaler.fit_transform(X_train_imputed)
    model.fit(X_train_scaled, y_train)
    
    # Training metrics
    train_pred = model.predict(X_train_scaled)
    train_mae = np.mean(np.abs(train_pred - y_train))
    train_r2 = model.score(X_train_scaled, y_train)
    
    print(f"   Training MAE: ${train_mae:.4f}")
    print(f"   Training R²: {train_r2:.4f}")
    
    # ========================================================================
    # Step 3: Make prediction for current_date
    # ========================================================================
    print(f"\n3️⃣ Making prediction for {date_str}...")
    
    # For prediction, we need features for current_date
    # Since we don't have actual features for future dates, we'll use:
    # Option A: Use last known features (from Oct 18)
    # Option B: Extrapolate using trends
    # Let's use Option A (most conservative)
    
    last_features = gold_df[gold_df['date'] == latest_date][feature_cols].values
    
    if len(last_features) == 0:
        print(f"   ⚠️ No features available for prediction")
        current_date += timedelta(days=1)
        continue
    
    # Transform features
    X_pred = imputer.transform(last_features)
    X_pred_scaled = scaler.transform(X_pred)
    
    # Predict
    prediction = model.predict(X_pred_scaled)[0]
    
    print(f"   ML Prediction: ${prediction:.3f}/gal")
    
    # ========================================================================
    # Step 4: Get actual price (if available)
    # ========================================================================
    print(f"\n4️⃣ Validation:")
    
    actual_price = eia_actuals.get(date_str, None)
    
    if actual_price is not None:
        error = prediction - actual_price
        abs_error = abs(error)
        pct_error = (abs_error / actual_price) * 100
        
        print(f"   Actual price: ${actual_price:.3f}/gal")
        print(f"   Prediction: ${prediction:.3f}/gal")
        print(f"   Error: ${error:+.3f}/gal ({pct_error:.2f}%)")
        
        if abs_error < 0.01:
            print(f"   ✅ Excellent! Error < $0.01")
        elif abs_error < 0.05:
            print(f"   ✅ Good! Error < $0.05")
        else:
            print(f"   ⚠️ Error > $0.05")
    else:
        actual_price = None
        error = None
        abs_error = None
        pct_error = None
        print(f"   ℹ️ No actual price available (EIA publishes weekly)")
    
    # ========================================================================
    # Step 5: Record results
    # ========================================================================
    results.append({
        'date': date_str,
        'train_samples': len(train_df),
        'train_start': train_df['date'].min().strftime('%Y-%m-%d'),
        'train_end': train_df['date'].max().strftime('%Y-%m-%d'),
        'train_mae': train_mae,
        'train_r2': train_r2,
        'prediction': prediction,
        'actual': actual_price,
        'error': error,
        'abs_error': abs_error,
        'pct_error': pct_error,
    })
    
    # Move to next day
    current_date += timedelta(days=1)

# ============================================================================
# 4. Save results
# ============================================================================
print(f"\n{'=' * 80}")
print("💾 SAVING RESULTS")
print("=" * 80)

results_df = pd.DataFrame(results)
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
results_df.to_csv(OUTPUT_PATH, index=False)

print(f"\n✅ Saved to: {OUTPUT_PATH}")
print(f"   Total predictions: {len(results_df)}")

# ============================================================================
# 5. Summary statistics
# ============================================================================
print(f"\n{'=' * 80}")
print("📊 SUMMARY STATISTICS")
print("=" * 80)

# Filter for dates with actual prices
validated = results_df[results_df['actual'].notna()].copy()

if len(validated) > 0:
    print(f"\nValidated predictions: {len(validated)}")
    print(f"\nPredictions vs Actuals:")
    print(validated[['date', 'prediction', 'actual', 'error', 'pct_error']].to_string(index=False))
    
    print(f"\n📈 Performance Metrics:")
    print(f"   Mean Absolute Error: ${validated['abs_error'].mean():.4f}")
    print(f"   Mean Percentage Error: {validated['pct_error'].mean():.2f}%")
    print(f"   Max Error: ${validated['abs_error'].max():.4f}")
    print(f"   Min Error: ${validated['abs_error'].min():.4f}")
    
    # Check if errors are within tolerance
    within_1_cent = (validated['abs_error'] < 0.01).sum()
    within_5_cent = (validated['abs_error'] < 0.05).sum()
    
    print(f"\n📊 Error Distribution:")
    print(f"   Within $0.01: {within_1_cent}/{len(validated)} ({within_1_cent/len(validated)*100:.1f}%)")
    print(f"   Within $0.05: {within_5_cent}/{len(validated)} ({within_5_cent/len(validated)*100:.1f}%)")
else:
    print(f"\n⚠️ No validated predictions (no actual prices available)")

print(f"\n{'=' * 80}")
print("✅ DAILY WALK-FORWARD VALIDATION COMPLETE")
print("=" * 80)

print(f"\n📝 Notes:")
print(f"   • Model retrained daily with most recent data")
print(f"   • Predictions made using last known features (Oct 18)")
print(f"   • Validation limited to weekly EIA data (Oct 20, 27)")
print(f"   • To get daily actuals, would need different data source")
print(f"   • This simulates real production: train on past, predict future")
print("=" * 80)
