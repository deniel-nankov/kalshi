"""
Multi-Period Cross-Validation for Model Robustness Assessment

Purpose:
    Test model performance across multiple historical October periods (2021-2024)
    to establish confidence intervals and assess temporal stability.

Problem Statement:
    Current baseline R²=0.595 is based on a single test period (Oct 2024-2025).
    This gives no indication of variability - the model could be consistently good
    (R²=0.60 ± 0.05) or highly unstable (R²=0.60 ± 0.40).

Solution:
    Walk-forward validation across 4 historical Octobers:
    - October 2021: Train on 2020-10-19 → 2021-09-30, Test on Oct 2021
    - October 2022: Train on 2020-10-19 → 2022-09-30, Test on Oct 2022
    - October 2023: Train on 2020-10-19 → 2023-09-30, Test on Oct 2023
    - October 2024: Train on 2020-10-19 → 2024-09-30, Test on Oct 2024

Outputs:
    - Multi-period R², RMSE, MAPE for each model (Ridge, Inventory, Futures, Ensemble)
    - Mean ± std deviation across periods
    - Coefficient of variation (stability metric)
    - Visualization: Bar chart with error bars
    - CSV: Detailed results by period

Expected Outcome:
    Ensemble R² = 0.55 ± 0.30 (example - actual values will vary)
    → Provides realistic expectations for production deployment

Usage:
    python multi_period_validation.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Add src to path
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.baseline_models import train_all_models, COMMON_FEATURES

# Paths
DATA_PATH = REPO_ROOT / "data" / "gold" / "master_model_ready.parquet"
OUTPUT_DIR = REPO_ROOT / "outputs" / "validation"

# Validation periods (October of each year)
TEST_PERIODS = [
    {"year": 2021, "train_start": "2020-10-19", "train_end": "2021-09-30", 
     "test_start": "2021-10-01", "test_end": "2021-10-31"},
    {"year": 2022, "train_start": "2020-10-19", "train_end": "2022-09-30",
     "test_start": "2022-10-01", "test_end": "2022-10-31"},
    {"year": 2023, "train_start": "2020-10-19", "train_end": "2023-09-30",
     "test_start": "2023-10-01", "test_end": "2023-10-31"},
    {"year": 2024, "train_start": "2020-10-19", "train_end": "2024-09-30",
     "test_start": "2024-10-01", "test_end": "2024-10-31"},
]


def load_data() -> pd.DataFrame:
    """Load model-ready dataset."""
    print("📂 Loading data...")
    df = pd.read_parquet(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])
    print(f"   ✓ Loaded {len(df):,} rows from {df['date'].min():%Y-%m-%d} → {df['date'].max():%Y-%m-%d}")
    return df


def validate_period(df: pd.DataFrame, period: Dict[str, str]) -> Dict[str, Dict[str, float]]:
    """
    Validate models on a single October period.
    
    Returns:
        Dictionary of model results with R², RMSE, MAPE for each model
    """
    year = period["year"]
    test_start = pd.Timestamp(period["test_start"])
    test_end = pd.Timestamp(period["test_end"])
    
    print(f"\n{'='*80}")
    print(f"VALIDATING OCTOBER {year}")
    print(f"{'='*80}")
    
    # Filter data
    train_data = df[df["date"] < test_start].copy()
    test_data = df[(df["date"] >= test_start) & (df["date"] <= test_end)].copy()
    
    print(f"Train: {len(train_data):,} rows ({train_data['date'].min():%Y-%m-%d} → {train_data['date'].max():%Y-%m-%d})")
    print(f"Test:  {len(test_data):,} rows ({test_data['date'].min():%Y-%m-%d} → {test_data['date'].max():%Y-%m-%d})")
    
    # Combine for train_all_models API
    combined = pd.concat([train_data, test_data], ignore_index=True)
    
    # Train models
    print(f"\n🔄 Training models...")
    results = train_all_models(combined, test_start=test_start, features=COMMON_FEATURES)
    
    # Extract metrics from ModelOutput objects
    metrics = {}
    for model_name in ["Ridge", "Inventory", "Futures", "Ensemble"]:
        if model_name in results:
            model_output = results[model_name]
            test_metrics = model_output.metrics.get("test", model_output.metrics)
            metrics[model_name] = {
                "r2": test_metrics["r2"],
                "rmse": test_metrics["rmse"],
                "mape": test_metrics.get("mape_pct", test_metrics.get("mape", 0)) / 100,  # Convert percentage to decimal
            }
    
    print(f"\n📊 RESULTS FOR OCTOBER {year}:")
    for model_name, model_metrics in metrics.items():
        print(f"   {model_name:12s}: R²={model_metrics['r2']:7.3f}, "
              f"RMSE=${model_metrics['rmse']:.4f}, MAPE={model_metrics['mape']:.2%}")
    
    return metrics


def aggregate_results(all_results: List[Dict[str, Dict[str, float]]]) -> pd.DataFrame:
    """
    Aggregate multi-period results into summary statistics.
    
    Returns:
        DataFrame with mean, std, min, max, CV for each model and metric
    """
    # Restructure into long format for easier analysis
    records = []
    for i, period_results in enumerate(all_results):
        year = TEST_PERIODS[i]["year"]
        for model_name, metrics in period_results.items():
            for metric_name, value in metrics.items():
                records.append({
                    "year": year,
                    "model": model_name,
                    "metric": metric_name,
                    "value": value
                })
    
    df = pd.DataFrame(records)
    
    # Calculate summary statistics
    summary = df.groupby(["model", "metric"])["value"].agg([
        ("mean", "mean"),
        ("std", "std"),
        ("min", "min"),
        ("max", "max"),
        ("count", "count")
    ]).reset_index()
    
    # Coefficient of variation (std / |mean|) - stability metric
    # Lower CV = more stable performance
    summary["cv"] = np.abs(summary["std"] / summary["mean"])
    
    return df, summary


def visualize_results(df: pd.DataFrame, summary: pd.DataFrame) -> None:
    """
    Create visualization of multi-period validation results.
    
    Generates:
        1. Bar chart with error bars (mean ± std for each model)
        2. Separate subplots for R², RMSE, MAPE
    """
    print(f"\n{'='*80}")
    print("CREATING VISUALIZATION")
    print(f"{'='*80}")
    
    # Filter to R² and RMSE (most important metrics)
    viz_metrics = ["r2", "rmse"]
    viz_summary = summary[summary["metric"].isin(viz_metrics)].copy()
    
    # Create figure with subplots
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Multi-Period Model Validation (October 2021-2024)", 
                 fontsize=14, fontweight="bold", y=1.02)
    
    models = ["Ridge", "Inventory", "Futures", "Ensemble"]
    colors = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12"]
    
    for idx, metric in enumerate(viz_metrics):
        ax = axes[idx]
        metric_data = viz_summary[viz_summary["metric"] == metric]
        
        # Reorder by model list
        metric_data = metric_data.set_index("model").reindex(models).reset_index()
        
        # Bar chart with error bars
        x = np.arange(len(models))
        bars = ax.bar(x, metric_data["mean"], yerr=metric_data["std"], 
                      capsize=5, alpha=0.8, color=colors, edgecolor="black", linewidth=1.5)
        
        # Formatting
        ax.set_xticks(x)
        ax.set_xticklabels(models, fontsize=11, fontweight="bold")
        ax.set_ylabel(f"{'R²' if metric == 'r2' else 'RMSE ($)'}", 
                      fontsize=11, fontweight="bold")
        ax.set_title(f"{'R² Score' if metric == 'r2' else 'Root Mean Squared Error'}", 
                     fontsize=12, fontweight="bold")
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        ax.axhline(y=0, color="black", linewidth=0.8)
        
        # Add value labels on bars
        for i, bar in enumerate(bars):
            height = bar.get_height()
            std = metric_data.iloc[i]["std"]
            label = f"{height:.3f}\n±{std:.3f}" if metric == "r2" else f"${height:.4f}\n±${std:.4f}"
            ax.text(bar.get_x() + bar.get_width() / 2, height + std + 0.01,
                   label, ha="center", va="bottom", fontsize=9, fontweight="bold")
    
    plt.tight_layout()
    
    output_path = OUTPUT_DIR / "multi_period_validation.png"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✓ Visualization saved to {output_path}")
    plt.close()


def print_summary_report(summary: pd.DataFrame) -> None:
    """Print formatted summary statistics."""
    print(f"\n{'='*80}")
    print("AGGREGATE STATISTICS (4 October Periods: 2021-2024)")
    print(f"{'='*80}")
    
    models = ["Ridge", "Inventory", "Futures", "Ensemble"]
    metrics_display = {"r2": "R²", "rmse": "RMSE", "mape": "MAPE"}
    
    for model in models:
        print(f"\n📊 {model.upper()}")
        model_summary = summary[summary["model"] == model]
        
        for metric, display_name in metrics_display.items():
            metric_row = model_summary[model_summary["metric"] == metric]
            if len(metric_row) == 0:
                continue
            
            mean = metric_row["mean"].iloc[0]
            std = metric_row["std"].iloc[0]
            min_val = metric_row["min"].iloc[0]
            max_val = metric_row["max"].iloc[0]
            cv = metric_row["cv"].iloc[0]
            
            if metric == "mape":
                print(f"   {display_name:6s}: {mean:.2%} ± {std:.2%}  "
                      f"[Range: {min_val:.2%} → {max_val:.2%}]  CV={cv:.2f}")
            elif metric == "rmse":
                print(f"   {display_name:6s}: ${mean:.4f} ± ${std:.4f}  "
                      f"[Range: ${min_val:.4f} → ${max_val:.4f}]  CV={cv:.2f}")
            else:
                print(f"   {display_name:6s}: {mean:.3f} ± {std:.3f}  "
                      f"[Range: {min_val:.3f} → {max_val:.3f}]  CV={cv:.2f}")


def interpret_results(summary: pd.DataFrame) -> None:
    """Provide interpretation and recommendations based on results."""
    print(f"\n{'='*80}")
    print("INTERPRETATION & RECOMMENDATIONS")
    print(f"{'='*80}")
    
    # Get Ensemble R² statistics
    ensemble_r2 = summary[(summary["model"] == "Ensemble") & (summary["metric"] == "r2")]
    mean_r2 = ensemble_r2["mean"].iloc[0]
    std_r2 = ensemble_r2["std"].iloc[0]
    cv_r2 = ensemble_r2["cv"].iloc[0]
    
    print(f"\n📈 ENSEMBLE PERFORMANCE:")
    print(f"   Mean R²: {mean_r2:.3f} ± {std_r2:.3f}")
    print(f"   95% Confidence Interval: [{mean_r2 - 1.96*std_r2:.3f}, {mean_r2 + 1.96*std_r2:.3f}]")
    print(f"   Coefficient of Variation: {cv_r2:.2f}")
    
    # Stability assessment
    print(f"\n🎯 STABILITY ASSESSMENT:")
    if cv_r2 < 0.5:
        stability = "HIGH STABILITY"
        emoji = "✅"
        recommendation = "Model performance is consistent across years."
    elif cv_r2 < 1.0:
        stability = "MODERATE STABILITY"
        emoji = "⚠️"
        recommendation = "Some year-to-year variation present. Consider regime modeling."
    else:
        stability = "LOW STABILITY"
        emoji = "❌"
        recommendation = "High variance across years. Investigate period-specific factors."
    
    print(f"   {emoji} {stability} (CV={cv_r2:.2f})")
    print(f"   {recommendation}")
    
    # Production expectations
    print(f"\n🚀 PRODUCTION EXPECTATIONS:")
    lower_bound = mean_r2 - std_r2
    upper_bound = mean_r2 + std_r2
    
    if mean_r2 > 0.5:
        print(f"   ✓ Strong predictive power (R² > 0.5)")
    elif mean_r2 > 0.3:
        print(f"   ⚠️  Moderate predictive power (0.3 < R² < 0.5)")
    else:
        print(f"   ❌ Weak predictive power (R² < 0.3)")
    
    print(f"   Expected range: R² ∈ [{lower_bound:.3f}, {upper_bound:.3f}]")
    print(f"   → In 68% of future Octobers, expect performance in this range")


def save_results(df: pd.DataFrame, summary: pd.DataFrame) -> None:
    """Save detailed and summary results to CSV."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Detailed results (by period)
    detail_path = OUTPUT_DIR / "multi_period_validation_detailed.csv"
    df.to_csv(detail_path, index=False)
    print(f"✓ Detailed results saved to {detail_path}")
    
    # Summary statistics
    summary_path = OUTPUT_DIR / "multi_period_validation_summary.csv"
    summary.to_csv(summary_path, index=False)
    print(f"✓ Summary statistics saved to {summary_path}")


def main():
    """Execute multi-period validation pipeline."""
    print("=" * 80)
    print("MULTI-PERIOD CROSS-VALIDATION")
    print("=" * 80)
    print(f"Testing on {len(TEST_PERIODS)} historical October periods: 2021-2024")
    print("=" * 80)
    
    # Load data
    df = load_data()
    
    # Validate each period
    all_results = []
    for period in TEST_PERIODS:
        period_results = validate_period(df, period)
        all_results.append(period_results)
    
    # Aggregate results
    print(f"\n{'='*80}")
    print("AGGREGATING RESULTS")
    print(f"{'='*80}")
    df_results, summary = aggregate_results(all_results)
    
    # Display summary
    print_summary_report(summary)
    
    # Interpret results
    interpret_results(summary)
    
    # Visualize
    visualize_results(df_results, summary)
    
    # Save
    print(f"\n{'='*80}")
    print("SAVING RESULTS")
    print(f"{'='*80}")
    save_results(df_results, summary)
    
    print(f"\n{'='*80}")
    print("MULTI-PERIOD VALIDATION COMPLETE ✅")
    print(f"{'='*80}")
    print("\n📊 Key Takeaway:")
    ensemble_r2 = summary[(summary["model"] == "Ensemble") & (summary["metric"] == "r2")]
    mean_r2 = ensemble_r2["mean"].iloc[0]
    std_r2 = ensemble_r2["std"].iloc[0]
    print(f"   Ensemble R² = {mean_r2:.3f} ± {std_r2:.3f} across 4 historical Octobers")
    print(f"   → This provides realistic expectations for production deployment\n")


if __name__ == "__main__":
    main()
