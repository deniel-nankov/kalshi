"""
Train and save regime-specific models for deployment.

- Loads Gold layer model-ready data
- Trains a Ridge model for each regime (Normal, Tight)
- Saves models to disk using joblib
"""
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
import joblib

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

GOLD_DIR = REPO_ROOT / "data" / "gold"
DATA_PATH = GOLD_DIR / "master_model_ready.parquet"
MODEL_DIR = REPO_ROOT / "deploy" / "models"
MODEL_DIR.mkdir(exist_ok=True)

# Define regimes locally to avoid import issues
REGIMES = ["Normal", "Tight", "Crisis"]

def regime_label(days_supply, utilization_pct) -> str:
    """Assigns a regime label based on supply/demand stress features."""
    if pd.isna(days_supply) or pd.isna(utilization_pct):
        return "Normal"
    if days_supply < 20 and utilization_pct > 90:
        return "Crisis"
    if days_supply < 24:
        return "Tight"
    return "Normal"

def main():
    df = pd.read_parquet(DATA_PATH)
    df = df.copy()
    df["regime"] = df.apply(lambda row: regime_label(row["days_supply"], row["utilization_pct"]), axis=1)
    
    # Exclude non-numeric and non-feature columns
    exclude_cols = ["date", "retail_price", "target", "regime", 
                    "hurricane_name", "refinery_impact_level",  # String columns
                    "landfall_latitude", "landfall_longitude"]  # High NaN columns
    feature_cols = [
        c for c in df.columns
        if c not in exclude_cols and df[c].dtype in ['float64', 'int64', 'float32', 'int32']
    ]
    
    X = df[feature_cols]
    y = df["retail_price"]
    
    # Fill NaN values with 0 (common for hurricane/event features)
    X = X.fillna(0)
    
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
