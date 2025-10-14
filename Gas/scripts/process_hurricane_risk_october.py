"""
Process historical hurricane risk for October from NOAA HURDAT2.

- Downloads or loads HURDAT2 data
- Computes October hurricane risk metric (e.g., probability, count)
- Saves as hurricane_risk_october.csv in data/silver/

Instructions:
- Download HURDAT2: https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2022-120922.txt
- Parse for October events and compute risk
"""
import pandas as pd
from pathlib import Path
import os

SILVER_DIR = Path(__file__).resolve().parents[2] / "data" / "silver"
SILVER_DIR.mkdir(parents=True, exist_ok=True)

# TODO: Download and parse HURDAT2, extract October hurricanes
# Example: count hurricanes per October, compute probability
# Save as CSV with columns: date, hurricane_risk

# Placeholder: create empty DataFrame
out_path = SILVER_DIR / "hurricane_risk_october.csv"
pd.DataFrame({"date": [], "hurricane_risk": []}).to_csv(out_path, index=False)
print(f"✓ Saved: {out_path}")
