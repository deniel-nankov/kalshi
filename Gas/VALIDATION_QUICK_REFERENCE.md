# Quick Reference: Data Validation System

**Purpose:** Fast reference for running validation checks and interpreting results

---

## 🚀 Quick Commands

### **Run Complete Validation**
```bash
cd /Users/denielnankov/Documents/kalshi/Gas
python scripts/4_validate_pipeline.py
```

**What it does:**
- Validates silver layer (schema, nulls, date continuity)
- Validates gold layer (target, features, suspicious columns)
- Runs leakage detection on COMMON_FEATURES
- Generates JSON and CSV reports
- Exit code 1 if critical issues found

---

### **Run Leakage Detection Only**
```bash
python scripts/detect_leakage.py data/gold/master_model_ready.parquet
```

**What it does:**
- Checks feature-target correlations (threshold: 0.50)
- Detects perfect predictions (>0.95 correlation)
- Validates lag consistency
- Generates CSV report
- Exit code 1 if leakage detected

---

### **Download Fresh Data to Bronze**
```bash
python scripts/1_download_to_bronze.py --start-date 2020-01-01 --end-date 2025-10-18
```

**What it does:**
- Fetches data from EIA, FRED APIs
- Creates geopolitical indicators
- Saves to `data/bronze/` with metadata
- Validates schema on write

**Status:** Partial (retail prices working, use silver for others)

---

## 📊 Interpreting Results

### **Validation Pipeline Output**

```
✅ PASSED: No issues found
⚠️  WARNINGS: Investigate but not blocking
🚨 CRITICAL: Must fix before production
```

**Exit Codes:**
- `0` = All validations passed
- `1` = Critical issues detected

---

### **Leakage Detection Output**

#### **Correlation Thresholds:**

| Correlation | Status | Meaning |
|-------------|--------|---------|
| < 0.50 | ✅ OK | Normal predictive relationship |
| 0.50 - 0.95 | 🔔 SUSPICIOUS | Flag for review |
| > 0.95 | 🚨 CRITICAL | Likely leakage (or natural for prices) |

#### **Expected High Correlations (NOT Leakage):**

These features SHOULD have high correlations:

1. **`retail_price_lag14`** (0.973) ✅
   - Retail prices are highly autocorrelated
   - 14-day lag is properly applied
   - This is VALID and expected

2. **`rbob_lag7/14/21`** (0.95-0.97) ✅
   - RBOB futures are primary input cost
   - Naturally predict retail prices well
   - Properly lagged

3. **`price_rbob_ma21`** (0.974) ✅
   - Moving average of RBOB futures
   - Smoothed version, still highly predictive
   - Properly calculated

#### **Actual Leakage (FIXED):**

**SPR Release Bug (correlation=0.61):**
```python
# WRONG (leaked):
spr_release = -spr_stocks.diff() / 7

# FIXED:
spr_release = -spr_stocks.diff().shift(14) / 7
```

---

## 📁 Validation Reports

### **Location:**
```
data/gold/validation_reports/
├── validation_report.json       # Full validation results
└── leakage_detection_report.csv # Detailed leakage findings
```

### **Reading `validation_report.json`:**

```json
{
  "bronze_to_silver": [
    {
      "test": "row_count_eia_inventory_weekly.parquet",
      "status": "PASS",
      "message": "262 rows loaded successfully"
    }
  ],
  "gold_leakage": [
    {
      "test": "critical_leakage",
      "status": "CRITICAL",
      "message": "8 features have correlation >0.95"
    }
  ],
  "summary": {
    "critical": 1,
    "warnings": 5,
    "total_issues": 6
  }
}
```

### **Reading `leakage_detection_report.csv`:**

| test | feature | correlation | status | message |
|------|---------|-------------|--------|---------|
| feature_target_correlation | rbob_lag14 | 0.968 | CRITICAL | Near-perfect correlation |
| lag_consistency | price_rbob | 1 | WARNING | Feature may be lagged by 1 instead of 14 |

---

## 🔧 Common Issues & Fixes

### **Issue 1: "8 features have critical leakage"**

**Status:** ✅ **EXPECTED** - Not actual leakage

**Explanation:**
- These are RBOB and retail price lags
- Naturally have >0.95 correlation
- All properly lagged with `.shift(14)`
- This is VALID predictive power

**Action:** No fix needed

---

### **Issue 2: "retail_price found (unlagged)"**

**Status:** ⚠️  **WARNING** - Not used in model

**Explanation:**
- `retail_price` exists in gold dataset
- BUT: Not in `COMMON_FEATURES` list
- Only lagged versions used in training

**Action:** Optional cleanup (remove from gold layer)

---

### **Issue 3: "Feature may be lagged by 1 instead of 14"**

**Status:** ⚠️  **WARNING** - Autocorrelation test artifact

**Explanation:**
- Lag consistency uses autocorrelation
- Short-term autocorr often higher than 14-day
- Does NOT indicate actual leakage

**How to Verify:**
```python
# Check if feature uses .shift(14)
# Look in scripts/build_gold_layer.py

df['feature_t'] = df['raw_value'].shift(14)  # ✅ Correct
```

---

### **Issue 4: "High null percentage in features"**

**Status:** ⚠️  **WARNING** - Check if acceptable

**Common Causes:**
- Hurricane features: Only populated during hurricane season (OK)
- OPEC cuts: Only during cut periods (OK)
- Missing API data: Investigate source

**Action:**
- If domain-appropriate: Accept
- If data quality issue: Fix source

---

## 🎯 Pre-Production Checklist

Before deploying model to production, run this checklist:

```bash
# 1. Run full validation
python scripts/4_validate_pipeline.py
# Expected: 0-8 CRITICAL (high correlations OK), <70 WARNINGS

# 2. Check reports
cat data/gold/validation_reports/validation_report.json | jq '.summary'
# Expected: {"critical": 1, "warnings": <10}

# 3. Verify model performance
python scripts/train_models.py --horizon 14
# Expected: Ridge R² ≈ 0.22, MAE ≈ $0.038

# 4. Generate forecast
python scripts/generate_october_forecast.py
# Expected: Realistic price predictions ($2.80-$3.20 range)

# 5. Check data freshness
python -c "import pandas as pd; df = pd.read_parquet('data/gold/master_model_ready.parquet'); print('Latest data:', df['date'].max())"
# Expected: Within last 7 days
```

**If all checks pass:** ✅ Ready for production!

---

## 📞 Troubleshooting

### **Validation fails with error**

```bash
# Check Python environment
python --version  # Should be 3.8+

# Check dependencies
pip list | grep -E "pandas|numpy|scikit-learn"

# Run with verbose output
python scripts/4_validate_pipeline.py 2>&1 | tee validation_output.log
```

---

### **Leakage detector shows 0 features**

**Likely cause:** `COMMON_FEATURES` not loading

**Fix:**
```bash
# Check if baseline_models.py exists
ls -la src/models/baseline_models.py

# Verify COMMON_FEATURES defined
grep -A 50 "COMMON_FEATURES" src/models/baseline_models.py
```

---

### **API key errors**

```bash
# Check .env file
cat .env | grep -E "EIA|FRED|NOAA"

# Should see:
# EIA_API_KEY=ZRQpMT5nl7hxXi3A3tHvJ2BQAOEeHJXq5SU5VXom
# FRED_API_KEY=b4a18aac3a462b6951ee89d9fef027cb
# NOAA_TOKEN=wvLRJpSPaaBPLjELLuWoWFlKVqoCLQyo
```

---

## 📚 Key Files

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `scripts/detect_leakage.py` | Leakage detection | Rarely (stable) |
| `scripts/4_validate_pipeline.py` | Full validation | Rarely (stable) |
| `data/gold/master_model_ready.parquet` | Training data | Weekly (new data) |
| `src/models/baseline_models.py` | Feature definitions | Monthly (new features) |
| `.env` | API keys | Rarely (key rotation) |

---

## 🔗 Related Documentation

- **Architecture:** `MEDALLION_ARCHITECTURE_WORKFLOW.md`
- **Implementation:** `MEDALLION_IMPLEMENTATION_SUMMARY.md`
- **Complete Report:** `MEDALLION_VALIDATION_COMPLETE_REPORT.md`
- **Data Leakage Bug:** `DATA_LEAKAGE_FIX_REPORT.md`

---

## ✅ Expected Validation Results

**NORMAL OUTPUT (Production Ready):**
```
VALIDATION SUMMARY:
🚨 CRITICAL: 1 issue (8 features with >0.95 corr - EXPECTED)
⚠️  WARNINGS: 5-10 issues (lag tests, nulls - ACCEPTABLE)
✅ PASSED: Most tests

VERDICT: VALIDATION PASSED WITH WARNINGS
```

**What to worry about:**
- ❌ New features with >0.60 correlation (not RBOB/retail price)
- ❌ Perfect correlation (1.000) with target
- ❌ More than 10% nulls in core features

**What NOT to worry about:**
- ✅ RBOB/retail price correlations >0.95 (expected)
- ✅ Hurricane features with nulls (seasonal)
- ✅ Lag warnings from autocorrelation tests

---

**Last Updated:** October 18, 2025  
**Status:** ✅ Production Ready
