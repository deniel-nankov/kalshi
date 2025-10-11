# Gas Price Forecasting - Data Collection Scripts

This directory contains scripts for downloading and processing data for the October 31, 2025 forecast.

## Scripts Overview

1. **download_eia_data.py** - Download EIA weekly inventory, utilization, imports
2. **download_rbob_data.py** - Download NYMEX RBOB futures prices
3. **download_wti_data.py** - Download WTI crude oil prices
4. **download_aaa_data.py** - Download retail gasoline prices (EIA proxy)
5. **build_gold_layer.py** - Join all data and create master modeling table
6. **validate_gold_layer.py** - Run data quality checks

## Setup

```bash
# Install dependencies
pip install pandas numpy requests yfinance pyarrow matplotlib scikit-learn

# Get EIA API key (free)
# Register at: https://www.eia.gov/opendata/register.php
# Add to environment: export EIA_API_KEY="your_key_here"
```

## Usage

```bash
# Run in order:
python download_eia_data.py
python download_rbob_data.py
python download_wti_data.py
python download_aaa_data.py
python build_gold_layer.py
python validate_gold_layer.py
```

## Expected Runtime

- Silver layer (all downloads): 2-3 hours
- Gold layer (processing): 1-2 hours
- Total: 3-5 hours

## Output

- `data/silver/` - Clean single-source files
- `data/gold/` - Master modeling tables
