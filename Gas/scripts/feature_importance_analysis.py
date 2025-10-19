"""
Comprehensive feature importance analysis for Gradient Boosting model.

This script computes:
1. Built-in feature importance (Gini/impurity-based)
2. SHAP values for feature importance
3. Permutation importance
4. Recommendations for feature selection

Outputs:
- Feature importance plots
- Feature ranking tables
- Recommendations for compact feature set
"""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance

try:
    import shap
except ImportError:
    shap = None
    print("⚠️ Warning: shap not installed. Install with: pip install shap")

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.baseline_models import COMMON_FEATURES, load_model_ready_dataset


def load_data_and_model():
    """Load dataset and trained Gradient Boosting model."""
    data_path = Path(__file__).resolve().parents[1] / "data" / "gold" / "master_model_ready.parquet"
    model_path = Path(__file__).resolve().parents[1] / "outputs" / "models" / "gradient_boosting_model.joblib"
    
    print(f"Loading data from: {data_path}")
    df = load_model_ready_dataset(data_path)
    
    # Ensure index is datetime
    if 'date' in df.columns:
        df = df.set_index('date')
    df.index = pd.to_datetime(df.index)
    
    print(f"Loading model from: {model_path}")
    model = joblib.load(model_path)
    
    # Split into train/test (same split as training)
    split_date = pd.Timestamp("2024-10-01")
    train = df[df.index < split_date].copy()
    test = df[df.index >= split_date].copy()
    
    X_train = train[COMMON_FEATURES]
    y_train = train["target"]
    X_test = test[COMMON_FEATURES]
    y_test = test["target"]
    
    print(f"Train samples: {len(X_train):,}")
    print(f"Test samples: {len(X_test):,}")
    print(f"Features: {len(COMMON_FEATURES)}")
    
    return model, X_train, y_train, X_test, y_test


def compute_builtin_importance(model, feature_names):
    """Compute built-in Gradient Boosting feature importance."""
    print("\n=== Built-in Feature Importance ===")
    
    # HistGradientBoostingRegressor doesn't have feature_importances_
    # Skip this method for Hist GB models
    if not hasattr(model, 'feature_importances_'):
        print("⚠️ Model doesn't support built-in feature importance")
        print("   (HistGradientBoostingRegressor doesn't expose feature_importances_)")
        print("   Skipping this method - will use permutation + SHAP instead")
        return None
    
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    importance_df = pd.DataFrame({
        'feature': [feature_names[i] for i in indices],
        'importance': importances[indices],
        'rank': range(1, len(feature_names) + 1)
    })
    
    print("\nTop 20 Features:")
    print(importance_df.head(20).to_string(index=False))
    
    return importance_df


def compute_permutation_importance(model, X_test, y_test, feature_names, n_repeats=10):
    """Compute permutation importance on test set."""
    print(f"\n=== Permutation Importance (test set, {n_repeats} repeats) ===")
    
    perm_importance = permutation_importance(
        model, X_test, y_test, 
        n_repeats=n_repeats, 
        random_state=42,
        scoring='r2'
    )
    
    indices = np.argsort(perm_importance.importances_mean)[::-1]
    
    perm_df = pd.DataFrame({
        'feature': [feature_names[i] for i in indices],
        'importance_mean': perm_importance.importances_mean[indices],
        'importance_std': perm_importance.importances_std[indices],
        'rank': range(1, len(feature_names) + 1)
    })
    
    print("\nTop 20 Features:")
    print(perm_df.head(20).to_string(index=False))
    
    return perm_df


def compute_shap_importance(model, X_sample, feature_names, max_samples=500):
    """Compute SHAP values for feature importance."""
    if shap is None:
        print("\n⚠️ Skipping SHAP analysis (package not installed)")
        return None
    
    print(f"\n=== SHAP Feature Importance (TreeExplainer, {max_samples} samples) ===")
    
    # Sample data for computational efficiency
    X_shap = X_sample.sample(n=min(max_samples, len(X_sample)), random_state=42)
    
    # Use TreeExplainer for gradient boosting (much faster than KernelExplainer)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_shap)
    
    # Compute mean absolute SHAP value for each feature
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    indices = np.argsort(mean_abs_shap)[::-1]
    
    shap_df = pd.DataFrame({
        'feature': [feature_names[i] for i in indices],
        'mean_abs_shap': mean_abs_shap[indices],
        'rank': range(1, len(feature_names) + 1)
    })
    
    print("\nTop 20 Features:")
    print(shap_df.head(20).to_string(index=False))
    
    # Save SHAP plots
    output_dir = Path(__file__).resolve().parents[1] / "outputs" / "interpretability"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Summary plot (top 20 features)
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_shap, max_display=20, show=False)
    plt.tight_layout()
    plt.savefig(output_dir / "shap_summary_gb.png", dpi=160, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved SHAP summary plot: {output_dir / 'shap_summary_gb.png'}")
    
    # Bar plot of mean absolute SHAP values
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_shap, plot_type="bar", max_display=20, show=False)
    plt.tight_layout()
    plt.savefig(output_dir / "shap_bar_gb.png", dpi=160, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved SHAP bar plot: {output_dir / 'shap_bar_gb.png'}")
    
    return shap_df


def create_consensus_ranking(builtin_df, perm_df, shap_df):
    """Create consensus ranking from all three methods."""
    print("\n=== Consensus Feature Ranking ===")
    
    # Start with permutation importance (always available)
    consensus = perm_df[['feature', 'rank']].rename(columns={'rank': 'perm_rank'})
    
    # Add built-in importance if available
    if builtin_df is not None:
        consensus = consensus.merge(
            builtin_df[['feature', 'rank']].rename(columns={'rank': 'builtin_rank'}),
            on='feature'
        )
    
    # Add SHAP if available
    if shap_df is not None:
        consensus = consensus.merge(
            shap_df[['feature', 'rank']].rename(columns={'rank': 'shap_rank'}),
            on='feature'
        )
    
    # Calculate average rank from available methods
    rank_cols = [col for col in consensus.columns if col.endswith('_rank')]
    consensus['avg_rank'] = consensus[rank_cols].mean(axis=1)
    
    consensus = consensus.sort_values('avg_rank')
    consensus['final_rank'] = range(1, len(consensus) + 1)
    
    # Add importance scores
    consensus = consensus.merge(perm_df[['feature', 'importance_mean']], on='feature')
    if builtin_df is not None:
        consensus = consensus.merge(builtin_df[['feature', 'importance']], on='feature')
    if shap_df is not None:
        consensus = consensus.merge(shap_df[['feature', 'mean_abs_shap']], on='feature')
    
    print("\nTop 30 Features (Consensus):")
    print(consensus.head(30).to_string(index=False))
    
    return consensus


def generate_recommendations(consensus_df, target_features=45):
    """Generate feature selection recommendations."""
    print(f"\n=== Feature Selection Recommendations ===")
    
    top_features = consensus_df.head(target_features)['feature'].tolist()
    
    print(f"\n✅ Recommended Compact Feature Set ({target_features} features):")
    print(f"   Use these for Ridge regression to improve performance")
    print()
    
    # Group features by category
    categories = {
        'Price & Futures': [],
        'Inventory': [],
        'Production & Utilization': [],
        'Hurricane & Weather': [],
        'Seasonality': [],
        'Market Microstructure': [],
        'Interactions': [],
        'Technical Indicators': []
    }
    
    for feat in top_features:
        if any(x in feat for x in ['rbob', 'wti', 'brent', 'crack', 'futures']):
            categories['Price & Futures'].append(feat)
        elif 'inventory' in feat or 'stock' in feat:
            categories['Inventory'].append(feat)
        elif any(x in feat for x in ['production', 'utilization', 'refinery', 'capacity']):
            categories['Production & Utilization'].append(feat)
        elif any(x in feat for x in ['hurricane', 'padd3', 'threat', 'wind']):
            categories['Hurricane & Weather'].append(feat)
        elif any(x in feat for x in ['month', 'day', 'quarter', 'holiday', 'october', 'winter']):
            categories['Seasonality'].append(feat)
        elif any(x in feat for x in ['volume', 'volatility', 'regime']):
            categories['Market Microstructure'].append(feat)
        elif '_x_' in feat or 'below' in feat or 'above' in feat:
            categories['Interactions'].append(feat)
        else:
            categories['Technical Indicators'].append(feat)
    
    for category, features in categories.items():
        if features:
            print(f"\n{category} ({len(features)}):")
            for feat in features:
                rank = consensus_df[consensus_df['feature'] == feat]['final_rank'].values[0]
                print(f"  {rank:2d}. {feat}")
    
    # Save compact feature list
    output_dir = Path(__file__).resolve().parents[1] / "outputs" / "interpretability"
    output_path = output_dir / "compact_feature_list.txt"
    with open(output_path, 'w') as f:
        f.write(f"# Compact Feature Set ({target_features} features)\n")
        f.write(f"# Generated from feature importance analysis\n")
        f.write(f"# Use for Ridge regression\n\n")
        f.write("COMMON_FEATURES_COMPACT = [\n")
        for feat in top_features:
            f.write(f'    "{feat}",\n')
        f.write("]\n")
    
    print(f"\n✓ Saved compact feature list: {output_path}")
    
    # Features to remove
    all_features = set(consensus_df['feature'].tolist())
    removed_features = all_features - set(top_features)
    
    print(f"\n❌ Features to Remove ({len(removed_features)}):")
    removed_df = consensus_df[consensus_df['feature'].isin(removed_features)].sort_values('final_rank')
    for _, row in removed_df.iterrows():
        print(f"  {row['final_rank']:2d}. {row['feature']}")
    
    return top_features


def plot_importance_comparison(builtin_df, perm_df, shap_df, output_dir):
    """Create comparison plot of all three importance methods."""
    print("\n=== Creating Comparison Plots ===")
    
    # Determine number of subplots based on available methods
    n_plots = sum([builtin_df is not None, perm_df is not None, shap_df is not None])
    if n_plots == 0:
        print("⚠️ No importance data to plot")
        return
    
    fig, axes = plt.subplots(1, n_plots, figsize=(6 * n_plots, 8))
    if n_plots == 1:
        axes = [axes]
    
    plot_idx = 0
    
    # Built-in importance
    if builtin_df is not None:
        top20_builtin = builtin_df.head(20).sort_values('importance')
        axes[plot_idx].barh(range(20), top20_builtin['importance'])
        axes[plot_idx].set_yticks(range(20))
        axes[plot_idx].set_yticklabels(top20_builtin['feature'], fontsize=8)
        axes[plot_idx].set_xlabel('Gini Importance')
        axes[plot_idx].set_title('Built-in Feature Importance')
        axes[plot_idx].grid(axis='x', alpha=0.3)
        plot_idx += 1
    
    # Permutation importance
    if perm_df is not None:
        top20_perm = perm_df.head(20).sort_values('importance_mean')
        axes[plot_idx].barh(range(20), top20_perm['importance_mean'])
        axes[plot_idx].set_yticks(range(20))
        axes[plot_idx].set_yticklabels(top20_perm['feature'], fontsize=8)
        axes[plot_idx].set_xlabel('Permutation Importance (R²)')
        axes[plot_idx].set_title('Permutation Importance (Test Set)')
        axes[plot_idx].grid(axis='x', alpha=0.3)
        plot_idx += 1
    
    # SHAP importance
    if shap_df is not None:
        top20_shap = shap_df.head(20).sort_values('mean_abs_shap')
        axes[plot_idx].barh(range(20), top20_shap['mean_abs_shap'])
        axes[plot_idx].set_yticks(range(20))
        axes[plot_idx].set_yticklabels(top20_shap['feature'], fontsize=8)
        axes[plot_idx].set_xlabel('Mean |SHAP|')
        axes[plot_idx].set_title('SHAP Feature Importance')
        axes[plot_idx].grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / "importance_comparison.png", dpi=160, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved comparison plot: {output_dir / 'importance_comparison.png'}")


def main():
    """Main analysis pipeline."""
    print("=" * 80)
    print("Feature Importance Analysis - Gradient Boosting Model")
    print("=" * 80)
    
    # Load data and model
    model, X_train, y_train, X_test, y_test = load_data_and_model()
    
    # Compute importance using three methods
    builtin_df = compute_builtin_importance(model, COMMON_FEATURES)
    perm_df = compute_permutation_importance(model, X_test, y_test, COMMON_FEATURES, n_repeats=10)
    shap_df = compute_shap_importance(model, X_test, COMMON_FEATURES, max_samples=500)
    
    # Create consensus ranking
    consensus_df = create_consensus_ranking(builtin_df, perm_df, shap_df)
    
    # Save consensus ranking
    output_dir = Path(__file__).resolve().parents[1] / "outputs" / "interpretability"
    output_dir.mkdir(parents=True, exist_ok=True)
    consensus_df.to_csv(output_dir / "feature_importance_consensus.csv", index=False)
    print(f"\n✓ Saved consensus ranking: {output_dir / 'feature_importance_consensus.csv'}")
    
    # Generate recommendations
    top_features = generate_recommendations(consensus_df, target_features=45)
    
    # Create comparison plots
    plot_importance_comparison(builtin_df, perm_df, shap_df, output_dir)
    
    print("\n" + "=" * 80)
    print("✅ Feature Importance Analysis Complete!")
    print("=" * 80)
    print(f"\nOutputs saved to: {output_dir}")
    print("\nNext Steps:")
    print("1. Review feature rankings in: feature_importance_consensus.csv")
    print("2. Update COMMON_FEATURES in src/models/baseline_models.py with compact set")
    print("3. Retrain Ridge model with compact features")
    print("4. Compare performance: Ridge (76 features) vs Ridge (45 features)")


if __name__ == "__main__":
    main()
