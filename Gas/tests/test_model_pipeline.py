import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.append(str(SRC_DIR))
sys.path.append(str(SCRIPTS_DIR))

from models.baseline_models import (  # noqa: E402
    COMMON_FEATURES,
    RIDGE_ALPHA_GRID,
    ridge_time_series_cv,
    train_all_models,
)  # noqa: E402

from walk_forward_validation import walk_forward_forecasts, plot_walk_forward  # noqa: E402


def _mock_master_model_ready() -> pd.DataFrame:
    start = pd.Timestamp("2020-10-01")
    dates = pd.date_range(start, periods=6 * 365, freq="D")
    n = len(dates)
    t = np.arange(n)

    price_rbob = 1.9 + 0.05 * np.sin(t / 30)
    price_wti = 60 + 2 * np.cos(t / 45)
    retail_price = price_rbob + 0.25 + 0.03 * np.sin(t / 20)

    df = pd.DataFrame({"date": dates, "price_rbob": price_rbob, "price_wti": price_wti, "retail_price": retail_price})
    df["inventory_mbbl"] = 220 + 5 * np.sin(t / 60)
    df["utilization_pct"] = 85 + 3 * np.cos(t / 40)
    df["net_imports_kbd"] = 500 + 20 * np.sin(t / 50)
    df["padd3_share"] = 36 + 0.3 * np.cos(t / 25)
    df["crack_spread"] = df["price_rbob"] - 0.02 * df["price_wti"]
    df["retail_margin"] = df["retail_price"] - df["price_rbob"]
    df["rbob_lag3"] = df["price_rbob"].shift(3)
    df["rbob_lag7"] = df["price_rbob"].shift(7)
    df["rbob_lag14"] = df["price_rbob"].shift(14)
    df["delta_rbob_1w"] = df["price_rbob"] - df["price_rbob"].shift(7)
    df["rbob_return_1d"] = df["price_rbob"].pct_change().fillna(0)
    df["vol_rbob_10d"] = df["rbob_return_1d"].rolling(10).std().fillna(0)

    df["winter_blend_effect"] = -0.12 * (1 - np.exp(-0.2 * np.maximum((df["date"] - pd.to_datetime(df["date"].dt.year.astype(str) + "-10-01")).dt.days, 0)))
    df["days_since_oct1"] = np.maximum((df["date"] - pd.to_datetime(df["date"].dt.year.astype(str) + "-10-01")).dt.days, 0)
    df["target"] = df["retail_price"]

    df = df.dropna().reset_index(drop=True)
    return df


def test_ridge_cv_handles_small_dataset():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=4, freq="D"),
            "feat": [1.0, 1.2, 1.4, 1.5],
            "target": [2.0, 2.1, 2.2, 2.3],
        }
    )

    result = ridge_time_series_cv(df, ["feat"], "target", alphas=[0.1, 1.0], n_splits=5)
    assert "best_alpha" in result
    assert result["best_alpha"] in [0.1, 1.0]
    assert not result["summary"].empty
    assert set(result["summary"]["alpha"]) <= {0.1, 1.0}


@pytest.fixture(scope="module")
def mock_dataset():
    return _mock_master_model_ready()


def test_train_all_models_outputs(tmp_path, mock_dataset):
    output_dir = tmp_path / "models"
    results = train_all_models(mock_dataset, output_dir=output_dir, test_start="2024-10-01")

    assert {"ridge_baseline", "futures_regression", "inventory_residual", "ensemble_weighted"} <= results.keys()

    ridge_out = results["ridge_baseline"]
    assert ridge_out.model_path and ridge_out.model_path.exists()
    assert (output_dir / "ridge_baseline_predictions.csv").exists()
    assert "best_alpha" in ridge_out.metrics

    inventory_out = results["inventory_residual"]
    assert inventory_out.metrics["best_alpha"] in [float(a) for a in RIDGE_ALPHA_GRID]

    ensemble_out = results["ensemble_weighted"]
    assert not ensemble_out.predictions.empty


def test_walk_forward_forecasts(tmp_path, mock_dataset):
    horizons = [7, 3]
    years = [2022, 2023]
    artefacts = walk_forward_forecasts(mock_dataset, horizons, years, tmp_path)

    metrics = artefacts["metrics"]
    preds = artefacts["predictions"]
    assert not metrics.empty
    assert not preds.empty
    assert set(metrics["horizon"]) == set(horizons) or set(metrics["horizon"]).issubset(set(horizons))

    plot_walk_forward(preds, tmp_path)
    pngs = list(tmp_path.glob("walk_forward_h*.png"))
    assert pngs, "Expected walk-forward plots to be created"
