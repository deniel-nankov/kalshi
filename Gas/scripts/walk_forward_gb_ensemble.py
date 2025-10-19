"""
Walk-forward validation for Gradient Boosting and Ensemble models.

Focused on 2-3 day forecast horizons for October 30th deadline.
Tests non-linear models that can leverage sentiment features better than Ridge.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Dict, Iterable, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, r2_score


SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.baseline_models import (  # noqa: E402
    COMMON_FEATURES,
    load_model_ready_dataset,
    prepare_forecast_frame,
)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Compute standard regression metrics."""
    return {
        "rmse": np.sqrt(mean_squared_error(y_true, y_pred)),
        "mae": mean_absolute_error(y_true, y_pred),
        "mape_pct": mean_absolute_percentage_error(y_true, y_pred) * 100,
        "r2": r2_score(y_true, y_pred),
    }


def train_gradient_boosting(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    params: dict = None
) -> GradientBoostingRegressor:
    """Train Gradient Boosting model with optimal hyperparameters."""
    if params is None:
        # Best params from previous tuning
        params = {
            'n_estimators': 200,
            'max_depth': 5,
            'learning_rate': 0.1,
            'min_samples_split': 10,
            'min_samples_leaf': 4,
            'subsample': 0.8,
            'random_state': 42
        }
    
    model = GradientBoostingRegressor(**params)
    model.fit(X_train, y_train)
    return model


def train_ensemble(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    alpha: float = 1.0
) -> Tuple[Ridge, GradientBoostingRegressor, dict]:
    """Train ensemble of Ridge + GB with weighted combination."""
    ridge = Ridge(alpha=alpha, random_state=42)
    ridge.fit(X_train, y_train)
    
    gb = train_gradient_boosting(X_train, y_train)
    
    # Ensemble weights (from previous training: GB=0.7, Ridge=0.3)
    weights = {'ridge': 0.3, 'gb': 0.7}
    
    return ridge, gb, weights


def predict_ensemble(
    ridge: Ridge,
    gb: GradientBoostingRegressor,
    X_test: pd.DataFrame,
    weights: dict
) -> np.ndarray:
    """Generate weighted ensemble predictions."""
    ridge_pred = ridge.predict(X_test)
    gb_pred = gb.predict(X_test)
    return weights['ridge'] * ridge_pred + weights['gb'] * gb_pred


def walk_forward_forecasts(
    df: pd.DataFrame,
    horizons: Iterable[int],
    years: Iterable[int],
    output_dir: Path,
    models: List[str] = None
) -> Dict[str, pd.DataFrame]:
    """
    Perform walk-forward validation for multiple models and horizons.
    
    Args:
        df: Gold layer dataset
        horizons: Forecast horizons (e.g., [2, 3])
        years: Years to evaluate (e.g., [2021, 2022, 2023, 2024])
        output_dir: Where to save results
        models: Which models to test ['gb', 'ensemble', 'ridge']
    """
    if models is None:
        models = ['gb', 'ensemble']
    
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_records = []
    prediction_records = []

    print("\n" + "="*80)
    print("🎯 WALK-FORWARD VALIDATION: GB & ENSEMBLE MODELS")
    print("="*80)
    print(f"Dataset: {len(df)} rows")
    print(f"Horizons: {list(horizons)} days")
    print(f"Years: {list(years)}")
    print(f"Models: {models}")
    print(f"Features: {len(COMMON_FEATURES)}")
    print("="*80 + "\n")

    for horizon in horizons:
        print(f"\n📅 HORIZON: {horizon} days")
        print("-" * 60)
        
        df_h = prepare_forecast_frame(df, horizon)
        target_col = "target"
        horizon_dir = output_dir / f"horizon_{horizon}"
        horizon_dir.mkdir(parents=True, exist_ok=True)

        for year in years:
            print(f"\n  Year {year} October:")
            start = pd.Timestamp(f"{year}-10-01")
            end = pd.Timestamp(f"{year}-10-31")

            train_mask = df_h["target_date"] < start
            test_mask = (df_h["target_date"] >= start) & (df_h["target_date"] <= end)

            train_df = df_h.loc[train_mask].copy()
            test_df = df_h.loc[test_mask].copy()

            if len(train_df) < 200 or test_df.empty:
                print(f"    ⚠️ Skipping (train={len(train_df)}, test={len(test_df)})")
                continue

            X_train = train_df[COMMON_FEATURES]
            y_train = train_df[target_col]
            X_test = test_df[COMMON_FEATURES]
            y_test = test_df[target_col]

            print(f"    Train: {len(train_df)} samples")
            print(f"    Test: {len(test_df)} samples")

            # Test each model
            for model_name in models:
                if model_name == 'gb':
                    print(f"    Training Gradient Boosting...")
                    model = train_gradient_boosting(X_train, y_train)
                    preds = model.predict(X_test)
                    
                elif model_name == 'ensemble':
                    print(f"    Training Ensemble (Ridge + GB)...")
                    ridge, gb, weights = train_ensemble(X_train, y_train)
                    preds = predict_ensemble(ridge, gb, X_test, weights)
                    
                elif model_name == 'ridge':
                    print(f"    Training Ridge (baseline)...")
                    from sklearn.model_selection import TimeSeriesSplit
                    from sklearn.linear_model import RidgeCV
                    
                    # Simple cross-validation for alpha
                    alphas = [0.1, 1.0, 10.0, 100.0]
                    cv = TimeSeriesSplit(n_splits=5)
                    model = RidgeCV(alphas=alphas, cv=cv)
                    model.fit(X_train, y_train)
                    preds = model.predict(X_test)
                
                else:
                    print(f"    ⚠️ Unknown model: {model_name}")
                    continue

                # Compute metrics
                metrics = compute_metrics(y_test, preds)
                metrics.update({
                    "model": model_name,
                    "year": year,
                    "horizon": horizon,
                    "n_train": len(train_df),
                    "n_test": len(test_df),
                })
                metrics_records.append(metrics)

                print(f"      {model_name.upper()}: R²={metrics['r2']:.4f}, MAE=${metrics['mae']:.4f}, MAPE={metrics['mape_pct']:.2f}%")

                # Store predictions
                for as_of_date, target_date, actual, pred in zip(
                    test_df["date"],
                    test_df["target_date"],
                    y_test,
                    preds,
                ):
                    prediction_records.append({
                        "model": model_name,
                        "horizon": horizon,
                        "year": year,
                        "as_of_date": as_of_date,
                        "target_date": target_date,
                        "actual": actual,
                        "prediction": pred,
                    })

    # Save results
    metrics_df = pd.DataFrame(metrics_records)
    predictions_df = pd.DataFrame(prediction_records)
    
    metrics_df.to_csv(output_dir / "walk_forward_gb_ensemble_metrics.csv", index=False)
    predictions_df.to_csv(output_dir / "walk_forward_gb_ensemble_predictions.csv", index=False)

    print("\n" + "="*80)
    print("✅ WALK-FORWARD VALIDATION COMPLETE")
    print("="*80)
    
    # Print summary
    print("\n📊 SUMMARY BY MODEL AND HORIZON:")
    print("-" * 60)
    summary = metrics_df.groupby(['model', 'horizon'])[['r2', 'mae', 'mape_pct']].mean()
    print(summary.to_string())
    
    print("\n💾 Results saved:")
    print(f"   Metrics: {output_dir / 'walk_forward_gb_ensemble_metrics.csv'}")
    print(f"   Predictions: {output_dir / 'walk_forward_gb_ensemble_predictions.csv'}")

    return {"metrics": metrics_df, "predictions": predictions_df}


def plot_model_comparison(predictions_df: pd.DataFrame, output_dir: Path) -> None:
    """Create comparison plots for different models across horizons."""
    if predictions_df.empty:
        print("[WARN] No predictions to plot")
        return

    for horizon in sorted(predictions_df["horizon"].unique()):
        subset = predictions_df[predictions_df["horizon"] == horizon]
        years = sorted(subset["year"].unique())
        models = sorted(subset["model"].unique())
        
        n_years = len(years)
        n_models = len(models)
        
        fig, axes = plt.subplots(n_years, n_models, figsize=(n_models * 5, n_years * 3.5), 
                                 squeeze=False, sharey=True)

        for year_idx, year in enumerate(years):
            for model_idx, model in enumerate(models):
                ax = axes[year_idx, model_idx]
                data = subset[(subset["year"] == year) & (subset["model"] == model)].sort_values("target_date")
                
                if data.empty:
                    ax.set_visible(False)
                    continue
                
                # Plot actual vs predicted
                ax.plot(data["target_date"], data["actual"], 
                       color="#1ABC9C", linewidth=2, label="Actual", marker='o', markersize=4)
                ax.plot(data["target_date"], data["prediction"], 
                       color="#F39C12", linewidth=1.8, linestyle="--", label="Prediction", marker='s', markersize=4)
                
                # Calculate R² for this fold
                r2 = r2_score(data["actual"], data["prediction"])
                mae = mean_absolute_error(data["actual"], data["prediction"])
                
                ax.set_title(f"{year} - {model.upper()}\nR²={r2:.3f}, MAE=${mae:.4f}", fontsize=10)
                ax.grid(alpha=0.2)
                ax.tick_params(axis="x", rotation=45)
                
                if year_idx == 0 and model_idx == 0:
                    ax.legend(loc="upper left", fontsize=8)

        fig.suptitle(f"Walk-Forward Forecasts – {horizon}-Day Horizon", fontsize=16, y=0.995)
        fig.tight_layout(rect=[0, 0, 1, 0.99])
        fig.savefig(output_dir / f"model_comparison_h{horizon}.png", dpi=160, bbox_inches='tight')
        plt.close(fig)
        
        print(f"   📊 Saved plot: model_comparison_h{horizon}.png")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Walk-forward validation for GB and Ensemble models (2-3 day horizons)"
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "gold" / "master_model_ready.parquet",
        help="Path to Gold model-ready dataset",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "walk_forward",
        help="Directory to store results",
    )
    parser.add_argument(
        "--horizons",
        type=int,
        nargs="*",
        default=[2, 3],
        help="Forecast horizons in days (default: 2, 3 for quick results)",
    )
    parser.add_argument(
        "--years",
        type=int,
        nargs="*",
        default=[2021, 2022, 2023, 2024],
        help="Years (October) to evaluate",
    )
    parser.add_argument(
        "--models",
        nargs="*",
        default=['gb', 'ensemble'],
        choices=['gb', 'ensemble', 'ridge'],
        help="Models to test (default: gb, ensemble)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    print("\n" + "="*80)
    print("🚀 STARTING WALK-FORWARD VALIDATION")
    print("="*80)
    print(f"Target: October 30th deadline (11 days)")
    print(f"Focus: 2-3 day horizons for strong sentiment signal")
    print("="*80 + "\n")
    
    df = load_model_ready_dataset(args.data_path)
    
    print(f"✅ Loaded dataset: {len(df)} rows, {len(df.columns)} features")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Sentiment features: {len([c for c in df.columns if 'sentiment' in c or 'news_' in c])}")
    
    artefacts = walk_forward_forecasts(
        df, 
        args.horizons, 
        args.years, 
        args.output_dir,
        args.models
    )
    
    print("\n📈 Creating comparison plots...")
    plot_model_comparison(artefacts["predictions"], args.output_dir)
    
    print("\n" + "="*80)
    print("✅ VALIDATION COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    main()
