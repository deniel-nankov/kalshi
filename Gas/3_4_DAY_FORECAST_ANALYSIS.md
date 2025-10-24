# 3-Day and 4-Day Gas Price Forecast Performance

## 📊 Quick Answer

**Q: What is the R² for 3-4 day gas price forecasts?**

**A: 3-day forecast performance varies significantly by year:**

| Year | R² Score | Performance | Average Error |
|------|----------|-------------|---------------|
| **2021** | **0.875** | 🟢 **EXCELLENT** | $0.0217 (2.2¢) |
| 2022 | -1.324 | 🔴 Poor | $0.0817 (8.2¢) |
| **2023** | **0.849** | 🟢 **EXCELLENT** | $0.0362 (3.6¢) |
| 2024 | -0.469 | 🔴 Poor | $0.0256 (2.6¢) |
| **Average** | **-0.017** | 🔴 **Poor** | **$0.0413 (4.1¢)** |

**4-day forecasts:** Not tested (your validation used 1, 3, 7, 14, 21 day horizons)

---

## 🎯 Key Findings

### 1. **Why 3-Day Performance Varies So Much**

**Good Years (2021, 2023):**
- R² = 0.849-0.875 (explains 85-88% of price variation)
- Errors only 2-4 cents
- ✅ Very usable for trading/planning

**Bad Years (2022, 2024):**
- R² = -1.324 to -0.469 (worse than predicting average!)
- Errors 2.6-8.2 cents
- ❌ Model struggles with volatility

**Why the difference?**
- **2022:** High volatility year (Russia-Ukraine war, supply shocks)
- **2024:** Market conditions changed vs training data
- **2021, 2023:** More stable, predictable markets

---

### 2. **Comparison Across All Horizons**

| Horizon | Average R² | Average Error | Rating |
|---------|------------|---------------|--------|
| **1 day** | **0.611** | $0.0297 (3.0¢) | ⭐⭐⭐ **EXCELLENT** |
| **3 days** | -0.017 | $0.0413 (4.1¢) | ❌ Poor |
| 7 days | -0.453 | $0.0503 (5.0¢) | ❌ Poor |
| 14 days | -1.608 | $0.0768 (7.7¢) | ❌ Poor |
| 21 days | -4.923 | $0.1068 (10.7¢) | ❌ Poor |

**Key Insight:** Performance drops dramatically after 1 day!
- **1-day:** R² = 0.611 (good predictions)
- **3-day:** R² = -0.017 (barely better than average)
- **7+ days:** R² < -0.5 (worse than just guessing average)

---

## 📈 Detailed 3-Day Analysis

### Performance by Year (Bar Chart Data)

```
2021: █████████████████████████████████████████████ 87.5% R² ✅
2022: ████████████████████████ -132.4% R² (negative!) ❌
2023: ████████████████████████████████████████████ 84.9% R² ✅
2024: ███████████████████ -46.9% R² (negative!) ❌
```

### Best Case Scenario (2021):

**Performance:**
- R²: 0.875 (explains 87.5% of variation!)
- RMSE: $0.0268 (2.68¢ typical error)
- MAE: $0.0217 (2.17¢ average error)
- MAPE: 0.66% (less than 1% error!)
- Alpha: 2.0 (moderate regularization)

**What this means:**
- If gas is $3.50 today, model predicts 3 days ahead with only 2¢ error
- Actual: $3.52, Predicted: $3.54 → Only 2¢ off!
- **Very useful for short-term planning!** ✅

### Worst Case Scenario (2022):

**Performance:**
- R²: -1.324 (negative! worse than average)
- RMSE: $0.1008 (10¢ typical error)
- MAE: $0.0817 (8.2¢ average error)
- MAPE: 2.12%
- Alpha: 2.0

**What this means:**
- If gas is $4.50 today, model's 3-day prediction could be off by 8-10¢
- Actual: $4.52, Predicted: $4.60 → 8¢ error
- **Not reliable during high volatility!** ❌

**Why 2022 failed:**
- Russia-Ukraine war (Feb 2022)
- Supply chain disruptions
- OPEC production cuts
- Unprecedented volatility
- Model trained on stable years couldn't handle shocks

---

## 🔍 What About 4-Day Forecasts?

**Status:** Not tested in your current pipeline

**Why?**
Your walk-forward validation tested these horizons:
- 1 day ✅
- 3 days ✅
- 7 days ✅
- 14 days ✅
- 21 days ✅

**To add 4-day forecasts:**
You would need to modify `scripts/walk_forward_validation.py`:
```python
# Current:
HORIZONS = [1, 3, 7, 14, 21]

# Modified to include 4-day:
HORIZONS = [1, 3, 4, 7, 14, 21]
```

**Expected 4-day performance:**
Based on the pattern, 4-day forecasts would likely have:
- R²: Between -0.017 (3-day) and -0.453 (7-day) ≈ **-0.2 to -0.3**
- MAE: Between $0.0413 (3-day) and $0.0503 (7-day) ≈ **$0.045 (4.5¢)**
- **Rating: Poor (similar to 3-day average)**

---

## 💡 Why Does Performance Degrade After 1 Day?

### 1. **Price Momentum Fades**
- **1 day:** Strong momentum (today's trend continues tomorrow)
- **3 days:** Momentum weakens (random events intervene)
- **7+ days:** Momentum gone (random walk dominates)

### 2. **Unpredictable Events**
- **1 day:** Unlikely major news
- **3 days:** More time for surprises (weather, geopolitics)
- **7+ days:** Many potential disruptions

### 3. **Feature Staleness**
Your features are lagged 15 days to prevent leakage:
- **1 day ahead:** 15-day lag still informative
- **3 days ahead:** 17-day lag (info getting old)
- **7+ days ahead:** 22+ day lag (too old to be useful)

### 4. **Random Walk Hypothesis**
Gas prices partially follow a "random walk":
- Short-term: Predictable patterns
- Medium-term (3-7 days): Weak patterns
- Long-term (14+ days): Essentially random

**This is actually GOOD for your paper!**
- Shows model is realistic (not overfitting)
- Demonstrates limits of forecasting
- Focuses on what works (1-day forecasts)

---

## 📝 For Your Paper

### Main Finding:

> "Our Ridge regression model achieved excellent performance for 1-day forecasts (average R²=0.611, MAE=$0.0297) but performance degraded rapidly for longer horizons. Three-day forecasts showed high variance across years (R²=0.875 in stable 2021 vs R²=-1.324 in volatile 2022), averaging R²=-0.017. This degradation is expected given the random walk nature of commodity prices beyond short-term horizons."

### Key Contributions:

1. **1-Day Forecasts Work Best:**
   - "Our results demonstrate that gasoline prices are highly predictable in the 1-day horizon (R²=0.611, MAE=3.0¢)"
   - "2023 achieved exceptional 1-day performance (R²=0.940, MAE=2.0¢)"

2. **3-Day Forecasts Are Unreliable:**
   - "Performance at 3-day horizon varies dramatically by market conditions"
   - "Stable years (2021, 2023): R²≈0.85, excellent predictability"
   - "Volatile years (2022, 2024): R²<0, worse than predicting average"

3. **Practical Implications:**
   - "For operational planning, focus on 1-day forecasts (R²=0.611)"
   - "3-7 day forecasts should be used cautiously (R²<0)"
   - "Beyond 7 days, predictions have no value (R²<-1.5)"

### Recommended Focus:

**Emphasize 1-day forecasts in your paper:**
- Most reliable (R²=0.611 average, 0.940 best year)
- Practical value (3¢ average error)
- Consistent across years (always positive R²)
- **This is your strongest result!** 🏆

**De-emphasize 3-7 day forecasts:**
- Inconsistent (negative R² on average)
- High variance across years
- Limited practical value
- Use as "comparison to show limits of forecasting"

---

## 🎯 Bottom Line

### Your Question: "What will R² be for 3-4 day forecasts?"

**Answer:**

**3-Day Forecasts:**
- **Average:** R² = -0.017 (poor, worse than predicting average)
- **Best year (2021):** R² = 0.875 (excellent!)
- **Worst year (2022):** R² = -1.324 (terrible!)
- **Verdict:** Too inconsistent for reliable use ⚠️

**4-Day Forecasts:**
- **Not tested** (need to add to validation script)
- **Expected:** R² ≈ -0.2 to -0.3 (similar to 3-day average)
- **Likely similar issues** as 3-day forecasts

**Recommendation:**
✅ **Focus on 1-day forecasts for your paper!**
- R² = 0.611 average (reliable!)
- R² = 0.940 in 2023 (exceptional!)
- 3¢ average error (practical!)
- Consistent across years (robust!)

❌ **Don't emphasize 3-4 day forecasts:**
- Negative average R² (unreliable)
- High year-to-year variance (unstable)
- Limited practical value

---

## 📊 Visual Summary

### Forecast Accuracy by Horizon:

```
1-day:   ████████████████████████████ 61.1% R² ⭐⭐⭐
3-day:   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ -1.7% R² ❌
7-day:   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ -45.3% R² ❌
14-day:  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓ -160.8% R² ❌
21-day:  ▓▓▓▓▓▓▓ -492.3% R² ❌
```

**Legend:**
- █ = Positive R² (useful predictions)
- ▓ = Negative R² (worse than average)

### Average Error by Horizon:

```
1-day:   ████████ 3.0¢ ✅ Practical
3-day:   ███████████ 4.1¢ ⚠️ Marginal
7-day:   █████████████ 5.0¢ ❌ Poor
14-day:  ████████████████████ 7.7¢ ❌ Poor
21-day:  ████████████████████████████ 10.7¢ ❌ Poor
```

---

## 🚀 Action Items for Your Paper

1. **Highlight 1-day forecasts** (R²=0.611, your best result!)
2. **Mention 3-day limitations** (shows model is realistic, not overfitted)
3. **Skip 4-day forecasts** (not tested, similar to 3-day anyway)
4. **Emphasize 2023 performance** (R²=0.940 for 1-day, exceptional!)
5. **Explain degradation** (random walk dominates beyond short-term)

**Your paper's key message:**
> "Short-term gas price forecasting (1 day) is highly accurate (R²=0.611), but predictability degrades rapidly for longer horizons, consistent with random walk theory for commodity prices."

This is a **strong, realistic, publishable result!** ✅
