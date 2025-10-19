"""
Analyze hurricane feature importance using trained Ridge model.

This script loads the trained Ridge baseline model and analyzes the 
importance of hurricane features in predicting October gas prices.
"""

from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Add src to path
SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from models.baseline_models import COMMON_FEATURES, load_model_ready_dataset

# Paths
MODEL_PATH = SCRIPT_DIR.parent / "outputs" / "models" / "ridge_baseline_model.joblib"
OUTPUT_DIR = SCRIPT_DIR.parent / "outputs" / "interpretability"
DATA_PATH = SCRIPT_DIR.parent / "data" / "gold" / "master_model_ready.parquet"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def analyze_hurricane_features():
    """Analyze hurricane feature coefficients and impact."""
    
    print("=" * 80)
    print("HURRICANE FEATURE IMPORTANCE ANALYSIS")
    print("=" * 80)
    
    # Load model
    print(f"\nLoading model from: {MODEL_PATH}")
    model_pipeline = joblib.load(MODEL_PATH)
    
    # Get the Ridge model from pipeline
    ridge_model = model_pipeline.named_steps['model']
    scaler = model_pipeline.named_steps['scaler']
    
    # Get coefficients
    coefficients = ridge_model.coef_
    
    # Create feature importance dataframe
    feature_importance = pd.DataFrame({
        'feature': COMMON_FEATURES,
        'coefficient': coefficients,
        'abs_coefficient': np.abs(coefficients)
    }).sort_values('abs_coefficient', ascending=False)
    
    # Identify hurricane features
    hurricane_features = [f for f in COMMON_FEATURES if 'hurricane' in f.lower()]
    
    print(f"\n📊 Hurricane Features in Model: {len(hurricane_features)}")
    print("=" * 80)
    
    hurricane_importance = feature_importance[feature_importance['feature'].isin(hurricane_features)]
    
    if len(hurricane_importance) > 0:
        print("\nHurricane Feature Coefficients:")
        print("-" * 80)
        for _, row in hurricane_importance.iterrows():
            impact = "positive" if row['coefficient'] > 0 else "negative"
            print(f"  {row['feature']:30s}: {row['coefficient']:+.6f}  ({impact} price impact)")
        
        # Rank among all features
        print(f"\n📈 Hurricane Feature Rankings (out of {len(COMMON_FEATURES)} total features):")
        print("-" * 80)
        for _, row in hurricane_importance.iterrows():
            rank = feature_importance[feature_importance['feature'] == row['feature']].index[0] + 1
            percentile = (rank / len(COMMON_FEATURES)) * 100
            print(f"  {row['feature']:30s}: Rank {rank:2d} / {len(COMMON_FEATURES)} (top {percentile:.1f}%)")
    
    else:
        print("⚠️  No hurricane features found in the model!")
        return
    
    # Load data to analyze actual impact
    print(f"\n📊 Loading data from: {DATA_PATH}")
    df = load_model_ready_dataset(DATA_PATH)
    
    # Filter to October data
    october_df = df[df['date'].dt.month == 10].copy()
    
    print(f"\nOctober data statistics:")
    print(f"  Total October observations: {len(october_df)}")
    
    for feature in hurricane_features:
        if feature in october_df.columns:
            values = october_df[feature]
            print(f"\n  {feature}:")
            print(f"    Mean: {values.mean():.4f}")
            print(f"    Std:  {values.std():.4f}")
            print(f"    Min:  {values.min():.4f}")
            print(f"    Max:  {values.max():.4f}")
            
            # Days with elevated risk
            if 'risk' in feature.lower() or 'probability' in feature.lower():
                elevated = (values > values.quantile(0.75)).sum()
                print(f"    Days with elevated {feature}: {elevated} ({elevated/len(values)*100:.1f}%)")
    
    # Create visualization
    create_hurricane_importance_plot(hurricane_importance)
    
    # Analyze October gas price impact
    analyze_hurricane_price_impact(october_df, hurricane_features, model_pipeline)
    
    print(f"\n✓ Hurricane analysis complete")
    print(f"  Outputs saved to: {OUTPUT_DIR}")


def create_hurricane_importance_plot(hurricane_importance):
    """Create bar plot of hurricane feature importance."""
    
    if len(hurricane_importance) == 0:
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors = ['#E74C3C' if c > 0 else '#3498DB' for c in hurricane_importance['coefficient']]
    
    ax.barh(hurricane_importance['feature'], hurricane_importance['coefficient'], color=colors)
    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
    ax.set_xlabel('Ridge Coefficient', fontsize=12)
    ax.set_title('Hurricane Feature Importance in Gas Price Model', fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    output_path = OUTPUT_DIR / 'hurricane_feature_importance.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\n✓ Saved feature importance plot: {output_path}")


def analyze_hurricane_price_impact(october_df, hurricane_features, model_pipeline):
    """Analyze how hurricane features correlate with gas prices."""
    
    if 'retail_price' not in october_df.columns:
        return
    
    print(f"\n📊 Hurricane-Price Correlation Analysis:")
    print("-" * 80)
    
    for feature in hurricane_features:
        if feature in october_df.columns:
            corr = october_df[[feature, 'retail_price']].corr().iloc[0, 1]
            print(f"  {feature:30s} ↔ retail_price: {corr:+.4f}")
    
    # Find days with actual hurricane events
    if 'is_hurricane_event' in october_df.columns:
        hurricane_days = october_df[october_df['is_hurricane_event'] == 1]
        normal_days = october_df[october_df['is_hurricane_event'] == 0]
        
        if len(hurricane_days) > 0:
            print(f"\n⚠️  Hurricane Event Days vs Normal Days:")
            print("-" * 80)
            print(f"  Hurricane days: {len(hurricane_days)}")
            print(f"  Normal days: {len(normal_days)}")
            print(f"\n  Average retail price:")
            print(f"    During hurricanes: ${hurricane_days['retail_price'].mean():.3f}")
            print(f"    Normal days:       ${normal_days['retail_price'].mean():.3f}")
            diff = hurricane_days['retail_price'].mean() - normal_days['retail_price'].mean()
            print(f"    Difference:        ${diff:+.3f} ({diff/normal_days['retail_price'].mean()*100:+.2f}%)")


def main():
    analyze_hurricane_features()


if __name__ == "__main__":
    main()
