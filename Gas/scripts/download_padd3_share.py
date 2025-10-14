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
API_KEY = "YOUR_EIA_API_KEY"

url = f"https://api.eia.gov/series/?api_key={API_KEY}&series_id={EIA_SERIES_ID}"
resp = requests.get(url)
data = resp.json()

# TODO: Parse and process data as needed
# Example assumes data['series'][0]['data'] is a list of [date, value]
df = pd.DataFrame(data['series'][0]['data'], columns=["date", "padd3_share"])
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

# Save as parquet
out_path = SILVER_DIR / "padd3_share_weekly.parquet"
df.to_parquet(out_path, index=False)
print(f"✓ Saved: {out_path}")
