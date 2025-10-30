# State-Level Gas Price Analysis - Side Project

**Status:** Experimental (Does NOT affect Oct 31 main forecast)  
**Purpose:** Research if state prices can improve national predictions  
**Location:** `state_analysis/` (completely isolated)

---

## 🎯 Research Questions

1. **Which states drive the national average most?**
   - Expected: CA, TX, FL dominate due to consumption volume
   
2. **Do some states lead national prices?** (Early warning system)
   - Test: Does California price spike → National spike 1-2 days later?
   - Method: Granger causality, cross-correlation analysis
   
3. **Can state prices improve forecast accuracy?**
   - Baseline: Your current model (MAE $0.0214)
   - Enhanced: Add top 3-5 state features → MAE $0.018? (15% improvement)

---

## 📁 Project Structure

```
state_analysis/
├── README.md                          # This file
├── data/
│   ├── daily_snapshots/               # Daily state prices (CSV)
│   └── historical_state_prices.csv    # Combined dataset (30+ days)
├── scripts/
│   ├── collect_state_prices.py        # Daily scraper (AAA all 50 states)
│   ├── analyze_correlations.py        # Which states move together?
│   ├── test_leading_indicators.py     # Granger causality test
│   └── enhance_model.py               # Add state features to model
└── outputs/
    ├── correlation_matrix.png         # State-to-state correlations
    ├── leading_indicators.csv         # States that lead national
    └── enhanced_model_results.csv     # Performance comparison

```

---

## 🚀 How to Run

### Daily Collection (Automated)

```bash
# Collect today's state prices (all 50 states + DC)
python state_analysis/scripts/collect_state_prices.py
```

**Schedule with cron (9:30 AM daily):**
```bash
30 9 * * * cd /Users/denielnankov/Documents/kalshi/Gas && /Users/denielnankov/Documents/kalshi/.venv/bin/python state_analysis/scripts/collect_state_prices.py
```

### Analysis (After 30 Days)

```bash
# 1. Correlation analysis
python state_analysis/scripts/analyze_correlations.py

# 2. Leading indicator test
python state_analysis/scripts/test_leading_indicators.py

# 3. Enhance model (if states help)
python state_analysis/scripts/enhance_model.py
```

---

## 📊 Data Source

**AAA State Gas Prices:**
- URL: `https://gasprices.aaa.com/?state={STATE_CODE}`
- Updates: Daily at 9:00 AM EST
- Coverage: All 50 states + DC
- Free, no API key needed

**Example:**
- California: `https://gasprices.aaa.com/?state=CA`
- Texas: `https://gasprices.aaa.com/?state=TX`
- New York: `https://gasprices.aaa.com/?state=NY`

---

## 🔬 Expected Findings

### Hypothesis 1: National = Volume-Weighted Average (Most Likely)

```
National = Σ(State_i × Consumption_i) / Total_Consumption

Top consumers:
  CA: 14.5% weight
  TX: 12.3% weight
  FL:  8.1% weight
  ...
```

**If true:** All states move together (same RBOB market, crude oil). No leading indicators.

**Implication:** State features won't improve model (redundant with RBOB).

### Hypothesis 2: Some States Lead (Possible Edge Case)

```
Example: Hurricane disrupts Gulf Coast
  Day 1: TX/LA spike (+$0.20)
  Day 2: National spike (+$0.03)
```

**If true:** TX/LA prices = 1-day leading indicator for national average!

**Implication:** Add `TX_lag1`, `LA_lag1` features → Improve MAE by 10-15%

---

## 🎯 Success Criteria

### Minimum (Validate Hypothesis)

- [ ] Collect 30 days of state prices (all 50 states)
- [ ] Calculate volume-weighted national average
- [ ] Compare to AAA national (should match within $0.01)
- [ ] Correlation matrix: Which states move together?

**Deliverable:** Report confirming national = weighted average

### Ideal (Find Leading Indicators)

- [ ] Granger causality: `State(t-1) → National(t)`
- [ ] Identify 3-5 states with significant lead (p < 0.05)
- [ ] Add state features to model
- [ ] Test on validation set: MAE improvement?

**Deliverable:** Enhanced model with state features (if they help)

---

## ⚠️ ISOLATION GUARANTEE

**This project is COMPLETELY SEPARATE from your Oct 31 forecast:**

✅ **Does NOT modify:**
- `data/gold/master_model_ready.parquet` (historical data)
- `scripts/automated_train_predict_oct31.py` (Oct 31 forecast)
- `outputs/final_validation/` (Oct 31 results)
- Any existing model or prediction

✅ **Only creates NEW files in:**
- `state_analysis/data/` (state prices only)
- `state_analysis/outputs/` (state analysis only)

✅ **Safe to run in parallel:**
- Oct 31 forecast: Uses national average (current system)
- State analysis: Collects state data (no interference)

---

## 📅 Timeline

### Phase 1: Data Collection (Oct 29 - Nov 27)

- **Day 1 (Today):** Set up scraper, collect first snapshot
- **Days 2-30:** Automatic daily collection
- **Day 30:** Have 30 days of state data → Run analysis

### Phase 2: Analysis (Nov 27-30)

- Correlation analysis
- Leading indicator tests
- Volume-weighted validation

### Phase 3: Model Enhancement (Dec 1-5)

- Add state features (if beneficial)
- Validate on test set
- Compare to baseline

---

## 💡 Quick Start

**Today (Oct 29):**

```bash
# 1. Collect first state snapshot
python state_analysis/scripts/collect_state_prices.py

# 2. Review data
cat state_analysis/data/daily_snapshots/state_prices_2025-10-29.csv
```

**Expected output:**
```
date,state,price,consumption_weight
2025-10-29,CA,3.456,14.5
2025-10-29,TX,2.987,12.3
2025-10-29,FL,3.123,8.1
...
```

**Tomorrow (Oct 30 - After deadline!):**

```bash
# Set up cron for automatic daily collection
crontab -e

# Add:
30 9 * * * cd /Users/denielnankov/Documents/kalshi/Gas && /Users/denielnankov/Documents/kalshi/.venv/bin/python state_analysis/scripts/collect_state_prices.py
```

---

## 📊 Current Status

- [x] Project structure created
- [x] Scraper script ready (`collect_state_prices.py`)
- [ ] First snapshot collected (run today!)
- [ ] 30 days collected (by Nov 27)
- [ ] Analysis complete
- [ ] Model enhancement tested

---

## 🎓 Research Value

Even if states DON'T improve predictions, this research is valuable:

1. **Validates national averaging** - Confirms AAA methodology
2. **Regional patterns** - Understand state-to-state relationships
3. **Future work** - State-level forecasting (CA only, TX only, etc.)
4. **Publication material** - Novel analysis for paper appendix

---

**Let's start collecting data! Run the first snapshot after your Oct 31 deadline.**
