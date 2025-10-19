# Rigorous Medallion Architecture Workflow

**Project:** Kalshi Gas Price Forecasting  
**Date:** October 18, 2025  
**Purpose:** End-to-end data pipeline with validation, leakage detection, and quality assurance

---

## 🏗️ **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES (APIs)                       │
│  EIA • FRED • NOAA • CME Futures • Manual OPEC Coding          │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BRONZE LAYER (Raw)                           │
│  • Exact API responses (no transformations)                     │
│  • Append-only (immutable)                                      │
│  • Full audit trail                                             │
└────────────┬────────────────────────────────────────────────────┘
             │ Validation: Schema, nulls, duplicates
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SILVER LAYER (Cleaned)                       │
│  • Standardized schemas                                         │
│  • Outlier detection                                            │
│  • Quality scores                                               │
└────────────┬────────────────────────────────────────────────────┘
             │ Validation: Temporal order, sanity checks
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     GOLD LAYER (Features)                        │
│  • Feature engineering                                          │
│  • Lag enforcement (CRITICAL for leakage)                       │
│  • Model-ready dataset                                          │
└────────────┬────────────────────────────────────────────────────┘
             │ Validation: Leakage tests, correlation checks
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     MODELS (Training)                            │
│  • Walk-forward validation                                      │
│  • Hyperparameter tuning                                        │
│  • Ensemble methods                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 **Complete Data Inventory**

### **1. Core EIA Data (Bronze → Silver → Gold)**

| Dataset | Source | Frequency | Bronze Status | Silver Status |
|---------|--------|-----------|---------------|---------------|
| Retail Gas Prices | EIA API | Weekly | ✅ Real | ✅ Real |
| RBOB Futures | CME/EIA | Daily | ✅ Real | ✅ Real |
| WTI Crude | EIA API | Daily | ✅ Real | ✅ Real |
| Gasoline Inventory | EIA PSR | Weekly | ✅ Real | ✅ Real |
| Refinery Utilization | EIA PSR | Weekly | ✅ Real | ✅ Real |
| Net Imports | EIA PSR | Weekly | ✅ Real | ✅ Real |

### **2. External Data (Direct to Gold - Needs Bronze/Silver)**

| Dataset | Source | Frequency | Current Status | Action Needed |
|---------|--------|-----------|----------------|---------------|
| SPR Stocks | EIA API | Weekly | ✅ Real (fixed) | ✅ Move to Bronze |
| SPR Releases | Calculated | Weekly | ✅ Fixed leakage | ✅ Validate lag |
| Unemployment | FRED API | Monthly | ✅ Real | ✅ Move to Bronze |
| Vehicle Miles | FRED API | Monthly | ✅ Real | ✅ Move to Bronze |
| Consumer Sentiment | FRED API | Monthly | ✅ Real | ✅ Move to Bronze |
| OPEC Cuts | Manual | Event-based | ✅ Verified | ✅ Move to Bronze |
| Sanctions | Manual | Binary | ✅ Real dates | ✅ Move to Bronze |
| Refinery Outages | Synthetic | Daily | ❌ **FAKE** | ❌ **REMOVE** |

### **3. Weather Data (Bronze → Silver → Gold)**

| Dataset | Source | Frequency | Bronze Status | Silver Status |
|---------|--------|-----------|---------------|---------------|
| Hurricane Data | NOAA API | 6-hourly | ✅ Real | ✅ Real |
| Temperature | NOAA API | Daily | ✅ Real | ✅ Real |

---

## 🔄 **Complete Pipeline Workflow**

### **Phase 1: Bronze Layer (Raw Ingestion)**

**Script:** `scripts/download_to_bronze.py` (NEW - to create)

```python
# Responsibilities:
# 1. Fetch raw data from APIs
# 2. Save exact responses (no transformations)
# 3. Add metadata (fetch_timestamp, source_url)
# 4. Validate schema on write
# 5. Detect duplicates
```

**Bronze Validation Checks:**
- ✅ Schema compliance (expected columns present)
- ✅ No duplicate records (by date/timestamp)
- ✅ Fetch timestamp recorded
- ✅ Source URL/API endpoint logged
- ✅ HTTP status codes saved

**Output Location:** `data/bronze/`

---

### **Phase 2: Silver Layer (Cleaning)**

**Script:** `scripts/clean_bronze_to_silver.py` (EXISTS - enhance)

```python
# Responsibilities:
# 1. Standardize column names
# 2. Convert data types
# 3. Handle missing values (flag, don't impute)
# 4. Detect outliers (flag, don't remove)
# 5. Add quality scores
```

**Silver Validation Checks:**
- ✅ Date continuity (no gaps >30 days)
- ✅ Value ranges (min/max sanity checks)
- ✅ Outlier detection (z-score > 3 flagged)
- ✅ Null percentage < 5%
- ✅ No future dates

**Output Location:** `data/silver/`

---

### **Phase 3: Gold Layer (Feature Engineering)**

**Script:** `scripts/build_gold_layer.py` (EXISTS - enhance validation)

```python
# Responsibilities:
# 1. Merge all silver datasets
# 2. Create features with STRICT lag enforcement
# 3. Forward fill ONLY when appropriate
# 4. Create horizon-specific targets
# 5. Run leakage detection tests
```

**Gold Validation Checks:**
- ✅ **CRITICAL: Temporal integrity** (no future leakage)
- ✅ **Target correlation check** (corr < 0.50 for lagged features)
- ✅ Feature completeness (no NaNs in model features)
- ✅ Date alignment (all rows have consistent date)
- ✅ Horizon validation (target is N days ahead)

**Output Location:** `data/gold/`

---

## 🚨 **Data Leakage Prevention (CRITICAL)**

### **Rule 1: All Features Must Be Lagged by Forecast Horizon**

```python
# CORRECT (14-day horizon):
df['feature_t'] = df['raw_value'].shift(14)  # Use data from 14 days ago

# WRONG:
df['feature_t'] = df['raw_value']  # Uses same-day data!
```

### **Rule 2: Diff/Change Features Must Be Double-Lagged**

```python
# CORRECT (14-day horizon):
df['change'] = df['value'].diff().shift(14)  # Shift AFTER diff

# WRONG:
df['change'] = df['value'].diff()  # Future leakage!
```

### **Rule 3: Forward Fill Only for Slow-Moving Variables**

```python
# OK to forward fill:
- unemployment_rate (monthly → daily)
- consumer_sentiment (monthly → daily)
- OPEC cuts (event-based → daily)

# NEVER forward fill:
- prices (changes daily)
- inventory (changes weekly, but volatile)
- utilization (changes weekly, sensitive)
```

### **Rule 4: Validation Test**

```python
def test_no_leakage(df, feature_col, target_col, horizon):
    """
    Test if feature at time t predicts target at t+horizon
    WITHOUT using information from t+1 to t+horizon.
    """
    correlation = df[feature_col].corr(df[target_col])
    
    # For properly lagged features:
    # - Direct correlations should be < 0.50
    # - Suspiciously high (>0.60) indicates leakage
    
    assert abs(correlation) < 0.50, f"Leakage detected: {correlation:.3f}"
```

---

## ✅ **Comprehensive Validation Script**

I'll create a master validation script that runs ALL checks:

**Script:** `scripts/validate_full_pipeline.py` (NEW)

```python
# Validation Stages:
# 1. Bronze: Raw data integrity
# 2. Silver: Cleaned data quality  
# 3. Gold: Feature leakage detection
# 4. Model: Walk-forward validation
```

---

## 📁 **Required Directory Structure**

```
Gas/
├── data/
│   ├── bronze/          # Raw API responses
│   │   ├── eia_retail_prices_raw.parquet
│   │   ├── eia_inventory_raw.parquet
│   │   ├── eia_utilization_raw.parquet
│   │   ├── eia_spr_raw.parquet
│   │   ├── fred_unemployment_raw.parquet
│   │   ├── fred_vmt_raw.parquet
│   │   ├── fred_sentiment_raw.parquet
│   │   ├── noaa_hurricanes_raw.parquet
│   │   └── metadata/    # Fetch logs, schemas
│   │
│   ├── silver/          # Cleaned, standardized
│   │   ├── eia_retail_prices_cleaned.parquet
│   │   ├── eia_inventory_weekly.parquet
│   │   ├── eia_utilization_weekly.parquet
│   │   ├── spr_stocks_weekly.parquet
│   │   ├── fred_macro_monthly.parquet
│   │   ├── hurricane_enhanced.parquet
│   │   └── quality_reports/
│   │
│   ├── gold/            # Feature-engineered
│   │   ├── master_daily.parquet
│   │   ├── master_model_ready.parquet
│   │   └── validation_reports/
│   │
│   └── external/        # TO BE DEPRECATED (move to bronze)
│       └── [old files to migrate]
│
├── scripts/
│   ├── 1_download_to_bronze.py      # NEW
│   ├── 2_clean_to_silver.py         # Enhance existing
│   ├── 3_build_gold_layer.py        # Enhance existing
│   ├── 4_validate_pipeline.py       # NEW
│   └── 5_train_models.py            # Existing
```

---

## 🎯 **Implementation Plan**

Let me create the complete validated pipeline now...

