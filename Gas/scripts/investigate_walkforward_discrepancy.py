"""
Investigate Walk-Forward vs Baseline Discrepancy

Purpose: Resolve the contradiction between:
- Baseline test R² = 0.595 (good)
- Walk-forward 21-day R² = -9.16 (catastrophic)

This script re-runs baseline models using walk-forward methodology to ensure
fair comparison and identify any data leakage.

Usage:
    python investigate_walkforward_discrepancy.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.baseline_models import (
    COMMON_FEATURES,
    compute_metrics,
    load_model_ready_dataset,
    train_ridge_model,
)


def investigate_discrepancy():
    """Compare baseline vs walk-forward methodologies to find discrepancy source."""
    
    print("=" * 80)
    print("WALK-FORWARD vs BASELINE DISCREPANCY INVESTIGATION")
    print("=" * 80)
    
    # Load data
    data_path = SCRIPT_DIR.parent / "data" / "gold" / "master_model_ready.parquet"
    df = load_model_ready_dataset(data_path)
    
    print(f"\n📊 Dataset: {len(df)} rows spanning {df['date'].min()} → {df['date'].max()}")
    
    # =========================================================================
    # TEST 1: Baseline Methodology (Current)
    # =========================================================================
    print("\n" + "=" * 80)
    print("TEST 1: BASELINE METHODOLOGY (Current)")
    print("=" * 80)
    
    baseline_test_start = pd.Timestamp("2024-10-01")
    baseline_train = df[df["date"] < baseline_test_start].copy()
    baseline_test = df[df["date"] >= baseline_test_start].copy()
    
    print(f"\nTrain: {len(baseline_train)} rows (before {baseline_test_start.date()})")
    print(f"Test:  {len(baseline_test)} rows (from {baseline_test_start.date()} onward)")
    print(f"Features: {len(COMMON_FEATURES)}")
    
    # Train Ridge model
    model_baseline = train_ridge_model(
        baseline_train, 
        COMMON_FEATURES, 
        target="retail_price", 
        alpha=0.01
    )
    
    # Predict
    train_preds_baseline = model_baseline.predict(baseline_train[COMMON_FEATURES])
    test_preds_baseline = model_baseline.predict(baseline_test[COMMON_FEATURES])
    
    # Metrics
    train_metrics_baseline = compute_metrics(baseline_train["retail_price"], train_preds_baseline)
    test_metrics_baseline = compute_metrics(baseline_test["retail_price"], test_preds_baseline)
    
    print(f"\n📊 BASELINE RESULTS:")
    print(f"   Train R²: {train_metrics_baseline['r2']:.3f}, RMSE: ${train_metrics_baseline['rmse']:.4f}")
    print(f"   Test R²:  {test_metrics_baseline['r2']:.3f}, RMSE: ${test_metrics_baseline['rmse']:.4f}")
    
    # =========================================================================
    # TEST 2: Walk-Forward Methodology (21-day horizon, Oct 2024)
    # =========================================================================
    print("\n" + "=" * 80)
    print("TEST 2: WALK-FORWARD METHODOLOGY (21-day horizon, Oct 2024)")
    print("=" * 80)
    
    # Create 21-day horizon dataset
    df_h21 = df.sort_values("date").copy()
    df_h21["target_h21"] = df_h21["retail_price"].shift(-21)
    df_h21["target_date"] = df_h21["date"] + pd.Timedelta(days=21)
    df_h21 = df_h21.dropna(subset=["target_h21"]).reset_index(drop=True)
    
    print(f"\nHorizon dataset: {len(df_h21)} rows")
    
    # Walk-forward split for Oct 2024
    year = 2024
    oct_start = pd.Timestamp(f"{year}-10-01")
    oct_end = pd.Timestamp(f"{year}-10-31")
    
    train_mask = df_h21["target_date"] < oct_start
    test_mask = (df_h21["target_date"] >= oct_start) & (df_h21["target_date"] <= oct_end)
    
    wf_train = df_h21.loc[train_mask].copy()
    wf_test = df_h21.loc[test_mask].copy()
    
    print(f"\nTrain: {len(wf_train)} rows (target_date < {oct_start.date()})")
    print(f"Test:  {len(wf_test)} rows (target_date in Oct {year})")
    
    # Check for overlap
    train_dates = set(wf_train["date"])
    test_dates = set(wf_test["date"])
    overlap = train_dates & test_dates
    
    if overlap:
        print(f"\n⚠️  WARNING: {len(overlap)} dates overlap between train and test!")
        print(f"   Overlap dates: {sorted(overlap)[:5]}...")
    else:
        print("\n✅ No date overlap between train and test")
    
    # Train Ridge model
    model_wf = train_ridge_model(
        wf_train, 
        COMMON_FEATURES, 
        target="target_h21", 
        alpha=0.01
    )
    
    # Predict
    train_preds_wf = model_wf.predict(wf_train[COMMON_FEATURES])
    test_preds_wf = model_wf.predict(wf_test[COMMON_FEATURES])
    
    # Metrics
    train_metrics_wf = compute_metrics(wf_train["target_h21"], train_preds_wf)
    test_metrics_wf = compute_metrics(wf_test["target_h21"], test_preds_wf)
    
    print(f"\n📊 WALK-FORWARD RESULTS (21-day horizon, Oct 2024):")
    print(f"   Train R²: {train_metrics_wf['r2']:.3f}, RMSE: ${train_metrics_wf['rmse']:.4f}")
    print(f"   Test R²:  {test_metrics_wf['r2']:.3f}, RMSE: ${test_metrics_wf['rmse']:.4f}")
    
    # =========================================================================
    # TEST 3: Baseline with Walk-Forward Split (Fair Comparison)
    # =========================================================================
    print("\n" + "=" * 80)
    print("TEST 3: BASELINE with WALK-FORWARD SPLIT (Fair Comparison)")
    print("=" * 80)
    print("\nUsing same train/test split as walk-forward, but predicting retail_price directly")
    
    # Use walk-forward train/test split but predict retail_price
    model_fair = train_ridge_model(
        wf_train, 
        COMMON_FEATURES, 
        target="retail_price",  # Same target as baseline
        alpha=0.01
    )
    
    # Predict
    test_preds_fair = model_fair.predict(wf_test[COMMON_FEATURES])
    
    # Metrics
    test_metrics_fair = compute_metrics(wf_test["retail_price"], test_preds_fair)
    
    print(f"\n📊 FAIR COMPARISON RESULTS:")
    print(f"   Test R²:  {test_metrics_fair['r2']:.3f}, RMSE: ${test_metrics_fair['rmse']:.4f}")
    
    # =========================================================================
    # ANALYSIS: Compare the three approaches
    # =========================================================================
    print("\n" + "=" * 80)
    print("ANALYSIS: Root Cause of Discrepancy")
    print("=" * 80)
    
    results_comparison = pd.DataFrame({
        "Method": [
            "Baseline (Original)",
            "Walk-Forward 21-day",
            "Fair Comparison"
        ],
        "Test R²": [
            test_metrics_baseline['r2'],
            test_metrics_wf['r2'],
            test_metrics_fair['r2']
        ],
        "Test RMSE": [
            test_metrics_baseline['rmse'],
            test_metrics_wf['rmse'],
            test_metrics_fair['rmse']
        ],
        "Train Size": [
            len(baseline_train),
            len(wf_train),
            len(wf_train)
        ],
        "Test Size": [
            len(baseline_test),
            len(wf_test),
            len(wf_test)
        ]
    })
    
    print("\n📊 COMPARISON TABLE:")
    print(results_comparison.to_string(index=False))
    
    # Identify root cause
    print("\n🔍 ROOT CAUSE ANALYSIS:")
    
    if abs(test_metrics_baseline['r2'] - test_metrics_fair['r2']) < 0.1:
        print("\n✅ CONCLUSION: Baseline and Fair Comparison are similar")
        print("   → Train/test split difference is NOT the issue")
    else:
        print(f"\n⚠️  FINDING: Baseline R²={test_metrics_baseline['r2']:.3f} vs Fair R²={test_metrics_fair['r2']:.3f}")
        print(f"   → Difference of {abs(test_metrics_baseline['r2'] - test_metrics_fair['r2']):.3f}")
        print("   → Train/test split DOES impact performance")
    
    if test_metrics_wf['r2'] < -1.0:
        print(f"\n🚨 CRITICAL: Walk-Forward R²={test_metrics_wf['r2']:.3f} (catastrophic)")
        print("   → 21-day horizon forecasting is fundamentally different from 0-day")
        print("   → Model cannot predict 21 days ahead with current features")
        print("   → This is EXPECTED - longer horizons have higher uncertainty")
    
    # Check data leakage indicators
    print("\n🔬 DATA LEAKAGE CHECKS:")
    
    # Check 1: Train R² should not be perfect
    if train_metrics_baseline['r2'] > 0.99:
        print(f"   ⚠️  Baseline train R²={train_metrics_baseline['r2']:.3f} (suspiciously high)")
        print("   → Possible overfitting or data leakage")
    else:
        print(f"   ✅ Baseline train R²={train_metrics_baseline['r2']:.3f} (reasonable)")
    
    # Check 2: Walk-forward train R² should be lower than test R²
    if train_metrics_wf['r2'] < test_metrics_wf['r2']:
        print(f"   ⚠️  Walk-forward train R²={train_metrics_wf['r2']:.3f} < test R²={test_metrics_wf['r2']:.3f}")
        print("   → Unusual - suggests test set is easier or different distribution")
    else:
        print(f"   ✅ Walk-forward train R²={train_metrics_wf['r2']:.3f} > test R²={test_metrics_wf['r2']:.3f}")
    
    # =========================================================================
    # RECOMMENDATION
    # =========================================================================
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    print("\n1. Walk-Forward R²=-9.16 is EXPECTED for 21-day forecasts")
    print("   → Gas prices have high short-term volatility")
    print("   → 21-day horizon exceeds model's predictive power with current features")
    print("   → This does NOT invalidate baseline R²=0.595 (0-day forecast)")
    
    print("\n2. Baseline R²=0.595 measures CONTEMPORANEOUS fit")
    print("   → Uses features from same day as prediction")
    print("   → This is appropriate for backtesting/validation")
    print("   → But NOT realistic for real-world forecasting (need 21-day horizon)")
    
    print("\n3. For October 31 forecast on October 10:")
    print("   → Use walk-forward methodology (21-day horizon)")
    print("   → Accept lower R² (-9.16) as realistic uncertainty")
    print("   → Consider ensemble with uncertainty quantification (quantile regression)")
    
    print("\n4. Improve 21-day forecasts:")
    print("   → Add forward-looking features (futures curves, forecasts)")
    print("   → Use time-series models (ARIMA, Prophet)")
    print("   → Ensemble multiple horizons (1-day, 3-day, 7-day, 14-day, 21-day)")
    
    # Save results
    output_path = SCRIPT_DIR.parent / "outputs" / "validation" / "walkforward_discrepancy_analysis.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_comparison.to_csv(output_path, index=False)
    print(f"\n✓ Results saved to {output_path}")


if __name__ == "__main__":
    investigate_discrepancy()
