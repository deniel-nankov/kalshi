"""
Predict gasoline prices for remainder of October 2025.

This script trains on ALL available historical data (2020-2024)
and generates forecasts for the remaining days of October 2025.
Uses Ridge regression (best performing model for 1-3 day forecasts).
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score

SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.baseline_models import COMMON_FEATURES, load_model_ready_dataset, prepare_forecast_frame


def train_final_model(df, horizon=1):
    """
    Train Ridge model on ALL historical data for October 2025 predictions.
    
    Args:
        df: Full dataset
        horizon: Forecast horizon (1, 2, or 3 days)
    
    Returns:
        model: Trained Ridge model
        train_data: Training data used
        test_data: October 2025 data for predictions
    """
    print(f"\n{'='*80}")
    print(f"🎯 TRAINING FINAL MODEL FOR OCTOBER 2025 PREDICTIONS")
    print(f"{'='*80}")
    print(f"Forecast horizon: {horizon} day(s) ahead")
    print(f"Today's date: {datetime.now().strftime('%Y-%m-%d')}")
    
    # Prepare forecast frame
    df_h = prepare_forecast_frame(df, horizon)
    
    # Split: Train on everything BEFORE October 2025, Test on October 2025
    oct_2025_start = pd.Timestamp('2025-10-01')
    oct_2025_end = pd.Timestamp('2025-10-31')
    
    train_mask = df_h['target_date'] < oct_2025_start
    test_mask = (df_h['target_date'] >= oct_2025_start) & (df_h['target_date'] <= oct_2025_end)
    
    train_df = df_h.loc[train_mask].copy()
    test_df = df_h.loc[test_mask].copy()
    
    print(f"\n📊 Data Split:")
    print(f"   Training: {len(train_df)} samples ({train_df['date'].min()} to {train_df['date'].max()})")
    print(f"   October 2025: {len(test_df)} samples ({test_df['date'].min()} to {test_df['date'].max()})")
    
    # Train Ridge model
    X_train = train_df[COMMON_FEATURES]
    y_train = train_df['target']
    X_test = test_df[COMMON_FEATURES]
    y_test = test_df['target']
    
    # Fill NaN values (sentiment features may be missing for recent dates)
    X_train = X_train.fillna(0)
    X_test = X_test.fillna(0)
    
    print(f"\n🏋️ Training Ridge model...")
    print(f"   Features: {len(COMMON_FEATURES)}")
    print(f"   Alpha: 1.0 (L2 regularization)")
    
    model = Ridge(alpha=1.0, random_state=42)
    model.fit(X_train, y_train)
    
    print(f"   ✅ Model trained!")
    
    return model, train_df, test_df, X_test, y_test


def generate_predictions(model, test_df, X_test, y_test, horizon):
    """Generate and display predictions."""
    
    print(f"\n{'='*80}")
    print(f"📈 OCTOBER 2025 PREDICTIONS ({horizon}-DAY HORIZON)")
    print(f"{'='*80}")
    
    predictions = model.predict(X_test)
    
    # Create results dataframe
    results = pd.DataFrame({
        'forecast_date': test_df['date'].values,  # When forecast is made
        'target_date': test_df['target_date'].values,  # Date being predicted
        'actual_price': y_test.values,
        'predicted_price': predictions,
        'error': predictions - y_test.values,
        'abs_error': np.abs(predictions - y_test.values),
        'pct_error': np.abs((predictions - y_test.values) / y_test.values) * 100
    })
    
    # Calculate metrics
    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(np.mean((y_test - predictions)**2))
    mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100
    r2 = r2_score(y_test, predictions)
    
    print(f"\n📊 PERFORMANCE METRICS:")
    print(f"   R² Score: {r2:.4f} ({r2*100:.2f}% variance explained)")
    print(f"   MAE: ${mae:.4f} ({mae*100:.2f} cents)")
    print(f"   RMSE: ${rmse:.4f}")
    print(f"   MAPE: {mape:.2f}%")
    
    # Show predictions
    today = pd.Timestamp.now().date()
    
    print(f"\n📅 DETAILED PREDICTIONS:")
    print(f"{'Date':<12} {'Actual':<10} {'Predicted':<10} {'Error':<10} {'Status'}")
    print("-" * 70)
    
    # Use itertuples() for better performance (5-10x faster than iterrows)
    for row in results.itertuples(index=False):
        target_date = row.target_date.date()
        actual = f"${row.actual_price:.4f}"
        predicted = f"${row.predicted_price:.4f}"
        error = f"${row.error:.4f}"
        
        # Check if this is a future date
        if target_date > today:
            status = "🔮 FUTURE"
            actual = "???"
        elif target_date == today:
            status = "📍 TODAY"
        else:
            status = "✅ PAST"
        
        print(f"{target_date} {actual:<10} {predicted:<10} {error:<10} {status}")
    
    # Highlight future predictions
    future_preds = results[pd.to_datetime(results['target_date']).dt.date > today]
    
    if len(future_preds) > 0:
        print(f"\n{'='*80}")
        print(f"🔮 ACTIONABLE FORECASTS (Future dates only):")
        print(f"{'='*80}")
        
        # Use itertuples() for better performance (5-10x faster than iterrows)
        for row in future_preds.itertuples(index=False):
            target_date = row.target_date.date()
            days_ahead = (target_date - today).days
            predicted = row.predicted_price
            
            print(f"\n📅 {target_date} ({days_ahead} day{'s' if days_ahead > 1 else ''} from today):")
            print(f"   Predicted price: ${predicted:.4f}")
            print(f"   Confidence: Based on R²={r2:.4f} from historical validation")
    else:
        print(f"\n⚠️ No future dates in October 2025 to predict")
        print(f"   All October 2025 dates have already occurred")
    
    return results, {'r2': r2, 'mae': mae, 'rmse': rmse, 'mape': mape}


def create_forecast_plot(results, horizon, metrics, output_dir):
    """Create visualization of predictions."""
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # Plot 1: Actual vs Predicted
    ax1 = axes[0]
    today = pd.Timestamp.now().date()
    
    # Past data
    past_mask = pd.to_datetime(results['target_date']).dt.date <= today
    future_mask = pd.to_datetime(results['target_date']).dt.date > today
    
    if past_mask.any():
        past_data = results[past_mask]
        ax1.plot(past_data['target_date'], past_data['actual_price'], 
                'o-', color='steelblue', linewidth=2, markersize=6, label='Actual Price')
        ax1.plot(past_data['target_date'], past_data['predicted_price'], 
                's--', color='coral', linewidth=1.5, markersize=5, label='Predicted Price')
    
    # Future predictions
    if future_mask.any():
        future_data = results[future_mask]
        ax1.plot(future_data['target_date'], future_data['predicted_price'], 
                'D--', color='green', linewidth=2, markersize=7, label='Future Forecast', alpha=0.7)
    
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Price ($/gallon)', fontsize=12)
    ax1.set_title(f'October 2025 Gasoline Price Forecasts ({horizon}-Day Horizon)\n' + 
                  f'R²={metrics["r2"]:.4f}, MAE=${metrics["mae"]:.4f}', 
                  fontsize=14, fontweight='bold')
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(alpha=0.3)
    ax1.tick_params(axis='x', rotation=45)
    
    # Plot 2: Prediction Errors
    ax2 = axes[1]
    if past_mask.any():
        past_data = results[past_mask]
        colors = ['green' if abs(e) < 0.02 else 'orange' if abs(e) < 0.05 else 'red' 
                  for e in past_data['error']]
        ax2.bar(past_data['target_date'], past_data['error'], color=colors, alpha=0.7)
    
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Prediction Error ($/gallon)', fontsize=12)
    ax2.set_title('Prediction Errors (Actual - Predicted)', fontsize=12, fontweight='bold')
    ax2.grid(alpha=0.3)
    ax2.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    output_file = output_dir / f'october_2025_forecast_h{horizon}.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\n📊 Forecast plot saved: {output_file}")


def main():
    """Main execution."""
    
    # Load data
    data_path = Path(__file__).resolve().parents[1] / "data" / "gold" / "master_model_ready.parquet"
    df = load_model_ready_dataset(data_path)
    
    print(f"\n{'='*80}")
    print(f"🚀 OCTOBER 2025 GASOLINE PRICE FORECASTING")
    print(f"{'='*80}")
    print(f"Dataset: {len(df)} rows, {len(df.columns)} features")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    
    sentiment_cols = [c for c in df.columns if 'sentiment' in c.lower() or 'news_' in c.lower()]
    print(f"Sentiment features: {len(sentiment_cols)}")
    
    # Create output directory
    output_dir = Path(__file__).resolve().parents[1] / "outputs" / "october_2025_forecast"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test multiple horizons
    all_results = {}
    
    for horizon in [1, 2, 3]:
        print(f"\n\n{'#'*80}")
        print(f"# HORIZON: {horizon} DAY{'S' if horizon > 1 else ''}")
        print(f"{'#'*80}")
        
        # Train model
        model, train_df, test_df, X_test, y_test = train_final_model(df, horizon)
        
        # Generate predictions
        results, metrics = generate_predictions(model, test_df, X_test, y_test, horizon)
        
        # Create visualization
        create_forecast_plot(results, horizon, metrics, output_dir)
        
        # Save results
        results_file = output_dir / f'predictions_h{horizon}.csv'
        results.to_csv(results_file, index=False)
        print(f"💾 Predictions saved: {results_file}")
        
        all_results[horizon] = {'results': results, 'metrics': metrics, 'model': model}
    
    # Summary comparison
    print(f"\n\n{'='*80}")
    print(f"📊 SUMMARY: BEST HORIZON FOR TRADING")
    print(f"{'='*80}")
    
    summary_data = []
    for h, data in all_results.items():
        summary_data.append({
            'Horizon': f'{h} day{"s" if h > 1 else ""}',
            'R²': data['metrics']['r2'],
            'MAE': data['metrics']['mae'],
            'MAPE': data['metrics']['mape']
        })
    
    summary_df = pd.DataFrame(summary_data)
    print("\n" + summary_df.to_string(index=False))
    
    # Recommendation
    best_horizon = max(all_results.items(), key=lambda x: x[1]['metrics']['r2'])[0]
    best_r2 = all_results[best_horizon]['metrics']['r2']
    best_mae = all_results[best_horizon]['metrics']['mae']
    
    print(f"\n{'='*80}")
    print(f"🏆 RECOMMENDATION:")
    print(f"{'='*80}")
    print(f"Best performing horizon: {best_horizon} day{'s' if best_horizon > 1 else ''}")
    print(f"   R² = {best_r2:.4f} ({best_r2*100:.2f}% variance explained)")
    print(f"   MAE = ${best_mae:.4f} ({best_mae*100:.2f} cents)")
    print(f"\n✅ Use this for Kalshi trading decisions!")
    
    print(f"\n{'='*80}")
    print(f"✅ FORECASTING COMPLETE")
    print(f"{'='*80}")
    print(f"Results saved to: {output_dir}")


if __name__ == "__main__":
    main()
