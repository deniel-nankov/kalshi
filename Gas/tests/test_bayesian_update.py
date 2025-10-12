import sys
from pathlib import Path

import numpy as np
import pandas as pd

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.bayesian_update import produce_forecast, load_dataset


def make_october_dataset():
    dates = pd.date_range("2020-10-01", "2025-10-31", freq="D")
    df = pd.DataFrame({"date": dates})
    df["price_rbob"] = 2 + 0.01 * np.sin(np.arange(len(df)) / 10)
    df["crack_spread"] = 0.4 + 0.05 * np.cos(np.arange(len(df)) / 15)
    df["winter_blend_effect"] = -0.05 + 0.02 * np.tanh((df["date"].dt.day - 10) / 5)
    df["days_since_oct1"] = (df["date"] - pd.to_datetime(df["date"].dt.year.astype(str) + "-10-01")).dt.days
    df["retail_price"] = df["price_rbob"] + 0.3 + 0.02 * np.sin(np.arange(len(df)) / 12)
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day
    df = df[df["month"] == 10].copy()
    return df


def test_produce_forecast_basic(tmp_path, monkeypatch):
    df = make_october_dataset()
    monkeypatch.setattr("models.bayesian_update.load_dataset", lambda path=None: df)
    forecast = produce_forecast(df, observation_day=10)
    assert isinstance(forecast.mean, float)
    assert forecast.variance > 0
    assert forecast.training_years
