"""
Train and save regime-specific models for deployment.

- Loads Gold layer model-ready data
- Trains a Ridge model for each regime (Normal, Tight)
- Saves models to disk using joblib
"""
import os
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
import joblib

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLD_DIR = REPO_ROOT / "data" / "gold"
DATA_PATH = GOLD_DIR / "master_model_ready.parquet"
MODEL_DIR = REPO_ROOT / "deploy" / "models"
MODEL_DIR.mkdir(exist_ok=True)


# Use shared regime logic
from Gas.deploy.regimes import REGIMES, regime_label
# REGIMES includes all possible outputs of regime_label (Normal, Tight, Crisis)

def main():
    df = pd.read_parquet(DATA_PATH)
    df = df.copy()
    df["regime"] = df["days_supply"].apply(regime_label)
    feature_cols = [
        c for c in df.columns
        if c not in ["date", "retail_price", "target", "regime"]
    ]
    X = df[feature_cols]
    y = df["retail_price"]
    for regime in REGIMES:
        mask = df["regime"] == regime
        if mask.sum() < 40:
            print(f"⚠️  Not enough samples for regime: {regime} ({mask.sum()} rows)")
            continue
        X_reg = X[mask]
        y_reg = y[mask]
        model = Ridge(alpha=1.0)
        model.fit(X_reg, y_reg)
        model_path = MODEL_DIR / f"ridge_{regime.lower()}.joblib"
        joblib.dump((model, feature_cols), model_path)
        print(f"✓ Saved {regime} model to {model_path}")

if __name__ == "__main__":
    main()
