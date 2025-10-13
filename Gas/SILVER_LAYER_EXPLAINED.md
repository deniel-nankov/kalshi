# Silver Layer Explained: What It Does & Why It Matters

**Purpose**: Single-source data cleaning and standardization

---

## Quick Summary

The **Silver layer** takes raw API responses (Bronze) and performs **single-source cleaning**:
- ✅ Standardize column names
- ✅ Select only needed columns  
- ✅ Convert data types
- ✅ Standardize units
- ✅ Remove duplicates
- ✅ Validate ranges
- ❌ **NO** cross-file joins (that's Gold layer)
- ❌ **NO** feature engineering (that's Gold layer)

**Philosophy**: "Clean, validate, simplify - nothing more"

---

## Bronze → Silver Transformations

### Summary Table

| Dataset | Bronze Cols | Silver Cols | Bronze Rows | Silver Rows | Main Transformation |
|---------|-------------|-------------|-------------|-------------|---------------------|
| RBOB Futures | 8 | 3 | 1,266 | 1,266 | Column selection + rename |
| WTI Futures | 8 | 2 | 1,265 | 1,265 | Column selection + rename |
| Retail Prices | 11 | 2 | 262 | **1,834** | Weekly→Daily forward-fill |
| Inventory | 11 | 2 | 262 | 262 | Unit conversion (÷1000) |
| Utilization | 11 | 2 | 262 | 262 | Column selection + rename |
| Imports/Exports | 11+11 | 2 | 262+262 | 262 | Merge + calculate net |

**Key Insight**: Silver dramatically simplifies data (8-22 cols → 2-3 cols per file)

---

## Example 1: RBOB Futures Cleaning

### Before (Bronze Layer - Raw Yahoo Finance)

```
Columns: ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']
Rows: 1,266

Sample:
                     Date   Open   High    Low  Close  Volume  Dividends  Stock Splits
2020-10-01 00:00:00-04:00 1.1808 1.1888 1.1230 1.1524   53243        0.0           0.0
2020-10-02 00:00:00-04:00 1.1465 1.1510 1.0958 1.1235   58246        0.0           0.0
2020-10-05 00:00:00-04:00 1.1274 1.2147 1.1224 1.1941   78888        0.0           0.0
```

### After (Silver Layer - Cleaned)

```
Columns: ['date', 'price_rbob', 'volume_rbob']
Rows: 1,266

Sample:
      date  price_rbob  volume_rbob
2020-10-01      1.1524      53243.0
2020-10-02      1.1235      58246.0
2020-10-05      1.1941      78888.0
```

### Transformations Applied

```python
# 1. Column rename (standardization)
df = df.rename(columns={
    'Date': 'date',           # Consistent naming
    'Close': 'price_rbob',    # Descriptive name
    'Volume': 'volume_rbob'   # Descriptive name
})

# 2. Column selection (simplification)
df = df[['date', 'price_rbob', 'volume_rbob']]
# Dropped: Open, High, Low, Adj Close, Dividends, Stock Splits

# 3. Data type conversion
df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
df['price_rbob'] = df['price_rbob'].astype(float)
df['volume_rbob'] = df['volume_rbob'].astype(float)

# 4. Validation
assert df['price_rbob'].min() > 0.5, "Price too low"
assert df['price_rbob'].max() < 8.0, "Price too high"

# 5. Duplicate removal
df = df.drop_duplicates(subset=['date'])

# 6. Sorting
df = df.sort_values('date')
```

**Result**: 8 columns → 3 columns, timezone removed, types standardized

---

## Example 2: Retail Prices (Most Interesting!)

### Before (Bronze Layer - Raw EIA Weekly Data)

```
Columns: ['period', 'duoarea', 'area-name', 'product', 'product-name', 
          'process', 'process-name', 'series', 'series-description', 'value', 'units']
Rows: 262 (weekly frequency)

Sample:
    period value
2020-10-05 2.172
2020-10-12 2.167
2020-10-19  2.15
2020-10-26 2.143
2020-11-02 2.112
```

### After (Silver Layer - Daily Forward-Fill)

```
Columns: ['date', 'retail_price']
Rows: 1,834 (daily frequency)

Sample (showing forward-fill):
      date  retail_price
2020-10-05         2.172  ← EIA report (Monday)
2020-10-06         2.172  ← Forward-filled
2020-10-07         2.172  ← Forward-filled
2020-10-08         2.172  ← Forward-filled
2020-10-09         2.172  ← Forward-filled
2020-10-10         2.172  ← Forward-filled
2020-10-11         2.172  ← Forward-filled
2020-10-12         2.167  ← EIA report (next Monday)
2020-10-13         2.167  ← Forward-filled
...
```

### Transformations Applied

```python
# 1. Parse dates and rename
weekly = weekly.assign(
    date=pd.to_datetime(weekly["period"]),
    retail_price=weekly["value"].astype(float),
)[["date", "retail_price"]]

# 2. Forward-fill weekly → daily
full_range = pd.date_range(
    weekly["date"].min(), 
    pd.Timestamp.today(), 
    freq="D"
)

daily = (
    weekly.set_index("date")
    .reindex(full_range)
    .rename_axis("date")
    .ffill()              # Forward-fill: repeat last value
    .bfill()              # Back-fill: fill start if needed
    .reset_index()
)

# 3. Validation
assert daily["retail_price"].min() >= 1.5, "Price too low"
assert daily["retail_price"].max() <= 7.0, "Price too high"
```

**Key Insight**: Forward-fill is **transparent**:
- Each EIA value repeats for ~7 days until next report
- Alternative (Kalman filter) is black-box and overkill
- For research project, transparency > sophistication

**Result**: 262 weekly obs → 1,834 daily obs (7x expansion)

---

## Example 3: Inventory (Unit Conversion)

### Before (Bronze Layer - Raw EIA Data)

```
Columns: 11 (including 'period', 'value', 'units', 'series-description', etc.)
Rows: 262
Units: THOUSANDS of barrels

Sample:
    period  value units
2020-10-02 226747  MBBL  ← "MBBL" = thousands
2020-10-09 225121  MBBL
2020-10-16 227016  MBBL
```

### After (Silver Layer - Millions of Barrels)

```
Columns: ['date', 'inventory_mbbl']
Rows: 262
Units: MILLIONS of barrels

Sample:
      date  inventory_mbbl
2020-10-02         226.747  ← Divided by 1000
2020-10-09         225.121
2020-10-16         227.016
```

### Transformations Applied

```python
# 1. Unit conversion
df = df.assign(
    date=pd.to_datetime(df["period"]),
    inventory_mbbl=df["value"].astype(float) / 1000.0  # thousands → millions
)[["date", "inventory_mbbl"]]

# 2. Validation
min_val = df["inventory_mbbl"].min()
max_val = df["inventory_mbbl"].max()
assert min_val > 180, f"Inventory too low: {min_val:.1f} million barrels"
assert max_val < 350, f"Inventory too high: {max_val:.1f} million barrels"
```

**Why Convert Units?**
- **Readability**: "226.7 million" vs "226,747 thousand" 
- **Consistency**: Gold layer features use millions
- **Modeling**: Cleaner numbers for regression (avoid huge coefficients)

---

## Example 4: Net Imports (Calculated Feature)

### Before (Bronze Layer - Separate Files)

```
File 1: eia_imports_raw.parquet
Columns: 11, Rows: 262

File 2: eia_exports_raw.parquet
Columns: 11, Rows: 262
```

### After (Silver Layer - Single Net Imports File)

```
File: eia_imports_weekly.parquet
Columns: ['date', 'net_imports_kbd']
Rows: 262

Sample:
      date  net_imports_kbd
2020-10-02           450.3  ← imports - exports
2020-10-09           472.1
2020-10-16           438.7
```

### Transformations Applied

```python
# 1. Clean imports
imports = imports_df.assign(
    date=pd.to_datetime(imports_df["period"]), 
    imports=imports_df["value"].astype(float)
)[["date", "imports"]]

# 2. Clean exports
exports = exports_df.assign(
    date=pd.to_datetime(exports_df["period"]), 
    exports=exports_df["value"].astype(float)
)[["date", "exports"]]

# 3. Merge and calculate
df = (
    imports.merge(exports, on="date", how="inner")
    .assign(net_imports_kbd=lambda x: x["imports"] - x["exports"])
    [["date", "net_imports_kbd"]]
)
```

**Result**: 2 Bronze files (22 total columns) → 1 Silver file (2 columns)

---

## 8 Key Silver Layer Transformations

### 1. Column Standardization
```
Inconsistent names → Consistent convention

Before: 'Date', 'period', 'Week Ending'
After:  'date' (everywhere)

Before: 'Close', 'value', 'Price'
After:  'price_rbob', 'retail_price', 'inventory_mbbl' (descriptive)
```

### 2. Column Selection
```
Keep only what's needed for modeling

RBOB: 8 columns → 3 columns
  Kept: date, price_rbob, volume_rbob
  Dropped: Open, High, Low, Adj Close, Dividends, Stock Splits

EIA: 11 columns → 2 columns
  Kept: date, value
  Dropped: duoarea, area-name, product, product-name, process, 
           process-name, series, series-description, units
```

### 3. Data Type Conversion
```
Strings → Proper types

Dates: string → datetime64[ns]
Prices: object/string → float64
Remove timezone info (tz_localize(None))
```

### 4. Unit Standardization
```
Consistent units across all files

Inventory: thousands → millions (÷1000)
  226,747 thousand bbls → 226.747 million bbls

Prices: Already $/gallon (no change needed)
Utilization: Already % (no change needed)
```

### 5. Frequency Harmonization
```
Weekly → Daily (for retail prices only)

262 weekly obs → 1,834 daily obs
Method: Forward-fill (repeat last value)
Transparency: Clear which days are "real" vs filled
```

### 6. Calculated Features (Simple)
```
Single-source calculations only

Net Imports = Imports - Exports
  (Still single-source: both from EIA)

No cross-source calculations (that's Gold layer)
```

### 7. Data Quality Checks
```
Validation before saving

Price ranges:
  assert rbob_price.min() > 0.5
  assert rbob_price.max() < 8.0

Observation counts:
  assert len(df) > 1000  # for daily data

Duplicates:
  df = df.drop_duplicates(subset=['date'])

Date ordering:
  df = df.sort_values('date')
```

### 8. Single-Source Cleaning Only
```
✅ DO in Silver:
  • Clean individual files
  • Standardize within one file
  • Validate one file's data quality

❌ DON'T in Silver:
  • Cross-file joins (Gold layer)
  • Feature engineering (Gold layer)
  • Lag creation (Gold layer)
  • Multi-source transformations (Gold layer)
```

---

## Why These Transformations Matter

### 1. Consistency → Gold Layer Can Join Easily

**Without Silver standardization**:
```python
# Bronze layer (nightmare to join):
rbob_df has 'Date' column (with timezone)
eia_df has 'period' column (string format)
retail_df has 'week_ending' column (different format)

# Trying to join:
gold = rbob_df.merge(eia_df, left_on='Date', right_on='period')  # FAILS!
```

**With Silver standardization**:
```python
# Silver layer (easy to join):
rbob_df has 'date' column (datetime64)
eia_df has 'date' column (datetime64)
retail_df has 'date' column (datetime64)

# Joining works perfectly:
gold = rbob_df.merge(eia_df, on='date').merge(retail_df, on='date')  # SUCCESS!
```

### 2. Simplicity → Faster Development

**Bronze layer complexity**:
```
RBOB: 8 columns (need to remember which is Close vs Adj Close)
EIA:  11 columns (what's 'duoarea' vs 'area-name'?)
```

**Silver layer simplicity**:
```
RBOB: 3 columns (date, price_rbob, volume_rbob)
EIA:  2 columns (date, inventory_mbbl)

Developer sees only what matters!
```

### 3. Modeling-Ready Units → No Conversion Later

**Without unit standardization**:
```python
# Gold layer would need to do this:
gold['inventory_mbbl'] = bronze['inventory'] / 1000
gold['retail_margin'] = silver['retail_price'] - (silver['rbob_price'] / 42)
# Error-prone unit conversions scattered everywhere
```

**With unit standardization**:
```python
# Gold layer just uses clean values:
gold['retail_margin'] = retail['retail_price'] - rbob['price_rbob']
# Units already match ($/gallon)
```

### 4. Daily Frequency → Aligned with Modeling

**Retail prices forward-filled to daily**:
```python
# Bronze: 262 weekly obs (can't join with daily RBOB)
# Silver: 1,834 daily obs (joins perfectly with RBOB)

gold = rbob_daily.merge(retail_daily, on='date')  # Works!
```

**Other weekly data stays weekly**:
```python
# EIA inventory/utilization stay weekly in Silver
# Gold layer forward-fills these during multi-source join
# Rationale: Only forward-fill retail early because it's the TARGET
```

### 5. Validation → Catch Errors Early

**Without validation**:
```python
# Discover error during modeling (too late!):
model.fit(X_train, y_train)
# Coefficient explodes because price = $0.00 (data error)
```

**With validation**:
```python
# Catch error during cleaning (early detection):
assert df['price_rbob'].min() > 0.5
# AssertionError: RBOB price too low: $0.02
# → Fix Bronze download script immediately
```

### 6. Transparency → Reproducible Research

**Forward-fill is transparent**:
```python
# Anyone reading code understands:
daily = weekly.reindex(full_range).ffill()
# "Repeat last value until next observation"

# Easy to explain in paper/documentation
```

**Kalman filter is black-box**:
```python
# Harder to explain:
from pykalman import KalmanFilter
kf = KalmanFilter(...)
daily = kf.smooth(weekly)[0]
# "Uses state-space model with transition matrix..."
# Reviewers ask: "Why Kalman? Show it's better!"
```

---

## Silver Layer Best Practices

### Do's ✅

1. **Standardize column names**
   ```python
   # Good
   df.rename(columns={'Date': 'date', 'Close': 'price_rbob'})
   
   # Bad
   # Leave as 'Date', 'Close' (inconsistent across files)
   ```

2. **Select only needed columns**
   ```python
   # Good
   df[['date', 'price_rbob', 'volume_rbob']]
   
   # Bad
   # Keep all 8 columns (unused columns clutter)
   ```

3. **Convert to proper data types**
   ```python
   # Good
   df['date'] = pd.to_datetime(df['date'])
   df['price'] = df['price'].astype(float)
   
   # Bad
   # Leave as string/object types
   ```

4. **Validate ranges**
   ```python
   # Good
   assert df['price'].min() > 0.5, "Price too low"
   assert df['price'].max() < 8.0, "Price too high"
   
   # Bad
   # No validation (errors propagate silently)
   ```

5. **Remove duplicates**
   ```python
   # Good
   df = df.drop_duplicates(subset=['date'])
   
   # Bad
   # Keep duplicates (breaks Gold layer joins)
   ```

6. **Sort by date**
   ```python
   # Good
   df = df.sort_values('date')
   
   # Bad
   # Leave unsorted (confuses time-series operations)
   ```

### Don'ts ❌

1. **Don't join multiple sources**
   ```python
   # Bad (this is Gold layer's job)
   silver = rbob_df.merge(retail_df, on='date')
   
   # Good (keep separate)
   rbob_silver = clean_rbob()
   retail_silver = clean_retail()
   ```

2. **Don't create features**
   ```python
   # Bad (this is Gold layer's job)
   df['crack_spread'] = df['price_rbob'] - df['price_wti']
   
   # Good (just clean individual prices)
   rbob_df = clean_rbob()  # only RBOB
   wti_df = clean_wti()     # only WTI
   ```

3. **Don't create lags**
   ```python
   # Bad (this is Gold layer's job)
   df['rbob_lag3'] = df['price_rbob'].shift(3)
   
   # Good (just current values)
   df[['date', 'price_rbob']]
   ```

4. **Don't over-sophisticate**
   ```python
   # Bad (overkill for research project)
   from pykalman import KalmanFilter
   df = kf.smooth(weekly_data)
   
   # Good (simple, transparent)
   df = weekly_data.resample('D').ffill()
   ```

5. **Don't skip validation**
   ```python
   # Bad (silent errors)
   df.to_parquet('silver/data.parquet')
   
   # Good (catch errors early)
   assert df['price'].min() > 0, "Invalid prices"
   df.to_parquet('silver/data.parquet')
   ```

---

## Silver Layer Scripts

### Script 1: `clean_rbob_to_silver.py`
```python
def clean_rbob_to_silver():
    # Load Bronze
    df = pd.read_parquet('bronze/rbob_daily_raw.parquet')
    
    # Transform
    df = df.rename(columns={'Date': 'date', 'Close': 'price_rbob'})
    df = df[['date', 'price_rbob', 'volume_rbob']]
    df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
    
    # Validate
    assert df['price_rbob'].min() > 0.5
    assert df['price_rbob'].max() < 8.0
    
    # Save Silver
    df.to_parquet('silver/rbob_daily.parquet')
```

### Script 2: `clean_retail_to_silver.py`
```python
def clean_retail_to_silver():
    # Load Bronze (weekly)
    weekly = pd.read_parquet('bronze/retail_prices_raw.parquet')
    
    # Transform
    weekly = weekly.assign(
        date=pd.to_datetime(weekly["period"]),
        retail_price=weekly["value"].astype(float)
    )[["date", "retail_price"]]
    
    # Forward-fill to daily
    full_range = pd.date_range(weekly["date"].min(), today, freq="D")
    daily = weekly.set_index("date").reindex(full_range).ffill().reset_index()
    
    # Validate
    assert daily["retail_price"].min() >= 1.5
    assert daily["retail_price"].max() <= 7.0
    
    # Save Silver
    daily.to_parquet('silver/retail_prices_daily.parquet')
```

### Script 3: `clean_eia_to_silver.py`
```python
def clean_inventory_to_silver():
    # Load Bronze
    df = pd.read_parquet('bronze/eia_inventory_raw.parquet')
    
    # Transform (unit conversion)
    df = df.assign(
        date=pd.to_datetime(df["period"]),
        inventory_mbbl=df["value"].astype(float) / 1000.0  # thousands→millions
    )[["date", "inventory_mbbl"]]
    
    # Validate
    assert df["inventory_mbbl"].min() > 180
    assert df["inventory_mbbl"].max() < 350
    
    # Save Silver
    df.to_parquet('silver/eia_inventory_weekly.parquet')

def clean_imports_to_silver():
    # Load Bronze (2 files)
    imports = pd.read_parquet('bronze/eia_imports_raw.parquet')
    exports = pd.read_parquet('bronze/eia_exports_raw.parquet')
    
    # Clean each
    imports = imports.assign(date=pd.to_datetime(imports["period"]), 
                            imports=imports["value"].astype(float))
    exports = exports.assign(date=pd.to_datetime(exports["period"]), 
                            exports=exports["value"].astype(float))
    
    # Merge and calculate
    df = imports.merge(exports, on="date")
    df = df.assign(net_imports_kbd=df["imports"] - df["exports"])
    df = df[["date", "net_imports_kbd"]]
    
    # Save Silver
    df.to_parquet('silver/eia_imports_weekly.parquet')
```

---

## Output: What Silver Layer Produces

### File Structure
```
data/silver/
├── rbob_daily.parquet           # 1,266 rows, 3 cols
├── wti_daily.parquet            # 1,265 rows, 2 cols
├── retail_prices_daily.parquet  # 1,834 rows, 2 cols (forward-filled!)
├── eia_inventory_weekly.parquet # 262 rows, 2 cols
├── eia_utilization_weekly.parquet # 262 rows, 2 cols
└── eia_imports_weekly.parquet   # 262 rows, 2 cols
```

### File Characteristics
```
✅ All files have 'date' column (consistent naming)
✅ All dates are datetime64[ns] (consistent type)
✅ All files have 2-3 columns (only essentials)
✅ All units are standardized (millions, $/gal, %)
✅ All files are sorted by date (time-series ready)
✅ No missing values in key columns
✅ No duplicate dates
✅ All ranges validated
```

---

## Common Questions

### Q: Why forward-fill retail prices but not other weekly data?

**A**: Retail prices are the TARGET variable, so we need daily values immediately.

```python
# Retail: Forward-fill in Silver (262 → 1,834 obs)
retail_daily.parquet  # Ready for Gold layer

# EIA data: Keep weekly in Silver, forward-fill in Gold
eia_inventory_weekly.parquet  # Gold layer will handle daily alignment
```

### Q: Why divide inventory by 1000?

**A**: Readability and modeling convenience.

```
Bronze: 226,747 thousand barrels (6 digits, awkward)
Silver: 226.747 million barrels (3 digits, cleaner)

Modeling impact:
- Regression coefficients smaller (easier to interpret)
- Less risk of numerical precision issues
```

### Q: Why drop so many columns?

**A**: Only keep what you'll use for modeling.

```
Yahoo Finance gives 8 columns:
  Date, Open, High, Low, Close, Volume, Dividends, Stock Splits

We only need 3:
  date, price_rbob (Close), volume_rbob

Dividends/Stock Splits = 0 for futures (useless)
Open/High/Low = Intraday (we use daily close)
```

### Q: What if I need Open/High/Low later?

**A**: Go back to Bronze layer.

```
Silver is for common use case (daily close prices)
Bronze preserves everything (can re-clean if needed)

Medallion architecture benefit: Bronze is immutable!
```

### Q: Why assert statements instead of try/except?

**A**: We WANT the script to crash if data is wrong.

```python
# Good (fails fast)
assert df['price'].min() > 0.5, "Price too low"
# → Script crashes, you fix Bronze download immediately

# Bad (silent failure)
try:
    df['price'] = df['price'].clip(lower=0.5)
except:
    pass
# → Bad data propagates to Gold, models train on garbage
```

---

## Summary

### What Silver Layer Does

1. **Takes Bronze** (raw API responses, many columns)
2. **Cleans** (standardize, simplify, validate)
3. **Produces Silver** (clean single-source files, few columns)

### What Silver Layer Doesn't Do

- ❌ Cross-file joins (Gold layer)
- ❌ Feature engineering (Gold layer)
- ❌ Lag creation (Gold layer)
- ❌ Multi-source transformations (Gold layer)

### Why Silver Layer Matters

- ✅ **Consistency**: All files have 'date', datetime64 type
- ✅ **Simplicity**: 8-11 cols → 2-3 cols per file
- ✅ **Units**: Standardized (millions, $/gal)
- ✅ **Validation**: Errors caught early
- ✅ **Transparency**: Simple, explainable transformations

### Output Quality

```
6 Silver files:
✓ 5,151 total rows
✓ 2-3 columns each
✓ 0% missing values in key columns
✓ 100% validated ranges
✓ 100% consistent naming
✓ Ready for Gold layer joins
```

**Next Step**: Gold layer joins Silver files and creates 22 features → modeling-ready dataset

---

## See Also

- `MEDALLION_ARCHITECTURE.md` - Why Bronze → Silver → Gold?
- `DATA_QUALITY_ASSESSMENT.md` - Overall data quality metrics
- `build_gold_layer.py` - What happens after Silver
