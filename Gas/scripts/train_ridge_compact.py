"""
Train Ridge regression model with compact feature set (45 features).

This script trains Ridge regression using only the top 45 features identified
through feature importance analysis to reduce multicollinearity and overfitting.

Expected improvement: Ridge R² from 0.21 → 0.35-0.45
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.baseline_models import (
    COMMON_FEATURES_COMPACT,
    DEFAULT_DATA_PATH,
    RIDGE_ALPHA_GRID,
    load_model_ready_dataset,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train Ridge regression with compact feature set"
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
        help="Forecast horizon in days (default: 14 for Oct 31 predictions)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "models",
        help="Directory to save trained model",
    )
    return parser.parse_args()


def train_ridge_compact(
    df: pd.DataFrame,
    features: list[str],
    target_col: str,
    horizon: int,
    alpha_grid: list[float],
    split_date: str = "2024-10-01",
) -> dict:
    """
    Train Ridge regression with compact feature set using time series CV.
    
    Args:
        df: Gold dataset with features and target
        features: List of feature names (compact set)
        target_col: Target column name
        horizon: Forecast horizon in days
        alpha_grid: Alpha values to search
        split_date: Train/test split date
        
    Returns:
        Dictionary with model, metrics, best alpha, predictions
    """
    print(f"\n{'='*80}")
    print(f"Training Ridge Regression (Compact Feature Set)")
    print(f"{'='*80}")
    print(f"Features: {len(features)} (vs 76 in full set)")
    print(f"Horizon: {horizon} days")
    print(f"Alpha grid: {alpha_grid}")
    
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
    
    print(f"\nTrain samples: {len(X_train):,} ({X_train.index[0]} to {X_train.index[-1]})")
    print(f"Test samples:  {len(X_test):,} ({X_test.index[0]} to {X_test.index[-1]})")
    
    # Cross-validation for alpha selection
    tscv = TimeSeriesSplit(n_splits=5)
    best_alpha = None
    best_cv_score = -np.inf
    
    print(f"\n{'Alpha':>8} {'CV R² Mean':>12} {'CV R² Std':>10}")
    print("-" * 32)
    
    for alpha in alpha_grid:
        cv_scores = []
        
        for train_idx, val_idx in tscv.split(X_train):
            X_cv_train, X_cv_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
            y_cv_train, y_cv_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
            
            # Build pipeline
            pipe = Pipeline([
                ('imputer', SimpleImputer(strategy='mean')),
                ('scaler', StandardScaler()),
                ('ridge', Ridge(alpha=alpha, random_state=42))
            ])
            
            pipe.fit(X_cv_train, y_cv_train)
            y_pred = pipe.predict(X_cv_val)
            score = r2_score(y_cv_val, y_pred)
            cv_scores.append(score)
        
        mean_score = np.mean(cv_scores)
        std_score = np.std(cv_scores)
        
        print(f"{alpha:>8.2f} {mean_score:>12.6f} {std_score:>10.6f}")
        
        if mean_score > best_cv_score:
            best_cv_score = mean_score
            best_alpha = alpha
    
    print(f"\n✅ Best alpha: {best_alpha} (CV R² = {best_cv_score:.6f})")
    
    # Train final model with best alpha
    print(f"\nTraining final model with alpha={best_alpha}...")
    
    model = Pipeline([
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', StandardScaler()),
        ('ridge', Ridge(alpha=best_alpha, random_state=42))
    ])
    
    model.fit(X_train, y_train)
    
    # Evaluate on train and test sets
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
        'train_metrics': train_metrics,
        'test_metrics': test_metrics,
        'best_alpha': best_alpha,
        'cv_score': best_cv_score,
        'predictions': predictions_df,
        'features': features,
        'horizon': horizon,
    }


def main():
    args = parse_args()
    
    print("="*80)
    print("Ridge Regression Training - Compact Feature Set (45 features)")
    print("="*80)
    
    # Load data
    print(f"\nLoading data from: {args.data_path}")
    df = load_model_ready_dataset(args.data_path)
    print(f"Loaded {len(df):,} rows")
    
    # Verify all features exist
    missing = [f for f in COMMON_FEATURES_COMPACT if f not in df.columns]
    if missing:
        raise ValueError(f"Missing features in dataset: {missing}")
    
    # Train model
    result = train_ridge_compact(
        df=df,
        features=COMMON_FEATURES_COMPACT,
        target_col="target",
        horizon=args.horizon,
        alpha_grid=RIDGE_ALPHA_GRID,
    )
    
    # Save model
    args.output_dir.mkdir(parents=True, exist_ok=True)
    model_path = args.output_dir / "ridge_compact_model.joblib"
    joblib.dump(result['model'], model_path)
    print(f"\n✅ Saved model: {model_path}")
    
    # Save metrics
    metrics_dict = {
        'model_name': 'ridge_compact',
        'n_features': len(result['features']),
        'horizon_days': result['horizon'],
        'best_alpha': result['best_alpha'],
        'cv_r2': result['cv_score'],
        'train_r2': result['train_metrics']['r2'],
        'train_rmse': result['train_metrics']['rmse'],
        'train_mae': result['train_metrics']['mae'],
        'test_r2': result['test_metrics']['r2'],
        'test_rmse': result['test_metrics']['rmse'],
        'test_mae': result['test_metrics']['mae'],
    }
    
    metrics_path = args.output_dir / "ridge_compact_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics_dict, f, indent=2)
    print(f"✅ Saved metrics: {metrics_path}")
    
    # Save predictions
    pred_path = args.output_dir / "ridge_compact_predictions.csv"
    result['predictions'].to_csv(pred_path, index=False)
    print(f"✅ Saved predictions: {pred_path}")
    
    # Save feature list
    features_path = args.output_dir / "ridge_compact_features.txt"
    with open(features_path, 'w') as f:
        f.write(f"# Ridge Compact Feature Set ({len(result['features'])} features)\n")
        f.write(f"# Horizon: {result['horizon']} days\n")
        f.write(f"# Best alpha: {result['best_alpha']}\n\n")
        for i, feat in enumerate(result['features'], 1):
            f.write(f"{i:2d}. {feat}\n")
    print(f"✅ Saved features: {features_path}")
    
    print("\n" + "="*80)
    print("✅ Ridge Compact Training Complete!")
    print("="*80)
    print(f"\nTest Performance:")
    print(f"  R² = {result['test_metrics']['r2']:.4f}")
    print(f"  RMSE = ${result['test_metrics']['rmse']:.5f}")
    print(f"  MAE = ${result['test_metrics']['mae']:.5f}")
    print(f"\nComparison to Full Ridge (76 features):")
    print(f"  Previous R² = 0.2073")
    print(f"  Expected improvement: +0.14 to +0.24 R² (target: 0.35-0.45)")


if __name__ == "__main__":
    main()
