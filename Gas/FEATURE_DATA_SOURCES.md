# Feature Data Sources Guide

**Complete mapping: 18 Features → Data Sources → Download Methods**

This document shows exactly how to obtain the data required for each of your 18 features.

---

## 📊 Feature-to-Data Mapping

### Category 1: Price & Market Structure (7 features)

| Feature | Data Required | Source | Download Method | File Output |
|---------|---------------|--------|-----------------|-------------|
| **RBOB_t-3, RBOB_t-7, RBOB_t-14** | Daily RBOB futures settle prices | Yahoo Finance / CME | yfinance library | `rbob_daily.parquet` |
| **CrackSpread** | RBOB - WTI (derived) | Yahoo Finance (both) | yfinance library | Calculated from RBOB + WTI files |
| **RetailMargin** | Retail price - RBOB (derived) | AAA + Yahoo Finance | EIA API + yfinance | Calculated in Gold layer |
| **Term Structure** | RBOB Nov-Dec spread | CME DataMine or Bloomberg | Manual or CME API (complex) | `rbob_curve_spreads.csv` |
| **Vol_RBOB_10d** | 10-day rolling volatility (derived) | Yahoo Finance | yfinance library | Calculated from RBOB prices |
| **🆕 RBOB_Momentum_7d** | 7-day price change % (derived) | Yahoo Finance | yfinance library | Calculated from RBOB prices |
| **Asymmetric_Δ** | Up vs down day indicator (derived) | Yahoo Finance | yfinance library | Calculated from RBOB daily changes |

**Summary**: 
- **Primary source**: Yahoo Finance (ticker: `RB=F` for RBOB front month)
- **Time required**: 30 minutes
- **Cost**: FREE

---

### Category 2: Supply & Fundamentals (6 features)

| Feature | Data Required | Source | Download Method | File Output |
|---------|---------------|--------|-----------------|-------------|
| **Days_Supply** | Inventory / (Production×7) (derived) | EIA API (both) | `download_eia_data.py` | Calculated in Gold layer |
| **Inv_Surprise** | Actual - Expected inventory (derived) | EIA API | `download_eia_data.py` | Calculated in Gold layer |
| **Util_Rate** | Weekly refinery utilization % | EIA API | `download_eia_data.py` | `eia_utilization_weekly.parquet` |
| **🆕 Util×Inv_Stress** | Util_Rate × (1/Days_Supply) (derived) | EIA API | `download_eia_data.py` | Calculated in Gold layer |
| **PADD3_Share** | Gulf Coast refining share % | EIA API (PADD-level data) | EIA API (series PET.WCRSTUS1.W for PADD3) | `eia_padd3_capacity.parquet` |
| **🆕 Import_Depend** | Net imports / Total supply % | EIA API | `download_eia_data.py` | Calculated from `eia_imports_weekly.parquet` |
| **Regime_Flag** | Normal/Tight/Crisis (derived) | Calculated from Days_Supply | Rule-based logic | Calculated in Gold layer |

**Summary**:
- **Primary source**: EIA API (https://www.eia.gov/opendata/)
- **Time required**: 1-2 hours (after API key obtained)
- **Cost**: FREE (API key registration required)
- **Scripts**: Already created in `scripts/download_eia_data.py`

---

### Category 3: Seasonal & October Effects (5 features)

| Feature | Data Required | Source | Download Method | File Output |
|---------|---------------|--------|-----------------|-------------|
| **WinterBlend_Effect** | Days since Sept 15 (regulatory date) | Hardcoded calendar logic | Python datetime | Calculated in Gold layer |
| **Days_Since_Oct1** | Day counter within October | Hardcoded calendar logic | Python datetime | Calculated in Gold layer |
| **Hurricane_Risk** | Probabilistic risk score | NOAA NHC or historical data | Web scraping or manual input | `hurricane_risk_oct.csv` |
| **Temp_Anom** | Temperature deviation from normal | NOAA NCEI API | NOAA API or manual CSV | `noaa_temp_daily.parquet` |
| **🆕 Weekday_Effect** | Day of week (Oct 31 = Friday) | Calendar logic | Python datetime | Calculated in Gold layer |
| **Is_Early_Oct** | Binary flag (days 1-10) | Calendar logic | Python datetime | Calculated in Gold layer |

**Summary**:
- **Primary source**: Python datetime (built-in), NOAA for temp (optional)
- **Time required**: 15 minutes (calendar features), 1 hour (NOAA temp if needed)
- **Cost**: FREE

---

## 🚀 Quick Start: Download Scripts

### Script 1: RBOB Futures (Yahoo Finance)

**File**: `scripts/download_rbob_data.py`

```python
import yfinance as yf
import pandas as pd

def download_rbob_futures():
    """Download daily RBOB gasoline futures from Yahoo Finance"""
    
    # RB=F is the front-month RBOB futures contract
    ticker = yf.Ticker("RB=F")
    
    # Download from Oct 2020 to present
    df = ticker.history(start="2020-10-01", end=pd.Timestamp.today())
    
    # Clean and format
    df = df.reset_index()
    df = df.rename(columns={
        'Date': 'date',
        'Close': 'price_rbob',
        'Volume': 'volume_rbob'
    })
    
    # Keep only needed columns
    df = df[['date', 'price_rbob', 'volume_rbob']]
    
    # Convert to $/gallon (Yahoo gives $/gallon already for RB=F)
    # Sanity check
    assert df['price_rbob'].min() > 0.5, "RBOB price too low"
    assert df['price_rbob'].max() < 8.0, "RBOB price too high"
    
    # Save
    df.to_parquet('../data/silver/rbob_daily.parquet', index=False)
    print(f"✓ Downloaded {len(df)} days of RBOB data")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  Price range: ${df['price_rbob'].min():.2f} - ${df['price_rbob'].max():.2f}")
    
    return df

def download_wti_futures():
    """Download daily WTI crude futures from Yahoo Finance"""
    
    ticker = yf.Ticker("CL=F")
    df = ticker.history(start="2020-10-01", end=pd.Timestamp.today())
    
    df = df.reset_index()
    df = df.rename(columns={
        'Date': 'date',
        'Close': 'price_wti'
    })
    
    df = df[['date', 'price_wti']]
    
    # Sanity check
    assert df['price_wti'].min() > 10, "WTI price too low"
    assert df['price_wti'].max() < 200, "WTI price too high"
    
    df.to_parquet('../data/silver/wti_daily.parquet', index=False)
    print(f"✓ Downloaded {len(df)} days of WTI data")
    print(f"  Price range: ${df['price_wti'].min():.2f} - ${df['price_wti'].max():.2f}")
    
    return df

if __name__ == "__main__":
    print("Downloading RBOB and WTI futures from Yahoo Finance...")
    download_rbob_futures()
    download_wti_futures()
    print("\n✓ All futures data downloaded to data/silver/")
```

**Install dependencies**:
```bash
pip install yfinance pandas pyarrow
```

**Time**: 10-15 minutes

---

### Script 2: Retail Gasoline Prices (EIA)

**File**: `scripts/download_retail_prices.py`

```python
import pandas as pd
import requests
import os

API_KEY = os.environ.get('EIA_API_KEY')  # Get from environment variable

def download_aaa_retail_prices():
    """
    Download daily retail gasoline prices from EIA
    (EIA aggregates AAA data)
    """
    
    # Series ID for U.S. Regular Gasoline Retail Price ($/gal)
    series_id = "PET.EMM_EPM0_PTE_NUS_DPG.D"
    
    url = f"https://api.eia.gov/v2/petroleum/pri/gnd/data/?api_key={API_KEY}&data[0]=value&facets[series][]={series_id}&frequency=daily&start=2020-10-01"
    
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(f"Message: {response.text}")
        return None
    
    data = response.json()
    
    # Parse
    df = pd.DataFrame(data['response']['data'])
    df['date'] = pd.to_datetime(df['period'])
    df['retail_price'] = df['value'].astype(float)
    
    df = df[['date', 'retail_price']].sort_values('date')
    
    # Sanity checks
    assert df['retail_price'].min() > 1.5, "Retail price too low"
    assert df['retail_price'].max() < 7.0, "Retail price too high"
    assert not df['retail_price'].isna().any(), "Missing retail prices"
    
    # Save
    df.to_parquet('../data/silver/retail_prices_daily.parquet', index=False)
    print(f"✓ Downloaded {len(df)} days of retail price data")
    print(f"  Price range: ${df['retail_price'].min():.2f} - ${df['retail_price'].max():.2f}")
    
    return df

if __name__ == "__main__":
    if not API_KEY:
        print("ERROR: EIA_API_KEY not set!")
        print("Get your key from: https://www.eia.gov/opendata/register.php")
        print("Then run: export EIA_API_KEY='your_key_here'")
    else:
        print("Downloading retail prices from EIA...")
        download_aaa_retail_prices()
        print("\n✓ Retail price data downloaded to data/silver/")
```

**Time**: 15 minutes

---

### Script 3: PADD3 Refining Data (EIA)

**File**: `scripts/download_padd3_data.py`

```python
import pandas as pd
import requests
import os

API_KEY = os.environ.get('EIA_API_KEY')

def download_padd3_capacity():
    """
    Download PADD3 (Gulf Coast) refinery capacity data
    Used to calculate PADD3_Share feature
    """
    
    # PADD3 refinery capacity (operable capacity)
    padd3_series = "PET.8_NA_8C0_NUS_6.W"  # Weekly operable capacity, PADD3
    total_series = "PET.8_NA_8C0_NUS_1.W"  # Total U.S. operable capacity
    
    # Download PADD3
    url_padd3 = f"https://api.eia.gov/v2/petroleum/sum/sndw/data/?api_key={API_KEY}&data[0]=value&facets[series][]={padd3_series}&frequency=weekly&start=2020-10-01"
    padd3_data = requests.get(url_padd3).json()
    df_padd3 = pd.DataFrame(padd3_data['response']['data'])
    
    # Download Total
    url_total = f"https://api.eia.gov/v2/petroleum/sum/sndw/data/?api_key={API_KEY}&data[0]=value&facets[series][]={total_series}&frequency=weekly&start=2020-10-01"
    total_data = requests.get(url_total).json()
    df_total = pd.DataFrame(total_data['response']['data'])
    
    # Merge
    df_padd3['date'] = pd.to_datetime(df_padd3['period'])
    df_padd3['padd3_capacity'] = df_padd3['value'].astype(float)
    
    df_total['date'] = pd.to_datetime(df_total['period'])
    df_total['total_capacity'] = df_total['value'].astype(float)
    
    df = df_padd3[['date', 'padd3_capacity']].merge(
        df_total[['date', 'total_capacity']], 
        on='date'
    )
    
    # Calculate share
    df['padd3_share'] = df['padd3_capacity'] / df['total_capacity'] * 100
    df = df[['date', 'padd3_share']].sort_values('date')
    
    # Sanity check (PADD3 is ~50% of U.S. capacity)
    assert df['padd3_share'].min() > 40, "PADD3 share too low"
    assert df['padd3_share'].max() < 60, "PADD3 share too high"
    
    df.to_parquet('../data/silver/padd3_share_weekly.parquet', index=False)
    print(f"✓ Downloaded {len(df)} weeks of PADD3 capacity data")
    print(f"  PADD3 share range: {df['padd3_share'].min():.1f}% - {df['padd3_share'].max():.1f}%")
    
    return df

if __name__ == "__main__":
    if not API_KEY:
        print("ERROR: EIA_API_KEY not set!")
        print("Get your key from: https://www.eia.gov/opendata/register.php")
        print("Then run: export EIA_API_KEY='your_key_here'")
    else:
        print("Downloading PADD3 refinery data from EIA...")
        download_padd3_capacity()
        print("\n✓ PADD3 data downloaded to data/silver/")
```

**Time**: 20 minutes

---

### Script 4: Temperature Data (NOAA) - OPTIONAL

**Note**: Temperature anomalies have **low priority** for October forecasting (minor impact). Skip this if time-constrained.

**File**: `scripts/download_noaa_temp.py`

```python
import pandas as pd
import requests

def download_noaa_temp():
    """
    Download U.S. temperature data from NOAA NCEI
    
    NOTE: This requires NOAA API token (free)
    Register at: https://www.ncdc.noaa.gov/cdo-web/token
    
    This is OPTIONAL - temp has low signal for October gas prices
    """
    
    NOAA_TOKEN = "YOUR_NOAA_TOKEN"
    
    # U.S. national average temperature
    url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data"
    
    params = {
        'datasetid': 'GHCND',
        'locationid': 'FIPS:US',
        'startdate': '2020-10-01',
        'enddate': pd.Timestamp.today().strftime('%Y-%m-%d'),
        'datatypeid': 'TAVG',
        'units': 'standard',
        'limit': 1000
    }
    
    headers = {'token': NOAA_TOKEN}
    
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    
    df = pd.DataFrame(data['results'])
    df['date'] = pd.to_datetime(df['date'])
    df['temp_avg'] = df['value'].astype(float)
    
    df = df[['date', 'temp_avg']].sort_values('date')
    df.to_parquet('../data/silver/noaa_temp_daily.parquet', index=False)
    
    print(f"✓ Downloaded {len(df)} days of temperature data")
    
    return df

if __name__ == "__main__":
    print("⚠️  Temperature data is OPTIONAL (low signal for October)")
    print("    Skip this if time-constrained - focus on price/inventory data first")
    print("\nIf you want to proceed:")
    print("1. Get NOAA token: https://www.ncdc.noaa.gov/cdo-web/token")
    print("2. Update NOAA_TOKEN in script")
    print("3. Run script")
```

**Time**: 30 minutes (if needed)

---

### Script 5: Hurricane Risk (Manual Entry) - OPTIONAL

**File**: `data/silver/hurricane_risk_october.csv`

```csv
date,hurricane_risk
2020-10-01,0.15
2020-10-15,0.10
2020-11-01,0.05
2021-10-01,0.12
2021-10-15,0.08
2021-11-01,0.03
2022-10-01,0.20
2022-10-15,0.15
2022-11-01,0.08
2023-10-01,0.18
2023-10-15,0.12
2023-11-01,0.06
2024-10-01,0.10
2024-10-15,0.08
2024-11-01,0.04
2025-10-01,0.10
2025-10-15,0.08
2025-11-01,0.03
```

**Source**: NOAA National Hurricane Center historical data + seasonal forecasts

**Time**: 30 minutes (manual research)

**Note**: This is probabilistic and subjective. For research purposes, you can use historical October averages (~10-15% risk in Gulf Coast).

---

## 📦 Complete Silver Layer Output

After running all scripts, you should have:

### Required Files (High Priority)
```
data/silver/
├── rbob_daily.parquet           # RBOB futures (Yahoo Finance)
├── wti_daily.parquet             # WTI crude (Yahoo Finance)
├── retail_prices_daily.parquet   # Retail prices (EIA)
├── eia_inventory_weekly.parquet  # Gasoline stocks (EIA)
├── eia_utilization_weekly.parquet # Refinery util (EIA)
├── eia_imports_weekly.parquet    # Net imports (EIA)
└── padd3_share_weekly.parquet    # PADD3 capacity (EIA)
```

### Optional Files (Low Priority)
```
data/silver/
├── noaa_temp_daily.parquet       # Temperature (NOAA) - OPTIONAL
└── hurricane_risk_october.csv    # Hurricane risk - OPTIONAL
```

**Total Required Files**: 7
**Total Optional Files**: 2

---

## ⚙️ Derived Features (Calculated in Gold Layer)

These features **don't require new data downloads** - they're calculated from the files above:

| Feature | Calculation | Source Files |
|---------|-------------|--------------|
| **RBOB_t-3, t-7, t-14** | Lag RBOB price by 3, 7, 14 days | `rbob_daily.parquet` |
| **CrackSpread** | RBOB - WTI | `rbob_daily.parquet` + `wti_daily.parquet` |
| **RetailMargin** | Retail - RBOB | `retail_prices_daily.parquet` + `rbob_daily.parquet` |
| **Vol_RBOB_10d** | `RBOB.rolling(10).std()` | `rbob_daily.parquet` |
| **RBOB_Momentum_7d** | `RBOB.pct_change(7)` | `rbob_daily.parquet` |
| **Asymmetric_Δ** | `np.where(RBOB.diff() > 0, 1, 0)` | `rbob_daily.parquet` |
| **Days_Supply** | `Inventory / (Production × 7)` | `eia_inventory_weekly.parquet` |
| **Inv_Surprise** | `(Actual - MA4) / StdDev` | `eia_inventory_weekly.parquet` |
| **Util×Inv_Stress** | `Util_Rate × (1 / Days_Supply)` | `eia_utilization_weekly.parquet` + derived |
| **Import_Depend** | `Net_Imports / Total_Supply × 100` | `eia_imports_weekly.parquet` |
| **Regime_Flag** | `if Days_Supply < 23: 'Crisis'` | Derived from Days_Supply |
| **WinterBlend_Effect** | `(date - Sept_15).days / 90` | Python datetime |
| **Days_Since_Oct1** | `(date - Oct_1).days` | Python datetime |
| **Weekday_Effect** | `date.dayofweek` | Python datetime |
| **Is_Early_Oct** | `1 if day <= 10 else 0` | Python datetime |

**No additional downloads needed for these 15 features!**

---

## 📋 Data Collection Checklist

### Phase 1: Setup (15 min)
- [ ] Install dependencies: `pip install yfinance pandas pyarrow requests`
- [ ] Get EIA API key: https://www.eia.gov/opendata/register.php
- [ ] Set environment variable: `export EIA_API_KEY='your_key'`
- [ ] Create directory structure: `mkdir -p data/silver data/gold data/raw`

### Phase 2: Core Downloads (2-3 hours)
- [ ] Run `scripts/download_rbob_data.py` → RBOB + WTI futures
- [ ] Run `scripts/download_retail_prices.py` → Retail prices
- [ ] Run `scripts/download_eia_data.py` → Inventory, utilization, imports
- [ ] Run `scripts/download_padd3_data.py` → PADD3 capacity share

### Phase 3: Optional Downloads (1 hour)
- [ ] Run `scripts/download_noaa_temp.py` → Temperature (if needed)
- [ ] Create `hurricane_risk_october.csv` manually (if needed)

### Phase 4: Validation (30 min)
- [ ] Check all parquet files exist
- [ ] Verify date ranges (Oct 2020 - Oct 2025)
- [ ] Check for missing values
- [ ] Validate price ranges (sanity checks)

---

## 🔍 Data Quality Checks

Run this validation script after downloads:

**File**: `scripts/validate_silver_layer.py`

```python
import pandas as pd
import os

def validate_silver_layer():
    """Validate all Silver layer files"""
    
    silver_dir = '../data/silver'
    
    required_files = [
        'rbob_daily.parquet',
        'wti_daily.parquet',
        'retail_prices_daily.parquet',
        'eia_inventory_weekly.parquet',
        'eia_utilization_weekly.parquet',
        'eia_imports_weekly.parquet',
        'padd3_share_weekly.parquet'
    ]
    
    print("=" * 60)
    print("SILVER LAYER VALIDATION")
    print("=" * 60)
    
    all_valid = True
    
    for file in required_files:
        filepath = os.path.join(silver_dir, file)
        
        if not os.path.exists(filepath):
            print(f"❌ MISSING: {file}")
            all_valid = False
            continue
        
        df = pd.read_parquet(filepath)
        
        print(f"\n✓ {file}")
        print(f"  Rows: {len(df)}")
        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"  Columns: {list(df.columns)}")
        
        # Check for missing values
        missing = df.isnull().sum()
        if missing.any():
            print(f"  ⚠️  Missing values: {missing[missing > 0].to_dict()}")
        
        # Check date coverage
        if df['date'].min() > pd.Timestamp('2020-10-15'):
            print(f"  ⚠️  Start date later than Oct 2020")
        
        if df['date'].max() < pd.Timestamp('2024-10-01'):
            print(f"  ⚠️  End date earlier than Oct 2024")
    
    print("\n" + "=" * 60)
    if all_valid:
        print("✓ ALL REQUIRED FILES PRESENT")
        print("Ready to build Gold layer!")
    else:
        print("❌ SOME FILES MISSING - Check download scripts")
    print("=" * 60)

if __name__ == "__main__":
    validate_silver_layer()
```

---

## 📚 Reference: EIA Series IDs

For your reference, here are all the EIA series IDs used:

| Data | Series ID | Description |
|------|-----------|-------------|
| Inventory | `PET.WGTSTUS1.W` | Total Motor Gasoline Stocks (Thousand Barrels) |
| Utilization | `PET.WPULEUS3.W` | Percent Utilization of Refinery Operable Capacity |
| Imports | `PET.WGTIMUS2.W` | Imports of Motor Gasoline (Thousand Barrels per Day) |
| Exports | `PET.WGTEXUS2.W` | Exports of Motor Gasoline (Thousand Barrels per Day) |
| Retail Price | `PET.EMM_EPM0_PTE_NUS_DPG.D` | U.S. Regular Gasoline Retail Price ($/gal) |
| PADD3 Capacity | `PET.8_NA_8C0_NUS_6.W` | PADD3 Operable Refinery Capacity |
| Total Capacity | `PET.8_NA_8C0_NUS_1.W` | Total U.S. Operable Refinery Capacity |

**Full EIA API Documentation**: https://www.eia.gov/opendata/

---

## ⏱️ Time Budget Summary

| Task | Time | Priority |
|------|------|----------|
| Setup + API keys | 15 min | HIGH |
| RBOB + WTI (Yahoo) | 15 min | HIGH |
| Retail prices (EIA) | 20 min | HIGH |
| Inventory/Util/Imports (EIA) | 45 min | HIGH |
| PADD3 capacity (EIA) | 30 min | HIGH |
| Temperature (NOAA) | 30 min | LOW |
| Hurricane risk (manual) | 30 min | LOW |
| Validation | 15 min | HIGH |
| **Total (required only)** | **~2.5 hours** | - |
| **Total (with optional)** | **~3.5 hours** | - |

---

## 🚦 Next Steps

After completing Silver layer:

1. **Validate**: Run `scripts/validate_silver_layer.py`
2. **Gold Layer**: Proceed to `DATA_IMPLEMENTATION_GUIDE.md` Section 2
3. **Feature Engineering**: Build master table with all 18 features
4. **Modeling**: Train 4-model ensemble

**Your current status**: Ready to execute Silver layer downloads!

---

## ❓ FAQ

**Q: Do I need Bloomberg or paid data?**
A: No! All required data is free (Yahoo Finance + EIA API).

**Q: What if EIA API returns an error?**
A: Check your API key, series ID, and rate limits (5000 calls/day).

**Q: Can I skip temperature and hurricane data?**
A: Yes! These are low-priority features. Focus on price/inventory first.

**Q: How do I handle missing dates (weekends, holidays)?**
A: The Gold layer script will forward-fill weekly data to daily frequency.

**Q: What if Yahoo Finance data is missing recent days?**
A: Check if markets were closed (holidays). Use `.ffill()` for 1-2 day gaps.

---

**Ready to start?** Run the scripts in order:

```bash
cd /Users/christianlee/Downloads/Kalshi/Gas/scripts
python download_rbob_data.py
python download_retail_prices.py
python download_eia_data.py
python download_padd3_data.py
python validate_silver_layer.py
```
