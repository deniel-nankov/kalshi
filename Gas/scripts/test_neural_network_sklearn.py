"""
Neural Network Testing using Scikit-Learn (TensorFlow Alternative)

TensorFlow has compatibility issues with Python 3.13 on macOS ARM.
Using scikit-learn's MLPRegressor as a simpler alternative.

This tests feedforward neural networks against Ridge baseline.
"""

import json
import sys
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Add src to path
SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.baseline_models import (
    load_model_ready_dataset,
    prepare_forecast_frame,
    COMMON_FEATURES
)

# Set random seed
np.random.seed(42)

# Output directory
OUTPUT_DIR = Path('outputs/neural_network_test')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("="*80)
print("🧠 NEURAL NETWORK TESTING (Scikit-Learn)")
print("="*80)
print("Note: Using MLPRegressor instead of LSTM due to TensorFlow compatibility issues")
print("Testing feedforward neural networks vs Ridge baseline on 1-3 day forecasts")
print("="*80)


def train_neural_network(X_train, y_train, X_val, y_val):
    """
    Train neural network using scikit-learn.
    
    Architecture: 2 hidden layers (100, 50 neurons) with ReLU activation
    """
    model = MLPRegressor(
        hidden_layer_sizes=(100, 50),
        activation='relu',
        solver='adam',
        alpha=0.01,  # L2 regularization
        batch_size=32,
        learning_rate_init=0.001,
        max_iter=500,
        early_stopping=True,
        validation_fraction=0.2,
        n_iter_no_change=20,
        random_state=42,
        verbose=False
    )
    
    print(f"      Training NN (100-50 architecture)...")
    model.fit(X_train, y_train)
    print(f"      ✅ Converged after {model.n_iter_} iterations")
    
    return model


def train_ridge_baseline(X_train, y_train, alpha=1.0):
    """Train Ridge regression baseline."""
    from sklearn.linear_model import Ridge
    model = Ridge(alpha=alpha, random_state=42)
    model.fit(X_train, y_train)
    return model


def compute_metrics(y_true, y_pred):
    """Compute comprehensive metrics."""
    return {
        'r2': r2_score(y_true, y_pred),
        'mae': mean_absolute_error(y_true, y_pred),
        'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
        'mape': np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    }


def walk_forward_validation():
    """
    Walk-forward validation for Neural Network vs Ridge.
    
    Tests on October periods: 2021, 2022, 2023, 2024
    Horizons: 1, 2, 3 days
    """
    print("\n📊 Loading data...")
    gold = load_model_ready_dataset()
    print(f"✅ Loaded {len(gold):,} rows")
    
    # Test periods (October months)
    test_periods = [
        ("2021-10-01", "2021-10-31", "October 2021"),
        ("2022-10-01", "2022-10-31", "October 2022"),
        ("2023-10-01", "2023-10-31", "October 2023"),
        ("2024-10-01", "2024-10-31", "October 2024"),
    ]
    
    horizons = [1, 2, 3]
    
    results = []
    
    print("\n" + "="*80)
    print("WALK-FORWARD VALIDATION")
    print("="*80)
    
    for horizon in horizons:
        print(f"\n{'='*80}")
        print(f"HORIZON: {horizon} DAY{'S' if horizon > 1 else ''}")
        print(f"{'='*80}")
        
        # Prepare data with proper future targets
        print(f"  Preparing data (shifting target by {horizon} days)...")
        df_h = prepare_forecast_frame(gold, horizon=horizon)
        print(f"  ✅ Prepared {len(df_h):,} rows (target is {horizon}-day ahead price)")
        
        # Features
        available_features = [f for f in COMMON_FEATURES if f in df_h.columns]
        print(f"  ✅ Using {len(available_features)} features")
        
        for start, end, period_name in test_periods:
            print(f"\n  {'-'*76}")
            print(f"  Testing: {period_name}")
            print(f"  {'-'*76}")
            
            start_date = pd.to_datetime(start)
            end_date = pd.to_datetime(end)
            
            # Split train/test
            train_mask = df_h['date'] < start_date
            test_mask = (df_h['date'] >= start_date) & (df_h['date'] <= end_date)
            
            train_df = df_h[train_mask].copy()
            test_df = df_h[test_mask].copy()
            
            print(f"    Train samples: {len(train_df):,} (up to {start_date.date()})")
            print(f"    Test samples:  {len(test_df):,} ({start_date.date()} to {end_date.date()})")
            
            if len(train_df) < 100 or len(test_df) < 5:
                print(f"    ⚠️ Insufficient data, skipping...")
                continue
            
            # Prepare features and targets
            X_train = train_df[available_features].fillna(0).values
            y_train = train_df['target'].values
            X_test = test_df[available_features].fillna(0).values
            y_test = test_df['target'].values
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Split for validation
            val_size = int(0.2 * len(X_train_scaled))
            X_train_nn = X_train_scaled[:-val_size]
            y_train_nn = y_train[:-val_size]
            X_val_nn = X_train_scaled[-val_size:]
            y_val_nn = y_train[-val_size:]
            
            try:
                # Train Neural Network
                print(f"\n    🧠 Training Neural Network...")
                nn_model = train_neural_network(
                    X_train_nn, y_train_nn,
                    X_val_nn, y_val_nn
                )
                
                # NN predictions
                nn_preds = nn_model.predict(X_test_scaled)
                nn_metrics = compute_metrics(y_test, nn_preds)
                
                print(f"      Neural Network Results:")
                print(f"        R²:   {nn_metrics['r2']:.4f}")
                print(f"        MAE:  ${nn_metrics['mae']:.4f}")
                print(f"        RMSE: ${nn_metrics['rmse']:.4f}")
                
                nn_success = True
                
            except Exception as e:
                print(f"      ❌ Neural Network failed: {str(e)}")
                nn_metrics = {'r2': np.nan, 'mae': np.nan, 'rmse': np.nan, 'mape': np.nan}
                nn_success = False
            
            # Train Ridge baseline
            print(f"\n    📊 Training Ridge baseline (alpha=1.0)...")
            ridge_model = train_ridge_baseline(X_train_scaled, y_train, alpha=1.0)
            ridge_preds = ridge_model.predict(X_test_scaled)
            ridge_metrics = compute_metrics(y_test, ridge_preds)
            
            print(f"      Ridge Results:")
            print(f"        R²:   {ridge_metrics['r2']:.4f}")
            print(f"        MAE:  ${ridge_metrics['mae']:.4f}")
            print(f"        RMSE: ${ridge_metrics['rmse']:.4f}")
            
            # Compare
            if nn_success:
                diff = nn_metrics['r2'] - ridge_metrics['r2']
                if diff > 0.05:
                    print(f"\n      ✅ Neural Network wins! (+{diff:.4f} R²)")
                elif diff < -0.05:
                    print(f"\n      ⚠️ Ridge wins! ({diff:.4f} R²)")
                else:
                    print(f"\n      🤝 Similar performance (diff: {diff:.4f})")
            
            # Store results
            results.append({
                'period': period_name,
                'horizon': horizon,
                'train_size': len(train_df),
                'test_size': len(test_df),
                'nn_r2': nn_metrics['r2'],
                'nn_mae': nn_metrics['mae'],
                'nn_rmse': nn_metrics['rmse'],
                'ridge_r2': ridge_metrics['r2'],
                'ridge_mae': ridge_metrics['mae'],
                'ridge_rmse': ridge_metrics['rmse'],
                'winner': 'Neural Network' if nn_success and nn_metrics['r2'] > ridge_metrics['r2'] else 'Ridge'
            })
    
    return pd.DataFrame(results)


def create_visualizations(results_df):
    """Create comprehensive visualization comparing Neural Network and Ridge."""
    print("\n" + "="*80)
    print("CREATING VISUALIZATIONS")
    print("="*80)
    
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    # 1. R² by Period
    ax1 = fig.add_subplot(gs[0, 0])
    periods = results_df['period'].unique()
    x = np.arange(len(periods))
    width = 0.35
    
    for i, horizon in enumerate([1, 2, 3]):
        data = results_df[results_df['horizon'] == horizon]
        offset = (i - 1) * width
        ax1.bar(x + offset, data['ridge_r2'], width, 
               label=f'{horizon}d Ridge', alpha=0.8)
        ax1.bar(x + offset, data['nn_r2'] - data['ridge_r2'], width,
               bottom=data['ridge_r2'], label=f'{horizon}d NN (diff)', alpha=0.6)
    
    ax1.set_xlabel('Test Period', fontsize=12, fontweight='bold')
    ax1.set_ylabel('R² Score', fontsize=12, fontweight='bold')
    ax1.set_title('Model Performance by Period', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(periods, rotation=45, ha='right')
    ax1.legend(fontsize=9)
    ax1.grid(axis='y', alpha=0.3)
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    # 2. Average R² by Horizon
    ax2 = fig.add_subplot(gs[0, 1])
    avg_by_horizon = results_df.groupby('horizon').agg({
        'nn_r2': 'mean',
        'ridge_r2': 'mean'
    }).reset_index()
    
    x_h = avg_by_horizon['horizon']
    ax2.plot(x_h, avg_by_horizon['ridge_r2'], 'o-', linewidth=3, 
            markersize=10, label='Ridge', color='#3498db')
    ax2.plot(x_h, avg_by_horizon['nn_r2'], 's-', linewidth=3,
            markersize=10, label='Neural Network', color='#e74c3c')
    ax2.set_xlabel('Forecast Horizon (days)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Average R² Score', fontsize=12, fontweight='bold')
    ax2.set_title('Performance by Forecast Horizon', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks([1, 2, 3])
    
    # 3. MAE Comparison
    ax3 = fig.add_subplot(gs[1, 0])
    for i, horizon in enumerate([1, 2, 3]):
        data = results_df[results_df['horizon'] == horizon]
        offset = (i - 1) * width
        ax3.bar(x + offset, data['ridge_mae'], width,
               label=f'{horizon}d Ridge', alpha=0.8, color=f'C{i}')
        ax3.bar(x + offset, data['nn_mae'] - data['ridge_mae'], width,
               bottom=data['ridge_mae'], label=f'{horizon}d NN (diff)', alpha=0.6, color=f'C{i+3}')
    
    ax3.set_xlabel('Test Period', fontsize=12, fontweight='bold')
    ax3.set_ylabel('MAE ($)', fontsize=12, fontweight='bold')
    ax3.set_title('Mean Absolute Error by Period', fontsize=14, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(periods, rotation=45, ha='right')
    ax3.legend(fontsize=9, ncol=2)
    ax3.grid(axis='y', alpha=0.3)
    
    # 4. Win/Loss Summary
    ax4 = fig.add_subplot(gs[1, 1])
    win_counts = results_df['winner'].value_counts()
    colors = ['#27ae60' if w == 'Neural Network' else '#3498db' for w in win_counts.index]
    ax4.bar(win_counts.index, win_counts.values, color=colors, alpha=0.8)
    ax4.set_ylabel('Number of Wins', fontsize=12, fontweight='bold')
    ax4.set_title('Model Win Count (12 tests total)', fontsize=14, fontweight='bold')
    ax4.grid(axis='y', alpha=0.3)
    
    # Add count labels
    for i, (model, count) in enumerate(win_counts.items()):
        ax4.text(i, count + 0.3, str(count), ha='center', fontsize=14, fontweight='bold')
    
    # 5. Performance Distribution
    ax5 = fig.add_subplot(gs[2, :])
    
    all_ridge = results_df[['horizon', 'period', 'ridge_r2']].copy()
    all_ridge['model'] = 'Ridge'
    all_ridge.rename(columns={'ridge_r2': 'r2'}, inplace=True)
    
    all_nn = results_df[['horizon', 'period', 'nn_r2']].copy()
    all_nn['model'] = 'Neural Network'
    all_nn.rename(columns={'nn_r2': 'r2'}, inplace=True)
    
    combined = pd.concat([all_ridge, all_nn])
    
    sns.boxplot(data=combined, x='horizon', y='r2', hue='model', ax=ax5,
               palette={'Ridge': '#3498db', 'Neural Network': '#e74c3c'})
    ax5.set_xlabel('Forecast Horizon (days)', fontsize=12, fontweight='bold')
    ax5.set_ylabel('R² Score', fontsize=12, fontweight='bold')
    ax5.set_title('Performance Distribution Across All Tests', fontsize=14, fontweight='bold')
    ax5.legend(title='Model', fontsize=11)
    ax5.grid(axis='y', alpha=0.3)
    ax5.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    
    plt.suptitle('Neural Network vs Ridge: Walk-Forward Validation Results', 
                fontsize=16, fontweight='bold', y=0.995)
    
    output_path = OUTPUT_DIR / 'nn_vs_ridge_comparison.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved visualization: {output_path}")
    
    plt.close()


def main():
    """Main execution."""
    print("\n⚠️ NOTE: Using MLPRegressor (feedforward NN) instead of LSTM")
    print("Reason: TensorFlow has compatibility issues with Python 3.13 on macOS ARM")
    print("MLPRegressor provides similar comparison: simple vs complex models\n")
    
    # Run walk-forward validation
    results_df = walk_forward_validation()
    
    # Save results
    results_path = OUTPUT_DIR / 'nn_vs_ridge_results.csv'
    results_df.to_csv(results_path, index=False)
    print(f"\n✅ Saved results to: {results_path}")
    
    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    print("\n📊 Average Performance:")
    print("\nRidge:")
    print(f"  R²:   {results_df['ridge_r2'].mean():.4f} ± {results_df['ridge_r2'].std():.4f}")
    print(f"  MAE:  ${results_df['ridge_mae'].mean():.4f} ± ${results_df['ridge_mae'].std():.4f}")
    
    print("\nNeural Network:")
    valid_nn = results_df[results_df['nn_r2'].notna()]
    print(f"  R²:   {valid_nn['nn_r2'].mean():.4f} ± {valid_nn['nn_r2'].std():.4f}")
    print(f"  MAE:  ${valid_nn['nn_mae'].mean():.4f} ± ${valid_nn['nn_mae'].std():.4f}")
    
    print("\n🏆 Winner Breakdown:")
    print(results_df['winner'].value_counts())
    
    # Create visualizations
    create_visualizations(results_df)
    
    print("\n" + "="*80)
    print("✅ NEURAL NETWORK TESTING COMPLETE!")
    print("="*80)
    print(f"\n📁 All results saved to: {OUTPUT_DIR}")
    print("\n🎯 Key Finding:")
    ridge_wins = (results_df['winner'] == 'Ridge').sum()
    nn_wins = (results_df['winner'] == 'Neural Network').sum()
    if ridge_wins > nn_wins:
        print(f"   Ridge dominates! Wins {ridge_wins}/{len(results_df)} tests")
        print("   ✅ Simple linear models outperform neural networks for this task")
    else:
        print(f"   Neural Network competitive! Wins {nn_wins}/{len(results_df)} tests")
    print("="*80)


if __name__ == "__main__":
    main()
