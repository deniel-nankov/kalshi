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

NOAA_TOKEN = "YOUR_NOAA_TOKEN"
STATION_ID = "GHCND:USW00012918"  # Example: Houston, TX
START_DATE = "2020-01-01"
END_DATE = "2024-12-31"

headers = {"token": NOAA_TOKEN}
url = f"https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=GHCND&datatypeid=TAVG&stationid={STATION_ID}&startdate={START_DATE}&enddate={END_DATE}&units=metric&limit=1000"
resp = requests.get(url, headers=headers)
data = resp.json()

# TODO: Parse and process data as needed
# Example assumes data['results'] is a list of dicts with 'date' and 'value'
df = pd.DataFrame(data['results'])
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

# Save as parquet
out_path = SILVER_DIR / "noaa_temp_daily.parquet"
df.to_parquet(out_path, index=False)
print(f"✓ Saved: {out_path}")
