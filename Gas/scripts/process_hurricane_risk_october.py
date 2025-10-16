"""
Process October hurricane risk for the Gulf Coast using NOAA HURDAT2.

Steps:
 1. Download the latest HURDAT2 dataset from the National Hurricane Center
 2. Parse storm tracks and isolate fixes within a Gulf/PADD3 bounding box
 3. Aggregate to daily October risk metrics (storm probability, shut-in estimate)
 4. Save output to data/silver/hurricane_risk_october.csv

Environment overrides:
 HURDAT_URL       : Custom URL for HURDAT2 file
 HURRICANE_START  : First season to include (default 2000)
 HURRICANE_END    : Last season (default current year)
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional

import numpy as np
import pandas as pd
import requests

DEFAULT_HURDAT_URL = "https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2023-070324.txt"
GULF_LAT_RANGE = (18.0, 32.0)   # degrees North
GULF_LON_RANGE = (-98.5, -80.0)  # degrees East (negative = West)
MIN_YEAR = int(os.getenv("HURRICANE_START", "2000"))
MAX_YEAR = int(os.getenv("HURRICANE_END", str(date.today().year)))

SILVER_DIR = Path(__file__).resolve().parents[2] / "data" / "silver"
OUTPUT_PATH = SILVER_DIR / "hurricane_risk_october.csv"

logger = logging.getLogger("process_hurricane_risk")
logging.basicConfig(level=logging.INFO, format="%(message)s")


@dataclass
class StormFix:
    storm_id: str
    storm_name: str
    timestamp: pd.Timestamp
    lat: float
    lon: float
    max_wind_kt: int


def download_hurdat2(url: str) -> str:
    logger.info("Downloading HURDAT2 dataset")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.text


def parse_lat(value: str) -> float:
    match = re.match(r"^\s*([0-9.]+)([NS])\s*$", value)
    if not match:
        raise ValueError(f"Invalid latitude value: {value}")
    magnitude = float(match.group(1))
    hemisphere = match.group(2)
    return magnitude if hemisphere == "N" else -magnitude


def parse_lon(value: str) -> float:
    match = re.match(r"^\s*([0-9.]+)([EW])\s*$", value)
    if not match:
        raise ValueError(f"Invalid longitude value: {value}")
    magnitude = float(match.group(1))
    hemisphere = match.group(2)
    return -magnitude if hemisphere == "W" else magnitude


def parse_hurdat_lines(raw_text: str) -> List[StormFix]:
    fixes: List[StormFix] = []
    current_id = ""
    current_name = ""

    for line in raw_text.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if not parts:
            continue

        if not parts[0] or parts[0][0].isalpha():
            # header line format: BASIN+ID, NAME, YEAR, NUM_ENTRIES
            current_id = parts[0]
            current_name = parts[1] if len(parts) > 1 else ""
            continue

        if len(parts) < 7:
            continue  # malformed data row

        fix_date = parts[0]
        fix_time = parts[1]
        lat = parse_lat(parts[4])
        lon = parse_lon(parts[5])

        try:
            max_wind = int(parts[6])
        except ValueError:
            max_wind = np.nan

        timestamp = pd.to_datetime(f"{fix_date} {fix_time}", format="%Y%m%d %H%M")
        fixes.append(
            StormFix(
                storm_id=current_id,
                storm_name=current_name,
                timestamp=timestamp,
                lat=lat,
                lon=lon,
                max_wind_kt=max_wind,
            )
        )

    return fixes


def prepare_gulf_october_dataset(fixes: Iterable[StormFix]) -> pd.DataFrame:
    df = pd.DataFrame([fix.__dict__ for fix in fixes])
    if df.empty:
        raise RuntimeError("No storm fixes parsed from HURDAT2 dataset.")

    df = df.assign(
        year=df["timestamp"].dt.year,
        month=df["timestamp"].dt.month,
        date=df["timestamp"].dt.floor("D"),
    )

    df = df[(df["year"] >= MIN_YEAR) & (df["year"] <= MAX_YEAR)]
    df = df[df["month"] == 10]  # October only

    # Gulf / PADD3 bounding box
    df = df[
        (df["lat"].between(*GULF_LAT_RANGE))
        & (df["lon"].between(*GULF_LON_RANGE))
    ]

    if df.empty:
        logger.warning("No Gulf Coast hurricane fixes found for October %s-%s.", MIN_YEAR, MAX_YEAR)

    agg = (
        df.groupby("date")
        .agg(
            storm_count=("storm_id", "nunique"),
            max_wind_kt=("max_wind_kt", "max"),
        )
        .reset_index()
    )

    # Derived metrics
    agg["storm_prob"] = np.clip(agg["storm_count"] / 2.0, 0.0, 1.0)
    agg["shut_in_est"] = np.clip(agg["max_wind_kt"] / 150.0, 0.0, 1.0)

    # Ensure complete October date range
    full_range = pd.date_range(
        start=pd.Timestamp(f"{MIN_YEAR}-10-01"),
        end=pd.Timestamp(f"{MAX_YEAR}-10-31"),
        freq="D",
    )
    out = (
        pd.DataFrame({"date": full_range})
        .merge(agg, on="date", how="left")
        .fillna({"storm_count": 0, "max_wind_kt": 0, "storm_prob": 0.0, "shut_in_est": 0.0})
    )

    # Cast to reasonable dtypes
    out["storm_count"] = out["storm_count"].astype("int16")
    for col in ["max_wind_kt", "storm_prob", "shut_in_est"]:
        out[col] = out[col].astype("float32")

    return out


def main() -> None:
    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    url = os.getenv("HURDAT_URL", DEFAULT_HURDAT_URL)
    logger.info("HURDAT2 source: %s", url)
    raw_text = download_hurdat2(url)

    fixes = parse_hurdat_lines(raw_text)
    dataset = prepare_gulf_october_dataset(fixes)
    dataset.to_csv(OUTPUT_PATH, index=False)

    logger.info("✓ Saved hurricane risk features to %s (%d rows)", OUTPUT_PATH, len(dataset))


if __name__ == "__main__":
    main()
