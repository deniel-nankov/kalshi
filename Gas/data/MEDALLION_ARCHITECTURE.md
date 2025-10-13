# Medallion Architecture: Bronze → Silver → Gold

This project implements a proper **medallion data architecture** with three distinct layers:

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                             │
│  Yahoo Finance (RBOB/WTI)  │  EIA API  │  Market Data          │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  📦 BRONZE LAYER - Raw Data                                      │
│  • Exact API responses, no transformations                       │
│  • All original columns preserved                                │
│  • Original data types and formats                               │
│                                                                   │
│  Files: *_raw.parquet                                            │
│  Location: Gas/data/bronze/                                      │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ [Cleaning & Validation Scripts]
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  🪙 SILVER LAYER - Cleaned Data                                  │
│  • Standardized column names                                     │
│  • Consistent data types (dates, floats)                         │
│  • Unit conversions (thousands → millions)                       │
│  • Sanity checks and validation                                  │
│  • Duplicates removed                                            │
│                                                                   │
│  Files: *_daily.parquet, *_weekly.parquet                        │
│  Location: Gas/data/silver/                                      │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ [Feature Engineering Script]
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  ⭐ GOLD LAYER - Model-Ready Data                                │
│  • Feature engineering (lags, spreads, volatility)              │
│  • Multi-source joins                                            │
│  • Forward-filling for continuity                                │
│  • October-specific features                                     │
│  • Complete feature matrix                                       │
│                                                                   │
│  Files: master_daily.parquet, master_october.parquet            │
│  Location: Gas/data/gold/                                        │
└─────────────────────────────────────────────────────────────────┘
```

## 🎯 Layer Definitions

### 📦 Bronze Layer (Raw)
**Purpose**: Immutable raw data exactly as received from source APIs

**Characteristics**:
- No transformations
- All original columns
- Original column names (e.g., "Date", "Close", "period", "value")
- Original data types
- May contain duplicates or errors

**Files**:
- `rbob_daily_raw.parquet` - Raw Yahoo Finance RBOB futures
- `wti_daily_raw.parquet` - Raw Yahoo Finance WTI futures
- `retail_prices_raw.parquet` - Raw EIA retail prices
- `eia_inventory_raw.parquet` - Raw EIA inventory data
- `eia_utilization_raw.parquet` - Raw EIA utilization data
- `eia_imports_raw.parquet` - Raw EIA imports data
- `eia_exports_raw.parquet` - Raw EIA exports data

### 🪙 Silver Layer (Clean)
**Purpose**: Cleaned, validated, standardized single-source datasets

**Transformations**:
- Column renaming: `Date` → `date`, `Close` → `price_rbob`
- Type conversions: strings → datetime, strings → float
- Unit standardization: thousands of barrels → millions
- Duplicate removal
- Date sorting
- Sanity checks (price ranges, inventory bounds)
- Weekly → Daily frequency conversion (forward-fill)

**Files**:
- `rbob_daily.parquet` - Clean RBOB prices (date, price_rbob, volume_rbob)
- `wti_daily.parquet` - Clean WTI prices (date, price_wti)
- `retail_prices_daily.parquet` - Clean retail prices (date, retail_price)
- `eia_inventory_weekly.parquet` - Clean inventory (date, inventory_mbbl)
- `eia_utilization_weekly.parquet` - Clean utilization (date, utilization_pct)
- `eia_imports_weekly.parquet` - Net imports (date, net_imports_kbd)
- `padd3_share_weekly.parquet` - PADD3 share (date, padd3_share)

### ⭐ Gold Layer (Model-Ready)
**Purpose**: Feature-engineered, multi-source datasets ready for ML

**Transformations**:
- Multi-source joins (daily + weekly data)
- Feature engineering:
  - Lags: RBOB_t-3, RBOB_t-7, RBOB_t-14
  - Spreads: crack_spread, retail_margin
  - Volatility: vol_rbob_10d
  - Momentum: delta_rbob_1w
  - Seasonality: winter_blend_effect, days_since_oct1
- Forward-filling for continuity
- October-specific filtering
- Complete case analysis (no missing values)

**Files**:
- `master_daily.parquet` - Full daily panel with all features
- `master_october.parquet` - October-only observations (2020+)
- `master_model_ready.parquet` - Complete cases for training

## 🚀 Quick Start

### Run Complete Pipeline
```bash
cd Gas
python scripts/run_medallion_pipeline.py
```

This executes:
1. ✅ Download raw data → Bronze
2. ✅ Clean data → Silver  
3. ✅ Validate Silver layer
4. ✅ Engineer features → Gold
5. ✅ Validate Gold layer

### Run Individual Steps

#### Bronze Layer (Downloads)
```bash
python scripts/download_rbob_data_bronze.py        # RBOB/WTI futures
python scripts/download_retail_prices_bronze.py    # Retail prices
python scripts/download_eia_data_bronze.py         # EIA inventory/utilization
```

#### Silver Layer (Cleaning)
```bash
python scripts/clean_rbob_to_silver.py       # Clean RBOB/WTI
python scripts/clean_retail_to_silver.py     # Clean retail prices
python scripts/clean_eia_to_silver.py        # Clean EIA data
python scripts/validate_silver_layer.py      # Validate
```

#### Gold Layer (Feature Engineering)
```bash
python scripts/build_gold_layer.py           # Build features
python scripts/validate_gold_layer.py        # Validate
```

## 📁 Directory Structure

```
Gas/
├── data/
│   ├── bronze/              # 📦 Raw API responses
│   │   ├── rbob_daily_raw.parquet
│   │   ├── wti_daily_raw.parquet
│   │   ├── retail_prices_raw.parquet
│   │   ├── eia_inventory_raw.parquet
│   │   ├── eia_utilization_raw.parquet
│   │   ├── eia_imports_raw.parquet
│   │   └── eia_exports_raw.parquet
│   │
│   ├── silver/              # 🪙 Cleaned data
│   │   ├── rbob_daily.parquet
│   │   ├── wti_daily.parquet
│   │   ├── retail_prices_daily.parquet
│   │   ├── eia_inventory_weekly.parquet
│   │   ├── eia_utilization_weekly.parquet
│   │   └── eia_imports_weekly.parquet
│   │
│   └── gold/                # ⭐ Model-ready data
│       ├── master_daily.parquet
│       ├── master_october.parquet
│       └── master_model_ready.parquet
│
└── scripts/
    ├── download_*_bronze.py      # Bronze layer downloads
    ├── clean_*_to_silver.py      # Silver layer cleaning
    ├── build_gold_layer.py        # Gold layer feature engineering
    ├── validate_*_layer.py        # Layer validation
    └── run_medallion_pipeline.py # Full pipeline orchestration
```

## 🔄 Data Flow

### Example: RBOB Futures

**Bronze → Silver → Gold**

```python
# BRONZE: Raw Yahoo Finance response
{
  'Date': Timestamp('2025-10-10 00:00:00+0000'),
  'Open': 2.15,
  'High': 2.18,
  'Low': 2.13,
  'Close': 2.16,
  'Volume': 12543,
  'Dividends': 0,
  'Stock Splits': 0
}

# ↓ clean_rbob_to_silver.py

# SILVER: Cleaned, standardized
{
  'date': datetime64('2025-10-10'),
  'price_rbob': 2.16,
  'volume_rbob': 12543.0
}

# ↓ build_gold_layer.py

# GOLD: Feature-engineered
{
  'date': datetime64('2025-10-10'),
  'price_rbob': 2.16,
  'rbob_lag3': 2.18,
  'rbob_lag7': 2.22,
  'rbob_lag14': 2.19,
  'crack_spread': 1.45,       # RBOB - WTI
  'retail_margin': 0.98,      # retail - RBOB
  'vol_rbob_10d': 0.034,
  'delta_rbob_1w': -0.06,
  'winter_blend_effect': -0.08,
  'days_since_oct1': 9
}
```

## ✅ Validation

Each layer has validation checks:

**Bronze**:
- ✓ Files exist
- ✓ Non-empty DataFrames
- ✓ API columns present

**Silver**:
- ✓ Standard column names
- ✓ Correct data types
- ✓ Date ranges (2020-10-01 onward)
- ✓ Value ranges (prices, inventory, utilization)
- ✓ No duplicates
- ✓ Sufficient row counts

**Gold**:
- ✓ All features present
- ✓ Proper joins (no unexpected missing values)
- ✓ Feature value ranges
- ✓ October subset exists
- ✓ Model-ready dataset has complete cases

## 🎓 Benefits of Medallion Architecture

1. **Reproducibility**: Can rebuild Silver/Gold from Bronze anytime
2. **Debugging**: Easy to trace issues to specific transformation
3. **Flexibility**: Can change Silver/Gold logic without re-downloading
4. **Auditing**: Raw data preserved for verification
5. **Performance**: Only download once, transform many times
6. **Testing**: Can unit test each transformation independently

## 📚 References

- [Databricks Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)
- [Data Lake Best Practices](https://docs.aws.amazon.com/prescriptive-guidance/latest/defining-bucket-names-data-lakes/data-lake-layers.html)

## 🔧 Maintenance

### Re-download fresh data
```bash
# Downloads new data, overwrites Bronze
python scripts/download_rbob_data_bronze.py
python scripts/clean_rbob_to_silver.py
```

### Re-engineer features
```bash
# Silver unchanged, rebuild Gold with new features
python scripts/build_gold_layer.py
```

### Full refresh
```bash
# Nuclear option: delete all layers and rebuild
# ⚠️  WARNING: This will permanently delete ALL data layers!
echo "WARNING: This will delete all Bronze, Silver, and Gold data layers."
echo "Type 'DELETE' (in capitals) to confirm:"
read -r confirmation
if [ "$confirmation" != "DELETE" ]; then
    echo "Aborted. No data was deleted."
    exit 1
fi

rm -rf Gas/data/bronze Gas/data/silver Gas/data/gold
python scripts/run_medallion_pipeline.py
```
