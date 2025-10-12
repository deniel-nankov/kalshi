"""Compute end-of-month (Oct 31, 2025) forecast using Oct 10 features."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "gold" / "master_model_ready.parquet"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "outputs" / "final_forecast.json"

FEATURES = [
    "price_rbob",
    "crack_spread",
    "winter_blend_effect",
    "days_since_oct1",
]

FORECAST_DAY = 10
TARGET_DAY = 31


def load_dataset(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["day"] = df["date"].dt.day
    return df


def build_training_matrix(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year in sorted(df["year"].unique()):
        if year >= 2025:
            continue  # hold-out year for forecast
        forecast_row = df[(df["year"] == year) & (df["day"] == FORECAST_DAY)].copy()
        target_row = df[(df["year"] == year) & (df["day"] == TARGET_DAY)]["retail_price"]
        if forecast_row.empty or target_row.empty:
            continue
        row = forecast_row.iloc[0][FEATURES].to_dict()
        row["target"] = float(target_row.iloc[0])
        row["year"] = year
        rows.append(row)
    return pd.DataFrame(rows)


def build_forecast_features(df: pd.DataFrame) -> Dict[str, float]:
    row = df[(df["year"] == 2025) & (df["day"] == FORECAST_DAY)]
    if row.empty:
        raise RuntimeError("No feature row available for Oct 10, 2025.")
    return row.iloc[0][FEATURES].to_dict()


def fit_linear_model(train_df: pd.DataFrame):
    X = sm.add_constant(train_df[FEATURES], has_constant="add")
    y = train_df["target"]
    model = sm.OLS(y, X).fit()
    return model


def predict_quantiles(train_df: pd.DataFrame, predict_features: Dict[str, float]):
    quantiles = {}
    features_df = pd.DataFrame([predict_features])
    features_df["const"] = 1.0
    for q in [0.1, 0.5, 0.9]:
        formula = "target ~ " + " + ".join(FEATURES)
        qr = smf.quantreg(formula, train_df).fit(q=q)
        quantiles[q] = float(qr.predict(features_df[FEATURES])[0])
    return quantiles


def main() -> None:
    df = load_dataset(DATA_PATH)
    train_df = build_training_matrix(df)
    if len(train_df) < 3:
        raise RuntimeError("Not enough historical years to fit pass-through forecast.")

    forecast_features = build_forecast_features(df)

    model = fit_linear_model(train_df)
    exog_names = model.model.exog_names
    forecast_df = pd.DataFrame([forecast_features])
    forecast_df = sm.add_constant(forecast_df, has_constant="add")
    forecast_df = forecast_df[exog_names]
    forecast_value = float(model.predict(forecast_df)[0])

    quantiles = predict_quantiles(train_df, forecast_features)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "forecast_date": "2025-10-31",
        "point_forecast": forecast_value,
        "quantile_p10": quantiles.get(0.1),
        "quantile_p50": quantiles.get(0.5),
        "quantile_p90": quantiles.get(0.9),
        "model_r2": float(model.rsquared),
        "training_years": train_df["year"].tolist(),
    }

    import json
    OUTPUT_PATH.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
