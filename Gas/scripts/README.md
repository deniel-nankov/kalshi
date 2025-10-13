# Gas Price Forecasting - Data Collection Scripts

This directory contains scripts for downloading and processing data for the October 31, 2025 forecast.

## Architecture

This project implements a **medallion architecture** with three data layers:
- 📦 **Bronze**: Raw API responses (no transformations)
- 🪙 **Silver**: Cleaned, validated data (standardized columns, types, units)
- ⭐ **Gold**: Feature-engineered, model-ready datasets

See `../data/MEDALLION_ARCHITECTURE.md` for detailed documentation.

## Scripts Overview

### Bronze Layer (Downloads)
1. **download_rbob_data_bronze.py** - Download raw RBOB/WTI futures to Bronze
2. **download_retail_prices_bronze.py** - Download raw retail prices to Bronze
3. **download_eia_data_bronze.py** - Download raw EIA data to Bronze

### Silver Layer (Cleaning)
4. **clean_rbob_to_silver.py** - Clean RBOB/WTI: Bronze → Silver
5. **clean_retail_to_silver.py** - Clean retail prices: Bronze → Silver
6. **clean_eia_to_silver.py** - Clean EIA data: Bronze → Silver

### Gold Layer (Feature Engineering)
7. **build_gold_layer.py** - Join Silver data and engineer features → Gold
### Validation & Pipeline
8. **validate_silver_layer.py** - Sanity checks for Silver layer outputs
9. **validate_gold_layer.py** - Data quality checks for the Gold layer
10. **run_medallion_pipeline.py** - **⭐ Run complete pipeline: Bronze → Silver → Gold**
11. **test_all_downloads.py** - End-to-end verification

### Visualization & Reporting
12. **visualize_layer_transition.py** - Animated comparison of Silver vs Gold price series
13. **report_data_freshness.py** - Generates Silver-layer recency dashboard (PNG|GIF)
### Modeling & Analysis
14. **train_models.py** - Train baseline models and save artefacts/metrics
15. **walk_forward_validation.py** - Horizon-by-year walk-forward evaluation & plots
16. **shap_analysis.py** - Compute SHAP explanations for the Ridge baseline
17. **model_diagnostics.py** - Yellowbrick regression diagnostics (residuals/prediction error)
18. **train_quantile_models.py** - Fit quantile regression bands and metrics
19. **visualize_quantile_regression.py** - Quantile fan chart, pinball loss, residual plots
20. **visualize_model_graph.py** - Graphviz schematic of the baseline ensemble
21. **asym_pass_through_analysis.py** - Behavioral pricing regression (up/down wholesale shocks)
22. **visualize_asym_pass_through.py** - Scatter/heatmap/bar plots for pass-through asymmetry
23. **bayesian_update.py** - Bayesian forecast updates (Oct10/16/23/30)
24. **final_month_forecast.py** - Point + quantile forecast for Oct 31, 2025

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

### Quick Start (Recommended)
```bash
# Run complete medallion pipeline: Bronze → Silver → Gold
python run_medallion_pipeline.py
```

### Manual Step-by-Step

#### Bronze Layer (Download Raw Data)
```bash
python download_rbob_data_bronze.py        # RBOB/WTI futures
python download_retail_prices_bronze.py    # Retail prices
python download_eia_data_bronze.py         # EIA data
```

#### Silver Layer (Clean Data)
```bash
python clean_rbob_to_silver.py       # Clean RBOB/WTI
python clean_retail_to_silver.py     # Clean retail prices
python clean_eia_to_silver.py        # Clean EIA data
python validate_silver_layer.py      # Validate
```

#### Gold Layer (Feature Engineering)
```bash
python build_gold_layer.py           # Build features
python validate_gold_layer.py        # Validate
```

### Legacy Scripts (Direct to Silver)
```bash
# Old approach: downloads directly to Silver (skips Bronze)
python download_rbob_data.py
python download_retail_prices.py
python download_eia_data.py

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
python asym_pass_through_analysis.py    # asymmetric pass-through regression → outputs/asym_pass_through/
python visualize_asym_pass_through.py   # plots behavioural pricing visuals → outputs/asym_pass_through/
python bayesian_update.py               # Bayesian forecast updates (default Oct 10/16/23/30)
python final_month_forecast.py          # deterministic + quantile forecast for Oct 31, 2025
python run_pipeline.py                  # runs core pipeline end-to-end
```

## Expected Runtime

- Silver layer (all downloads): 2-3 hours
- Gold layer (processing): 1-2 hours
- Total: 3-5 hours

## Output

- `data/bronze/` - Raw API responses (immutable)
  - `*_raw.parquet` files
- `data/silver/` - Clean single-source files
  - `*_daily.parquet`, `*_weekly.parquet`
- `data/gold/` - Model-ready feature datasets
  - `master_daily.parquet` (forward-filled fusion of all features)
  - `master_october.parquet` (October-only slice for historical analysis)
  - `master_model_ready.parquet` (rows with complete target + lagged features for training)

`build_gold_layer.py` trims the first few days without retail data and forward-fills weekend gaps so the model-ready table contains zero missing values on core features.

See `../data/MEDALLION_ARCHITECTURE.md` for complete layer documentation.

## Testing

- Unit tests (API client + fetch logic):
  ```bash
  python -m pytest ../tests
  ```
- Full pipeline smoke:
  ```bash
  python test_all_downloads.py
  ```
