"""
Setup Conformal Prediction with Fresh Ridge Model

This script:
1. Loads gold data
2. Handles missing values with median imputation
3. Trains a fresh Ridge model (60% train, 20% val)
4. Calibrates conformal predictor on recent 20% data
5. Evaluates coverage
6. Saves everything for daily prediction use
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.impute import SimpleImputer
from conformal_prediction import ConformalPredictor
import pickle
from pathlib import Path


def main():
    print('='*80)
    print('🚀 CREATING CONFORMAL PREDICTOR WITH FRESH RIDGE MODEL')
    print('='*80)
    print()
    
    # Load data
    print('Loading data...')
    df = pd.read_parquet('data/gold/master_model_ready.parquet')
    df = df.sort_values('date').reset_index(drop=True)
    
    # Prepare features
    target_col = 'target'
    feature_cols = [col for col in df.columns 
                   if col not in ['date', target_col] 
                   and df[col].dtype in ['float64', 'int64']]
    
    X = df[feature_cols].values
    y = df[target_col].values
    dates = df['date'].values
    
    print(f'Data loaded:')
    print(f'  Total samples: {len(X)}')
    print(f'  Features: {len(feature_cols)}')
    print(f'  Date range: {dates[0]} to {dates[-1]}')
    
    # Check for NaNs
    nan_count = np.isnan(X).sum()
    print(f'  NaN values: {nan_count}')
    print()
    
    # Impute NaNs
    print('Handling missing values...')
    imputer = SimpleImputer(strategy='median')
    X = imputer.fit_transform(X)
    nan_after = np.isnan(X).sum()
    print(f'  NaN values after imputation: {nan_after}')
    print()
    
    # Split: 60% train, 20% validation, 20% calibration
    n = len(X)
    n_train = int(n * 0.60)
    n_val = int(n * 0.20)
    n_cal = n - n_train - n_val
    
    X_train = X[:n_train]
    y_train = y[:n_train]
    X_val = X[n_train:n_train+n_val]
    y_val = y[n_train:n_train+n_val]
    X_cal = X[n_train+n_val:]
    y_cal = y[n_train+n_val:]
    
    print(f'Data split:')
    print(f'  Training:     {n_train} samples ({dates[0]} to {dates[n_train-1]})')
    print(f'  Validation:   {n_val} samples ({dates[n_train]} to {dates[n_train+n_val-1]})')
    print(f'  Calibration:  {n_cal} samples ({dates[n_train+n_val]} to {dates[-1]})')
    print()
    
    # Train Ridge model
    print('Training Ridge model...')
    ridge = Ridge(alpha=1.0)
    ridge.fit(X_train, y_train)
    
    # Evaluate on validation
    y_pred_val = ridge.predict(X_val)
    r2_val = 1 - np.sum((y_val - y_pred_val)**2) / np.sum((y_val - np.mean(y_val))**2)
    mae_val = np.mean(np.abs(y_val - y_pred_val))
    
    print(f'✅ Ridge model trained!')
    print(f'Validation performance:')
    print(f'  R²:  {r2_val:.4f}')
    print(f'  MAE: ${mae_val:.4f}')
    print()
    
    # Create and calibrate conformal predictor
    print(f'Calibrating conformal predictor on {n_cal} samples...')
    print()
    cp = ConformalPredictor(model=ridge, alpha=0.05, method='absolute')
    cp.calibrate(X_cal, y_cal, verbose=True)
    
    # Evaluate coverage on calibration set
    metrics = cp.evaluate_coverage(X_cal, y_cal, verbose=True)
    
    # Save everything
    Path('outputs/conformal').mkdir(parents=True, exist_ok=True)
    
    # Save imputer (needed for prediction!)
    with open('outputs/conformal/imputer.pkl', 'wb') as f:
        pickle.dump(imputer, f)
    print('✅ Imputer saved to: outputs/conformal/imputer.pkl')
    
    # Save Ridge model
    with open('outputs/conformal/ridge_model.pkl', 'wb') as f:
        pickle.dump(ridge, f)
    print('✅ Ridge model saved to: outputs/conformal/ridge_model.pkl')
    
    # Save feature columns (critical for alignment!)
    with open('outputs/conformal/feature_cols.pkl', 'wb') as f:
        pickle.dump(feature_cols, f)
    print('✅ Feature columns saved to: outputs/conformal/feature_cols.pkl')
    
    # Save conformal predictor
    cp.save('outputs/conformal/conformal_ridge.pkl')
    
    print()
    print('='*80)
    print('✅ SUCCESS! CONFORMAL PREDICTION FULLY CALIBRATED')
    print('='*80)
    print()
    print(f'Summary:')
    print(f'  Calibration set: {n_cal} samples (Oct 2024 - Oct 2025)')
    print(f'  Target coverage: 95.0%')
    print(f'  Empirical coverage: {metrics["coverage"]*100:.1f}%')
    print(f'  Interval width: ${metrics["mean_interval_width"]:.4f}')
    print()
    print('Files created:')
    print('  - outputs/conformal/imputer.pkl')
    print('  - outputs/conformal/ridge_model.pkl')
    print('  - outputs/conformal/feature_cols.pkl')
    print('  - outputs/conformal/conformal_ridge.pkl')
    print()
    print('Next steps:')
    print('  1. Integrate into daily_prediction.py')
    print('  2. Compare conformal vs Bayesian intervals')
    print('  3. Collect data Oct 20-29 for paper')
    print()


if __name__ == '__main__':
    main()
