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
import os
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests

BASE_URL = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data"
DEFAULT_STATIONS = [
    "GHCND:USW00012918",  # Houston (IAH)
    "GHCND:USW00012924",  # Corpus Christi International
    "GHCND:USW00012946",  # Beaumont/Port Arthur
    "GHCND:USW00012917",  # Lake Charles Regional
]
DEFAULT_START = "2020-01-01"
DEFAULT_END = date.today().isoformat()
REQUEST_LIMIT = 1000  # NOAA API maximum per request
ROLLING_WINDOW_DAYS = 365
ROLLING_MIN_PERIODS = 30  # ensure early periods still have values

ROOT_DIR = Path(__file__).resolve().parents[1]
BRONZE_DIR = ROOT_DIR / "data" / "bronze"
SILVER_DIR = ROOT_DIR / "data" / "silver"
BRONZE_PATH = BRONZE_DIR / "noaa_temp_raw.parquet"
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
        "datatypeid": ["TAVG", "TMAX", "TMIN"],
        "stationid": config.station_id,
        "startdate": config.start_date,
        "enddate": config.end_date,
        "units": "metric",
        "limit": REQUEST_LIMIT,
        "sortfield": "date",
        "sortorder": "asc",
    }

    records: list[dict] = []
    max_attempts = int(os.getenv("NOAA_MAX_RETRIES", "10"))
    for start, end in _generate_daily_chunks(config.start_date, config.end_date):
        params["startdate"] = start
        params["enddate"] = end
        params["offset"] = 1

        while True:
            attempt = 0
            while attempt < max_attempts:
                attempt += 1
                try:
                    response = session.get(
                        BASE_URL,
                        params=_encode_params(params),
                        headers=headers,
                        timeout=60,
                    )
                except requests.exceptions.ReadTimeout:
                    logger.warning(
                        "NOAA request timeout for %s (%s-%s) attempt %d/%d",
                        config.station_id,
                        start,
                        end,
                        attempt,
                        max_attempts,
                    )
                    time.sleep(2 ** attempt)
                    continue

                if response.status_code in (502, 503, 504):
                    logger.warning(
                        "NOAA service unavailable (%s) for %s (%s-%s) attempt %d/%d",
                        response.status_code,
                        config.station_id,
                        start,
                        end,
                        attempt,
                        max_attempts,
                    )
                    time.sleep(2 ** attempt)
                    continue

                if response.status_code >= 400:
                    body = response.text.strip()
                    if response.status_code == 400 and "no data" in body.lower():
                        logger.info(
                            "No NOAA temperature data for %s between %s and %s",
                            config.station_id,
                            start,
                            end,
                        )
                        results = []
                    else:
                        logger.error(
                            "NOAA request failed (%s %s) for %s (%s-%s). Response: %s",
                            response.status_code,
                            response.reason,
                            config.station_id,
                            start,
                            end,
                            body,
                        )
                        response.raise_for_status()
                else:
                    payload = response.json()
                    results = payload.get("results", [])
                break
            else:
                logger.error(
                    "NOAA temperature request failed after retries for %s (%s-%s); skipping chunk",
                    config.station_id,
                    start,
                    end,
                )
                results = []

            if not results:
                break

            records.extend(results)

            if len(results) < REQUEST_LIMIT:
                break
            params["offset"] += REQUEST_LIMIT
            time.sleep(0.2)
    if not records:
        logger.warning("No temperature observations returned for station %s", config.station_id)
        return pd.DataFrame(columns=["date", "datatype", "station", "value", "attributes"])

    df = pd.DataFrame(records)
    df["station"] = config.station_id
    return df[["date", "datatype", "station", "value", "attributes"]]


def transform_raw_temperature(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty:
        return pd.DataFrame(columns=["date", "station", "temp_c"])

    raw_df = raw_df.copy()
    raw_df["value"] = pd.to_numeric(raw_df["value"], errors="coerce")
    raw_df["date"] = pd.to_datetime(raw_df["date"]).dt.tz_localize(None)
    raw_df = raw_df.dropna(subset=["date", "value", "datatype"])

    frames: List[pd.DataFrame] = []
    for station_id, station_df in raw_df.groupby("station"):
        pivot = (
            station_df.pivot_table(index="date", columns="datatype", values="value", aggfunc="first")
            .sort_index()
            .reset_index()
        )

        if {"TMAX", "TMIN"}.issubset(pivot.columns):
            pivot["TAVG_COMPUTED"] = (pivot["TMAX"] + pivot["TMIN"]) / 2.0

        if "TAVG" in pivot.columns:
            temp_tenths = pivot["TAVG"].fillna(pivot.get("TAVG_COMPUTED"))
        else:
            temp_tenths = pivot.get("TAVG_COMPUTED")

        if temp_tenths is None:
            logger.warning("No usable temperature records for station %s", station_id)
            continue

        temp_c = temp_tenths / 10.0
        out = pd.DataFrame({
            "date": pivot["date"],
            "station": station_id,
            "temp_c": temp_c,
        })
        out = out.dropna(subset=["date", "temp_c"]).sort_values("date")
        frames.append(out)

    if not frames:
        return pd.DataFrame(columns=["date", "station", "temp_c"])

    return pd.concat(frames, ignore_index=True)


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

    raw_frames = []
    session = requests.Session()
    for station in stations:
        config = StationConfig(station_id=station, start_date=start_date, end_date=end_date)
        raw_frames.append(fetch_station_temperature(config, token=token, session=session))

    combined_raw = pd.concat(raw_frames, ignore_index=True)
    if combined_raw.empty:
        raise RuntimeError("No temperature observations retrieved for the configured stations.")

    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    combined_raw.to_parquet(BRONZE_PATH, index=False)
    logger.info("✓ Saved raw temperature observations to %s (%d rows)", BRONZE_PATH, len(combined_raw))

    station_daily = transform_raw_temperature(combined_raw)
    features = prepare_temperature_features(station_daily)
    save_temperature_dataset(features)


def _encode_params(params: dict) -> dict:
    encoded = {}
    for key, value in params.items():
        if isinstance(value, list):
            encoded[key] = value
        else:
            encoded[key] = value
    return encoded


def _generate_daily_chunks(start: str, end: str) -> Iterable[Tuple[str, str]]:
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)

    current_start = start_dt
    while current_start <= end_dt:
        current_end = min(current_start + timedelta(days=364), end_dt)
        yield current_start.date().isoformat(), current_end.date().isoformat()
        current_start = current_end + timedelta(days=1)


if __name__ == "__main__":
    main()
