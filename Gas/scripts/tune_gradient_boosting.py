"""
Hyperparameter tuning for Gradient Boosting model using grid search.

This script performs a comprehensive grid search over key GB hyperparameters:
- learning_rate: Controls step size for each tree
- max_depth: Maximum depth of individual trees
- max_iter: Number of boosting iterations (trees)
- min_samples_leaf: Minimum samples required in leaf nodes

Expected improvement: +2-5% R² over baseline GB (R²=0.2142)
Target: R² = 0.22-0.25
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from itertools import product

import joblib
import numpy as np
import pandas as pd
from sklearn.experimental import enable_hist_gradient_boosting  # noqa: F401
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.baseline_models import (
    COMMON_FEATURES,
    DEFAULT_DATA_PATH,
    load_model_ready_dataset,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hyperparameter tuning for Gradient Boosting"
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help="Path to Gold model-ready dataset",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=14,
        help="Forecast horizon in days",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "models",
        help="Directory to save tuned model",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Use smaller parameter grid for faster tuning",
    )
    return parser.parse_args()


def tune_gradient_boosting(
    df: pd.DataFrame,
    features: list[str],
    target_col: str,
    horizon: int,
    param_grid: dict,
    split_date: str = "2024-10-01",
    n_splits: int = 5,
) -> dict:
    """
    Tune Gradient Boosting hyperparameters using time series cross-validation.
    
    Args:
        df: Gold dataset
        features: Feature names
        target_col: Target column
        horizon: Forecast horizon
        param_grid: Parameter grid to search
        split_date: Train/test split date
        n_splits: Number of CV folds
        
    Returns:
        Dictionary with best model, parameters, and results
    """
    print(f"\n{'='*80}")
    print(f"Gradient Boosting Hyperparameter Tuning")
    print(f"{'='*80}")
    print(f"Features: {len(features)}")
    print(f"Horizon: {horizon} days")
    print(f"CV folds: {n_splits}")
    
    # Prepare data
    df_sorted = df.sort_index()
    
    # Ensure index is datetime
    if 'date' in df_sorted.columns:
        df_sorted = df_sorted.set_index('date')
    df_sorted.index = pd.to_datetime(df_sorted.index)
    
    df_shifted = df_sorted[features + [target_col]].shift(-horizon)
    df_ready = pd.concat([df_sorted[features], df_shifted[[target_col]]], axis=1)
    df_ready = df_ready.dropna(subset=[target_col])
    
    # Train/test split
    split_date = pd.Timestamp(split_date)
    train = df_ready[df_ready.index < split_date]
    test = df_ready[df_ready.index >= split_date]
    
    X_train = train[features]
    y_train = train[target_col]
    X_test = test[features]
    y_test = test[target_col]
    
    print(f"\nTrain samples: {len(X_train):,}")
    print(f"Test samples: {len(X_test):,}")
    
    # Generate parameter combinations
    param_names = list(param_grid.keys())
    param_values = [param_grid[name] for name in param_names]
    param_combinations = list(product(*param_values))
    
    print(f"\nParameter grid:")
    for name, values in param_grid.items():
        print(f"  {name}: {values}")
    print(f"\nTotal combinations: {len(param_combinations)}")
    
    # Grid search with time series CV
    tscv = TimeSeriesSplit(n_splits=n_splits)
    
    results = []
    best_score = -np.inf
    best_params = None
    
    print(f"\n{'#':>4} {'LR':>6} {'Depth':>6} {'Iters':>6} {'MinLeaf':>8} {'CV R²':>10} {'Std':>8} {'Time':>6}")
    print("-" * 62)
    
    import time
    
    for i, param_vals in enumerate(param_combinations, 1):
        params = dict(zip(param_names, param_vals))
        
        start_time = time.time()
        cv_scores = []
        
        for train_idx, val_idx in tscv.split(X_train):
            X_cv_train, X_cv_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
            y_cv_train, y_cv_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
            
            # Build pipeline
            pipe = Pipeline([
                ('imputer', SimpleImputer(strategy='mean')),
                ('scaler', StandardScaler()),
                ('gb', HistGradientBoostingRegressor(
                    random_state=42,
                    **params
                ))
            ])
            
            pipe.fit(X_cv_train, y_cv_train)
            y_pred = pipe.predict(X_cv_val)
            score = r2_score(y_cv_val, y_pred)
            cv_scores.append(score)
        
        elapsed = time.time() - start_time
        mean_score = np.mean(cv_scores)
        std_score = np.std(cv_scores)
        
        print(f"{i:>4} {params['learning_rate']:>6.3f} {params['max_depth']:>6} "
              f"{params['max_iter']:>6} {params.get('min_samples_leaf', 20):>8} "
              f"{mean_score:>10.6f} {std_score:>8.6f} {elapsed:>6.1f}s")
        
        results.append({
            'params': params,
            'mean_cv_score': mean_score,
            'std_cv_score': std_score,
            'all_cv_scores': cv_scores,
            'elapsed_time': elapsed,
        })
        
        if mean_score > best_score:
            best_score = mean_score
            best_params = params
    
    print(f"\n{'='*80}")
    print(f"✅ Best parameters found (CV R² = {best_score:.6f}):")
    for name, value in best_params.items():
        print(f"  {name}: {value}")
    
    # Train final model with best parameters
    print(f"\nTraining final model with best parameters...")
    
    model = Pipeline([
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', StandardScaler()),
        ('gb', HistGradientBoostingRegressor(
            random_state=42,
            **best_params
        ))
    ])
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    train_metrics = {
        'r2': r2_score(y_train, y_train_pred),
        'rmse': np.sqrt(mean_squared_error(y_train, y_train_pred)),
        'mae': mean_absolute_error(y_train, y_train_pred),
    }
    
    test_metrics = {
        'r2': r2_score(y_test, y_test_pred),
        'rmse': np.sqrt(mean_squared_error(y_test, y_test_pred)),
        'mae': mean_absolute_error(y_test, y_test_pred),
    }
    
    print(f"\n{'Metric':<12} {'Train':>12} {'Test':>12}")
    print("-" * 38)
    print(f"{'R²':<12} {train_metrics['r2']:>12.6f} {test_metrics['r2']:>12.6f}")
    print(f"{'RMSE':<12} ${train_metrics['rmse']:>11.5f} ${test_metrics['rmse']:>11.5f}")
    print(f"{'MAE':<12} ${train_metrics['mae']:>11.5f} ${test_metrics['mae']:>11.5f}")
    
    # Create predictions dataframe
    predictions_df = pd.DataFrame({
        'date': test.index,
        'actual': y_test.values,
        'predicted': y_test_pred,
        'residual': y_test.values - y_test_pred,
    })
    
    return {
        'model': model,
        'best_params': best_params,
        'best_cv_score': best_score,
        'train_metrics': train_metrics,
        'test_metrics': test_metrics,
        'all_results': results,
        'predictions': predictions_df,
    }


def main():
    args = parse_args()
    
    print("="*80)
    print("Gradient Boosting Hyperparameter Tuning")
    print("="*80)
    
    # Define parameter grid
    if args.quick:
        # Quick grid for testing
        param_grid = {
            'learning_rate': [0.05, 0.10],
            'max_depth': [3, 4],
            'max_iter': [400, 600],
            'min_samples_leaf': [15, 20],
        }
    else:
        # Full grid for thorough search
        param_grid = {
            'learning_rate': [0.01, 0.05, 0.10],
            'max_depth': [3, 4, 5],
            'max_iter': [400, 600, 800],
            'min_samples_leaf': [10, 15, 20],
        }
    
    # Load data
    print(f"\nLoading data from: {args.data_path}")
    df = load_model_ready_dataset(args.data_path)
    print(f"Loaded {len(df):,} rows")
    
    # Run tuning
    result = tune_gradient_boosting(
        df=df,
        features=COMMON_FEATURES,
        target_col="target",
        horizon=args.horizon,
        param_grid=param_grid,
    )
    
    # Save tuned model
    args.output_dir.mkdir(parents=True, exist_ok=True)
    model_path = args.output_dir / "gradient_boosting_tuned_model.joblib"
    joblib.dump(result['model'], model_path)
    print(f"\n✅ Saved tuned model: {model_path}")
    
    # Save metrics
    metrics_dict = {
        'model_name': 'gradient_boosting_tuned',
        'n_features': len(COMMON_FEATURES),
        'horizon_days': args.horizon,
        'best_params': result['best_params'],
        'best_cv_r2': result['best_cv_score'],
        'train_r2': result['train_metrics']['r2'],
        'train_rmse': result['train_metrics']['rmse'],
        'train_mae': result['train_metrics']['mae'],
        'test_r2': result['test_metrics']['r2'],
        'test_rmse': result['test_metrics']['rmse'],
        'test_mae': result['test_metrics']['mae'],
    }
    
    metrics_path = args.output_dir / "gradient_boosting_tuned_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics_dict, f, indent=2)
    print(f"✅ Saved metrics: {metrics_path}")
    
    # Save all tuning results
    results_df = pd.DataFrame([
        {
            **r['params'],
            'mean_cv_r2': r['mean_cv_score'],
            'std_cv_r2': r['std_cv_score'],
            'time_seconds': r['elapsed_time'],
        }
        for r in result['all_results']
    ])
    results_df = results_df.sort_values('mean_cv_r2', ascending=False)
    
    results_path = args.output_dir / "gradient_boosting_tuning_results.csv"
    results_df.to_csv(results_path, index=False)
    print(f"✅ Saved tuning results: {results_path}")
    
    # Save predictions
    pred_path = args.output_dir / "gradient_boosting_tuned_predictions.csv"
    result['predictions'].to_csv(pred_path, index=False)
    print(f"✅ Saved predictions: {pred_path}")
    
    print("\n" + "="*80)
    print("✅ Hyperparameter Tuning Complete!")
    print("="*80)
    print(f"\nBest Test Performance:")
    print(f"  R² = {result['test_metrics']['r2']:.4f}")
    print(f"  RMSE = ${result['test_metrics']['rmse']:.5f}")
    print(f"  MAE = ${result['test_metrics']['mae']:.5f}")
    print(f"\nComparison to Baseline GB:")
    print(f"  Baseline R² = 0.2142")
    print(f"  Improvement: {(result['test_metrics']['r2'] - 0.2142) / 0.2142 * 100:+.1f}%")
    
    print(f"\nTop 5 Parameter Combinations:")
    print(results_df.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
