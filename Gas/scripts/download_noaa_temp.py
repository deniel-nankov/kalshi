"""
Download and process daily Gulf Coast temperature data from NOAA.

- Retrieves daily observations from the NOAA CDO API (GHCND dataset)
- Aggregates across one or more stations to represent Gulf Coast refinery demand
- Computes rolling anomalies (temperature and cooling-degree-day)
- Saves cleaned output to data/silver/noaa_temp_daily.parquet

Environment prerequisites
-------------------------
NOAA_TOKEN  : NOAA CDO API token (https://www.ncdc.noaa.gov/cdo-web/token)

Optional overrides (environment variables)
------------------------------------------
NOAA_STATIONS : Comma-separated list of station IDs (default: Houston & New Orleans)
NOAA_START    : Start date in YYYY-MM-DD (default: 2020-01-01)
NOAA_END      : End date in YYYY-MM-DD   (default: today)
"""

from __future__ import annotations

import logging
import math
import os
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional

import numpy as np
import pandas as pd
import requests

BASE_URL = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data"
DEFAULT_STATIONS = [
    "GHCND:USW00012918",  # Houston, TX
    "GHCND:USW00093937",  # New Orleans, LA
]
DEFAULT_START = "2020-01-01"
DEFAULT_END = date.today().isoformat()
REQUEST_LIMIT = 1000  # NOAA API maximum per request
ROLLING_WINDOW_DAYS = 365
ROLLING_MIN_PERIODS = 30  # ensure early periods still have values

SILVER_DIR = Path(__file__).resolve().parents[2] / "data" / "silver"
SILVER_PATH = SILVER_DIR / "noaa_temp_daily.parquet"

logger = logging.getLogger("download_noaa_temp")
logging.basicConfig(level=logging.INFO, format="%(message)s")


@dataclass
class StationConfig:
    station_id: str
    start_date: str
    end_date: str


def _get_station_list() -> List[str]:
    env_value = os.getenv("NOAA_STATIONS")
    if env_value:
        stations = [s.strip() for s in env_value.split(",") if s.strip()]
        if stations:
            return stations
    return DEFAULT_STATIONS


def _get_date_range() -> tuple[str, str]:
    start = os.getenv("NOAA_START", DEFAULT_START)
    end = os.getenv("NOAA_END", DEFAULT_END)
    return start, end


def fetch_station_temperature(
    config: StationConfig,
    token: str,
    session: Optional[requests.Session] = None,
) -> pd.DataFrame:
    """Fetch daily temperature observations for a single station."""
    session = session or requests.Session()
    headers = {"token": token}
    params = {
        "datasetid": "GHCND",
        "datatypeid": "TAVG",
        "stationid": config.station_id,
        "startdate": config.start_date,
        "enddate": config.end_date,
        "units": "metric",
        "limit": REQUEST_LIMIT,
        "offset": 1,
        "sortfield": "date",
        "sortorder": "asc",
    }

    records: list[dict] = []
    while True:
        response = session.get(BASE_URL, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results", [])
        if not results:
            break

        records.extend(results)

        # pagination
        if len(results) < REQUEST_LIMIT:
            break
        params["offset"] += REQUEST_LIMIT
        time.sleep(0.2)  # friendly throttling

    df = pd.DataFrame(records)
    if df.empty:
        logger.warning("No temperature observations returned for station %s", config.station_id)
        return pd.DataFrame(columns=["date", "station", "temp_c"])

    # NOAA GHCND TAVG values are tenths of °C when units=metric
    if "value" not in df.columns:
        raise ValueError(f"'value' column missing for station {config.station_id}")

    df = df.rename(columns={"value": "temp_tenths_c"})
    df["temp_c"] = pd.to_numeric(df["temp_tenths_c"], errors="coerce") / 10.0
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    df["station"] = config.station_id

    df = df.dropna(subset=["date", "temp_c"]).sort_values("date")
    return df[["date", "station", "temp_c"]]


def prepare_temperature_features(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate station-level temperatures and compute anomalies."""
    if df.empty:
        return df

    agg = (
        df.groupby("date", as_index=False)["temp_c"]
        .mean()
        .sort_values("date")
        .reset_index(drop=True)
    )

    temp_c = agg["temp_c"]
    rolling_mean = temp_c.rolling(ROLLING_WINDOW_DAYS, min_periods=ROLLING_MIN_PERIODS).mean()
    temp_anomaly_c = temp_c - rolling_mean

    temp_f = temp_c * 9 / 5 + 32
    temp_anomaly_f = temp_anomaly_c * 9 / 5

    cooling_degree_day = np.maximum(temp_c - 18.0, 0.0)
    cdd_roll = cooling_degree_day.rolling(ROLLING_WINDOW_DAYS, min_periods=ROLLING_MIN_PERIODS).mean()
    cooling_degree_day_anom = cooling_degree_day - cdd_roll

    out = agg.assign(
        temp_anomaly=temp_anomaly_c,
        temp_anomaly_c=temp_anomaly_c,
        temp_anomaly_f=temp_anomaly_f,
        temp_f=temp_f,
        cooling_degree_day=cooling_degree_day,
        cooling_degree_day_anomaly=cooling_degree_day_anom,
    )

    # cast to reasonable dtypes
    for col in out.columns:
        if col != "date":
            out[col] = out[col].astype("float32")

    return out


def save_temperature_dataset(df: pd.DataFrame) -> Path:
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(SILVER_PATH, index=False)
    logger.info("✓ Saved cleaned temperature data to %s (%d rows)", SILVER_PATH, len(df))
    return SILVER_PATH


def main() -> None:
    token = os.getenv("NOAA_TOKEN")
    if not token:
        raise RuntimeError(
            "NOAA_TOKEN environment variable not set. "
            "Obtain a token from https://www.ncdc.noaa.gov/cdo-web/token and export it."
        )

    stations = _get_station_list()
    start_date, end_date = _get_date_range()

    logger.info("Downloading NOAA temperature data for stations: %s", ", ".join(stations))
    logger.info("Date range: %s → %s", start_date, end_date)

    frames = []
    session = requests.Session()
    for station in stations:
        config = StationConfig(station_id=station, start_date=start_date, end_date=end_date)
        frames.append(fetch_station_temperature(config, token=token, session=session))

    combined = pd.concat(frames, ignore_index=True)
    if combined.empty:
        raise RuntimeError("No temperature observations retrieved for the configured stations.")

    features = prepare_temperature_features(combined)
    save_temperature_dataset(features)


if __name__ == "__main__":
    main()
