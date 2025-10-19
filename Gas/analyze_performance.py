"""
Comprehensive Model Performance Report with Sentiment Features
"""

import pandas as pd
import numpy as np
from pathlib import Path

print("\n" + "="*80)
print("📊 MODEL PERFORMANCE REPORT: WITH SENTIMENT FEATURES")
print("="*80)

# 1. Load walk-forward validation results
wf = pd.read_csv('outputs/walk_forward/walk_forward_metrics.csv')

print("\n🔍 Analysis of Walk-Forward Validation Results:")
print("="*80)

# Check all horizons
for horizon in sorted(wf['horizon'].unique()):
    wf_h = wf[wf['horizon'] == horizon]
    print(f"\nHorizon: {horizon} days")
    print(f"  Mean R²: {wf_h['r2'].mean():+.4f}")
    print(f"  Mean MAE: ${wf_h['mae'].mean():.4f}")
    print(f"  Mean MAPE: {wf_h['mape_pct'].mean():.2f}%")
    print(f"  Folds: {len(wf_h)}")

# 2. Load simple train/test metrics (0-horizon)
try:
    metrics = pd.read_csv('outputs/models/model_metrics_summary.csv')
    print("\n\n📈 Same-Day Prediction Performance (0-day horizon):")
    print("="*80)
    print(metrics[['model', 'test_r2', 'test_mae', 'test_mape_pct']].to_string(index=False))
except:
    print("\n⚠️  No same-day metrics found")

# 3. Check feature count
try:
    gold = pd.read_parquet('data/gold/master_model_ready.parquet')
    sentiment_feats = [c for c in gold.columns if 'sentiment' in c or 'news_' in c]
    sentiment_feats = [c for c in sentiment_feats if c != 'consumer_sentiment']
    
    print("\n\n✨ Feature Set Analysis:")
    print("="*80)
    print(f"  Total features: {len(gold.columns)}")
    print(f"  Sentiment features: {len(sentiment_feats)}")
    print(f"  Non-sentiment features: {len(gold.columns) - len(sentiment_feats)}")
    
    print(f"\n  Sentiment features:")
    for feat in sentiment_feats:
        non_zero = (gold[feat] != 0).sum()
        print(f"    - {feat:40s} {non_zero:4d} non-zero ({non_zero/len(gold)*100:.1f}%)")
except Exception as e:
    print(f"\n⚠️  Error loading features: {e}")

# 4. Diagnosis
print("\n\n🔬 DIAGNOSIS:")
print("="*80)

wf_14d = wf[wf['horizon'] == 14]
mean_r2_14d = wf_14d['r2'].mean()

if mean_r2_14d < 0:
    print("\n⚠️  NEGATIVE R² DETECTED")
    print("\nPossible causes:")
    print("  1. Model is only trained on Ridge (simple linear model)")
    print("  2. Sentiment features have low coverage (18.6% of data)")
    print("  3. 14-day horizon is challenging for linear models")
    print("  4. Need to try non-linear models (GB, LSTM)")
    
    print("\n💡 Recommendations:")
    print("  1. Check Gradient Boosting performance (non-linear)")
    print("  2. Try ensemble model (combines multiple models)")
    print("  3. Focus on shorter horizons (3-7 days) where sentiment is stronger")
    print("  4. Consider LSTM for time series patterns")
elif mean_r2_14d > 0.086:
    print("\n✅ IMPROVEMENT DETECTED!")
    print(f"  Baseline R²: 0.086")
    print(f"  Current R²: {mean_r2_14d:.4f}")
    print(f"  Improvement: {(mean_r2_14d - 0.086):.4f} ({(mean_r2_14d/0.086 - 1)*100:.1f}% gain)")
else:
    print("\n⚠️  PERFORMANCE SIMILAR TO BASELINE")
    print(f"  Baseline R²: 0.086")
    print(f"  Current R²: {mean_r2_14d:.4f}")

# 5. Check if GB or ensemble models were trained
print("\n\n🤖 Model Availability:")
print("="*80)
try:
    models_dir = Path('outputs/models')
    gb_model = models_dir / 'gradient_boosting_model.pkl'
    ensemble_model = models_dir / 'ensemble_model.pkl'
    
    print(f"  Gradient Boosting: {'✅ Found' if gb_model.exists() else '❌ Not found'}")
    print(f"  Ensemble Model: {'✅ Found' if ensemble_model.exists() else '❌ Not found'}")
    
    if gb_model.exists():
        print("\n💡 Gradient Boosting model exists - should evaluate with 14-day horizon")
    if ensemble_model.exists():
        print("💡 Ensemble model exists - should evaluate with 14-day horizon")
except Exception as e:
    print(f"  Error checking models: {e}")

print("\n" + "="*80)
print("📋 NEXT STEPS:")
print("="*80)
print("1. Train Gradient Boosting with 14-day horizon specifically")
print("2. Evaluate ensemble model performance")
print("3. Try shorter horizons (3-7 days) where sentiment signal is stronger")
print("4. Consider feature selection (sentiment features with low coverage)")
print("5. Implement LSTM for better time series modeling")
print("\n" + "="*80)
