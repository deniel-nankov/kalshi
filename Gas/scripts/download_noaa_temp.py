"""
Download and process daily temperature data from NOAA.

- Fetches daily temperature data for a specified location or region
- Cleans and saves as noaa_temp_daily.parquet in data/silver/

Instructions:
- Register for a NOAA CDO API token: https://www.ncdc.noaa.gov/cdo-web/token
- Replace the station/location and date range as needed
"""
import pandas as pd
from pathlib import Path
import requests
import os

SILVER_DIR = Path(__file__).resolve().parents[2] / "data" / "silver"
SILVER_DIR.mkdir(parents=True, exist_ok=True)

import logging
NOAA_TOKEN = os.getenv("NOAA_TOKEN")
if not NOAA_TOKEN:
	raise RuntimeError("NOAA_TOKEN environment variable not set. Please set it to your NOAA API token.")
STATION_ID = "GHCND:USW00012918"  # Example: Houston, TX
START_DATE = "2020-01-01"
END_DATE = "2024-12-31"


headers = {"token": NOAA_TOKEN}
url = f"https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=GHCND&datatypeid=TAVG&stationid={STATION_ID}&startdate={START_DATE}&enddate={END_DATE}&units=metric&limit=1000"
try:
	resp = requests.get(url, headers=headers)
	resp.raise_for_status()
	try:
		data = resp.json()
	except Exception as e:
		logging.error(f"Failed to parse JSON from NOAA response: {e}\nResponse text: {resp.text}")
		raise
except requests.exceptions.RequestException as e:
	logging.error(f"HTTP request to NOAA failed: {e}")
	raise

# Validate API response
if not isinstance(data, dict) or "results" not in data or not isinstance(data["results"], list):
	logging.error(f"NOAA API response missing 'results' key or not a list. Response: {data}")
	raise ValueError("NOAA API response missing 'results' key or not a list.")
if not data["results"]:
	logging.warning("NOAA API returned empty results list.")
	df = pd.DataFrame()
else:
	df = pd.DataFrame(data["results"])
	if "date" in df.columns:
		df["date"] = pd.to_datetime(df["date"])
	df = df.sort_values("date")

# Save as parquet
out_path = SILVER_DIR / "noaa_temp_daily.parquet"
df.to_parquet(out_path, index=False)
print(f"✓ Saved: {out_path}")
