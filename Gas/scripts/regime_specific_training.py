"""
Train and evaluate regime-specific models for gasoline price forecasting.

- Splits data into Normal and Tight regimes based on days_supply.
- Trains separate models for each regime.
- Evaluates and compares performance by regime.

Usage:
    python regime_specific_training.py

Requirements:
    - master_model_ready.parquet (Gold layer)
    - sklearn, pandas, numpy

Regime definitions:
    - Normal: days_supply > 26
    - Tight: 23 < days_supply <= 26
    - Crisis: days_supply <= 23 (optional)
"""

import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_squared_error

# Paths
REPO_ROOT = Path(__file__).resolve().parents[1]
GOLD_DIR = REPO_ROOT / "data" / "gold"
DATA_PATH = GOLD_DIR / "master_model_ready.parquet"

# Regime thresholds
def regime_label(days_supply):
    if days_supply > 26:
        return "Normal"
    elif days_supply > 23:
        return "Tight"
    else:
        return "Crisis"



from sklearn.model_selection import TimeSeriesSplit

def main():
    # Load data
    df = pd.read_parquet(DATA_PATH)
    df = df.copy()
    df["regime"] = df["days_supply"].apply(regime_label)

    # Features and target
    feature_cols = [
        c for c in df.columns
        if c not in ["date", "retail_price", "target", "regime"]
    ]
    X = df[feature_cols]
    y = df["retail_price"]

    # Regime splits
    regimes = ["Normal", "Tight"]
    results = {}
    for regime in regimes:
        mask = df["regime"] == regime
        n_obs = mask.sum()
        if n_obs < 40:
            print(f"⚠️  Not enough samples for regime: {regime} ({n_obs} rows, need >=40 for robust validation)")
            continue
        X_reg = X[mask].reset_index(drop=True)
        y_reg = y[mask].reset_index(drop=True)
        # In-sample fit
        model = Ridge(alpha=1.0)
        model.fit(X_reg, y_reg)

        y_pred = model.predict(X_reg)
        r2 = r2_score(y_reg, y_pred)
        rmse = np.sqrt(mean_squared_error(y_reg, y_pred))
        # Out-of-sample: time-series split
        tscv = TimeSeriesSplit(n_splits=5)
        r2_cv, rmse_cv = [], []
        for train_idx, test_idx in tscv.split(X_reg):
            X_tr, X_te = X_reg.iloc[train_idx], X_reg.iloc[test_idx]
            y_tr, y_te = y_reg.iloc[train_idx], y_reg.iloc[test_idx]
            m = Ridge(alpha=1.0)
            m.fit(X_tr, y_tr)
            y_pred_te = m.predict(X_te)
            r2_cv.append(r2_score(y_te, y_pred_te))
            rmse_cv.append(np.sqrt(mean_squared_error(y_te, y_pred_te)))
        results[regime] = {
            "r2": r2,
            "rmse": rmse,
            "n": n_obs,
            "r2_cv_mean": np.mean(r2_cv),
            "r2_cv_std": np.std(r2_cv),
            "rmse_cv_mean": np.mean(rmse_cv),
            "rmse_cv_std": np.std(rmse_cv),
        }
        print(f"\nRegime: {regime}")
        print(f"  In-sample:   R²={r2:.3f}, RMSE={rmse:.3f}, N={n_obs}")
        print(f"  OOS (CV):    R²={np.mean(r2_cv):.3f} ± {np.std(r2_cv):.3f}, RMSE={np.mean(rmse_cv):.3f} ± {np.std(rmse_cv):.3f}")

    print("\nSummary:")
    for regime, metrics in results.items():
        print(f"  {regime}: In-sample R²={metrics['r2']:.3f}, OOS R²={metrics['r2_cv_mean']:.3f} ± {metrics['r2_cv_std']:.3f}, N={metrics['n']}")


if __name__ == "__main__":
    main()
