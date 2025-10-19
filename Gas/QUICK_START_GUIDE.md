# Quick Start Guide - Gas Price Forecasting Models

**Last Updated:** October 17, 2025  
**Best Model:** Gradient Boosting (R²=0.214, MAE=$0.037)  
**Current Forecast:** October 31, 2025 → $3.00/gal (bearish -1.92%)

---

## 🚀 Quick Commands

### Generate New Forecast
```bash
# October 31, 2025 forecast (14-day ahead)
python scripts/generate_october_forecast.py

# Output: outputs/forecasts/october_31_2025_forecast.csv
```

### Retrain Models (with latest data)
```bash
# Full model suite (Ridge, GB, Ensemble)
python scripts/train_models.py --horizon 14

# Ridge compact only (45 features)
python scripts/train_ridge_compact.py --horizon 14

# Output: outputs/models/*_model.joblib
```

### Feature Importance Analysis
```bash
# Comprehensive analysis (permutation + SHAP)
python scripts/feature_importance_analysis.py

# Output: outputs/interpretability/*
```

### Update Gold Layer (refresh data)
```bash
# Rebuild with latest bronze/silver data
python scripts/build_gold_layer.py

# Output: data/gold/master_model_ready.parquet (91 features, 1,816 rows)
```

---

## 📊 Model Selection Guide

### Use Gradient Boosting When:
✅ Maximum predictive accuracy needed  
✅ Comfortable with "black box" model  
✅ Forecasting for trading/betting (Kalshi)  
✅ Have 76 features available  

**Model:** `outputs/models/gradient_boosting_model.joblib`  
**Performance:** R²=0.214, MAE=$0.037

### Use Ridge Compact When:
✅ Need model interpretability  
✅ Want linear coefficients for explanation  
✅ Have only top 45 features  
✅ Prefer simpler model  

**Model:** `outputs/models/ridge_compact_model.joblib`  
**Performance:** R²=0.238, MAE=$0.037

### Use Ensemble When:
✅ Want robustness to model errors  
✅ Diversification across model types  
✅ Confidence intervals important  

**Models:** All 5 models (Ridge, GB, Inventory, Futures, Ensemble)  
**Performance:** R²=0.182, MAE=$0.038

---

## 📁 Key Files Reference

### Data Files
```
data/gold/master_model_ready.parquet  # Main dataset (1,816 rows, 91 features)
data/gold/master_daily_panel.parquet  # Full daily panel (1,837 rows)
data/gold/october_subset.parquet      # October-only (166 rows)
```

### Model Files
```
outputs/models/gradient_boosting_model.joblib    # ⭐ BEST (R²=0.214)
outputs/models/ridge_compact_model.joblib        # 45 features (R²=0.238)
outputs/models/ridge_baseline_model.joblib       # 76 features (R²=0.207)
outputs/models/ensemble_weighted_*               # Ensemble predictions
```

### Forecast Files
```
outputs/forecasts/october_31_2025_forecast.csv           # Ensemble forecast
outputs/forecasts/october_31_2025_model_predictions.csv  # Individual models
```

### Analysis Files
```
outputs/interpretability/feature_importance_consensus.csv  # Feature rankings
outputs/interpretability/shap_summary_gb.png              # SHAP plots
outputs/interpretability/compact_feature_list.txt         # Top 45 features
```

### Documentation
```
TIER1_FEATURE_RESULTS.md          # Tier 1 feature analysis
PHASE2_IMPROVEMENT_SUMMARY.md     # This session's improvements
OCTOBER_31_FORECAST.md            # Forecast details
HORIZON_14_RESULTS.md             # Horizon correction analysis
```

---

## 🎯 Feature Sets Reference

### COMMON_FEATURES (76 features) - Full Set
**Use for:** Gradient Boosting, Ridge Full, Ensemble  
**Location:** `src/models/baseline_models.py` line 32  
**Categories:** Price (14), Inventory (7), Production (4), Hurricane (14), Seasonality (8), Technical (18), Tier 1 (11)

### COMMON_FEATURES_COMPACT (45 features) - Optimized
**Use for:** Ridge Compact  
**Location:** `src/models/baseline_models.py` line 87  
**Top Features:**
1. retail_price_lag7 (strongest predictor)
2. winter_blend_effect (seasonality)
3. retail_price_lag14 (momentum)
4. util_inv_interaction (supply constraint)
5. crack_spread_ma21 (profitability)

---

## 📈 Performance Benchmarks

### Test Set Performance (Oct 2024 - Oct 2025, 366 days)

| Model | R² | RMSE | MAE | Features | Speed |
|-------|------|------|-----|----------|-------|
| **GB (Best)** | **0.214** | **$0.047** | **$0.037** | 76 | Fast |
| Ridge Compact | 0.238 | $0.046 | $0.037 | 45 | Fastest |
| Ridge Full | 0.207 | $0.047 | $0.037 | 76 | Fastest |
| Ensemble | 0.182 | $0.048 | $0.038 | 76 | Medium |

**Interpretation:**
- R² = 0.214 means model explains 21.4% of price variance (realistic for 14-day forecasting)
- MAE = $0.037 means average error is ±3.7¢/gallon
- For current price ~$3.00/gal, that's ±1.2% error

---

## 🔧 Troubleshooting

### Issue: "Model file not found"
**Solution:** Retrain models
```bash
python scripts/train_models.py --horizon 14
python scripts/train_ridge_compact.py --horizon 14
```

### Issue: "Missing features in dataset"
**Solution:** Rebuild gold layer
```bash
python scripts/build_gold_layer.py
```

### Issue: "Data too old"
**Solution:** Update bronze/silver layers first
```bash
# Update bronze layer (EIA API)
python scripts/update_bronze_data.py

# Update silver layer
python scripts/build_silver_layer.py

# Then rebuild gold
python scripts/build_gold_layer.py
```

### Issue: "Forecast date unavailable"
**Solution:** Check data date range
```python
import pandas as pd
df = pd.read_parquet('data/gold/master_model_ready.parquet')
print(f"Date range: {df.index[0]} to {df.index[-1]}")
```

---

## 📊 Interpreting Forecasts

### Forecast Output Columns
```csv
forecast_date,forecast_from,horizon_days,point_forecast,lower_95,upper_95,mae,current_price,expected_change,expected_change_pct
2025-10-31,2025-10-17,14,3.0021,2.9288,3.0755,0.0374,3.0610,-0.0589,-1.92
```

**Columns:**
- `point_forecast`: Best estimate ($3.00/gal)
- `lower_95`/`upper_95`: 95% confidence interval ($2.93-$3.08)
- `expected_change`: Predicted price movement (-$0.06 = bearish)
- `expected_change_pct`: Percentage change (-1.92%)

### Trading Signals
- **Bullish (>+1%):** BUY 'Yes' on price increase markets
- **Bearish (<-1%):** BUY 'No' on price increase markets
- **Neutral (-1% to +1%):** AVOID or wait for more data

### Confidence Assessment
- **High confidence:** Model agreement <$0.05, interval width <$0.10
- **Medium confidence:** Model agreement $0.05-$0.10, interval width $0.10-$0.15
- **Low confidence:** Model agreement >$0.10, interval width >$0.15

**Current forecast (Oct 31):**
- Model agreement: $0.074 (medium)
- Interval width: $0.147 (medium)
- **Confidence:** MEDIUM

---

## 🔄 Daily Workflow

### 1. Update Data (Daily)
```bash
# 8:00 AM: EIA releases weekly data (Wednesdays)
python scripts/update_bronze_data.py     # Pull latest EIA
python scripts/build_silver_layer.py     # Process to silver
python scripts/build_gold_layer.py       # Create model-ready
```

### 2. Check Model Performance (Weekly)
```bash
# After data update, retrain and evaluate
python scripts/train_models.py --horizon 14
python scripts/evaluate_models.py        # Generate performance report
```

### 3. Generate Forecasts (As Needed)
```bash
# Before Kalshi market decisions
python scripts/generate_october_forecast.py

# Review outputs/forecasts/*.csv
# Execute trades based on signals
```

### 4. Monitor Feature Importance (Monthly)
```bash
# Check if feature rankings changed
python scripts/feature_importance_analysis.py

# Review outputs/interpretability/feature_importance_consensus.csv
# Update COMMON_FEATURES_COMPACT if needed
```

---

## 🎯 Next Improvements (Roadmap)

### Phase 3: External Data Integration (2-3 weeks)
**Expected Gain:** +5-10% R²

**Priority Features:**
1. **Refinery outages** (EIA Table 1, 4, 5) → +2-3% R²
2. **SPR releases** (EIA SPR API) → +1-2% R²
3. **OPEC production** (manual) → +1-2% R²
4. **Macroeconomic** (FRED API) → +1-2% R²

**Script to create:** `scripts/fetch_external_data.py`

### Phase 4: Model Robustness (1-2 weeks)
**Expected Gain:** +2-5% R²

**Enhancements:**
1. Walk-forward validation (rolling test sets)
2. Regime detection (normal vs. crisis)
3. Ensemble weight optimization
4. Prediction interval calibration

### Phase 5: Deployment Automation (1 week)
**Goal:** Hands-off daily forecasting

**Components:**
1. Airflow DAG for data pipeline
2. Auto-retraining scheduler
3. Kalshi API integration
4. Email/Slack alerts

---

## 📞 Support

### Error Logs
```bash
# Check Python traceback
tail -f outputs/logs/training.log
tail -f outputs/logs/forecast.log
```

### Model Diagnostics
```python
# Check model details
import joblib
model = joblib.load('outputs/models/gradient_boosting_model.joblib')
print(model.named_steps['gb'].get_params())
```

### Feature Coverage
```python
# Check for missing values
import pandas as pd
df = pd.read_parquet('data/gold/master_model_ready.parquet')
print(df[COMMON_FEATURES].isnull().sum())
```

---

**Quick Reference Version:** 1.0  
**Last Model Training:** October 17, 2025  
**Best Model File:** `gradient_boosting_model.joblib`  
**Current Forecast:** $3.00/gal (Oct 31, bearish)
