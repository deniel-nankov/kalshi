"""
Predict retail gasoline prices using regime-specific models.

Usage:
    python predict.py --input <input.csv> [--output <output.csv>]

- Loads regime-specific models from disk
- Assigns regime for each row in input
- Uses the appropriate model for prediction
"""
import argparse
import pandas as pd
import numpy as np
import joblib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = REPO_ROOT / "deploy" / "models"

REGIMES = ["Normal", "Tight"]

def regime_label(days_supply):
    if days_supply > 26:
        return "Normal"
    elif days_supply > 23:
        return "Tight"
    else:
        return "Crisis"

def load_models():
    models = {}
    for regime in REGIMES:
        path = MODEL_DIR / f"ridge_{regime.lower()}.joblib"
        if path.exists():
            model, feature_cols = joblib.load(path)
            models[regime] = (model, feature_cols)
    return models

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input CSV file with features")
    parser.add_argument("--output", default=None, help="Optional output CSV file")
    args = parser.parse_args()
    df = pd.read_csv(args.input)
    if "days_supply" not in df.columns:
        raise ValueError("Input must contain 'days_supply' column for regime assignment.")
    df["regime"] = df["days_supply"].apply(regime_label)
    models = load_models()
    preds = []
    for idx, row in df.iterrows():
        regime = row["regime"]
        if regime not in models:
            preds.append(np.nan)
            continue
        model, feature_cols = models[regime]
        X_row = row[feature_cols].values.reshape(1, -1)
        pred = model.predict(X_row)[0]
        preds.append(pred)
    df["predicted_retail_price"] = preds
    if args.output:
        df.to_csv(args.output, index=False)
        print(f"✓ Predictions saved to {args.output}")
    else:
        print(df[["regime", "predicted_retail_price"]].head())

if __name__ == "__main__":
    main()
