import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.quantile_regression import prepare_features, train_quantile_models


def make_dataset() -> pd.DataFrame:
    dates = pd.date_range("2021-01-01", periods=500, freq="D")
    t = np.arange(len(dates))
    df = pd.DataFrame({
        "date": dates,
        "price_rbob": 2 + 0.01 * np.sin(t / 10),
        "price_wti": 60 + np.cos(t / 20),
        "inventory_mbbl": 220 + np.sin(t / 30),
        "utilization_pct": 85 + np.cos(t / 25),
        "net_imports_kbd": 500 + np.sin(t / 50),
        "padd3_share": 36 + np.cos(t / 45),
        "crack_spread": 0.5 + np.sin(t / 15),
        "retail_margin": 0.3 + np.cos(t / 18),
        "rbob_lag7": 2 + 0.01 * np.sin((t-7) / 10),
        "rbob_lag14": 2 + 0.01 * np.sin((t-14) / 10),
        "delta_rbob_1w": 0.01 * (np.sin(t/10) - np.sin((t-7)/10)),
        "winter_blend_effect": -0.05 + 0.01 * np.cos(t / 35),
        "days_since_oct1": np.maximum((dates - pd.to_datetime(dates.year.astype(str) + "-10-01")).days, 0),
    })
    df["retail_price"] = df["price_rbob"] + df["retail_margin"] + 0.02 * np.sin(t / 12)
    return df


def test_prepare_features_missing_columns():
    df = pd.DataFrame({"date": pd.date_range("2020-01-01", periods=5), "retail_price": [2, 2, 2, 2, 2]})
    with pytest.raises(ValueError):
        prepare_features(df)


def test_train_quantile_models(tmp_path):
    df = make_dataset()
    results = train_quantile_models(df, output_dir=tmp_path, quantiles=[0.1, 0.5], test_start="2021-12-01")
    assert set(results.keys()) == {0.1, 0.5}
    for res in results.values():
        assert "train" in res.metrics and "test" in res.metrics
        assert res.predictions["prediction"].notna().all()
    summary_file = tmp_path / "quantile_metrics_summary.csv"
    assert summary_file.exists()
    summary_df = pd.read_csv(summary_file)
    assert not summary_df.empty
