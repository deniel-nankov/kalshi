"""
October-Specific Training Comparison

Purpose: Test whether training ONLY on October data improves forecasting
for October predictions (vs training on all months).

Hypothesis: October has unique patterns (hurricane risk, winter blend transition)
that may be diluted when training on all months (Jan-Dec).

Methodology:
1. Train on October-only data (Oct 2020-2023) → Test on Oct 2024
2. Train on All-months data (Jan-Dec 2020-Sep 2024) → Test on Oct 2024
3. Compare performance (R², RMSE, MAPE)

Usage:
    python october_specific_training.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.baseline_models import (
    COMMON_FEATURES,
    compute_metrics,
    load_model_ready_dataset,
    train_all_models,
)


def october_specific_comparison():
    """Compare October-only vs All-months training strategies."""
    
    print("=" * 80)
    print("OCTOBER-SPECIFIC TRAINING COMPARISON")
    print("=" * 80)
    
    # Load data
    data_path = SCRIPT_DIR.parent / "data" / "gold" / "master_model_ready.parquet"
    df = load_model_ready_dataset(data_path)
    
    print(f"\n📊 Full Dataset: {len(df)} rows spanning {df['date'].min()} → {df['date'].max()}")
    
    # Extract October data
    df['month'] = df['date'].dt.month
    october_data = df[df['month'] == 10].copy()
    
    print(f"📊 October Data: {len(october_data)} rows across {october_data['date'].dt.year.nunique()} years")
    print(f"   Years: {sorted(october_data['date'].dt.year.unique())}")
    
    # Define test period (Oct 2024)
    test_start = pd.Timestamp("2024-10-01")
    test_end = pd.Timestamp("2024-10-31")
    
    # =========================================================================
    # STRATEGY 1: All-Months Training (Current Baseline)
    # =========================================================================
    print("\n" + "=" * 80)
    print("STRATEGY 1: ALL-MONTHS TRAINING (Current Baseline)")
    print("=" * 80)
    
    all_train = df[df['date'] < test_start].copy()
    all_test = df[(df['date'] >= test_start) & (df['date'] <= test_end)].copy()
    
    print(f"\nTrain: {len(all_train)} rows (all months from {all_train['date'].min().date()} to {all_train['date'].max().date()})")
    print(f"Test:  {len(all_test)} rows (Oct 2024 only)")
    
    # Month distribution in training
    train_month_dist = all_train['month'].value_counts().sort_index()
    print(f"\nTraining data month distribution:")
    for month, count in train_month_dist.items():
        pct = 100 * count / len(all_train)
        month_name = pd.Timestamp(f"2024-{month:02d}-01").strftime('%B')
        marker = "🎯" if month == 10 else ""
        print(f"   {month_name:>9}: {count:4d} rows ({pct:5.2f}%) {marker}")
    
    print(f"\n🔄 Training models with all-months data...")
    # Combine train+test for train_all_models API
    all_combined = pd.concat([all_train, all_test], ignore_index=True)
    results_all = train_all_models(all_combined, test_start=test_start, features=COMMON_FEATURES)
    
    print(f"\n📊 ALL-MONTHS RESULTS:")
    for model_name in ['Ridge', 'Inventory', 'Futures', 'Ensemble']:
        if model_name in results_all:
            metrics = results_all[model_name].metrics['test']
            print(f"   {model_name:12s}: R²={metrics['r2']:6.3f}, RMSE=${metrics['rmse']:.4f}, MAPE={metrics['mape_pct']:.2f}%")
    
    # =========================================================================
    # STRATEGY 2: October-Only Training
    # =========================================================================
    print("\n" + "=" * 80)
    print("STRATEGY 2: OCTOBER-ONLY TRAINING")
    print("=" * 80)
    
    oct_train = october_data[october_data['date'] < test_start].copy()
    oct_test = october_data[(october_data['date'] >= test_start) & (october_data['date'] <= test_end)].copy()
    
    print(f"\nTrain: {len(oct_train)} rows (October only from {oct_train['date'].min().date()} to {oct_train['date'].max().date()})")
    print(f"Test:  {len(oct_test)} rows (Oct 2024 only)")
    
    # Year distribution in training
    train_year_dist = oct_train['date'].dt.year.value_counts().sort_index()
    print(f"\nTraining data year distribution:")
    for year, count in train_year_dist.items():
        print(f"   October {year}: {count:2d} rows")
    
    print(f"\n🔄 Training models with October-only data...")
    # Combine train+test for train_all_models API
    oct_combined = pd.concat([oct_train, oct_test], ignore_index=True)
    results_oct = train_all_models(oct_combined, test_start=test_start, features=COMMON_FEATURES)
    
    print(f"\n📊 OCTOBER-ONLY RESULTS:")
    for model_name in ['Ridge', 'Inventory', 'Futures', 'Ensemble']:
        if model_name in results_oct:
            metrics = results_oct[model_name].metrics['test']
            print(f"   {model_name:12s}: R²={metrics['r2']:6.3f}, RMSE=${metrics['rmse']:.4f}, MAPE={metrics['mape_pct']:.2f}%")
    
    # =========================================================================
    # COMPARISON ANALYSIS
    # =========================================================================
    print("\n" + "=" * 80)
    print("COMPARISON ANALYSIS")
    print("=" * 80)
    
    comparison_data = []
    
    for model_name in ['Ridge', 'Inventory', 'Futures', 'Ensemble']:
        if model_name in results_all and model_name in results_oct:
            all_metrics = results_all[model_name].metrics['test']
            oct_metrics = results_oct[model_name].metrics['test']
            
            comparison_data.append({
                'Model': model_name,
                'All-Months R²': all_metrics['r2'],
                'October-Only R²': oct_metrics['r2'],
                'R² Difference': oct_metrics['r2'] - all_metrics['r2'],
                'All-Months RMSE': all_metrics['rmse'],
                'October-Only RMSE': oct_metrics['rmse'],
                'RMSE Difference': oct_metrics['rmse'] - all_metrics['rmse'],
            })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    print("\n📊 SIDE-BY-SIDE COMPARISON:")
    print(comparison_df.to_string(index=False))
    
    # Interpret results
    print("\n🔍 INTERPRETATION:")
    
    ensemble_improvement = comparison_df[comparison_df['Model'] == 'Ensemble']['R² Difference'].values[0]
    
    if ensemble_improvement > 0.05:
        print(f"\n✅ WINNER: October-Only Training")
        print(f"   Ensemble R² improved by {ensemble_improvement:.3f} (+{ensemble_improvement*100:.1f}%)")
        print(f"   REASON: October-specific patterns (hurricane risk, winter blend) matter")
        print(f"   RECOMMENDATION: Use October-only training for production")
    elif ensemble_improvement < -0.05:
        print(f"\n⚠️  WINNER: All-Months Training")
        print(f"   Ensemble R² worsened by {ensemble_improvement:.3f} ({ensemble_improvement*100:.1f}%)")
        print(f"   REASON: October-only has insufficient data (only {len(oct_train)} rows)")
        print(f"   RECOMMENDATION: Keep current all-months training")
    else:
        print(f"\n🟡 NEUTRAL: Similar Performance")
        print(f"   Ensemble R² difference: {ensemble_improvement:.3f} ({ensemble_improvement*100:.1f}%)")
        print(f"   REASON: October patterns not significantly different from other months")
        print(f"   RECOMMENDATION: Keep all-months training (more data = more robust)")
    
    # Sample size consideration
    print(f"\n📊 SAMPLE SIZE CONSIDERATION:")
    print(f"   All-Months Training:  {len(all_train):4d} rows → {len(all_test):2d} test observations")
    print(f"   October-Only Training: {len(oct_train):4d} rows → {len(oct_test):2d} test observations")
    print(f"   Training size ratio: {len(oct_train)/len(all_train):.1%}")
    
    if len(oct_train) < 100:
        print(f"\n⚠️  WARNING: October-only training has only {len(oct_train)} rows")
        print(f"   This may lead to overfitting and unstable estimates")
        print(f"   Recommend minimum 200 rows for robust model training")
    
    # =========================================================================
    # VISUALIZATION
    # =========================================================================
    print("\n" + "=" * 80)
    print("CREATING COMPARISON VISUALIZATION")
    print("=" * 80)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: R² Comparison
    ax1 = axes[0]
    models = comparison_df['Model']
    x = np.arange(len(models))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, comparison_df['All-Months R²'], width, 
                    label='All-Months', color='#3498DB', alpha=0.8)
    bars2 = ax1.bar(x + width/2, comparison_df['October-Only R²'], width, 
                    label='October-Only', color='#E74C3C', alpha=0.8)
    
    ax1.set_xlabel('Model', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Test R²', fontsize=12, fontweight='bold')
    ax1.set_title('R² Comparison: All-Months vs October-Only', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(models, fontsize=10)
    ax1.legend(fontsize=10)
    ax1.grid(axis='y', alpha=0.3)
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.3f}',
                    ha='center', va='bottom' if height > 0 else 'top', 
                    fontsize=9)
    
    # Plot 2: RMSE Comparison
    ax2 = axes[1]
    
    bars3 = ax2.bar(x - width/2, comparison_df['All-Months RMSE'], width, 
                    label='All-Months', color='#3498DB', alpha=0.8)
    bars4 = ax2.bar(x + width/2, comparison_df['October-Only RMSE'], width, 
                    label='October-Only', color='#E74C3C', alpha=0.8)
    
    ax2.set_xlabel('Model', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Test RMSE ($)', fontsize=12, fontweight='bold')
    ax2.set_title('RMSE Comparison: All-Months vs October-Only', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(models, fontsize=10)
    ax2.legend(fontsize=10)
    ax2.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bars in [bars3, bars4]:
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'${height:.4f}',
                    ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    
    # Save visualization
    output_path = SCRIPT_DIR.parent / "outputs" / "validation" / "october_specific_comparison.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Visualization saved to {output_path}")
    
    # Save comparison table
    csv_path = SCRIPT_DIR.parent / "outputs" / "validation" / "october_specific_comparison.csv"
    comparison_df.to_csv(csv_path, index=False)
    print(f"✓ Comparison table saved to {csv_path}")
    
    # =========================================================================
    # MULTI-YEAR VALIDATION (Bonus)
    # =========================================================================
    print("\n" + "=" * 80)
    print("MULTI-YEAR VALIDATION (Testing Stability)")
    print("=" * 80)
    
    test_years = [2021, 2022, 2023, 2024]
    multi_year_results = []
    
    for test_year in test_years:
        print(f"\n🔄 Testing on October {test_year}...")
        
        test_start_year = pd.Timestamp(f"{test_year}-10-01")
        test_end_year = pd.Timestamp(f"{test_year}-10-31")
        
        # All-months approach
        all_train_year = df[df['date'] < test_start_year].copy()
        all_test_year = df[(df['date'] >= test_start_year) & (df['date'] <= test_end_year)].copy()
        
        # October-only approach
        oct_train_year = october_data[october_data['date'] < test_start_year].copy()
        oct_test_year = october_data[(october_data['date'] >= test_start_year) & (october_data['date'] <= test_end_year)].copy()
        
        if len(all_test_year) == 0 or len(oct_test_year) == 0:
            print(f"   ⚠️  No test data for {test_year}, skipping...")
            continue
        
        # Train both approaches
        try:
            # Combine train+test for train_all_models API
            all_combined_year = pd.concat([all_train_year, all_test_year], ignore_index=True)
            oct_combined_year = pd.concat([oct_train_year, oct_test_year], ignore_index=True)
            
            results_all_year = train_all_models(all_combined_year, test_start=test_start_year, features=COMMON_FEATURES)
            results_oct_year = train_all_models(oct_combined_year, test_start=test_start_year, features=COMMON_FEATURES)
            
            # Extract ensemble metrics
            if 'Ensemble' in results_all_year and 'Ensemble' in results_oct_year:
                all_r2 = results_all_year['Ensemble'].metrics['test']['r2']
                oct_r2 = results_oct_year['Ensemble'].metrics['test']['r2']
                
                multi_year_results.append({
                    'Year': test_year,
                    'All-Months R²': all_r2,
                    'October-Only R²': oct_r2,
                    'Difference': oct_r2 - all_r2,
                    'Train Size (All)': len(all_train_year),
                    'Train Size (Oct)': len(oct_train_year),
                })
                
                print(f"   All-Months R²: {all_r2:.3f}, October-Only R²: {oct_r2:.3f}, Diff: {oct_r2-all_r2:+.3f}")
        except Exception as e:
            print(f"   ⚠️  Error training on {test_year}: {e}")
    
    if multi_year_results:
        multi_year_df = pd.DataFrame(multi_year_results)
        
        print(f"\n📊 MULTI-YEAR SUMMARY:")
        print(multi_year_df.to_string(index=False))
        
        avg_diff = multi_year_df['Difference'].mean()
        std_diff = multi_year_df['Difference'].std()
        
        print(f"\n📊 AGGREGATE STATISTICS:")
        print(f"   Mean R² difference: {avg_diff:+.3f} ± {std_diff:.3f}")
        print(f"   Years where October-Only wins: {(multi_year_df['Difference'] > 0).sum()}/{len(multi_year_df)}")
        
        # Save multi-year results
        multi_csv_path = SCRIPT_DIR.parent / "outputs" / "validation" / "october_specific_multiyear.csv"
        multi_year_df.to_csv(multi_csv_path, index=False)
        print(f"\n✓ Multi-year results saved to {multi_csv_path}")
    
    # =========================================================================
    # FINAL RECOMMENDATION
    # =========================================================================
    print("\n" + "=" * 80)
    print("FINAL RECOMMENDATION")
    print("=" * 80)
    
    if multi_year_results:
        avg_diff = multi_year_df['Difference'].mean()
        
        if avg_diff > 0.05:
            print(f"\n✅ RECOMMENDATION: Switch to October-Only Training")
            print(f"   Reason: Consistent R² improvement of +{avg_diff:.3f} across {len(multi_year_results)} years")
            print(f"   Action: Update train_models.py to filter for October data")
        elif avg_diff < -0.05:
            print(f"\n✅ RECOMMENDATION: Keep All-Months Training")
            print(f"   Reason: October-only performs worse by {avg_diff:.3f} across {len(multi_year_results)} years")
            print(f"   Action: No changes needed (current approach is optimal)")
        else:
            print(f"\n🟡 RECOMMENDATION: Keep All-Months Training (Default)")
            print(f"   Reason: Negligible difference ({avg_diff:+.3f}) - prefer more data for robustness")
            print(f"   Note: October-only has only {len(oct_train)} training rows vs {len(all_train)} all-months")
    else:
        print(f"\n⚠️  Insufficient multi-year data for conclusive recommendation")
        print(f"   Default: Keep all-months training (more robust with {len(all_train)} rows)")


if __name__ == "__main__":
    october_specific_comparison()
