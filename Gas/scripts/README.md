# Gas Price Forecasting - Data Collection Scripts

This directory contains scripts for downloading and processing data for the October 31, 2025 forecast.

## Scripts Overview

1. **download_rbob_data.py** - Download NYMEX RBOB futures and WTI crude prices from Yahoo Finance
2. **download_retail_prices.py** - Download AAA/EIA retail gasoline price series
3. **download_eia_data.py** - Download EIA weekly inventory, utilization, imports
4. **download_padd3_data.py** - Derive Gulf Coast (PADD3) supply share feature
5. **build_gold_layer.py** - Join all Silver data and create the master modeling tables (daily / October / model-ready)
6. **validate_silver_layer.py** - Sanity checks for Silver layer outputs
7. **validate_gold_layer.py** - Data quality checks for the Gold layer
8. **test_all_downloads.py** - End-to-end verification of download + validation pipeline
9. **visualize_layer_transition.py** - Animated comparison of Silver vs Gold price series
10. **report_data_freshness.py** - Generates Silver-layer recency dashboard (PNG|GIF)
11. **train_models.py** - Train baseline models and save artefacts/metrics
12. **walk_forward_validation.py** - Horizon-by-year walk-forward evaluation & plots
13. **shap_analysis.py** - Compute SHAP explanations for the Ridge baseline
14. **model_diagnostics.py** - Yellowbrick regression diagnostics (residuals/prediction error)
15. **train_quantile_models.py** - Fit quantile regression bands and metrics
16. **visualize_quantile_regression.py** - Quantile fan chart, pinball loss, residual plots
17. **visualize_model_graph.py** - Graphviz schematic of the baseline ensemble
18. **run_pipeline.py** - Orchestrate build → validate → model → reports

## Setup & Credentials

- Install dependencies:
  ```bash
  pip install pandas numpy requests yfinance pyarrow matplotlib scikit-learn pytest
  ```
- Add your EIA API key to the environment or the project `.env` file:
  ```bash
  export EIA_API_KEY="your_key_here"
  ```
  (Scripts look for `EIA_API_KEY` first, then fall back to `.env`.)

## Usage

```bash
# Silver layer downloads
python download_rbob_data.py
python download_retail_prices.py
python download_eia_data.py
python download_padd3_data.py

# Validation + Gold layer
python validate_silver_layer.py
python build_gold_layer.py
python validate_gold_layer.py

# Integration sweep
python test_all_downloads.py

# Visualization
python visualize_layer_transition.py  # generates outputs/silver_gold_prices.gif & outputs/silver_gold_fundamentals.gif
python report_data_freshness.py         # generates outputs/data_freshness_report.(png|gif)

# Modeling
python train_models.py                  # trains baseline models → outputs/models/
python walk_forward_validation.py       # walk-forward metrics → outputs/walk_forward/
python shap_analysis.py                 # saves SHAP plots → outputs/interpretability/
python model_diagnostics.py             # saves Yellowbrick diagnostics → outputs/model_diagnostics/
python train_quantile_models.py         # fits quantile regression → outputs/quantile_regression/
python visualize_quantile_regression.py # plots quantile fan chart/pinball/residuals
python visualize_model_graph.py         # renders ensemble flow diagram → outputs/visualizations/
python run_pipeline.py                  # runs core pipeline end-to-end
```

## Expected Runtime

- Silver layer (all downloads): 2-3 hours
- Gold layer (processing): 1-2 hours
- Total: 3-5 hours

## Output

- `data/silver/` - Clean single-source files
- `data/gold/`
  - `master_daily.parquet` (forward-filled fusion of all features)
  - `master_october.parquet` (October-only slice for historical analysis)
  - `master_model_ready.parquet` (rows with complete target + lagged features for training)

`build_gold_layer.py` trims the first few days without retail data and forward-fills weekend gaps so the model-ready table contains zero missing values on core features.

## Testing

- Unit tests (API client + fetch logic):
  ```bash
  python -m pytest ../tests
  ```
- Full pipeline smoke:
  ```bash
  python test_all_downloads.py
  ```
