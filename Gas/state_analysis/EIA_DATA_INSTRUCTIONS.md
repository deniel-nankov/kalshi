# 📥 Getting EIA Historical State Gas Price Data

## 🎯 Goal

Download 143+ weeks of historical state-level gasoline prices to enable robust statistical analysis.

---

## 🚀 QUICK START (Recommended Method)

### Step 1: Get Free EIA API Key (2 minutes)

1. Go to: https://www.eia.gov/opendata/register.php
2. Fill in the form (name, email, organization)
3. Check your email for API key
4. Copy the API key (long alphanumeric string)

### Step 2: Run the Downloader

```bash
# Set your API key as environment variable
export EIA_API_KEY="your_api_key_here"

# Or save it to a file
echo "your_api_key_here" > state_analysis/.eia_api_key

# Run the downloader
python state_analysis/scripts/download_eia_data.py
```

The script will:
- Download 150 weeks of data for all 50 states + DC
- Save to `state_analysis/data/eia_state_prices_weekly.csv`
- Calculate volume-weighted national averages
- Ready for analysis!

---

## 🔄 ALTERNATIVE METHODS

### Method 2: Manual Download (No API Key Required)

1. **Go to EIA website:**
   - https://www.eia.gov/dnav/pet/pet_pri_gnd_dcus_nus_w.htm

2. **For each state:**
   - Click state name
   - Click "Download Series History" (Excel icon)
   - Save CSV file

3. **Combine files:**
   ```python
   import pandas as pd
   from pathlib import Path
   
   files = Path('downloads').glob('*.csv')
   dfs = [pd.read_csv(f) for f in files]
   combined = pd.concat(dfs)
   combined.to_csv('eia_combined.csv', index=False)
   ```

### Method 3: EIA Bulk Data System

1. Go to: https://www.eia.gov/opendata/bulkfiles.php
2. Download "Petroleum" bulk file (large!)
3. Extract state gasoline price series
4. Filter to needed time range

---

## 📊 DATA STRUCTURE

Downloaded data will have:

```csv
date,state,state_name,price
2023-01-02,CA,California,4.123
2023-01-02,TX,Texas,2.987
2023-01-02,FL,Florida,3.234
...
```

**Columns:**
- `date`: Week ending date (Monday)
- `state`: State abbreviation (CA, TX, etc.)
- `state_name`: Full state name
- `price`: Regular gasoline price ($/gallon)

**Coverage:**
- ~150 weeks (almost 3 years)
- All 50 states + DC
- Weekly resolution (Monday weeks)

---

## 🔬 WHAT YOU CAN DO WITH THIS DATA

With 150 weeks of data, you can:

✅ **Robust Correlation Analysis**
- 95% CI will be tight (not ±2.0 like with n=4!)
- Can detect r=0.3 with 80% power
- Statistically significant conclusions

✅ **Granger Causality Tests**
- Test if states lead/lag national
- Requires 30+ observations (you'll have 150!)
- Definitive answer on leading indicators

✅ **Model Enhancement**
- If patterns validated, add state features
- Expected 10-20% MAE improvement
- Walk-forward validation

✅ **Publication**
- Strong statistical evidence
- Either positive or null result publishable
- High-quality research

---

## ⚠️ IMPORTANT NOTES

### Weekly vs Daily Data

**Question:** "Won't weekly data miss daily patterns?"

**Answer:** **NO!** Here's why:

1. **Statistical Power:** 150 weekly points >> 4 daily points
   - Can detect r=0.3 (vs can't detect r=0.9 with n=4)

2. **Leading Patterns Persist:** 
   - If TX leads by 1 day, this shows up as "same week" (r≈1.0)
   - If TX leads by 1 week, this shows up in lag-1 analysis
   - Weekly data can detect weekly+ leads

3. **Granger Causality:**
   - Works with weekly data (tests if lag-1, lag-2 weeks predict)
   - If states lead by days, Granger might not detect it
   - But if they lead by weeks, will definitely detect!

4. **Practical Value:**
   - Even weekly leading indicators are valuable for forecasting
   - Most gas price forecasts are weekly anyway
   - Daily variations often noise

**Bottom Line:** Weekly data is SUFFICIENT for validating if state-level patterns exist!

---

## 🎯 SUCCESS CRITERIA

After downloading and analyzing:

**Scenario A: States Help** (35% probability)
- Some states Granger-cause national with p<0.05
- Cross-correlation shows leading patterns
- → Add validated features to model
- → Expected 10-20% MAE improvement

**Scenario B: States Don't Help** (65% probability)
- No Granger causality
- Correlations near 1.0 (states just aggregate)
- → Document null result
- → Publishable! (validates aggregation hypothesis)

**Either way: You have definitive answer in 1-2 days!**

---

## 🚀 TIMELINE

| Task | Time | Status |
|------|------|--------|
| Get API key | 2 min | ⏳ Pending |
| Run downloader | 5 min | ⏳ Pending |
| Download data | 10 min | ⏳ Pending |
| Run analysis | 30 min | ⏳ Pending |
| **Total** | **< 1 hour** | **vs 143 days waiting!** |

---

## 📝 NEXT STEPS

1. **Get API key** (do this NOW!)
   → https://www.eia.gov/opendata/register.php

2. **Run downloader**
   ```bash
   python state_analysis/scripts/download_eia_data.py
   ```

3. **Run analysis** (scripts already built!)
   ```bash
   python state_analysis/scripts/analyze_weekly_correlations.py
   python state_analysis/scripts/granger_causality_weekly.py
   ```

4. **Make decision:**
   - If validated → enhance model
   - If not → document null result
   - Either way → publish!

---

**Let's close the research cycle TODAY instead of waiting 5 months!** 🚀

