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


from Gas.deploy.regimes import REGIMES, regime_label

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
    # Validate required features: days_supply and utilization_pct
    for col in ["days_supply", "utilization_pct"]:
        if col not in df.columns:
            raise ValueError(f"Input is missing required column: {col}")
    # Assign regime using full row (regime_label expects row)
    df["regime"] = df.apply(regime_label, axis=1)
    models = load_models()
    preds = []
    # Validate all required feature columns only for regimes present in input
    present_regimes = set(df["regime"].unique())
    for regime in present_regimes:
        if regime not in models:
            continue  # Will be handled in prediction loop
        _, feature_cols = models[regime]
        missing = [col for col in feature_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing columns for regime '{regime}': {missing}")
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
