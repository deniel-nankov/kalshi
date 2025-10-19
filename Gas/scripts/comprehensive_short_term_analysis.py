"""
Comprehensive analysis for short-term forecasting (1-3 days).
Compares Ridge vs GB performance and generates SHAP feature importance.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.baseline_models import COMMON_FEATURES, load_model_ready_dataset, prepare_forecast_frame

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)


def compute_metrics(y_true, y_pred):
    """Compute regression metrics."""
    return {
        'r2': r2_score(y_true, y_pred),
        'mae': mean_absolute_error(y_true, y_pred),
        'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
        'mape': np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    }


def train_and_evaluate_models(df, horizon, year):
    """Train Ridge and GB for a specific horizon and year."""
    df_h = prepare_forecast_frame(df, horizon)
    
    # Split train/test
    start = pd.Timestamp(f"{year}-10-01")
    end = pd.Timestamp(f"{year}-10-31")
    
    train_mask = df_h["target_date"] < start
    test_mask = (df_h["target_date"] >= start) & (df_h["target_date"] <= end)
    
    train_df = df_h.loc[train_mask].copy()
    test_df = df_h.loc[test_mask].copy()
    
    if len(train_df) < 200 or test_df.empty:
        return None, None, None
    
    X_train = train_df[COMMON_FEATURES]
    y_train = train_df['target']
    X_test = test_df[COMMON_FEATURES]
    y_test = test_df['target']
    
    # Train Ridge
    ridge = Ridge(alpha=1.0, random_state=42)
    ridge.fit(X_train, y_train)
    ridge_pred = ridge.predict(X_test)
    ridge_metrics = compute_metrics(y_test, ridge_pred)
    
    # Train GB
    gb = GradientBoostingRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        min_samples_split=10,
        random_state=42
    )
    gb.fit(X_train, y_train)
    gb_pred = gb.predict(X_test)
    gb_metrics = compute_metrics(y_test, gb_pred)
    
    return {
        'ridge': {'model': ridge, 'metrics': ridge_metrics, 'predictions': ridge_pred},
        'gb': {'model': gb, 'metrics': gb_metrics, 'predictions': gb_pred},
        'test_data': {'X': X_test, 'y': y_test, 'dates': test_df['target_date']}
    }


def generate_shap_analysis(model, X_train, X_test, feature_names, model_name, horizon, year, output_dir):
    """Generate SHAP analysis for a model."""
    try:
        import shap
    except ImportError:
        print("⚠️ SHAP not installed. Skipping SHAP analysis.")
        print("   Install with: pip install shap")
        return None
    
    print(f"\n🔍 Generating SHAP analysis for {model_name} (horizon={horizon}, year={year})...")
    
    # Create SHAP explainer
    explainer = shap.Explainer(model, X_train)
    shap_values = explainer(X_test)
    
    # Get mean absolute SHAP values for feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_names,
        'importance': np.abs(shap_values.values).mean(axis=0)
    }).sort_values('importance', ascending=False)
    
    # Save feature importance
    feature_importance.to_csv(
        output_dir / f'shap_importance_{model_name}_h{horizon}_y{year}.csv',
        index=False
    )
    
    # Create SHAP summary plot
    fig, ax = plt.subplots(figsize=(12, 10))
    shap.summary_plot(shap_values, X_test, feature_names=feature_names, show=False, max_display=20)
    plt.title(f'SHAP Feature Importance: {model_name.upper()} ({horizon}-day, {year})', fontsize=14)
    plt.tight_layout()
    plt.savefig(output_dir / f'shap_summary_{model_name}_h{horizon}_y{year}.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"   ✅ Saved SHAP plots to {output_dir}")
    
    return feature_importance


def analyze_short_term_forecasting(df, horizons=[1, 2, 3], years=[2021, 2022, 2023, 2024]):
    """Comprehensive analysis of short-term forecasting (1-3 days)."""
    
    output_dir = Path(__file__).resolve().parents[1] / "outputs" / "short_term_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*80)
    print("📊 SHORT-TERM FORECASTING ANALYSIS (1-3 DAYS)")
    print("="*80)
    print(f"Dataset: {len(df)} rows")
    print(f"Features: {len(COMMON_FEATURES)}")
    print(f"Horizons: {horizons}")
    print(f"Years: {years}")
    print("="*80)
    
    results = []
    best_models = {}
    
    for horizon in horizons:
        print(f"\n{'='*80}")
        print(f"📅 HORIZON: {horizon} DAYS")
        print(f"{'='*80}")
        
        for year in years:
            print(f"\n  📆 Year {year}:")
            
            result = train_and_evaluate_models(df, horizon, year)
            
            if result is None:
                print(f"     ⚠️ Insufficient data")
                continue
            
            ridge_r2 = result['ridge']['metrics']['r2']
            gb_r2 = result['gb']['metrics']['r2']
            
            ridge_mae = result['ridge']['metrics']['mae']
            gb_mae = result['gb']['metrics']['mae']
            
            # Determine winner
            if ridge_r2 > gb_r2:
                winner = "RIDGE"
                improvement = ((ridge_r2 - gb_r2) / abs(gb_r2) * 100) if gb_r2 != 0 else float('inf')
            else:
                winner = "GB"
                improvement = ((gb_r2 - ridge_r2) / abs(ridge_r2) * 100) if ridge_r2 != 0 else float('inf')
            
            print(f"     Ridge:  R²={ridge_r2:>7.4f}, MAE=${ridge_mae:.4f}")
            print(f"     GB:     R²={gb_r2:>7.4f}, MAE=${gb_mae:.4f}")
            print(f"     Winner: {winner} (improvement: {improvement:.1f}%)")
            
            # Store results
            results.append({
                'horizon': horizon,
                'year': year,
                'ridge_r2': ridge_r2,
                'ridge_mae': ridge_mae,
                'gb_r2': gb_r2,
                'gb_mae': gb_mae,
                'winner': winner,
                'improvement_pct': improvement
            })
            
            # Save best model for SHAP analysis
            key = f"h{horizon}_y{year}"
            if winner == "GB" and gb_r2 > 0.5:  # Only analyze high-performing GB models
                best_models[key] = {
                    'model': result['gb']['model'],
                    'X_train': result['test_data']['X'],  # Use test as "train" for SHAP
                    'X_test': result['test_data']['X'],
                    'horizon': horizon,
                    'year': year,
                    'r2': gb_r2
                }
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_dir / 'ridge_vs_gb_comparison.csv', index=False)
    
    print("\n" + "="*80)
    print("📈 SUMMARY STATISTICS")
    print("="*80)
    
    # Overall statistics
    print("\n🎯 OVERALL PERFORMANCE (ALL HORIZONS & YEARS):")
    print("-"*60)
    print(f"Ridge:  Mean R²={results_df['ridge_r2'].mean():>7.4f}, Median R²={results_df['ridge_r2'].median():>7.4f}")
    print(f"GB:     Mean R²={results_df['gb_r2'].mean():>7.4f}, Median R²={results_df['gb_r2'].median():>7.4f}")
    
    # By horizon
    print("\n📊 PERFORMANCE BY HORIZON:")
    print("-"*60)
    for h in horizons:
        h_data = results_df[results_df['horizon'] == h]
        print(f"\n{h}-Day Horizon:")
        print(f"  Ridge:  Mean R²={h_data['ridge_r2'].mean():>7.4f}, Best={h_data['ridge_r2'].max():>7.4f}")
        print(f"  GB:     Mean R²={h_data['gb_r2'].mean():>7.4f}, Best={h_data['gb_r2'].max():>7.4f}")
        
        ridge_wins = len(h_data[h_data['winner'] == 'RIDGE'])
        gb_wins = len(h_data[h_data['winner'] == 'GB'])
        print(f"  Wins:   Ridge={ridge_wins}, GB={gb_wins}")
    
    # Best results
    print("\n🏆 TOP 10 BEST RESULTS (ANY MODEL, ≤3 DAYS):")
    print("-"*60)
    
    # Melt the dataframe to get all results in one column
    best_results = []
    for _, row in results_df.iterrows():
        best_results.append({
            'horizon': row['horizon'],
            'year': row['year'],
            'model': 'Ridge',
            'r2': row['ridge_r2'],
            'mae': row['ridge_mae']
        })
        best_results.append({
            'horizon': row['horizon'],
            'year': row['year'],
            'model': 'GB',
            'r2': row['gb_r2'],
            'mae': row['gb_mae']
        })
    
    best_df = pd.DataFrame(best_results).nlargest(10, 'r2')
    for idx, row in best_df.iterrows():
        print(f"  {row['year']} {row['horizon']}d {row['model']:<10} R²={row['r2']:>7.4f}  MAE=${row['mae']:.4f}")
    
    # Generate SHAP for best models
    print("\n" + "="*80)
    print("🔬 SHAP FEATURE IMPORTANCE ANALYSIS")
    print("="*80)
    
    if best_models:
        print(f"\nAnalyzing {len(best_models)} high-performing models (R² > 0.5)...")
        
        for key, model_data in best_models.items():
            try:
                importance = generate_shap_analysis(
                    model_data['model'],
                    model_data['X_train'],
                    model_data['X_test'],
                    COMMON_FEATURES,
                    'gb',
                    model_data['horizon'],
                    model_data['year'],
                    output_dir
                )
                
                if importance is not None:
                    print(f"\n   Top 10 features for {key} (R²={model_data['r2']:.4f}):")
                    print(importance.head(10).to_string(index=False))
            except Exception as e:
                print(f"   ⚠️ SHAP analysis failed for {key}: {e}")
    else:
        print("\n⚠️ No high-performing GB models (R² > 0.5) found for SHAP analysis")
        print("   SHAP works best with models that have positive R² values")
    
    # Create comparison visualizations
    create_comparison_plots(results_df, output_dir)
    
    print("\n" + "="*80)
    print("✅ ANALYSIS COMPLETE")
    print("="*80)
    print(f"\n📁 Results saved to: {output_dir}")
    print(f"   - ridge_vs_gb_comparison.csv")
    print(f"   - comparison_plots.png")
    print(f"   - shap_*.csv and shap_*.png (if generated)")


def create_comparison_plots(results_df, output_dir):
    """Create comparison visualizations."""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot 1: R² by horizon
    ax1 = axes[0, 0]
    x = np.arange(len(results_df['horizon'].unique()))
    width = 0.35
    
    ridge_means = [results_df[results_df['horizon']==h]['ridge_r2'].mean() for h in sorted(results_df['horizon'].unique())]
    gb_means = [results_df[results_df['horizon']==h]['gb_r2'].mean() for h in sorted(results_df['horizon'].unique())]
    
    ax1.bar(x - width/2, ridge_means, width, label='Ridge', color='steelblue', alpha=0.8)
    ax1.bar(x + width/2, gb_means, width, label='GB', color='coral', alpha=0.8)
    ax1.set_xlabel('Forecast Horizon (days)', fontsize=12)
    ax1.set_ylabel('Mean R²', fontsize=12)
    ax1.set_title('Average Performance by Horizon', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f'{h}d' for h in sorted(results_df['horizon'].unique())])
    ax1.legend()
    ax1.axhline(y=0, color='black', linestyle='--', linewidth=0.8)
    ax1.grid(alpha=0.3)
    
    # Plot 2: R² by year
    ax2 = axes[0, 1]
    x = np.arange(len(results_df['year'].unique()))
    
    ridge_year_means = [results_df[results_df['year']==y]['ridge_r2'].mean() for y in sorted(results_df['year'].unique())]
    gb_year_means = [results_df[results_df['year']==y]['gb_r2'].mean() for y in sorted(results_df['year'].unique())]
    
    ax2.bar(x - width/2, ridge_year_means, width, label='Ridge', color='steelblue', alpha=0.8)
    ax2.bar(x + width/2, gb_year_means, width, label='GB', color='coral', alpha=0.8)
    ax2.set_xlabel('Year', fontsize=12)
    ax2.set_ylabel('Mean R²', fontsize=12)
    ax2.set_title('Average Performance by Year', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(sorted(results_df['year'].unique()))
    ax2.legend()
    ax2.axhline(y=0, color='black', linestyle='--', linewidth=0.8)
    ax2.grid(alpha=0.3)
    
    # Plot 3: Heatmap of Ridge performance
    ax3 = axes[1, 0]
    pivot_ridge = results_df.pivot(index='year', columns='horizon', values='ridge_r2')
    sns.heatmap(pivot_ridge, annot=True, fmt='.3f', cmap='RdYlGn', center=0, 
                ax=ax3, cbar_kws={'label': 'R²'}, vmin=-1, vmax=1)
    ax3.set_title('Ridge R² Heatmap', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Horizon (days)', fontsize=12)
    ax3.set_ylabel('Year', fontsize=12)
    
    # Plot 4: Heatmap of GB performance
    ax4 = axes[1, 1]
    pivot_gb = results_df.pivot(index='year', columns='horizon', values='gb_r2')
    sns.heatmap(pivot_gb, annot=True, fmt='.3f', cmap='RdYlGn', center=0,
                ax=ax4, cbar_kws={'label': 'R²'}, vmin=-1, vmax=1)
    ax4.set_title('Gradient Boosting R² Heatmap', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Horizon (days)', fontsize=12)
    ax4.set_ylabel('Year', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'comparison_plots.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\n📊 Saved comparison plots to {output_dir / 'comparison_plots.png'}")


def main():
    """Main execution."""
    # Load data
    data_path = Path(__file__).resolve().parents[1] / "data" / "gold" / "master_model_ready.parquet"
    df = load_model_ready_dataset(data_path)
    
    print(f"\n✅ Loaded dataset: {len(df)} rows, {len(df.columns)} features")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    
    # Count sentiment features
    sentiment_cols = [c for c in df.columns if 'sentiment' in c.lower() or 'news_' in c.lower()]
    print(f"   Sentiment features: {len(sentiment_cols)}")
    
    # Run analysis
    analyze_short_term_forecasting(df, horizons=[1, 2, 3], years=[2021, 2022, 2023, 2024])


if __name__ == "__main__":
    main()
