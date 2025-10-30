# State Analysis Quick Reference

## 🎯 What This Project Does

**Research Question:** Can state-level gas prices improve national forecasts?

**Current Status:** Data collection infrastructure ready  
**Impact on Oct 31 forecast:** ZERO (completely isolated)

---

## 📊 Files Created

### Main Scripts
1. **`collect_state_prices.py`** - Scrapes all 50 states + DC daily
2. **`analyze_correlations.py`** - Which states move together? (after 30 days)
3. **`test_leading_indicators.py`** - Do states lead national? (after 30 days)

### Data Structure
```
state_analysis/
├── data/
│   ├── daily_snapshots/              # state_prices_YYYY-MM-DD.csv
│   ├── historical_state_prices.csv   # Combined dataset
│   ├── daily_summaries.json          # Collection metadata
│   └── collection_log.txt            # Execution logs
└── outputs/
    ├── correlation_heatmap.png       # State-to-state correlations
    ├── state_correlation_matrix.csv  # Full correlation matrix
    └── leading_indicators.csv        # States that lead national
```

---

## 🚀 How to Run

### First Collection (Today)

```bash
cd /Users/denielnankov/Documents/kalshi/Gas
/Users/denielnankov/Documents/kalshi/.venv/bin/python state_analysis/scripts/collect_state_prices.py
```

**What it does:**
1. Scrapes AAA for all 50 states + DC (~2 minutes)
2. Saves daily snapshot to `data/daily_snapshots/`
3. Updates `historical_state_prices.csv`
4. Calculates volume-weighted national average
5. Logs everything to `collection_log.txt`

### Automatic Daily Collection

```bash
# Edit cron
crontab -e

# Add this line (runs at 9:30 AM daily)
30 9 * * * cd /Users/denielnankov/Documents/kalshi/Gas && /Users/denielnankov/Documents/kalshi/.venv/bin/python state_analysis/scripts/collect_state_prices.py >> /Users/denielnankov/Documents/kalshi/Gas/state_analysis/data/cron.log 2>&1
```

### Analysis (After 30 Days)

```bash
# Correlation analysis
/Users/denielnankov/Documents/kalshi/.venv/bin/python state_analysis/scripts/analyze_correlations.py

# Leading indicator test
/Users/denielnankov/Documents/kalshi/.venv/bin/python state_analysis/scripts/test_leading_indicators.py
```

---

## ✅ Verification

After first run, check:

```bash
# 1. Daily snapshot created?
ls -lh state_analysis/data/daily_snapshots/

# 2. Historical file updated?
wc -l state_analysis/data/historical_state_prices.csv

# 3. Log shows success?
tail -20 state_analysis/data/collection_log.txt

# 4. Summary stats saved?
cat state_analysis/data/daily_summaries.json | tail -20
```

Expected output:
- Daily snapshot: ~51 rows (one per state)
- Historical file: 51 × number_of_days rows
- Log: Shows success rate (should be >80%)

---

## 📅 Timeline

| Date | Days | Action |
|------|------|--------|
| Oct 29 | 1 | First collection (today) |
| Oct 30-Nov 27 | 2-30 | Daily automatic collection |
| Nov 27 | 30 | Run correlation analysis |
| Nov 28-30 | | Test leading indicators |
| Dec 1+ | | Enhance model if states help |

---

## 🎯 Expected Findings

### Most Likely: No Leading Indicators

**Reason:** All states react to same RBOB market simultaneously

```
RBOB futures change → All 51 states adjust together → National average changes
(No lag, no leading indicator)
```

**Value:** Confirms current model (RBOB dominance) is optimal

### Possible: Regional Leading Indicators

**Example:** Gulf Coast hurricane

```
Day 1: TX/LA spike (+$0.20) due to refinery shutdown
Day 2: National average increases (+$0.03) as other states catch up
```

**Value:** Add TX_lag1, LA_lag1 features → 10-15% MAE improvement

---

## 🔬 Isolation Guarantee

**This project CANNOT affect your Oct 31 forecast:**

✅ **Separate directory:** `state_analysis/` (isolated)  
✅ **No shared files:** Uses own data files only  
✅ **No model changes:** Doesn't touch `scripts/automated_train_predict_oct31.py`  
✅ **Safe to run in parallel:** Both systems use different data sources

**Oct 31 system:**
- Uses: `outputs/aaa_daily_oct18_29.csv` (national average)
- Predicts: $3.046/gal
- Status: ✅ Ready for submission

**State analysis:**
- Uses: `state_analysis/data/historical_state_prices.csv` (state-level)
- Predicts: Nothing yet (data collection phase)
- Status: 🔄 Collecting data for 30 days

---

## 💡 Quick Start Checklist

- [ ] Read `state_analysis/README.md`
- [ ] Run first collection: `python state_analysis/scripts/collect_state_prices.py`
- [ ] Verify data saved to `state_analysis/data/daily_snapshots/`
- [ ] (Optional) Set up cron for daily collection
- [ ] Wait 30 days
- [ ] Run correlation analysis
- [ ] Test leading indicators
- [ ] Enhance model if states help

---

## 📊 What Success Looks Like

### Minimum Success (Most Likely)

- 30 days of state data collected ✅
- Correlation analysis shows states move together (>0.95 correlation) ✅
- No leading indicators found ✅
- **Conclusion:** National average = volume-weighted mean (validates current model)

### Maximum Success (Less Likely but Valuable!)

- 30 days of state data collected ✅
- Found 3-5 states that lead national by 1-2 days ✅
- Added state features to model ✅
- **Result:** MAE improved from $0.0214 → $0.018 (15% better!)

---

## 🎓 Research Value

Even if NO improvement:
1. Validates AAA national averaging methodology
2. Understands regional gas price dynamics
3. Identifies high-impact states (CA, TX, FL)
4. Publication-worthy analysis (paper appendix)
5. Foundation for state-specific forecasting

---

**Start collecting today! Run after your Oct 31 deadline.** 🚀
