"""
Comprehensive analysis of enhanced hurricane features with geographic and refinery-specific modeling.

This script analyzes the importance and impact of all hurricane-related features including:
- Basic risk indicators
- Geographic proximity features
- Refinery exposure metrics
- Lagged and rolling features
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


def analyze_enhanced_hurricane_features():
    """Comprehensive analysis of all hurricane features."""
    
    print("=" * 80)
    print("ENHANCED HURRICANE FEATURE ANALYSIS")
    print("=" * 80)
    print("\n🌀 Analyzing geographic and refinery-specific hurricane modeling")
    
    # Load model
    print(f"\nLoading model from: {MODEL_PATH}")
    model_pipeline = joblib.load(MODEL_PATH)
    ridge_model = model_pipeline.named_steps['model']
    coefficients = ridge_model.coef_
    
    # Create feature importance dataframe
    feature_importance = pd.DataFrame({
        'feature': COMMON_FEATURES,
        'coefficient': coefficients,
        'abs_coefficient': np.abs(coefficients)
    }).sort_values('abs_coefficient', ascending=False)
    
    # Identify ALL hurricane-related features
    hurricane_features = [
        f for f in COMMON_FEATURES 
        if any(keyword in f.lower() for keyword in [
            'hurricane', 'padd3_threat', 'refiner', 'landfall', 'gulf_coast'
        ])
    ]
    
    # Exclude padd3_share (that's a general market feature, not hurricane-specific)
    hurricane_features = [f for f in hurricane_features if f != 'padd3_share']
    
    print(f"\n📊 Hurricane Features in Model: {len(hurricane_features)}")
    print("=" * 80)
    
    hurricane_importance = feature_importance[feature_importance['feature'].isin(hurricane_features)]
    
    # Categorize features
    basic_features = [f for f in hurricane_features if f in [
        'hurricane_risk_score', 'hurricane_probability', 'hurricane_intensity',
        'is_hurricane_event', 'hurricane_category'
    ]]
    
    geographic_features = [f for f in hurricane_features if any(x in f for x in [
        'distance', 'landfall', 'gulf_coast', 'padd3_threat', 'refiner'
    ])]
    
    lagged_features = [f for f in hurricane_features if any(x in f for x in [
        'days_since', 'days_until', '_7d_', '_14d_', '_30d_'
    ])]
    
    print("\n🔹 BASIC RISK FEATURES:")
    print("-" * 80)
    for _, row in hurricane_importance[hurricane_importance['feature'].isin(basic_features)].iterrows():
        rank = feature_importance[feature_importance['feature'] == row['feature']].index[0] + 1
        impact = "positive" if row['coefficient'] > 0 else "negative"
        print(f"  {row['feature']:35s}: {row['coefficient']:+.6f}  (Rank {rank:2d}/50, {impact})")
    
    print("\n🌍 GEOGRAPHIC & REFINERY-SPECIFIC FEATURES:")
    print("-" * 80)
    geo_importance = hurricane_importance[hurricane_importance['feature'].isin(geographic_features)]
    if len(geo_importance) > 0:
        for _, row in geo_importance.iterrows():
            rank = feature_importance[feature_importance['feature'] == row['feature']].index[0] + 1
            impact = "positive" if row['coefficient'] > 0 else "negative"
            print(f"  {row['feature']:35s}: {row['coefficient']:+.6f}  (Rank {rank:2d}/50, {impact})")
    else:
        print("  ⚠️  No geographic features found in top importance")
    
    print("\n⏱️  LAGGED & ROLLING FEATURES:")
    print("-" * 80)
    for _, row in hurricane_importance[hurricane_importance['feature'].isin(lagged_features)].iterrows():
        rank = feature_importance[feature_importance['feature'] == row['feature']].index[0] + 1
        impact = "positive" if row['coefficient'] > 0 else "negative"
        print(f"  {row['feature']:35s}: {row['coefficient']:+.6f}  (Rank {rank:2d}/50, {impact})")
    
    # Overall ranking statistics
    print(f"\n📈 Hurricane Feature Ranking Statistics:")
    print("=" * 80)
    ranks = []
    for feat in hurricane_features:
        rank = feature_importance[feature_importance['feature'] == feat].index[0] + 1
        ranks.append(rank)
    
    print(f"  Best rank:    {min(ranks)}/50 (top {min(ranks)/50*100:.1f}%)")
    print(f"  Worst rank:   {max(ranks)}/50 (top {max(ranks)/50*100:.1f}%)")
    print(f"  Mean rank:    {np.mean(ranks):.1f}/50 (top {np.mean(ranks)/50*100:.1f}%)")
    print(f"  Median rank:  {np.median(ranks):.1f}/50 (top {np.median(ranks)/50*100:.1f}%)")
    
    # Load data for correlation analysis
    print(f"\n📊 Loading data from: {DATA_PATH}")
    df = load_model_ready_dataset(DATA_PATH)
    
    # Analyze correlations with gas prices
    print(f"\n📊 Hurricane Feature - Gas Price Correlations:")
    print("=" * 80)
    correlations = []
    for feature in hurricane_features:
        if feature in df.columns:
            corr = df[[feature, 'retail_price']].corr().iloc[0, 1]
            correlations.append((feature, corr))
    
    correlations.sort(key=lambda x: abs(x[1]), reverse=True)
    
    for feat, corr in correlations:
        emoji = "📈" if corr > 0 else "📉"
        print(f"  {emoji} {feat:35s} ↔ retail_price: {corr:+.4f}")
    
    # Analyze hurricane event days
    analyze_geographic_specificity(df, hurricane_features)
    
    # Create comprehensive visualization
    create_enhanced_hurricane_plot(hurricane_importance, feature_importance)
    
    print(f"\n✓ Enhanced hurricane analysis complete")
    print(f"  Outputs saved to: {OUTPUT_DIR}")


def analyze_geographic_specificity(df, hurricane_features):
    """Analyze the impact of geographic specificity on predictions."""
    
    print(f"\n🌍 GEOGRAPHIC SPECIFICITY ANALYSIS:")
    print("=" * 80)
    
    # Check if we have the enhanced features
    if 'padd3_threat_level' in df.columns:
        # Categorize hurricanes by threat level
        high_threat = df[df['padd3_threat_level'] >= 7]  # Direct refinery threat
        medium_threat = df[(df['padd3_threat_level'] >= 4) & (df['padd3_threat_level'] < 7)]
        low_threat = df[(df['padd3_threat_level'] > 0) & (df['padd3_threat_level'] < 4)]
        no_threat = df[df['padd3_threat_level'] == 0]
        
        print(f"\n  Days by PADD 3 Threat Level:")
        print(f"    🔴 High Threat (≥7):     {len(high_threat):4d} days  (Avg price: ${high_threat['retail_price'].mean():.3f})")
        print(f"    🟡 Medium Threat (4-7):  {len(medium_threat):4d} days  (Avg price: ${medium_threat['retail_price'].mean():.3f})")
        print(f"    🟢 Low Threat (1-4):     {len(low_threat):4d} days  (Avg price: ${low_threat['retail_price'].mean():.3f})")
        print(f"    ⚪ No Threat (0):        {len(no_threat):4d} days  (Avg price: ${no_threat['retail_price'].mean():.3f})")
        
        if len(high_threat) > 0 and len(no_threat) > 0:
            price_diff = high_threat['retail_price'].mean() - no_threat['retail_price'].mean()
            pct_diff = (price_diff / no_threat['retail_price'].mean()) * 100
            print(f"\n  💥 High Threat vs No Threat Impact: ${price_diff:+.3f} ({pct_diff:+.1f}%)")
    
    if 'is_gulf_coast_landfall' in df.columns:
        gulf_landfalls = df[df['is_gulf_coast_landfall'] == 1]
        non_gulf = df[df['is_hurricane_event'] == 1][df['is_gulf_coast_landfall'] == 0]
        
        print(f"\n  Gulf Coast vs Non-Gulf Hurricanes:")
        if len(gulf_landfalls) > 0:
            print(f"    🌊 Gulf Coast (TX/LA) landfalls: {len(gulf_landfalls):3d} days  (Avg price: ${gulf_landfalls['retail_price'].mean():.3f})")
        if len(non_gulf) > 0:
            print(f"    🌴 Non-Gulf hurricanes:          {len(non_gulf):3d} days  (Avg price: ${non_gulf['retail_price'].mean():.3f})")
    
    if 'refineries_at_risk_count' in df.columns:
        refinery_risk = df[df['refineries_at_risk_count'] > 0]
        hurricane_no_refinery = df[(df['is_hurricane_event'] == 1) & (df['refineries_at_risk_count'] == 0)]
        
        print(f"\n  Refinery Exposure Analysis:")
        if len(refinery_risk) > 0:
            print(f"    ⚠️  Days with refineries at risk:  {len(refinery_risk):3d} days  (Avg price: ${refinery_risk['retail_price'].mean():.3f})")
            print(f"        Avg refineries threatened: {refinery_risk['refineries_at_risk_count'].mean():.1f}")
        if len(hurricane_no_refinery) > 0:
            print(f"    ✅ Hurricane but no refinery risk: {len(hurricane_no_refinery):3d} days  (Avg price: ${hurricane_no_refinery['retail_price'].mean():.3f})")


def create_enhanced_hurricane_plot(hurricane_importance, feature_importance):
    """Create comprehensive visualization of hurricane feature importance."""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Left plot: Hurricane feature coefficients
    colors = ['#E74C3C' if c > 0 else '#3498DB' for c in hurricane_importance['coefficient']]
    
    ax1.barh(hurricane_importance['feature'], hurricane_importance['coefficient'], color=colors)
    ax1.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
    ax1.set_xlabel('Ridge Coefficient', fontsize=12)
    ax1.set_title('Enhanced Hurricane Feature Importance\n(Geographic + Refinery-Specific)', 
                  fontsize=14, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)
    
    # Right plot: Overall feature importance ranking
    top_30 = feature_importance.head(30)
    hurricane_mask = top_30['feature'].isin(hurricane_importance['feature'])
    colors_rank = ['#E67E22' if h else '#95A5A6' for h in hurricane_mask]
    
    ax2.barh(range(len(top_30)), top_30['abs_coefficient'], color=colors_rank)
    ax2.set_yticks(range(len(top_30)))
    ax2.set_yticklabels(top_30['feature'], fontsize=9)
    ax2.set_xlabel('Absolute Coefficient', fontsize=12)
    ax2.set_title('Top 30 Features Overall\n(🟧 = Hurricane Features)', 
                  fontsize=14, fontweight='bold')
    ax2.grid(axis='x', alpha=0.3)
    ax2.invert_yaxis()
    
    plt.tight_layout()
    output_path = OUTPUT_DIR / 'enhanced_hurricane_feature_analysis.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\n✓ Saved enhanced visualization: {output_path}")


def main():
    analyze_enhanced_hurricane_features()


if __name__ == "__main__":
    main()
