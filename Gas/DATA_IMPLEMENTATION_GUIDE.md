# Data Layer Implementation Guide

**Based on architecture.md specifications**

This guide provides step-by-step instructions to implement the Silver and Gold data layers for your October 31, 2025 gas price forecast.

---

## 📋 Overview

**Time Budget**: 2-3 days total
- Silver Layer: 4-6 hours (data collection + basic cleaning)
- Gold Layer: 1-2 days (joins, forward-fill, feature engineering)

**Data Sources**: 4 primary sources (all free/accessible)
1. EIA (Energy Information Administration) - Weekly inventory/utilization
2. NYMEX (CME Group) - Daily RBOB futures
3. AAA - Daily retail gasoline prices
4. NOAA - Temperature data (optional, low priority)

---

## 🪙 Phase 1: Silver Layer (4-6 hours)

### Goal
Create clean, validated single-source files with consistent units and dates.

### Directory Setup

```bash
# Create directory structure
cd /Users/christianlee/Downloads/Kalshi/Gas
mkdir -p data/silver
mkdir -p data/gold
mkdir -p data/raw
```

---

### Source 1: EIA Weekly Petroleum Status Report

**What you need**:
- Gasoline stocks (total U.S.)
- Refinery utilization rate
- Imports/exports
- Production

**How to get it**:

```python
# File: scripts/download_eia_data.py

import pandas as pd
import requests
import os

# EIA API key (free, register at https://www.eia.gov/opendata/)
API_KEY = "YOUR_EIA_API_KEY"  # Get from https://www.eia.gov/opendata/register.php

def download_eia_inventory():
    """Download weekly gasoline inventory data"""
    # Series ID for Total Motor Gasoline Stocks (Thousand Barrels)
    series_id = "PET.WGTSTUS1.W"
    
    url = f"https://api.eia.gov/v2/petroleum/stoc/wstk/data/?api_key={API_KEY}&data[0]=value&facets[series][]={series_id}&frequency=weekly&start=2020-10-01"
    
    response = requests.get(url)
    data = response.json()
    
    # Parse into dataframe
    df = pd.DataFrame(data['response']['data'])
    df['date'] = pd.to_datetime(df['period'])
    df['inventory_mbbl'] = df['value'].astype(float) / 1000  # Convert to millions
    df = df[['date', 'inventory_mbbl']].sort_values('date')
    
    # Sanity check
    assert df['inventory_mbbl'].min() > 180, "Inventory too low (data error?)"
    assert df['inventory_mbbl'].max() < 350, "Inventory too high (data error?)"
    
    # Save to silver
    df.to_parquet('data/silver/eia_inventory_weekly.parquet', index=False)
    print(f"✓ Downloaded {len(df)} weeks of inventory data")
    return df

def download_eia_utilization():
    """Download weekly refinery utilization rate"""
    series_id = "PET.WPULEUS3.W"  # Percent Utilization of Refinery Operable Capacity
    
    url = f"https://api.eia.gov/v2/petroleum/pnp/wiup/data/?api_key={API_KEY}&data[0]=value&facets[series][]={series_id}&frequency=weekly&start=2020-10-01"
    
    response = requests.get(url)
    data = response.json()
    
    df = pd.DataFrame(data['response']['data'])
    df['date'] = pd.to_datetime(df['period'])
    df['utilization_pct'] = df['value'].astype(float)
    df = df[['date', 'utilization_pct']].sort_values('date')
    
    # Sanity check
    assert df['utilization_pct'].min() > 50, "Utilization too low"
    assert df['utilization_pct'].max() < 100, "Utilization over 100%"
    
    df.to_parquet('data/silver/eia_utilization_weekly.parquet', index=False)
    print(f"✓ Downloaded {len(df)} weeks of utilization data")
    return df

def download_eia_imports():
    """Download weekly imports minus exports"""
    # Net imports = Imports - Exports
    imports_series = "PET.WGTIMUS2.W"
    exports_series = "PET.WGTEXUS2.W"
    
    # Download imports
    url_imports = f"https://api.eia.gov/v2/petroleum/move/wkly/data/?api_key={API_KEY}&data[0]=value&facets[series][]={imports_series}&frequency=weekly&start=2020-10-01"
    imports_data = requests.get(url_imports).json()
    df_imports = pd.DataFrame(imports_data['response']['data'])
    
    # Download exports
    url_exports = f"https://api.eia.gov/v2/petroleum/move/wkly/data/?api_key={API_KEY}&data[0]=value&facets[series][]={exports_series}&frequency=weekly&start=2020-10-01"
    exports_data = requests.get(url_exports).json()
    df_exports = pd.DataFrame(exports_data['response']['data'])
    
    # Merge and calculate net imports
    df_imports['date'] = pd.to_datetime(df_imports['period'])
    df_imports['imports'] = df_imports['value'].astype(float)
    df_exports['date'] = pd.to_datetime(df_exports['period'])
    df_exports['exports'] = df_exports['value'].astype(float)
    
    df = df_imports[['date', 'imports']].merge(df_exports[['date', 'exports']], on='date')
    df['net_imports_kbd'] = df['imports'] - df['exports']  # Thousand barrels per day
    df = df[['date', 'net_imports_kbd']].sort_values('date')
    
    df.to_parquet('data/silver/eia_imports_weekly.parquet', index=False)
    print(f"✓ Downloaded {len(df)} weeks of import/export data")
    return df

if __name__ == "__main__":
    print("Downloading EIA data...")
    download_eia_inventory()
    download_eia_utilization()
    download_eia_imports()
    print("✓ EIA data downloaded to data/silver/")
```

**Time**: 1-2 hours (including API setup)

**Output Files**:
- `data/silver/eia_inventory_weekly.parquet`
- `data/silver/eia_utilization_weekly.parquet`
- `data/silver/eia_imports_weekly.parquet`

---

### Source 2: NYMEX RBOB Futures (Daily)

**What you need**: Daily RBOB gasoline futures prices (front month contract)

**How to get it**:

**Option A: Manual Download (Free)**
1. Go to https://www.cmegroup.com/markets/energy/refined-products/rbob-gasoline.html
2. Download historical data (CSV)
3. Select date range: Oct 2020 - Present

**Option B: Yahoo Finance (Free API)**
```python
# File: scripts/download_rbob_data.py

import pandas as pd
import yfinance as yf

def download_rbob_yahoo():
    """Download RBOB futures from Yahoo Finance"""
    # RBOB futures ticker on Yahoo Finance
    ticker = "RB=F"
    
    # Download data from 2020-10-01 to present
    rbob = yf.download(ticker, start="2020-10-01", end=pd.Timestamp.today())
    
    # Clean up
    df = rbob.reset_index()
    df = df.rename(columns={'Date': 'date', 'Close': 'rbob_price'})
    df['date'] = pd.to_datetime(df['date'])
    df['rbob_price'] = df['rbob_price'] / 42  # Convert $/barrel to $/gallon
    df = df[['date', 'rbob_price']].sort_values('date')
    
    # Sanity check
    assert df['rbob_price'].min() > 0.50, "RBOB price too low"
    assert df['rbob_price'].max() < 6.00, "RBOB price too high"
    
    # Forward fill weekends (markets closed)
    df = df.set_index('date').resample('D').ffill().reset_index()
    
    df.to_parquet('data/silver/rbob_daily.parquet', index=False)
    print(f"✓ Downloaded {len(df)} days of RBOB data")
    return df

if __name__ == "__main__":
    # Install: pip install yfinance
    download_rbob_yahoo()
```

**Time**: 30 minutes

**Output**: `data/silver/rbob_daily.parquet`

---

### Source 3: WTI Crude Oil Prices (Daily)

**What you need**: Daily WTI crude oil spot price (for crack spread calculation)

```python
# File: scripts/download_wti_data.py

import pandas as pd
import yfinance as yf

def download_wti_yahoo():
    """Download WTI crude oil prices from Yahoo Finance"""
    ticker = "CL=F"  # WTI Crude Oil Futures
    
    wti = yf.download(ticker, start="2020-10-01", end=pd.Timestamp.today())
    
    df = wti.reset_index()
    df = df.rename(columns={'Date': 'date', 'Close': 'wti_price'})
    df['date'] = pd.to_datetime(df['date'])
    df['wti_price'] = df['wti_price'] / 42  # Convert $/barrel to $/gallon
    df = df[['date', 'wti_price']].sort_values('date')
    
    # Forward fill weekends
    df = df.set_index('date').resample('D').ffill().reset_index()
    
    df.to_parquet('data/silver/wti_daily.parquet', index=False)
    print(f"✓ Downloaded {len(df)} days of WTI data")
    return df

if __name__ == "__main__":
    download_wti_yahoo()
```

**Time**: 15 minutes

**Output**: `data/silver/wti_daily.parquet`

---

### Source 4: AAA Retail Gasoline Prices (Daily)

**What you need**: U.S. national average retail regular gasoline price

**How to get it**:

**Option A: AAA Gas Prices API (Free)**
```python
# File: scripts/download_aaa_data.py

import pandas as pd
import requests

def download_aaa_prices():
    """
    AAA doesn't have a public historical API.
    Alternative: Use EIA retail prices (they track AAA data)
    """
    # EIA tracks weekly retail prices, we'll use this as proxy
    # Series: U.S. Regular All Formulations Retail Gasoline Prices ($/gal)
    API_KEY = "YOUR_EIA_API_KEY"
    series_id = "PET.EMM_EPM0_PTE_NUS_DPG.W"
    
    url = f"https://api.eia.gov/v2/petroleum/pri/gnd/data/?api_key={API_KEY}&data[0]=value&facets[series][]={series_id}&frequency=weekly&start=2020-10-01"
    
    response = requests.get(url)
    data = response.json()
    
    df = pd.DataFrame(data['response']['data'])
    df['date'] = pd.to_datetime(df['period'])
    df['retail_price'] = df['value'].astype(float)
    df = df[['date', 'retail_price']].sort_values('date')
    
    # Sanity check
    assert df['retail_price'].min() > 1.00, "Retail price too low"
    assert df['retail_price'].max() < 7.00, "Retail price too high"
    
    # Forward fill to daily (prices don't change every day in reality)
    df = df.set_index('date').resample('D').ffill().reset_index()
    
    df.to_parquet('data/silver/retail_daily.parquet', index=False)
    print(f"✓ Downloaded {len(df)} days of retail price data")
    return df

if __name__ == "__main__":
    download_aaa_prices()
```

**Time**: 30 minutes

**Output**: `data/silver/retail_daily.parquet`

---

### Silver Layer: Final Checklist

After running all download scripts:

```bash
ls -lh data/silver/

# You should see:
# eia_inventory_weekly.parquet    (~10 KB)
# eia_utilization_weekly.parquet  (~10 KB)
# eia_imports_weekly.parquet      (~10 KB)
# rbob_daily.parquet              (~50 KB)
# wti_daily.parquet               (~50 KB)
# retail_daily.parquet            (~30 KB)
```

**Create a README**:
```bash
cat > data/silver/README.txt << EOF
Silver Layer Data
Downloaded: October 10, 2025
Sources:
- EIA API (https://www.eia.gov/opendata/)
- Yahoo Finance (RBOB/WTI futures)
- EIA Retail Prices (proxy for AAA)

Date Range: October 2020 - October 2025
Frequency: Daily (futures/retail), Weekly (EIA fundamentals)
Units: $/gallon (prices), million barrels (inventory), % (utilization)
EOF
```

**Total Silver Layer Time**: ✅ 4-6 hours

---

## 🟡 Phase 2: Gold Layer (1-2 days)

### Goal
Create a single master table with all features aligned to daily frequency, ready for modeling.

### Implementation

```python
# File: scripts/build_gold_layer.py

import pandas as pd
import numpy as np

def load_silver_data():
    """Load all silver layer files"""
    print("Loading silver data...")
    
    # Daily data
    rbob = pd.read_parquet('data/silver/rbob_daily.parquet')
    wti = pd.read_parquet('data/silver/wti_daily.parquet')
    retail = pd.read_parquet('data/silver/retail_daily.parquet')
    
    # Weekly data
    inventory = pd.read_parquet('data/silver/eia_inventory_weekly.parquet')
    utilization = pd.read_parquet('data/silver/eia_utilization_weekly.parquet')
    imports = pd.read_parquet('data/silver/eia_imports_weekly.parquet')
    
    return rbob, wti, retail, inventory, utilization, imports

def create_daily_master_table():
    """Join all data sources into daily frequency"""
    
    rbob, wti, retail, inventory, utilization, imports = load_silver_data()
    
    # Start with retail (our target variable)
    gold = retail.copy()
    gold = gold.rename(columns={'retail_price': 'price_retail'})
    
    # Join daily prices
    gold = gold.merge(rbob.rename(columns={'rbob_price': 'price_rbob'}), on='date', how='outer')
    gold = gold.merge(wti.rename(columns={'wti_price': 'price_wti'}), on='date', how='outer')
    
    # Join weekly data (will have NaN for days without EIA reports)
    gold = gold.merge(inventory.rename(columns={'inventory_mbbl': 'inventory'}), on='date', how='left')
    gold = gold.merge(utilization.rename(columns={'utilization_pct': 'util_rate'}), on='date', how='left')
    gold = gold.merge(imports.rename(columns={'net_imports_kbd': 'net_imports'}), on='date', how='left')
    
    # Forward fill weekly data to daily
    gold['inventory'] = gold['inventory'].ffill()
    gold['util_rate'] = gold['util_rate'].ffill()
    gold['net_imports'] = gold['net_imports'].ffill()
    
    # Sort by date
    gold = gold.sort_values('date').reset_index(drop=True)
    
    print(f"✓ Created master table with {len(gold)} days")
    return gold

def add_derived_features(gold):
    """Add calculated features from raw data"""
    
    print("Adding derived features...")
    
    # 1. Crack spread
    gold['crack_spread'] = gold['price_rbob'] - gold['price_wti']
    
    # 2. Retail margin
    gold['retail_margin'] = gold['price_retail'] - gold['price_rbob']
    
    # 3. Days since October 1
    gold['days_since_oct1'] = gold['date'].apply(
        lambda x: (x - pd.Timestamp(f'{x.year}-10-01')).days if x.month == 10 else 0
    )
    gold['days_since_oct1'] = gold['days_since_oct1'].clip(lower=0)
    
    # 4. October indicators
    gold['is_october'] = (gold['date'].dt.month == 10).astype(int)
    gold['is_early_oct'] = ((gold['date'].dt.month == 10) & (gold['date'].dt.day <= 15)).astype(int)
    gold['is_late_oct'] = ((gold['date'].dt.month == 10) & (gold['date'].dt.day > 15)).astype(int)
    
    # 5. Weekday effect (Oct 31, 2025 is Friday)
    gold['day_of_week'] = gold['date'].dt.dayofweek  # 0=Monday, 6=Sunday
    gold['is_weekend'] = (gold['day_of_week'] >= 4).astype(int)  # Fri/Sat/Sun
    
    # 6. Rolling volatility (10-day)
    gold['vol_rbob_10d'] = gold['price_rbob'].rolling(window=10, min_periods=5).std()
    
    # 7. Price changes (for momentum)
    gold['delta_rbob_1d'] = gold['price_rbob'].diff(1)
    gold['delta_rbob_1w'] = gold['price_rbob'].diff(7)
    
    # 8. RBOB momentum (7-day % change)
    gold['rbob_momentum_7d'] = gold['price_rbob'].pct_change(7)
    
    # 9. Import dependency (net imports / consumption proxy)
    # Approximate consumption as ~9,000 kbd (thousand barrels/day)
    gold['import_dependency'] = gold['net_imports'] / 9000
    
    print(f"✓ Added {9} derived feature groups")
    return gold

def add_lags(gold):
    """Add lagged features for modeling"""
    
    print("Adding lagged features...")
    
    # RBOB lags (3, 7, 14 days)
    gold['rbob_lag3'] = gold['price_rbob'].shift(3)
    gold['rbob_lag7'] = gold['price_rbob'].shift(7)
    gold['rbob_lag14'] = gold['price_rbob'].shift(14)
    
    # Retail margin lag
    gold['retail_margin_lag1'] = gold['retail_margin'].shift(1)
    
    # Inventory lag (for surprise calculation later)
    gold['inventory_lag1'] = gold['inventory'].shift(1)
    gold['inventory_lag4'] = gold['inventory'].shift(4)  # 4 weeks
    
    # Asymmetric RBOB changes (for rockets & feathers)
    gold['rbob_increase'] = gold['delta_rbob_1d'].clip(lower=0)  # Only positive changes
    gold['rbob_decrease'] = gold['delta_rbob_1d'].clip(upper=0)  # Only negative changes
    
    print(f"✓ Added lagged features")
    return gold

def add_interactions(gold):
    """Add interaction features"""
    
    print("Adding interaction terms...")
    
    # 1. Utilization × Inventory stress (compounding tightness)
    # Days of supply = Inventory / (consumption rate ≈ 9000 kbd × 7 days)
    gold['days_supply'] = gold['inventory'] / (9.0 * 7)  # Approximate: 9M bbl/week consumption
    gold['util_inv_stress'] = gold['util_rate'] * (1 / gold['days_supply'])
    
    # 2. Crack spread × utilization (capacity constraint)
    gold['crack_util'] = gold['crack_spread'] * gold['util_rate']
    
    # 3. Days supply squared (non-linear threshold effect)
    gold['days_supply_sq'] = gold['days_supply'] ** 2
    
    print(f"✓ Added 3 interaction terms")
    return gold

def filter_october_data(gold):
    """Filter to October only for training"""
    
    october = gold[gold['is_october'] == 1].copy()
    october = october.dropna(subset=['price_retail', 'price_rbob'])  # Drop rows missing critical features
    
    print(f"✓ Filtered to {len(october)} October days (2020-2025)")
    return october

def save_gold_layer(gold):
    """Save master table and October subset"""
    
    # Save full table
    gold.to_parquet('data/gold/master_daily.parquet', index=False)
    print(f"✓ Saved master table: data/gold/master_daily.parquet")
    
    # Save October subset for modeling
    october = filter_october_data(gold)
    october.to_parquet('data/gold/master_october.parquet', index=False)
    print(f"✓ Saved October table: data/gold/master_october.parquet")
    
    # Print summary stats
    print("\n📊 Gold Layer Summary:")
    print(f"  Total days: {len(gold)}")
    print(f"  October days: {len(october)}")
    print(f"  Features: {len(gold.columns)}")
    print(f"  Date range: {gold['date'].min()} to {gold['date'].max()}")
    print(f"  Missing values: {gold.isnull().sum().sum()}")
    
    return gold, october

def main():
    """Build complete gold layer"""
    
    print("=" * 60)
    print("BUILDING GOLD LAYER")
    print("=" * 60)
    
    # Step 1: Join all data sources
    gold = create_daily_master_table()
    
    # Step 2: Add derived features
    gold = add_derived_features(gold)
    
    # Step 3: Add lags
    gold = add_lags(gold)
    
    # Step 4: Add interactions
    gold = add_interactions(gold)
    
    # Step 5: Save
    gold, october = save_gold_layer(gold)
    
    print("\n✅ Gold layer complete!")
    print("\nNext steps:")
    print("  1. Inspect data: pd.read_parquet('data/gold/master_october.parquet')")
    print("  2. Check for missing values")
    print("  3. Visualize key features")
    print("  4. Begin model training")
    
    return gold, october

if __name__ == "__main__":
    gold, october = main()
```

**Time**: 4-6 hours (coding + validation)

---

## 📊 Validation & QA

```python
# File: scripts/validate_gold_layer.py

import pandas as pd
import matplotlib.pyplot as plt

def validate_gold_layer():
    """Run data quality checks on gold layer"""
    
    gold = pd.read_parquet('data/gold/master_october.parquet')
    
    print("🔍 DATA QUALITY REPORT")
    print("=" * 60)
    
    # 1. Check missing values
    print("\n1. Missing Values:")
    missing = gold.isnull().sum()
    missing_pct = (missing / len(gold) * 100).round(2)
    print(missing[missing > 0])
    
    # 2. Check value ranges
    print("\n2. Value Ranges:")
    print(f"  Retail price: ${gold['price_retail'].min():.2f} - ${gold['price_retail'].max():.2f}")
    print(f"  RBOB price: ${gold['price_rbob'].min():.2f} - ${gold['price_rbob'].max():.2f}")
    print(f"  Crack spread: ${gold['crack_spread'].min():.2f} - ${gold['crack_spread'].max():.2f}")
    print(f"  Inventory: {gold['inventory'].min():.1f} - {gold['inventory'].max():.1f} Mbbl")
    print(f"  Utilization: {gold['util_rate'].min():.1f}% - {gold['util_rate'].max():.1f}%")
    print(f"  Days supply: {gold['days_supply'].min():.1f} - {gold['days_supply'].max():.1f}")
    
    # 3. Check October coverage
    print("\n3. October Coverage by Year:")
    yearly_counts = gold.groupby(gold['date'].dt.year).size()
    print(yearly_counts)
    
    # 4. Correlation check
    print("\n4. Top Correlations with Retail Price:")
    features = ['price_rbob', 'rbob_lag3', 'rbob_lag7', 'crack_spread', 'retail_margin', 
                'days_supply', 'util_rate', 'vol_rbob_10d']
    corrs = gold[features + ['price_retail']].corr()['price_retail'].sort_values(ascending=False)
    print(corrs[1:6])  # Top 5 (excluding self-correlation)
    
    # 5. Plot key series
    fig, axes = plt.subplots(3, 1, figsize=(12, 8))
    
    axes[0].plot(gold['date'], gold['price_retail'], label='Retail')
    axes[0].plot(gold['date'], gold['price_rbob'], label='RBOB', alpha=0.7)
    axes[0].set_ylabel('Price ($/gal)')
    axes[0].legend()
    axes[0].set_title('Prices Over Time (October Only)')
    
    axes[1].plot(gold['date'], gold['inventory'], label='Inventory', color='green')
    axes[1].set_ylabel('Inventory (Mbbl)')
    axes[1].legend()
    axes[1].set_title('Gasoline Inventory')
    
    axes[2].plot(gold['date'], gold['util_rate'], label='Utilization', color='orange')
    axes[2].set_ylabel('Utilization (%)')
    axes[2].legend()
    axes[2].set_title('Refinery Utilization')
    
    plt.tight_layout()
    plt.savefig('data/gold/data_validation_plots.png', dpi=150)
    print("\n✓ Saved validation plots: data/gold/data_validation_plots.png")
    
    print("\n✅ Validation complete!")

if __name__ == "__main__":
    validate_gold_layer()
```

---

## 🚀 Quick Start Commands

```bash
# 1. Set up environment
cd /Users/christianlee/Downloads/Kalshi/Gas
python3 -m venv venv
source venv/bin/activate
pip install pandas numpy requests yfinance pyarrow matplotlib scikit-learn

# 2. Run silver layer (download data)
python scripts/download_eia_data.py
python scripts/download_rbob_data.py
python scripts/download_wti_data.py
python scripts/download_aaa_data.py

# 3. Run gold layer (build master table)
python scripts/build_gold_layer.py

# 4. Validate data quality
python scripts/validate_gold_layer.py

# 5. Check output
ls -lh data/gold/
# Should see: master_daily.parquet, master_october.parquet, data_validation_plots.png
```

---

## 📦 Expected Output

After completing both layers:

```
Gas/
├── data/
│   ├── silver/
│   │   ├── eia_inventory_weekly.parquet      (~10 KB, ~250 weeks)
│   │   ├── eia_utilization_weekly.parquet    (~10 KB)
│   │   ├── eia_imports_weekly.parquet        (~10 KB)
│   │   ├── rbob_daily.parquet                (~50 KB, ~1,800 days)
│   │   ├── wti_daily.parquet                 (~50 KB)
│   │   ├── retail_daily.parquet              (~30 KB)
│   │   └── README.txt
│   │
│   └── gold/
│       ├── master_daily.parquet              (~200 KB, all dates)
│       ├── master_october.parquet            (~30 KB, ~150 October days)
│       └── data_validation_plots.png
│
└── scripts/
    ├── download_eia_data.py
    ├── download_rbob_data.py
    ├── download_wti_data.py
    ├── download_aaa_data.py
    ├── build_gold_layer.py
    └── validate_gold_layer.py
```

---

## ✅ Success Criteria

Your data layer is ready when:

1. ✅ Silver layer has 6 clean parquet files
2. ✅ Gold layer has ~150 October observations (2020-2025)
3. ✅ No missing values in critical features (price_retail, price_rbob, rbob_lag3)
4. ✅ Value ranges are reasonable (see validation checks)
5. ✅ Validation plots look correct
6. ✅ Feature correlations match expectations (RBOB lags → retail price > 0.7)

---

## 🔧 Troubleshooting

**Issue**: EIA API returns 403 error  
**Fix**: Register for free API key at https://www.eia.gov/opendata/register.php

**Issue**: Yahoo Finance download fails  
**Fix**: Install yfinance: `pip install yfinance`, or use manual CSV download

**Issue**: Missing values in gold layer  
**Fix**: Check forward-fill logic in `create_daily_master_table()`, ensure weekly data propagates

**Issue**: Feature count doesn't match architecture (18 features)  
**Fix**: Some features are derived during modeling (e.g., winter blend effect, inventory surprise). Gold layer provides base features.

---

## ⏱️ Time Breakdown

| Phase | Task | Time |
|-------|------|------|
| **Silver** | EIA API setup + download | 1-2 hours |
| **Silver** | RBOB/WTI download | 30 min |
| **Silver** | Retail prices | 30 min |
| **Silver** | Validation | 30 min |
| **Gold** | Join + forward-fill | 1 hour |
| **Gold** | Derived features | 2 hours |
| **Gold** | Lags + interactions | 1 hour |
| **Gold** | Validation + plots | 1 hour |
| **TOTAL** | | **7-9 hours** |

---

## 📖 Next Steps

After data layer is complete:

1. **Feature Engineering** (1 day)
   - Calculate inventory surprises
   - Fit winter blend λ parameter
   - Create regime indicators

2. **Model Training** (2 days)
   - Ridge regression (Model 1)
   - Inventory surprise model (Model 2)
   - Futures curve model (Model 3)
   - Regime-weighted ensemble (Model 4)

3. **Validation** (1 day)
   - Walk-forward backtests
   - Quantile regression
   - Out-of-sample testing

4. **Forecast** (1 day)
   - Generate Oct 31, 2025 forecast
   - Create scenarios
   - Visualizations

---

**Total Project Timeline**: 2-3 weeks ✅
**Data Layer Complete**: End of Week 1 ✅
