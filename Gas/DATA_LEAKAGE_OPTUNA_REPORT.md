# Data Leakage Investigation Report - Optuna Results
**Date:** October 19, 2025  
**Issue:** Optuna achieved R²=1.0000 but validation revealed severe overfitting

## 🔍 Problem Discovery

During rigorous validation testing of Optuna optimization results, we discovered:
1. **Ridge (Optuna)** achieved perfect R²=1.0000 on training data
2. **Validation test** revealed severe overfitting (gap=0.70, test R²=0.29)
3. **Data leakage warning:** `retail_price` and `target` are 100% correlated

## 🐛 Root Cause Analysis

### Investigation Results:
```
retail_price == target: 1,819 / 1,819 rows (100% identical!)
Correlation: 1.000000
Difference mean: 0.000000
```

### Code Inspection:

**File:** `scripts/build_gold_layer.py` (Line 441)
```python
gold["target"] = gold["retail_price"]
```

**Problem:** Target is set to CURRENT retail price, not FUTURE retail price!

## ✅ Why Walk-Forward Validation Worked

Your walk-forward scripts correctly handle this:

**File:** `src/models/baseline_models.py` (Line 354)
```python
def prepare_forecast_frame(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Prepare a modeling dataframe for a particular forecast horizon."""
    df_sorted = df.sort_values("date").reset_index(drop=True).copy()
    
    # ✅ THIS CREATES THE PROPER FUTURE TARGET
    df_sorted["target"] = df_sorted["retail_price"].shift(-horizon)
    df_sorted["target_date"] = df_sorted["date"] + pd.to_timedelta(horizon, unit="D")
    
    prepared = df_sorted.dropna(subset=["target"]).reset_index(drop=True)
    return prepared
```

**Example:**
- For horizon=1: Today's features → Tomorrow's price ✅
- For horizon=2: Today's features → Day-after-tomorrow's price ✅
- For horizon=3: Today's features → 3 days ahead price ✅

## ❌ Why Optuna Failed

**File:** `scripts/tune_with_optuna.py`
```python
# Load data
df = pd.read_parquet('data/gold/master_model_ready.parquet')

# Problem: Used gold layer directly WITHOUT calling prepare_forecast_frame()!
X = df[feature_cols].fillna(0)
y = df['target']  # ❌ This is CURRENT price, not FUTURE price!

# Result: Model learns: "Given today's price, predict today's price"
# Perfect R²=1.0000 but useless for forecasting!
```

## 📊 Impact on Results

### Walk-Forward Validation (✅ Correct):
- Ridge (alpha=1.0): R²=0.931 (1-day horizon)
- Ensemble: R²=0.796 (2-day horizon)
- **Uses proper future targets via `prepare_forecast_frame()`**

### Optuna Optimization (❌ Incorrect):
- Ridge (Optuna): R²=1.0000 training, R²=0.29 test
- GB (Optuna): R²=1.0000 training, R²=-1.41 test
- **Used leaky targets - predicting present from present**

### Rigorous Validation Test (✅ Exposed the issue):
```
❌ Ridge (Optuna) NOT RECOMMENDED - Use Baseline!
   - High overfitting (gap: 0.7044)
   - Worse than baseline (diff: -0.0190, -6.1%)

❌ GB (Optuna) still NOT RECOMMENDED
   - Poor test performance (R²: -1.4137)
```

## 🎯 Correct Approach

### For Training Models:
```python
# ALWAYS use prepare_forecast_frame() for each horizon
for horizon in [1, 2, 3]:
    df_h = prepare_forecast_frame(gold, horizon=horizon)
    # Now df_h["target"] is the FUTURE price
    X = df_h[features]
    y = df_h["target"]
    model.fit(X, y)
```

### For Hyperparameter Tuning:
```python
# Must prepare data BEFORE optimization
df_h = prepare_forecast_frame(gold, horizon=1)  # ✅ Proper future targets
X = df_h[features]
y = df_h["target"]

# Now optimize
optuna.optimize(...)
```

## 📝 Additional Findings

### Sentiment Features Not Properly Lagged:
- `consumer_sentiment`: ❌ NOT LAGGED
- `news_sentiment_7d_avg`: ❌ NOT LAGGED  
- `news_sentiment_14d_avg`: ❌ NOT LAGGED
- `news_sentiment_volatility_7d`: ❌ NOT LAGGED
- `news_sentiment_volatility_14d`: ❌ NOT LAGGED
- `sentiment_momentum_7d`: ❌ NOT LAGGED

Only 2/8 sentiment features are properly lagged:
- `news_sentiment_lag15`: ✅ LAGGED
- `extreme_sentiment_flag`: ✅ LAGGED

**Note:** This may contribute to overfitting, but the main issue is the target variable leak.

## ✅ Conclusion

1. **Optuna results are INVALID** due to data leakage
2. **Walk-forward validation results are VALID** (proper temporal setup)
3. **Stick with Ridge (alpha=1.0)** from original GridSearchCV:
   - 1-day: R²=0.931
   - 2-day: R²=0.796 (ensemble)
   - 3-day: R²=0.851 (baseline)
4. **Do NOT use Optuna parameters** - they were trained on leaky data

## 🚀 Next Steps

1. ✅ **Keep existing walk-forward results** - they are scientifically sound
2. ✅ **Discard Optuna results** - data leakage invalidates them
3. ⏳ **Proceed to Neural Networks** - using proper `prepare_forecast_frame()`
4. ⏳ **Update paper** - explain why simpler models (Ridge) work best
5. ⏳ **Create visualizations** - show walk-forward performance

## 📚 Lessons Learned

1. **Always validate with rigorous testing** - caught a critical bug!
2. **Temporal data requires careful handling** - use proper shifting
3. **Perfect scores are suspicious** - R²=1.0000 should raise red flags
4. **Your walk-forward approach was correct all along** ✅

## 📁 Files Created

- `DATA_LEAKAGE_OPTUNA_REPORT.md` (this file)
- `outputs/optuna_validation/validation_results.csv` (detailed test results)
- `outputs/optuna_validation/validation_analysis.png` (6-panel visualization)
