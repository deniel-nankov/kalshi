"""
Generate October 31, 2025 production forecast using best model.

This script:
1. Loads the latest gold dataset
2. Selects the best performing model (Gradient Boosting R²=0.2142)
3. Generates 14-day ahead forecast for October 31, 2025
4. Provides confidence intervals and trading recommendations
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timedelta

import joblib
import numpy as np
import pandas as pd

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.baseline_models import COMMON_FEATURES, COMMON_FEATURES_COMPACT, load_model_ready_dataset


def main():
    print("="*80)
    print("October 31, 2025 Production Forecast")
    print("="*80)
    
    # Load data
    data_path = Path(__file__).resolve().parents[1] / "data" / "gold" / "master_model_ready.parquet"
    print(f"\nLoading data from: {data_path}")
    df = load_model_ready_dataset(data_path)
    
    # Set date as index for easier date-based lookups
    df = df.set_index('date')
    
    print(f"Loaded {len(df):,} rows")
    print(f"Date range: {df.index[0].date()} to {df.index[-1].date()}")
    
    # Target date
    target_date = pd.Timestamp("2025-10-31")
    forecast_from_date = target_date - timedelta(days=14)
    
    print(f"\nTarget date: {target_date.date()}")
    print(f"Forecast from: {forecast_from_date.date()} (14 days ahead)")
    
    # Find the closest date in our dataset
    df.index = pd.to_datetime(df.index)
    available_dates = df.index[df.index <= forecast_from_date]
    
    if len(available_dates) == 0:
        print(f"\n❌ Error: No data available before {forecast_from_date.date()}")
        print(f"   Latest available date: {df.index[-1].date()}")
        print(f"   Need to update data sources first!")
        return
    
    forecast_date = available_dates[-1]
    print(f"Using data from: {forecast_date.date()}")
    
    # Get features for forecast
    X_forecast_full = df.loc[[forecast_date], COMMON_FEATURES]
    X_forecast_compact = df.loc[[forecast_date], COMMON_FEATURES_COMPACT]
    
    print(f"\nFeature values on {forecast_date.date()}:")
    print(f"  retail_price_lag7: ${X_forecast_full['retail_price_lag7'].values[0]:.4f}")
    print(f"  price_rbob: ${X_forecast_full['price_rbob'].values[0]:.4f}")
    print(f"  inventory_mbbl: {X_forecast_full['inventory_mbbl'].values[0]:.1f} million barrels")
    print(f"  utilization_pct: {X_forecast_full['utilization_pct'].values[0]:.1f}%")
    print(f"  winter_blend_effect: {X_forecast_full['winter_blend_effect'].values[0]:.4f}")
    
    # Load models and generate predictions
    models_dir = Path(__file__).resolve().parents[1] / "outputs" / "models"
    
    print(f"\n{'='*80}")
    print("Model Predictions for October 31, 2025")
    print(f"{'='*80}")
    
    # Map models to their feature sets
    models_to_use = [
        ("Gradient Boosting (Best)", "gradient_boosting_model.joblib", X_forecast_full),
        ("Ridge Compact (45 features)", "ridge_compact_model.joblib", X_forecast_compact),
        ("Ridge Full (76 features)", "ridge_baseline_model.joblib", X_forecast_full),
    ]
    
    predictions = {}
    
    for model_name, model_file, X_features in models_to_use:
        model_path = models_dir / model_file
        
        if not model_path.exists():
            print(f"\n⚠️ {model_name}: Model file not found")
            continue
        
        model = joblib.load(model_path)
        
        # Make prediction
        pred = model.predict(X_features)[0]
        predictions[model_name] = pred
        
        print(f"\n{model_name}:")
        print(f"  Prediction: ${pred:.4f}/gallon")
    
    # Ensemble prediction (average of all models)
    if len(predictions) > 0:
        ensemble_pred = np.mean(list(predictions.values()))
        ensemble_std = np.std(list(predictions.values()))
        
        print(f"\n{'='*80}")
        print("Ensemble Forecast (Average of All Models)")
        print(f"{'='*80}")
        print(f"\n📊 Point Forecast: ${ensemble_pred:.4f}/gallon")
        print(f"   Model agreement (std): ${ensemble_std:.4f}")
        
        # Add uncertainty based on test MAE
        mae = 0.0374  # From best model (GB)
        lower_bound = ensemble_pred - 1.96 * mae
        upper_bound = ensemble_pred + 1.96 * mae
        
        print(f"\n📈 95% Confidence Interval:")
        print(f"   Lower: ${lower_bound:.4f}/gallon")
        print(f"   Upper: ${upper_bound:.4f}/gallon")
        print(f"   Width: ${upper_bound - lower_bound:.4f}")
        
        # Historical context
        recent_prices = df['target'].tail(30)
        print(f"\n📅 Recent Historical Context (last 30 days):")
        print(f"   Mean: ${recent_prices.mean():.4f}")
        print(f"   Min: ${recent_prices.min():.4f}")
        print(f"   Max: ${recent_prices.max():.4f}")
        print(f"   Current: ${df['target'].iloc[-1]:.4f} (as of {df.index[-1].date()})")
        
        # Trading recommendation
        current_price = df['target'].iloc[-1]
        predicted_change = ensemble_pred - current_price
        percent_change = (predicted_change / current_price) * 100
        
        print(f"\n{'='*80}")
        print("Kalshi Trading Recommendation")
        print(f"{'='*80}")
        print(f"\nCurrent Price (Oct {df.index[-1].day}): ${current_price:.4f}")
        print(f"Predicted Price (Oct 31): ${ensemble_pred:.4f}")
        print(f"Expected Change: ${predicted_change:+.4f} ({percent_change:+.2f}%)")
        
        if percent_change > 1:
            print(f"\n✅ BULLISH Signal: Price expected to INCREASE")
            print(f"   Recommendation: BUY 'Yes' on price increase markets")
        elif percent_change < -1:
            print(f"\n⚠️ BEARISH Signal: Price expected to DECREASE")
            print(f"   Recommendation: BUY 'No' on price increase markets")
        else:
            print(f"\n➖ NEUTRAL Signal: Price expected to remain stable")
            print(f"   Recommendation: AVOID or wait for more data")
        
        # Risk factors
        print(f"\n⚠️ Risk Factors:")
        print(f"   • Model uncertainty: ±${mae:.4f} MAE")
        print(f"   • Days until forecast: {(target_date - df.index[-1]).days}")
        print(f"   • Hurricane season: Active (check latest threats)")
        print(f"   • Inventory levels: {X_forecast_full['inventory_mbbl'].values[0]:.1f}M bbl")
        print(f"   • Refinery utilization: {X_forecast_full['utilization_pct'].values[0]:.1f}%")
        
        # Save forecast
        output_dir = Path(__file__).resolve().parents[1] / "outputs" / "forecasts"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        forecast_df = pd.DataFrame({
            'forecast_date': [target_date],
            'forecast_from': [forecast_date],
            'horizon_days': [14],
            'point_forecast': [ensemble_pred],
            'lower_95': [lower_bound],
            'upper_95': [upper_bound],
            'mae': [mae],
            'current_price': [current_price],
            'expected_change': [predicted_change],
            'expected_change_pct': [percent_change],
        })
        
        forecast_path = output_dir / "october_31_2025_forecast.csv"
        forecast_df.to_csv(forecast_path, index=False)
        print(f"\n✅ Saved forecast to: {forecast_path}")
        
        # Also save model predictions
        model_preds_df = pd.DataFrame({
            'model': list(predictions.keys()),
            'prediction': list(predictions.values()),
        })
        model_preds_path = output_dir / "october_31_2025_model_predictions.csv"
        model_preds_df.to_csv(model_preds_path, index=False)
        print(f"✅ Saved model predictions to: {model_preds_path}")
    
    print(f"\n{'='*80}")
    print("✅ Forecast Generation Complete!")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
