"""
Download and process PADD3 (Gulf Coast) gasoline share data from EIA.

- Fetches weekly PADD3 gasoline inventory or production data
- Processes to compute share (if needed)
- Saves as padd3_share_weekly.parquet in data/silver/

Instructions:
- You may need to register for an EIA API key: https://www.eia.gov/opendata/
- Replace the URL or API call below with the correct EIA series for PADD3 gasoline
"""
import pandas as pd
from pathlib import Path
import requests
import os

SILVER_DIR = Path(__file__).resolve().parents[2] / "data" / "silver"
SILVER_DIR.mkdir(parents=True, exist_ok=True)

# TODO: Replace with actual EIA API call or CSV download
EIA_SERIES_ID = "PET.W_EPM0_P3_SAE_DPG.W"  # Example: Weekly PADD3 gasoline stocks
import logging
API_KEY = os.getenv("EIA_API_KEY")
if not API_KEY:
	raise RuntimeError("EIA_API_KEY environment variable not set. Please set it to your EIA API key.")


url = f"https://api.eia.gov/series/?api_key={API_KEY}&series_id={EIA_SERIES_ID}"
try:
	resp = requests.get(url)
	resp.raise_for_status()
	try:
		data = resp.json()
	except Exception as e:
		logging.error(f"Failed to parse JSON from EIA response: {e}\nResponse text: {resp.text}")
		raise
except requests.exceptions.RequestException as e:
	logging.error(f"HTTP request to EIA failed: {e}")
	raise

# Validate API response structure
if not isinstance(data, dict) or "series" not in data or not isinstance(data["series"], list) or not data["series"]:
	logging.error(f"EIA API response missing 'series' key or not a list. Response: {data}")
	raise ValueError("EIA API response missing 'series' key or not a list.")
series0 = data["series"][0]
if not isinstance(series0, dict) or "data" not in series0 or not isinstance(series0["data"], list):
	logging.error(f"EIA API response 'series[0]' missing 'data' key or not a list. Response: {series0}")
	raise ValueError("EIA API response 'series[0]' missing 'data' key or not a list.")
if not series0["data"]:
	logging.warning("EIA API returned empty data list.")
	df = pd.DataFrame()
else:
	df = pd.DataFrame(series0["data"], columns=["date", "padd3_share"])
	df["date"] = pd.to_datetime(df["date"])
	df = df.sort_values("date")

# Save as parquet
out_path = SILVER_DIR / "padd3_share_weekly.parquet"
df.to_parquet(out_path, index=False)
print(f"✓ Saved: {out_path}")
