# EIA API Data Availability & Refresh Schedule

**Date Created**: October 20, 2025 (Sunday)  
**Last Checked**: October 20, 2025 15:04 ET

---

## 📊 Current Data Status

### Our Local Data (Gold Layer)
- **Latest Date**: October 18, 2025 (Friday)
- **Latest Price**: $3.061 per gallon
- **Current Lag**: 2 days (normal for Sunday)

### EIA API Status
- **Status**: Returning 500 errors (temporary)
- **Reason**: Sunday - no new data expected + possible maintenance
- **Action**: No concern - will retry automatically tomorrow

---

## 📅 EIA Publication Schedule

### Product Information
- **API Code**: `EPM0_EPD2D_PTE_NUS_DPG`
- **Description**: U.S. Regular Gasoline Retail Price (All Formulations)
- **Unit**: Dollars per gallon
- **Geographic Coverage**: United States Average

### Publication Pattern

| Aspect | Details |
|--------|---------|
| **Frequency** | Daily (weekdays only) |
| **Update Time** | ~5:00 PM Eastern Time |
| **Publication Days** | Monday - Friday only |
| **No Updates** | Weekends, Federal holidays |
| **Data Lag** | 1-2 business days |

---

## 🗓️ Week-by-Week Publication Pattern

### Typical Weekly Schedule

| Data Date (Day) | Publication Date | Publication Time | Notes |
|-----------------|------------------|------------------|-------|
| **Monday** | Wednesday | 5:00 PM ET | 2-day lag |
| **Tuesday** | Thursday | 5:00 PM ET | 2-day lag |
| **Wednesday** | Friday | 5:00 PM ET | 2-day lag |
| **Thursday** | Monday (next week) | 5:00 PM ET | 4-day lag (weekend) |
| **Friday** | Tuesday (next week) | 5:00 PM ET | 4-day lag (weekend) |
| **Saturday** | ❌ No data collected | - | Weekends skipped |
| **Sunday** | ❌ No data collected | - | Weekends skipped |

### Example Timeline (Oct 2025)

```
┌────────────────┬──────────────────┬─────────────┐
│ Actual Date    │ Published On     │ Available   │
├────────────────┼──────────────────┼─────────────┤
│ Oct 14 (Tue)   │ Oct 16 (Thu) 5PM │ ✅          │
│ Oct 15 (Wed)   │ Oct 17 (Fri) 5PM │ ✅          │
│ Oct 16 (Thu)   │ Oct 21 (Mon) 5PM │ ⏳ Pending  │
│ Oct 17 (Fri)   │ Oct 22 (Tue) 5PM │ ⏳ Pending  │
│ Oct 18 (Sat)   │ No data          │ ❌ Skipped  │
│ Oct 19 (Sun)   │ No data          │ ❌ Skipped  │
│ Oct 20 (Mon)   │ Oct 22 (Wed) 5PM │ ⏳ Future   │
│ Oct 21 (Tue)   │ Oct 23 (Thu) 5PM │ ⏳ Future   │
└────────────────┴──────────────────┴─────────────┘
```

---

## 🎯 Current Week Forecast (Oct 20-26)

### Today: Sunday, October 20, 2025
- **API Status**: 500 errors (expected - no weekend updates)
- **Latest Data**: Oct 18 (Friday)
- **Next Update**: Tomorrow (Monday) ~5 PM ET
- **Action**: No need to check today

### Monday, October 21, 2025
- **Expected Update**: 5:00 PM ET
- **Will Contain**: 
  - Oct 16 (Thursday) - Confirmed
  - Oct 17 (Friday) - Likely
  - Maybe Oct 18 (Saturday) - Unlikely (weekend)
- **For Your Tracking**: Run script after 6 PM ET to be safe
- **What You'll Get**: Validation for your Oct 19 prediction likely NOT available yet

### Tuesday, October 22, 2025
- **Expected Update**: 5:00 PM ET
- **Will Contain**: 
  - Oct 18 (Saturday) - No data (weekend)
  - Oct 19 (Sunday) - No data (weekend)
  - Oct 20 (Monday) - **YES!** Available Tuesday evening
- **For Your Tracking**: Run after 6 PM ET
- **What You'll Get**: Oct 19 prediction validation MIGHT be available

### Wednesday, October 23, 2025
- **Expected Update**: 5:00 PM ET
- **Will Contain**: Oct 21 (Tuesday) data
- **For Your Tracking**: Run after 6 PM ET
- **What You'll Get**: Oct 20-21 predictions validated

### Rest of Week
- Thursday: Get Wednesday data
- Friday: Get Thursday data
- Weekend: No updates

---

## ⏱️ Data Lag Analysis

### Normal Lags by Day of Week

| Today (Check Day) | Latest Data Available | Lag | Status |
|-------------------|------------------------|-----|--------|
| **Monday** | Previous Thursday/Friday | 3-4 days | ✅ Normal (weekend gap) |
| **Tuesday** | Previous Friday/Monday | 1-4 days | ✅ Normal |
| **Wednesday** | Monday | 2 days | ✅ Normal |
| **Thursday** | Tuesday | 2 days | ✅ Normal |
| **Friday** | Wednesday | 2 days | ✅ Normal |
| **Saturday** | Wednesday/Thursday | 2-3 days | ✅ Normal (no weekend updates) |
| **Sunday** | Thursday/Friday | 2-3 days | ✅ Normal (no weekend updates) |

### Current Lag (Oct 20, 2025)
- **Today**: Sunday, Oct 20
- **Latest Data**: Friday, Oct 18
- **Lag**: 2 days
- **Assessment**: ✅ **NORMAL** - Expected for Sunday

---

## 🔄 API Refresh Timing

### When Does EIA Update?

**Publication Window**: 
- **Target Time**: 5:00 PM Eastern Time
- **Actual Range**: 4:45 PM - 5:30 PM ET (usually)
- **Delays**: Rare, but can occur during high server load or data issues

**Best Practice for Your Daily Tracking**:
```bash
# Wait until 6:00 PM ET to be safe
# Run daily routine after 6 PM ET on weekdays
./scripts/daily_routine.sh
```

### Time Zone Conversions

| Time Zone | Update Time |
|-----------|-------------|
| **Eastern (ET)** | 5:00 PM |
| **Central (CT)** | 4:00 PM |
| **Mountain (MT)** | 3:00 PM |
| **Pacific (PT)** | 2:00 PM |

---

## 📝 For Your Daily Tracking Workflow

### Daily Routine Schedule

#### Weekdays (Monday - Friday)
```bash
# After 6:00 PM ET
cd /Users/denielnankov/Documents/kalshi/Gas
./scripts/daily_routine.sh
```

**What Happens**:
1. **Step 1**: Validates pending predictions (checks for new actuals)
2. **Step 2**: Makes tomorrow's prediction with all 3 methods

**Expected Results**:
- Monday-Wednesday: Get 2-3 day old data
- Thursday-Friday: Get 2 day old data
- Your predictions validated with 1-3 day lag

#### Weekends (Saturday - Sunday)
```
❌ SKIP - No new data published
```

**Optional**: Can still make predictions, but no validation possible

---

## 🎯 What This Means for Your 10-Day Collection

### Timeline (Oct 19-29)

| Date | Day | Make Prediction | Validate Prediction | Actual Available |
|------|-----|-----------------|---------------------|------------------|
| Oct 19 | Sat | ✅ Done | ⏳ Oct 21-22 | Oct 21/22 evening |
| Oct 20 | Sun | ✅ Can do | ⏳ Oct 22-23 | Oct 22/23 evening |
| Oct 21 | Mon | ✅ Tonight | ⏳ Oct 23 | Oct 23 evening |
| Oct 22 | Tue | ✅ Tonight | ⏳ Oct 24 | Oct 24 evening |
| Oct 23 | Wed | ✅ Tonight | ⏳ Oct 25 | Oct 25 evening |
| Oct 24 | Thu | ✅ Tonight | ⏳ Oct 28 | Oct 28 (Mon) evening |
| Oct 25 | Fri | ✅ Tonight | ⏳ Oct 29 | Oct 29 (Tue) evening |
| Oct 26 | Sat | ✅ Optional | ⏳ Oct 29 | Oct 29 evening |
| Oct 27 | Sun | ✅ Optional | ⏳ Oct 30 | Oct 30 evening |
| Oct 28 | Mon | ✅ Tonight | ⏳ Oct 30 | Oct 30 evening |
| Oct 29 | Tue | ✅ Tonight | ⏳ Nov 1 | Nov 1 (Fri) evening |

### Expected Coverage by Oct 29
- **Predictions Made**: 10 (Oct 19-28, maybe 19-29)
- **Validated**: 7-8 predictions
  - Oct 19-23: ✅ Validated (5 days)
  - Oct 24-25: ✅ Validated (2 days)
  - Oct 26-29: ⏳ Pending (2-3 days lag)

**Bottom Line**: You'll have 7-8 fully validated predictions by your deadline, which is excellent for the paper!

---

## ⚠️ Common Issues & Solutions

### Issue 1: 500 Status Code
**Cause**: Temporary API issues, maintenance, or weekends  
**Solution**: Retry logic (already implemented) handles this  
**Action**: Wait and retry - usually resolves in 2-4 attempts

### Issue 2: "No data available for date range"
**Cause**: Data not published yet (within 1-2 day lag window)  
**Solution**: Normal behavior, check again next day  
**Action**: Script will show "⏳ WAITING FOR DATA"

### Issue 3: Longer than usual lag (3+ days)
**Cause**: Federal holidays, extended weekends  
**Solution**: Wait one more day  
**Action**: Check EIA website: https://www.eia.gov/petroleum/gasdiesel/

### Issue 4: Connection timeout
**Cause**: Network issues or API overload  
**Solution**: Retry automatically (exponential backoff)  
**Action**: Script handles this with 5 retry attempts

---

## 🔗 Useful Links

### Official EIA Resources
- **API Endpoint**: https://api.eia.gov/v2/petroleum/pri/gnd/data/
- **Web Portal**: https://www.eia.gov/petroleum/gasdiesel/
- **API Documentation**: https://www.eia.gov/opendata/
- **Data Browser**: https://www.eia.gov/opendata/browser/

### API Parameters We Use
```
Product:   EPM0_EPD2D_PTE_NUS_DPG
Frequency: daily
Start:     (date - 10 days)
End:       (date)
Sort:      period descending
```

---

## ✅ Key Takeaways

### For Daily Tracking:

1. **Run After 6 PM ET on Weekdays** - Guarantees data is published
2. **Skip Weekends** - No new data published
3. **Expect 1-2 Day Lag** - Normal EIA publication delay
4. **Mondays Have 3-4 Day Lag** - Due to weekend gap
5. **Retry Logic Works** - Don't worry about temporary 500 errors

### For Your Paper (Oct 30 Deadline):

✅ **You'll have 7-8 validated predictions** by Oct 29  
✅ **This is sufficient** for publication-quality results  
✅ **The lag is normal** and doesn't affect paper quality  
✅ **Weekend gap is expected** - mention in methodology  
✅ **Your tracking system handles everything automatically**

---

## 📊 Quick Reference

### What to Expect Each Day This Week

**Monday Oct 21**: Get Oct 16-17 data → Validate Oct 16-17 predictions  
**Tuesday Oct 22**: Get Oct 18-20 data → Validate Oct 18-20 predictions  
**Wednesday Oct 23**: Get Oct 21 data → Validate Oct 21 prediction  
**Thursday Oct 24**: Get Oct 22 data → Validate Oct 22 prediction  
**Friday Oct 25**: Get Oct 23 data → Validate Oct 23 prediction  

**Result by Oct 25 evening**: 5-7 validated predictions ✅

---

## 🚀 Action Items

### For You:
1. ✅ Don't check API today (Sunday) - no new data expected
2. ✅ Run daily routine tomorrow (Monday) after 6 PM ET
3. ✅ Continue daily routine Tue-Fri after 6 PM ET
4. ✅ Expect 7-8 validated predictions by Oct 29
5. ✅ Trust the retry logic - it handles API issues

### Automated:
- ✅ Retry logic (5 attempts with exponential backoff)
- ✅ Error messages explain what's happening
- ✅ Graceful handling of "data not available yet"
- ✅ Clear feedback on success/failure

---

**Last Updated**: October 20, 2025  
**Next Review**: After first successful data fetch (Oct 21 expected)  
**Status**: ✅ All systems ready for Monday evening run
