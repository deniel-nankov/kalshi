import os
from datetime import datetime

import numpy as np
import pandas as pd
import pytest


# Ensure scripts directory is importable
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "Gas" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from download_noaa_temp import prepare_temperature_features  # type: ignore  # noqa: E402
from process_hurricane_risk_october import (  # type: ignore  # noqa: E402
    prepare_gulf_october_dataset,
    parse_hurdat_lines,
)


def test_prepare_temperature_features_computes_anomalies():
    dates = pd.date_range("2024-01-01", periods=40, freq="D")
    temps = np.linspace(20, 30, 40)  # gradual warming
    df = pd.DataFrame(
        {
            "date": np.repeat(dates, 2),
            "station": ["A", "B"] * 40,
            "temp_c": np.tile(temps, 2),
        }
    )

    result = prepare_temperature_features(df)
    assert set(
        ["date", "temp_c", "temp_anomaly", "temp_anomaly_c", "temp_anomaly_f", "temp_f",
         "cooling_degree_day", "cooling_degree_day_anomaly"]
    ).issubset(result.columns)

    result = result.set_index("date")
    expected_cdd = np.maximum(result["temp_c"] - 18.0, 0.0)
    np.testing.assert_allclose(
        result["cooling_degree_day"].iloc[-5:],
        expected_cdd.iloc[-5:],
        rtol=1e-5,
        atol=1e-5,
    )
    rolling = result["temp_c"].rolling(365, min_periods=30).mean()
    expected_anomaly = result["temp_c"] - rolling
    np.testing.assert_allclose(
        result["temp_anomaly"],
        expected_anomaly,
        rtol=1e-5,
        atol=1e-5,
        equal_nan=True,
    )


def test_prepare_gulf_october_dataset_from_sample(monkeypatch):
    sample_text = """AL012020, ARTHUR, 2020, 4
20200516, 0000, , TD, 30.0N, 75.0W, 35, 1005, 34, 0, 0, 0,
20201007, 1200, , TS, 26.0N, 90.0W, 50, 995, 50, 0, 0, 0,
AL022021, BETA, 2021, 3
20211005, 0600, , TS, 24.0N, 88.0W, 45, 1000, 45, 0, 0, 0,
20211006, 1200, , TS, 20.0N, 93.0W, 55, 998, 55, 0, 0, 0,
"""
    fixes = parse_hurdat_lines(sample_text)

    monkeypatch.setenv("HURRICANE_START", "2020")
    monkeypatch.setenv("HURRICANE_END", "2021")

    dataset = prepare_gulf_october_dataset(fixes)
    dataset = dataset.set_index("date")

    # October 7 2020 should register one storm
    assert dataset.loc["2020-10-07", "storm_count"] == 1
    assert pytest.approx(dataset.loc["2020-10-07", "storm_prob"], rel=1e-5) == 0.5

    # October 6 2021 has at least one storm with 55 kt winds
    assert dataset.loc["2021-10-06", "max_wind_kt"] == 55
    assert dataset.loc["2021-10-06", "shut_in_est"] > 0.0
