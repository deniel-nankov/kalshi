"""
Performance Metrics Visualizer

Creates detailed visualizations of:
1. Model performance comparison
2. Walk-forward validation results
3. Feature importance analysis
4. Training metrics over time
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from pathlib import Path
import seaborn as sns


def create_model_performance_dashboard(output_path: Path):
    """Create comprehensive model performance comparison dashboard."""
    
    # Load actual metrics
    metrics_path = Path(__file__).resolve().parents[1] / "outputs" / "models" / "model_metrics_summary.csv"
    
    if not metrics_path.exists():
        print(f"⚠️  Metrics file not found: {metrics_path}")
        return
    
    df = pd.read_csv(metrics_path)
    
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # Main title
    fig.suptitle('Model Performance Dashboard', fontsize=20, fontweight='bold', y=0.98)
    
    # ===== SUBPLOT 1: RMSE Comparison =====
    ax1 = fig.add_subplot(gs[0, :2])
    models = df['model'].tolist()
    train_rmse = df['train_rmse'].tolist()
    test_rmse = df['test_rmse'].tolist()
    
    x = np.arange(len(models))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, train_rmse, width, label='Train RMSE', 
                    color='#3498DB', alpha=0.8, edgecolor='black')
    bars2 = ax1.bar(x + width/2, test_rmse, width, label='Test RMSE', 
                    color='#E74C3C', alpha=0.8, edgecolor='black')
    
    ax1.set_xlabel('Model', fontsize=12, fontweight='bold')
    ax1.set_ylabel('RMSE ($/gallon)', fontsize=12, fontweight='bold')
    ax1.set_title('Root Mean Squared Error Comparison', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(models, fontsize=11)
    ax1.legend(fontsize=10)
    ax1.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0.01:  # Only show if significant
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.4f}', ha='center', va='bottom', fontsize=9)
    
    # ===== SUBPLOT 2: R² Score Comparison =====
    ax2 = fig.add_subplot(gs[0, 2])
    test_r2 = df['test_r2'].tolist()
    
    colors = ['#27AE60' if r > 0 else '#E74C3C' for r in test_r2]
    bars = ax2.barh(models, test_r2, color=colors, alpha=0.7, edgecolor='black')
    
    ax2.set_xlabel('R² Score', fontsize=12, fontweight='bold')
    ax2.set_title('Test R² Performance', fontsize=14, fontweight='bold')
    ax2.axvline(x=0, color='black', linestyle='--', linewidth=1)
    ax2.grid(axis='x', alpha=0.3)
    
    for i, (bar, val) in enumerate(zip(bars, test_r2)):
        if abs(val) > 1:
            label_text = f'{val:.1f}'
        else:
            label_text = f'{val:.3f}'
        ax2.text(val + 0.1, i, label_text, va='center', fontsize=9, fontweight='bold')
    
    # ===== SUBPLOT 3: MAPE Comparison =====
    ax3 = fig.add_subplot(gs[1, :2])
    test_mape = df['test_mape_pct'].tolist()
    
    bars = ax3.bar(models, test_mape, color='#9B59B6', alpha=0.7, edgecolor='black')
    ax3.set_xlabel('Model', fontsize=12, fontweight='bold')
    ax3.set_ylabel('MAPE (%)', fontsize=12, fontweight='bold')
    ax3.set_title('Mean Absolute Percentage Error', fontsize=14, fontweight='bold')
    ax3.set_xticklabels(models, fontsize=11)
    ax3.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # ===== SUBPLOT 4: Model Summary Table =====
    ax4 = fig.add_subplot(gs[1, 2])
    ax4.axis('off')
    
    table_data = []
    for _, row in df.iterrows():
        table_data.append([
            row['model'],
            f"{row['test_rmse']:.4f}",
            f"{row['test_r2']:.3f}",
            f"{row['test_mape_pct']:.2f}%"
        ])
    
    table = ax4.table(cellText=table_data,
                     colLabels=['Model', 'RMSE', 'R²', 'MAPE'],
                     cellLoc='center',
                     loc='center',
                     bbox=[0, 0, 1, 1])
    
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    # Style header
    for i in range(4):
        table[(0, i)].set_facecolor('#34495E')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Style rows
    for i in range(1, len(table_data) + 1):
        for j in range(4):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#ECF0F1')
    
    ax4.set_title('Performance Summary', fontsize=14, fontweight='bold', pad=20)
    
    # ===== SUBPLOT 5: Train vs Test Scatter =====
    ax5 = fig.add_subplot(gs[2, :])
    
    train_vals = df['train_rmse'].tolist()
    test_vals = df['test_rmse'].tolist()
    
    for i, model in enumerate(models):
        ax5.scatter(train_vals[i], test_vals[i], s=200, alpha=0.7, 
                   label=model, edgecolors='black', linewidth=2)
        ax5.annotate(model, (train_vals[i], test_vals[i]), 
                    xytext=(5, 5), textcoords='offset points', fontsize=9)
    
    # Perfect prediction line
    max_val = max(max(train_vals), max(test_vals))
    ax5.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, linewidth=2, label='Perfect (Train=Test)')
    
    ax5.set_xlabel('Train RMSE', fontsize=12, fontweight='bold')
    ax5.set_ylabel('Test RMSE', fontsize=12, fontweight='bold')
    ax5.set_title('Train vs Test Error (closer to diagonal = better generalization)', 
                 fontsize=14, fontweight='bold')
    ax5.legend(fontsize=9)
    ax5.grid(alpha=0.3)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved model performance dashboard to {output_path}")


def create_walk_forward_visualization(output_path: Path):
    """Create comprehensive walk-forward validation visualization."""
    
    metrics_path = Path(__file__).resolve().parents[1] / "outputs" / "walk_forward" / "walk_forward_metrics.csv"
    
    if not metrics_path.exists():
        print(f"⚠️  Walk-forward metrics not found: {metrics_path}")
        return
    
    df = pd.read_csv(metrics_path)
    
    fig = plt.figure(figsize=(18, 10))
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
    
    fig.suptitle('Walk-Forward Validation Analysis', fontsize=20, fontweight='bold', y=0.98)
    
    # ===== SUBPLOT 1: RMSE by Horizon =====
    ax1 = fig.add_subplot(gs[0, 0])
    
    horizon_stats = df.groupby('horizon')['rmse'].agg(['mean', 'std']).reset_index()
    
    ax1.errorbar(horizon_stats['horizon'], horizon_stats['mean'], 
                yerr=horizon_stats['std'], marker='o', markersize=10,
                linewidth=2, capsize=5, capthick=2, color='#E74C3C', alpha=0.8)
    
    ax1.set_xlabel('Forecast Horizon (days)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('RMSE ($/gallon)', fontsize=12, fontweight='bold')
    ax1.set_title('Error Growth with Forecast Horizon', fontsize=13, fontweight='bold')
    ax1.grid(alpha=0.3)
    ax1.set_xticks(horizon_stats['horizon'])
    
    # ===== SUBPLOT 2: R² by Horizon =====
    ax2 = fig.add_subplot(gs[0, 1])
    
    r2_stats = df.groupby('horizon')['r2'].agg(['mean', 'std']).reset_index()
    
    colors = ['#27AE60' if r > 0 else '#E74C3C' for r in r2_stats['mean']]
    bars = ax2.bar(r2_stats['horizon'], r2_stats['mean'], 
                   color=colors, alpha=0.7, edgecolor='black', linewidth=2)
    
    ax2.axhline(y=0, color='black', linestyle='--', linewidth=1)
    ax2.set_xlabel('Forecast Horizon (days)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('R² Score', fontsize=12, fontweight='bold')
    ax2.set_title('Predictive Power vs Horizon', fontsize=13, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    
    for bar, val in zip(bars, r2_stats['mean']):
        label_y = val + 0.1 if val > 0 else val - 0.15
        ax2.text(bar.get_x() + bar.get_width()/2., label_y,
                f'{val:.2f}', ha='center', fontsize=9, fontweight='bold')
    
    # ===== SUBPLOT 3: MAPE by Horizon =====
    ax3 = fig.add_subplot(gs[0, 2])
    
    mape_stats = df.groupby('horizon')['mape_pct'].agg(['mean', 'std']).reset_index()
    
    ax3.plot(mape_stats['horizon'], mape_stats['mean'], 
            marker='s', markersize=10, linewidth=3, color='#9B59B6', alpha=0.8)
    ax3.fill_between(mape_stats['horizon'], 
                     mape_stats['mean'] - mape_stats['std'],
                     mape_stats['mean'] + mape_stats['std'],
                     alpha=0.2, color='#9B59B6')
    
    ax3.set_xlabel('Forecast Horizon (days)', fontsize=12, fontweight='bold')
    ax3.set_ylabel('MAPE (%)', fontsize=12, fontweight='bold')
    ax3.set_title('Percentage Error Growth', fontsize=13, fontweight='bold')
    ax3.grid(alpha=0.3)
    ax3.set_xticks(mape_stats['horizon'])
    
    # ===== SUBPLOT 4: Heatmap - RMSE by Year and Horizon =====
    ax4 = fig.add_subplot(gs[1, :2])
    
    pivot = df.pivot(index='year', columns='horizon', values='rmse')
    
    sns.heatmap(pivot, annot=True, fmt='.4f', cmap='RdYlGn_r', 
               cbar_kws={'label': 'RMSE ($/gallon)'}, ax=ax4,
               linewidths=1, linecolor='white')
    
    ax4.set_xlabel('Forecast Horizon (days)', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Year', fontsize=12, fontweight='bold')
    ax4.set_title('RMSE Heatmap: Performance by Year and Horizon', fontsize=13, fontweight='bold')
    
    # ===== SUBPLOT 5: Best Alpha Distribution =====
    ax5 = fig.add_subplot(gs[1, 2])
    
    alpha_counts = df['best_alpha'].value_counts().sort_index()
    
    ax5.pie(alpha_counts.values, labels=[f'α={a:.2f}' for a in alpha_counts.index],
           autopct='%1.1f%%', startangle=90, colors=sns.color_palette('Set2'))
    ax5.set_title('Optimal Alpha Distribution\n(Ridge Regularization)', 
                 fontsize=13, fontweight='bold')
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved walk-forward visualization to {output_path}")


def create_feature_importance_chart(output_path: Path):
    """Create feature importance visualization from Ridge model."""
    
    import pickle
    
    model_path = Path(__file__).resolve().parents[1] / "outputs" / "models" / "ridge_model.pkl"
    
    if not model_path.exists():
        print(f"⚠️  Ridge model not found: {model_path}")
        return
    
    # Load model
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Get feature names from baseline_models
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from models.baseline_models import COMMON_FEATURES
    
    # Extract coefficients
    coefs = model.coef_
    feature_importance = pd.DataFrame({
        'feature': COMMON_FEATURES,
        'coefficient': coefs,
        'abs_coefficient': np.abs(coefs)
    }).sort_values('abs_coefficient', ascending=False)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 10))
    
    fig.suptitle('Ridge Regression Feature Importance', fontsize=20, fontweight='bold')
    
    # ===== SUBPLOT 1: Absolute Importance =====
    colors = ['#E74C3C' if c > 0 else '#3498DB' for c in feature_importance['coefficient']]
    
    ax1.barh(range(len(feature_importance)), feature_importance['abs_coefficient'],
            color=colors, alpha=0.7, edgecolor='black')
    ax1.set_yticks(range(len(feature_importance)))
    ax1.set_yticklabels(feature_importance['feature'], fontsize=9)
    ax1.set_xlabel('Absolute Coefficient Magnitude', fontsize=12, fontweight='bold')
    ax1.set_title('Feature Importance (by magnitude)', fontsize=14, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for i, val in enumerate(feature_importance['abs_coefficient']):
        ax1.text(val, i, f' {val:.4f}', va='center', fontsize=8)
    
    # ===== SUBPLOT 2: Signed Coefficients =====
    sorted_by_coef = feature_importance.sort_values('coefficient')
    colors2 = ['#E74C3C' if c > 0 else '#3498DB' for c in sorted_by_coef['coefficient']]
    
    ax2.barh(range(len(sorted_by_coef)), sorted_by_coef['coefficient'],
            color=colors2, alpha=0.7, edgecolor='black')
    ax2.set_yticks(range(len(sorted_by_coef)))
    ax2.set_yticklabels(sorted_by_coef['feature'], fontsize=9)
    ax2.set_xlabel('Coefficient Value', fontsize=12, fontweight='bold')
    ax2.set_title('Feature Direction (positive = increases price)', fontsize=14, fontweight='bold')
    ax2.axvline(x=0, color='black', linestyle='--', linewidth=2)
    ax2.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for i, val in enumerate(sorted_by_coef['coefficient']):
        x_pos = val + 0.01 if val > 0 else val - 0.01
        ha = 'left' if val > 0 else 'right'
        ax2.text(x_pos, i, f'{val:.4f}', va='center', ha=ha, fontsize=8)
    
    # Legend
    red_patch = mpatches.Patch(color='#E74C3C', label='Positive (↑ feature → ↑ price)', alpha=0.7)
    blue_patch = mpatches.Patch(color='#3498DB', label='Negative (↑ feature → ↓ price)', alpha=0.7)
    ax2.legend(handles=[red_patch, blue_patch], loc='lower right', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved feature importance chart to {output_path}")


def create_data_quality_dashboard(output_path: Path):
    """Create data quality and pipeline health visualization."""
    
    gold_path = Path(__file__).resolve().parents[1] / "data" / "gold" / "master_model_ready.parquet"
    
    if not gold_path.exists():
        print(f"⚠️  Gold layer not found: {gold_path}")
        return
    
    df = pd.read_parquet(gold_path)
    df['date'] = pd.to_datetime(df['date'])
    
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 3, hspace=0.4, wspace=0.3)
    
    fig.suptitle('Data Quality & Pipeline Health Dashboard', fontsize=20, fontweight='bold', y=0.98)
    
    # ===== SUBPLOT 1: Data Completeness Over Time =====
    ax1 = fig.add_subplot(gs[0, :])
    
    df_sorted = df.sort_values('date')
    completeness = (1 - df_sorted.isnull().sum(axis=1) / len(df_sorted.columns)) * 100
    
    ax1.plot(df_sorted['date'], completeness, linewidth=2, color='#27AE60', alpha=0.8)
    ax1.fill_between(df_sorted['date'], completeness, 100, alpha=0.2, color='#27AE60')
    ax1.axhline(y=100, color='green', linestyle='--', linewidth=2, label='Perfect (100%)')
    
    ax1.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Completeness (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Data Completeness Over Time', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(alpha=0.3)
    ax1.set_ylim([95, 101])
    
    # ===== SUBPLOT 2: Missing Data by Feature =====
    ax2 = fig.add_subplot(gs[1, 0])
    
    missing = df.isnull().sum().sort_values(ascending=False)
    if missing.sum() > 0:
        top_missing = missing[missing > 0].head(10)
        ax2.barh(range(len(top_missing)), top_missing.values, color='#E74C3C', alpha=0.7)
        ax2.set_yticks(range(len(top_missing)))
        ax2.set_yticklabels(top_missing.index, fontsize=9)
    else:
        ax2.text(0.5, 0.5, 'No Missing Data! ✓', ha='center', va='center', 
                fontsize=16, fontweight='bold', color='#27AE60',
                transform=ax2.transAxes)
        ax2.set_xlim([0, 1])
        ax2.set_ylim([0, 1])
    
    ax2.set_xlabel('Missing Count', fontsize=12, fontweight='bold')
    ax2.set_title('Missing Data by Feature', fontsize=13, fontweight='bold')
    ax2.grid(axis='x', alpha=0.3)
    
    # ===== SUBPLOT 3: Data Distribution =====
    ax3 = fig.add_subplot(gs[1, 1])
    
    date_range = (df['date'].max() - df['date'].min()).days
    rows_per_year = len(df) / (date_range / 365)
    
    stats = {
        'Total Rows': len(df),
        'Date Range (days)': date_range,
        'Features': len(df.columns) - 1,  # Exclude date
        'Avg Rows/Year': f'{rows_per_year:.0f}',
        'Min Date': df['date'].min().strftime('%Y-%m-%d'),
        'Max Date': df['date'].max().strftime('%Y-%m-%d')
    }
    
    ax3.axis('off')
    y_pos = 0.9
    for key, value in stats.items():
        ax3.text(0.1, y_pos, f'{key}:', fontsize=11, fontweight='bold', va='center')
        ax3.text(0.95, y_pos, str(value), fontsize=11, va='center', ha='right', color='#E74C3C')
        y_pos -= 0.15
    
    ax3.set_title('Dataset Statistics', fontsize=13, fontweight='bold', pad=20)
    
    # ===== SUBPLOT 4: October Data Distribution =====
    ax4 = fig.add_subplot(gs[1, 2])
    
    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year
    
    october_counts = df[df['month'] == 10].groupby('year').size()
    
    ax4.bar(october_counts.index, october_counts.values, color='#F39C12', alpha=0.7, edgecolor='black')
    ax4.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax4.set_ylabel('October Days', fontsize=12, fontweight='bold')
    ax4.set_title('October Data Availability', fontsize=13, fontweight='bold')
    ax4.grid(axis='y', alpha=0.3)
    
    for x, y in zip(october_counts.index, october_counts.values):
        ax4.text(x, y+0.5, str(y), ha='center', fontsize=9, fontweight='bold')
    
    # ===== SUBPLOT 5: Feature Correlation Heatmap =====
    ax5 = fig.add_subplot(gs[2, :])
    
    # Select key features for correlation
    key_features = ['price_rbob', 'price_wti', 'retail_price', 'inventory_mbbl', 
                   'utilization_pct', 'crack_spread', 'days_supply']
    
    available_features = [f for f in key_features if f in df.columns]
    
    if len(available_features) > 1:
        corr = df[available_features].corr()
        
        sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                   square=True, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax5,
                   vmin=-1, vmax=1)
        
        ax5.set_title('Feature Correlation Matrix (Key Variables)', fontsize=14, fontweight='bold')
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved data quality dashboard to {output_path}")


def main():
    """Generate all performance visualizations."""
    
    output_dir = Path(__file__).resolve().parents[1] / "outputs" / "visualizations"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("📊 GENERATING PERFORMANCE VISUALIZATIONS")
    print("="*70 + "\n")
    
    create_model_performance_dashboard(output_dir / "05_model_performance_dashboard.png")
    create_walk_forward_visualization(output_dir / "06_walk_forward_analysis.png")
    create_feature_importance_chart(output_dir / "07_feature_importance.png")
    create_data_quality_dashboard(output_dir / "08_data_quality_dashboard.png")
    
    print("\n" + "="*70)
    print(f"✓ All performance visualizations saved to {output_dir}")
    print("="*70)
    print("\nGenerated files:")
    for f in sorted(output_dir.glob("*.png")):
        size_kb = f.stat().st_size / 1024
        print(f"  • {f.name:50s} {size_kb:>8.1f} KB")
    print()


if __name__ == "__main__":
    main()
