"""
Generate October hurricane risk features for Gulf Coast refineries using
NHC "best track" shapefiles (Option A).

Pipeline steps
--------------
1. Download the IBTrACS North Atlantic catalogue to identify storms for the
   requested seasons (default: current year plus previous five years).
2. For each storm with an ATCF identifier (e.g., ``AL052024``), download the
   NHC per-storm best-track shapefile
   (``https://www.nhc.noaa.gov/gis/best_track/al052024_best_track.zip``).
3. Parse the ``*_pts.shp`` file with ``pyshp`` to extract track fixes.
4. Filter fixes to (a) lie within the PADD-3 Gulf bounding box and
   (b) occur during October.
5. Aggregate daily risk metrics (storm count, max wind, probability, shut-in
   estimate) and save to ``data/silver/hurricane_risk_october.csv``.

Bronze artefacts
----------------
- ``data/bronze/hurricanes/ibtracs_na.csv`` – catalogue snapshot used for storm
  discovery.
- ``data/bronze/hurricanes/<storm_id>.zip`` – cached per-storm best track
  shapefiles.

Environment overrides
---------------------
HURRICANE_START : first season to include (default = current year - 5)
HURRICANE_END   : final season to include (default = current year)
HURRICANE_STORMS: optional comma-separated override of ATCF IDs to process
PYSHAPE_RETRIES : number of download retries for shapefiles (default = 5)

This script depends on the ``pyshp`` package (``pip install pyshp``).
"""

from __future__ import annotations

import io
import logging
import os
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional

import numpy as np
import pandas as pd
import requests

try:
    import shapefile  # type: ignore
except ImportError as exc:  # pragma: no cover
    shapefile = None


IBTRACS_URL = (
    "https://www.ncei.noaa.gov/data/"
    "international-best-track-archive-for-climate-stewardship-ibtracs/"
    "v04r01/access/csv/ibtracs.NA.list.v04r01.csv"
)
GULF_LAT_RANGE = (18.0, 32.0)
GULF_LON_RANGE = (-98.5, -80.0)
DEFAULT_LOOKBACK_YEARS = 5
PYSHAPE_RETRIES = int(os.getenv("PYSHAPE_RETRIES", "5"))

ROOT_DIR = Path(__file__).resolve().parents[1]
BRONZE_DIR = ROOT_DIR / "data" / "bronze" / "hurricanes"
SILVER_DIR = ROOT_DIR / "data" / "silver"
IBTRACS_PATH = BRONZE_DIR / "ibtracs_na.csv"
OUTPUT_PATH = SILVER_DIR / "hurricane_risk_october.csv"

BRONZE_DIR.mkdir(parents=True, exist_ok=True)
SILVER_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("process_hurricane_risk")
logging.basicConfig(level=logging.INFO, format="%(message)s")


@dataclass
class StormMeta:
    atcf_id: str
    season: int


def determine_year_range() -> range:
    current_year = date.today().year
    start_default = current_year - DEFAULT_LOOKBACK_YEARS
    start_year = int(os.getenv("HURRICANE_START", str(start_default)))
    end_year = int(os.getenv("HURRICANE_END", str(current_year)))
    if start_year > end_year:
        start_year, end_year = end_year, start_year
    return range(start_year, end_year + 1)


def download_ibtracs_catalogue() -> pd.DataFrame:
    if IBTRACS_PATH.exists():
        logger.info("Using cached IBTrACS catalogue: %s", IBTRACS_PATH)
        content = IBTRACS_PATH.read_bytes()
    else:
        logger.info("Downloading IBTrACS North Atlantic catalogue")
        response = requests.get(IBTRACS_URL, timeout=120)
        response.raise_for_status()
        content = response.content
        IBTRACS_PATH.write_bytes(content)
        logger.info("✓ Saved IBTrACS catalogue to %s (%d bytes)", IBTRACS_PATH, len(content))

    # Second row contains units; skip it
    df = pd.read_csv(io.BytesIO(content), skiprows=[1])
    return df


def discover_storms(df: pd.DataFrame, years: range) -> List[StormMeta]:
    df = df[df["BASIN"] == "NA"]
    df = df[df["SEASON"].between(min(years), max(years))]
    atcf = df["USA_ATCF_ID"].dropna().astype(str).str.upper().str.strip()
    atcf = atcf[atcf.str.startswith("AL")]

    override = os.getenv("HURRICANE_STORMS")
    if override:
        storms = [storm.strip().upper() for storm in override.split(",") if storm.strip()]
    else:
        storms = sorted(atcf.unique())

    result: List[StormMeta] = []
    for storm_id in storms:
        if len(storm_id) != 8:
            continue
        try:
            season = int(storm_id[-4:])
        except ValueError:
            continue
        if season not in years:
            continue
        result.append(StormMeta(atcf_id=storm_id, season=season))

    if not result:
        logger.warning("No storms found for seasons %s", list(years))
    else:
        logger.info("Identified %d storms between %d–%d", len(result), min(years), max(years))
    return result


def download_storm_shapefile(storm: StormMeta) -> Optional[Path]:
    storm_id = storm.atcf_id.upper()
    zip_path = BRONZE_DIR / f"{storm_id}.zip"
    if zip_path.exists():
        return zip_path

    url = f"https://www.nhc.noaa.gov/gis/best_track/{storm_id.lower()}_best_track.zip"
    logger.info("Fetching best track shapefile for %s", storm_id)

    for attempt in range(1, PYSHAPE_RETRIES + 1):
        try:
            response = requests.get(url, timeout=60)
            if response.status_code == 404:
                logger.warning("Best track shapefile not found for %s", storm_id)
                return None
            response.raise_for_status()
            zip_path.write_bytes(response.content)
            logger.info("✓ Saved %s", zip_path)
            return zip_path
        except requests.RequestException as exc:
            logger.warning(
                "Attempt %d/%d failed for %s (%s)", attempt, PYSHAPE_RETRIES, storm_id, exc
            )
            if attempt == PYSHAPE_RETRIES:
                logger.error("Exceeded retries downloading %s", storm_id)
                return None
    return None


def load_storm_points(storm: StormMeta, zip_path: Path) -> pd.DataFrame:
    storm_id = storm.atcf_id.upper()
    extract_dir = BRONZE_DIR / f"{storm_id}_tmp"
    if extract_dir.exists():
        for child in extract_dir.iterdir():
            child.unlink()
    else:
        extract_dir.mkdir()

    try:
        with zipfile.ZipFile(zip_path) as zf:
            members = {Path(name).name: name for name in zf.namelist()}
            pts_name = members.get(f"{storm_id}_pts.shp")
            if pts_name is None:
                logger.warning("Pts shapefile missing for %s", storm_id)
                return pd.DataFrame()
            zf.extractall(extract_dir)

        shp_path = extract_dir / f"{storm_id}_pts.shp"
        reader = shapefile.Reader(str(shp_path))
        fields = [field[0] for field in reader.fields[1:]]
        records = [dict(zip(fields, rec)) for rec in reader.records()]

        df = pd.DataFrame(records)
        if df.empty:
            return df

        df["STORM_ID"] = storm_id
        return df
    finally:
        for child in extract_dir.iterdir():
            child.unlink()
        extract_dir.rmdir()


def build_daily_risk(fix_df: pd.DataFrame) -> pd.DataFrame:
    if fix_df.empty:
        return pd.DataFrame()

    df = fix_df.copy()

    # Convert DTG (e.g., 2024081118) to timestamp
    def parse_dtg(value: object) -> Optional[pd.Timestamp]:
        if pd.isna(value):
            return None
        value_str = str(value).split(".")[0]
        if len(value_str) == 10:
            fmt = "%Y%m%d%H"
        elif len(value_str) == 12:
            fmt = "%Y%m%d%H%M"
        else:
            return None
        try:
            return pd.to_datetime(value_str, format=fmt)
        except ValueError:
            return None

    df["timestamp"] = df["DTG"].apply(parse_dtg)
    df = df.dropna(subset=["timestamp", "LAT", "LON"])

    df = df[
        (df["LAT"].between(GULF_LAT_RANGE[0], GULF_LAT_RANGE[1]))
        & (df["LON"].between(GULF_LON_RANGE[0], GULF_LON_RANGE[1]))
        & (df["timestamp"].dt.month == 10)
    ]

    if df.empty:
        return df

    df["date"] = df["timestamp"].dt.floor("D")
    df["intensity"] = pd.to_numeric(df.get("INTENSITY"), errors="coerce").fillna(0.0)

    storm_daily = (
        df.groupby(["date", "STORM_ID"], as_index=False)
        .agg(max_wind_kt=("intensity", "max"))
    )

    storm_daily["storm_prob_contrib"] = 0.5  # each storm contributes 0.5 probability mass per day
    storm_daily["shut_in_contrib"] = (storm_daily["max_wind_kt"] / 150.0).clip(0.0, 1.0)

    daily = (
        storm_daily.groupby("date")
        .agg(
            storm_count=("STORM_ID", "nunique"),
            max_wind_kt=("max_wind_kt", "max"),
            storm_prob=("storm_prob_contrib", "sum"),
            shut_in_est=("shut_in_contrib", "max"),
        )
        .reset_index()
    )

    daily["storm_prob"] = daily["storm_prob"].clip(0.0, 1.0)
    daily["shut_in_est"] = daily["shut_in_est"].clip(0.0, 1.0)

    return daily


def main() -> None:
    if shapefile is None:
        logger.error("pyshp is required. Install via `python3 -m pip install pyshp`.")
        return

    years = determine_year_range()
    catalogue = download_ibtracs_catalogue()
    storms = discover_storms(catalogue, years)
    if not storms:
        logger.warning("No storms to process; skipping hurricane risk generation")
        return

    daily_frames: List[pd.DataFrame] = []
    for storm in storms:
        zip_path = download_storm_shapefile(storm)
        if zip_path is None:
            continue
        points = load_storm_points(storm, zip_path)
        if points.empty:
            continue
        daily = build_daily_risk(points)
        if not daily.empty:
            daily_frames.append(daily)

    if not daily_frames:
        logger.warning("No Gulf October storm fixes found in shapefiles; skipping output")
        return

    combined = pd.concat(daily_frames, ignore_index=True)
    combined = (
        combined.groupby("date", as_index=False)
        .agg(
            storm_count=("storm_count", "sum"),
            max_wind_kt=("max_wind_kt", "max"),
            storm_prob=("storm_prob", "sum"),
            shut_in_est=("shut_in_est", "max"),
        )
        .sort_values("date")
    )
    combined["storm_prob"] = combined["storm_prob"].clip(0.0, 1.0)

    combined.to_csv(OUTPUT_PATH, index=False)
    logger.info("✓ Saved hurricane risk features to %s (%d rows)", OUTPUT_PATH, len(combined))


if __name__ == "__main__":
    main()
