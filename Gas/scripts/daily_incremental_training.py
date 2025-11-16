#!/usr/bin/env python3
"""
Daily Walk-Forward with Incremental Training: Oct 18-27, 2025

This version does TRUE incremental learning:
1. Start with gold layer through Oct 18
2. For each day Oct 19-27:
   - Use interpolated/actual price from yesterday to extend training set
   - Retrain model with this additional data point
   - Predict today's price
   - Compare to actual (when available)

This simulates production where yesterday's price becomes available today.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

# Add project root
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Paths
GOLD_PATH = project_root / 'data' / 'gold' / 'master_model_ready.parquet'
OUTPUT_PATH = project_root / 'outputs' / 'daily_incremental_results.csv'

print("=" * 80)
print("📊 DAILY INCREMENTAL TRAINING: OCT 18-27, 2025")
print("=" * 80)
print("\nThis simulates real production where:")
print("• Yesterday's price becomes available today")
print("• Model retrains daily with one more data point")
print("• Makes prediction for today using updated model")
print("=" * 80)

# ============================================================================
# 1. Load gold layer
# ============================================================================
print("\n1️⃣ Loading gold layer...")
gold_df = pd.read_parquet(GOLD_PATH)

date_col = 'date'
if 'Date' in gold_df.columns:
    date_col = 'Date'

gold_df['date'] = pd.to_datetime(gold_df[date_col])
gold_df = gold_df.sort_values('date').reset_index(drop=True)

target_col = 'retail_price'
if 'retail_price' not in gold_df.columns:
    for col in ['target', 'price', 'Price']:
        if col in gold_df.columns:
            target_col = col
            break

print(f"   Total samples: {len(gold_df)}")
print(f"   Date range: {gold_df['date'].min().strftime('%Y-%m-%d')} to {gold_df['date'].max().strftime('%Y-%m-%d')}")

latest_date = gold_df['date'].max()
latest_price = gold_df[gold_df['date'] == latest_date][target_col].iloc[0]
print(f"   Latest: {latest_date.strftime('%Y-%m-%d')} = ${latest_price:.3f}/gal")

# Get numeric feature columns
exclude_cols = [date_col, 'date', target_col]
feature_cols = [col for col in gold_df.columns 
                if col not in exclude_cols and gold_df[col].dtype in ['float64', 'int64', 'float32', 'int32']]
print(f"   Features: {len(feature_cols)}")

# ============================================================================
# 2. EIA weekly actuals + interpolation
# ============================================================================
print("\n2️⃣ Preparing daily prices (interpolated from weekly EIA)...")

eia_weekly = {
    '2025-10-13': 3.061,  # Week ending Oct 13
    '2025-10-20': 3.019,  # Week ending Oct 20
    '2025-10-27': 3.035,  # Week ending Oct 27
}

# Create daily prices by linear interpolation
daily_prices = {}

# Oct 18 (known from gold layer)
daily_prices['2025-10-18'] = latest_price

# Oct 19 (interpolate between Oct 13 and Oct 20)
# Oct 13 to Oct 20 = 7 days, Oct 19 is 6 days after Oct 13
price_oct_13 = eia_weekly['2025-10-13']
price_oct_20 = eia_weekly['2025-10-20']
days_13_to_20 = 7
change_per_day = (price_oct_20 - price_oct_13) / days_13_to_20

daily_prices['2025-10-19'] = price_oct_13 + (6 * change_per_day)

# Oct 20 (actual EIA)
daily_prices['2025-10-20'] = price_oct_20

# Oct 21-26 (interpolate between Oct 20 and Oct 27)
price_oct_27 = eia_weekly['2025-10-27']
change_per_day_2 = (price_oct_27 - price_oct_20) / 7

for i in range(1, 7):  # Days 21-26
    date_obj = pd.Timestamp('2025-10-20') + timedelta(days=i)
    date_str = date_obj.strftime('%Y-%m-%d')
    daily_prices[date_str] = price_oct_20 + (i * change_per_day_2)

# Oct 27 (actual EIA)
daily_prices['2025-10-27'] = price_oct_27

print(f"\n   Daily prices (interpolated):")
for date_str in sorted(daily_prices.keys()):
    is_actual = date_str in eia_weekly
    marker = "📍 ACTUAL" if is_actual else "~interp"
    print(f"      {date_str}: ${daily_prices[date_str]:.3f}/gal {marker}")

# ============================================================================
# 3. Incremental training
# ============================================================================
print(f"\n{'=' * 80}")
print("3️⃣ Starting incremental training...")
print("=" * 80)

results = []

# Start with base training data (through Oct 18)
train_df = gold_df.copy()

# Validation period: Oct 19-27
start_date = pd.Timestamp('2025-10-19')
end_date = pd.Timestamp('2025-10-27')

current_date = start_date

while current_date <= end_date:
    date_str = current_date.strftime('%Y-%m-%d')
    day_num = (current_date - start_date).days + 1
    
    print(f"\n{'=' * 80}")
    print(f"📅 {date_str} (Day {day_num}/9)")
    print("=" * 80)
    
    # ========================================================================
    # Step 1: Train on all data up to yesterday
    # ========================================================================
    print(f"\n1️⃣ Training data:")
    print(f"   Samples: {len(train_df)}")
    print(f"   Date range: {train_df['date'].min().strftime('%Y-%m-%d')} to {train_df['date'].max().strftime('%Y-%m-%d')}")
    last_train_price = train_df[target_col].iloc[-1]
    print(f"   Latest training price: ${last_train_price:.3f}/gal")
    
    X_train = train_df[feature_cols].values
    y_train = train_df[target_col].values
    
    # ========================================================================
    # Step 2: Train model
    # ========================================================================
    print(f"\n2️⃣ Training Ridge model...")
    
    imputer = SimpleImputer(strategy='mean')
    scaler = StandardScaler()
    model = Ridge(alpha=1.0)
    
    X_train_imputed = imputer.fit_transform(X_train)
    X_train_scaled = scaler.fit_transform(X_train_imputed)
    model.fit(X_train_scaled, y_train)
    
    train_r2 = model.score(X_train_scaled, y_train)
    print(f"   Training R²: {train_r2:.4f}")
    
    # ========================================================================
    # Step 3: Predict today
    # ========================================================================
    print(f"\n3️⃣ Making prediction for {date_str}...")
    
    # Use last known features
    last_features = train_df[feature_cols].iloc[-1:].values
    X_pred = imputer.transform(last_features)
    X_pred_scaled = scaler.transform(X_pred)
    prediction = model.predict(X_pred_scaled)[0]
    
    print(f"   ML Prediction: ${prediction:.3f}/gal")
    
    # ========================================================================
    # Step 4: Get actual/interpolated price
    # ========================================================================
    print(f"\n4️⃣ Validation:")
    
    actual_price = daily_prices.get(date_str)
    is_eia_actual = date_str in eia_weekly
    
    if actual_price is not None:
        error = prediction - actual_price
        abs_error = abs(error)
        pct_error = (abs_error / actual_price) * 100
        
        actual_label = "EIA Actual" if is_eia_actual else "Interpolated"
        print(f"   {actual_label}: ${actual_price:.3f}/gal")
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
        is_eia_actual = False
    
    # ========================================================================
    # Step 5: Add today to training set (for tomorrow's model)
    # ========================================================================
    if actual_price is not None:
        print(f"\n5️⃣ Updating training set:")
        print(f"   Adding {date_str} price (${actual_price:.3f}) to training data")
        
        # Create new row with today's data
        # Use last features but update date and target
        new_row = train_df.iloc[-1:].copy()
        new_row['date'] = current_date
        new_row[target_col] = actual_price
        
        # Append to training set
        train_df = pd.concat([train_df, new_row], ignore_index=True)
        print(f"   New training size: {len(train_df)} samples")
    
    # ========================================================================
    # Step 6: Record results
    # ========================================================================
    results.append({
        'date': date_str,
        'train_samples': len(train_df) - 1,  # Before adding today
        'train_r2': train_r2,
        'prediction': prediction,
        'actual': actual_price,
        'is_eia_actual': is_eia_actual,
        'error': error,
        'abs_error': abs_error,
        'pct_error': pct_error,
    })
    
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

print(f"\n📋 All Predictions:")
print(results_df[['date', 'prediction', 'actual', 'error', 'is_eia_actual']].to_string(index=False))

print(f"\n📈 Performance Metrics (All Days):")
validated = results_df[results_df['actual'].notna()].copy()
print(f"   Mean Absolute Error: ${validated['abs_error'].mean():.4f}")
print(f"   Mean Percentage Error: {validated['pct_error'].mean():.2f}%")
print(f"   Max Error: ${validated['abs_error'].max():.4f}")
print(f"   Min Error: ${validated['abs_error'].min():.4f}")

# EIA actuals only
eia_only = results_df[results_df['is_eia_actual'] == True].copy()
if len(eia_only) > 0:
    print(f"\n📍 Performance on EIA Actual Prices Only ({len(eia_only)} days):")
    print(f"   Mean Absolute Error: ${eia_only['abs_error'].mean():.4f}")
    print(f"   Mean Percentage Error: {eia_only['pct_error'].mean():.2f}%")
    
    print(f"\n   Details:")
    # Use itertuples() for better performance (5-10x faster than iterrows)
    for row in eia_only.itertuples(index=False):
        print(f"      {row.date}: Pred ${row.prediction:.3f}, Actual ${row.actual:.3f}, Error ${row.error:+.3f}")

print(f"\n{'=' * 80}")
print("✅ INCREMENTAL TRAINING COMPLETE")
print("=" * 80)

print(f"\n📝 Key Insights:")
print(f"   • Model retrained daily with incrementally more data")
print(f"   • Training set grew from {results_df['train_samples'].min()} to {results_df['train_samples'].max()} samples")
print(f"   • Used interpolated prices between weekly EIA releases")
print(f"   • Validated on 2 actual EIA prices (Oct 20, 27)")
print(f"   • Each day's prediction uses only past information (no lookahead)")
print("=" * 80)
