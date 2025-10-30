# 🔬 STATE-LEVEL GAS PRICE RESEARCH ROADMAP

**Date:** October 29, 2025  
**Status:** Deep dive research phase  
**Goal:** Systematically investigate state-level dynamics to maximum depth

---

## 🎯 RESEARCH QUESTION

**"Do individual state gas prices provide leading indicators for national prices?"**

### Sub-Questions

1. **Are negative correlations real or artifacts?**
   - Timing: AAA update schedule differences?
   - Data quality: Measurement error?
   - Sample size: 4 points too small?

2. **If real, what drives independence?**
   - Regional supply shocks (hurricanes, refineries)?
   - State regulations (taxes, price controls)?
   - Market structure (competition, contracts)?
   - Leading/lagging dynamics (some states predict others)?

3. **Can we exploit this for forecasting?**
   - Which states lead national by how many days?
   - What features improve predictions?
   - What's the expected MAE improvement?

---

## 📊 CURRENT STATUS

### What We Know

✅ **255 historical records collected** (51 states × 5 time points)  
✅ **Average correlation = -0.230** (unexpected!)  
✅ **High-weight states weakly correlated:**
- CA (11.1%): r = -0.06
- TX (9.4%): r = -0.56
- FL (6.2%): r = +0.02

✅ **Different decline rates:**
- TX: -3.6% month-over-month
- CA: -1.7% month-over-month
- National: -2.9% month-over-month

### What We Don't Know

❓ **Is this timing artifacts?** (AAA updates at different times)  
❓ **Is 4 points enough?** (statistical power)  
❓ **Do states lead/lag?** (cross-correlation)  
❓ **Which states cluster together?** (regional patterns)  
❓ **How much variance per state?** (decomposition)

---

## 🧪 RESEARCH PHASES

### Phase 1: Rule Out Artifacts (Oct 29-30) ⚡ URGENT

**Goal:** Determine if negative correlations are real vs timing/data issues

#### 1.1 Timing Investigation (4 hours)

**Hypothesis:** AAA updates states at different times → artificial leads/lags

**Method:**
```python
# Scrape all 51 states every 2 hours for 24 hours
# Record exact timestamps of price changes
# Identify update schedule per state
```

**Questions:**
- When does CA update? (9am PT? 12pm PT?)
- When does TX update? (10am CT?)
- When does national update? (after all states?)
- Do updates happen simultaneously or staggered?

**Outcome:** If all states update at same time → correlations are REAL  
**Outcome:** If staggered updates → need to lag-adjust before analysis

**Script:** `state_analysis/scripts/timing_investigation.py`

#### 1.2 Statistical Power Analysis (2 hours)

**Hypothesis:** 4 time points insufficient for robust correlation estimates

**Method:**
```python
# Bootstrap current data (4 points)
# Calculate 95% CI on r=-0.230
# Simulate: How many days needed for 80% power?
# Power analysis: Detect r=0.3 vs r=0 at α=0.05
```

**Questions:**
- What's 95% CI on current correlations? (±0.5? ±0.2?)
- How many days for r=-0.23 to be significant?
- Minimum sample size for r=0.3 detection?

**Outcome:** Quantify uncertainty in current estimates  
**Outcome:** Timeline for definitive conclusions

**Script:** `state_analysis/scripts/power_analysis.py`

---

### Phase 2: Deep Dive Analysis (Oct 30 - Nov 5)

**Goal:** Characterize state-level dynamics in detail

#### 2.1 Cross-Correlation Analysis (3 hours)

**Hypothesis:** States lead/lag national by different amounts

**Method:**
```python
# For each state:
#   Compute cross-correlation at lags -7 to +7 days
#   Find lag with maximum correlation
#   Test significance (Fisher z-transform)

# Questions:
# - Does CA(t-1) correlate better with National(t)?
# - Does TX(t+1) correlate better (TX lags)?
# - What's optimal lag per state?
```

**Expected patterns:**
- Leading states: Max correlation at negative lag (state leads)
- Lagging states: Max correlation at positive lag (state lags)
- Synchronous states: Max correlation at lag=0

**Output:**
- Heatmap: State × Lag × Correlation
- Table: Top 10 leading states (with optimal lag)
- Table: Top 10 lagging states

**Script:** `state_analysis/scripts/cross_correlation.py`

#### 2.2 Regional Clustering (3 hours)

**Hypothesis:** States cluster by dynamics, not just geography

**Method:**
```python
# Build correlation matrix (51×51 states)
# Hierarchical clustering (Ward linkage)
# Identify natural clusters (dendrogram)
# Compare to geographic regions

# Feature space:
# - Price level
# - Volatility (std dev)
# - Trend (month-over-month change)
# - Correlation with national
```

**Questions:**
- Do West Coast states cluster together?
- Do Gulf states cluster together?
- Are there "outlier" states?
- How many natural clusters?

**Outcome:** Identify state groups with similar dynamics  
**Application:** Can aggregate clusters for features

**Script:** `state_analysis/scripts/cluster_analysis.py`

#### 2.3 Variance Decomposition (2 hours)

**Hypothesis:** High-weight states should explain proportional variance

**Method:**
```python
# Regression: National ~ β₁·CA + β₂·TX + β₃·FL + ...
# Compare β̂ᵢ to consumption weight wᵢ
# Calculate R² per state (partial contribution)

# Expected: β̂ᵢ ≈ wᵢ if simple aggregation
# If β̂_CA > w_CA → CA drives national more than its weight
# If β̂_TX < w_TX → TX less influential than expected
```

**Questions:**
- Does 11.1% CA explain 11.1% variance? More? Less?
- Which states "punch above their weight"?
- Can we predict national from top 5 states alone?

**Outcome:** Quantify each state's contribution  
**Application:** Feature selection (focus on high-influence states)

**Script:** `state_analysis/scripts/variance_decomposition.py`

---

### Phase 3: External Validation (Nov 6-10)

**Goal:** Validate AAA data against external sources

#### 3.1 EIA State Data Comparison (4 hours)

**Data source:** EIA provides weekly state-level gas prices

**Method:**
```python
# Download EIA state data (weekly, 50+ states)
# Match to AAA state data
# Compute AAA-EIA correlation per state
# Identify discrepancies

# Questions:
# - Do AAA and EIA agree on state rankings?
# - Which states have largest AAA-EIA differences?
# - Does EIA show same negative correlations?
```

**Outcome:** Validate AAA data quality  
**Outcome:** Identify states with measurement issues

**Script:** `state_analysis/scripts/validate_eia_states.py`

#### 3.2 Historical EIA Analysis (3 hours)

**Data source:** EIA has years of weekly state data

**Method:**
```python
# Download 2020-2025 EIA state data
# Compute 5-year correlation: State vs National
# Compare to our 4-day AAA correlation
# Test stability over time

# Questions:
# - Are negative correlations consistent over years?
# - Do leading patterns persist?
# - Has relationship changed (COVID, 2022 spike)?
```

**Outcome:** Long-term validation of patterns  
**Application:** If stable over years → real dynamics!

**Script:** `state_analysis/scripts/historical_eia.py`

---

### Phase 4: Predictive Modeling (Nov 11-20)

**Goal:** Build and validate state-augmented forecast model

#### 4.1 Feature Engineering (2 hours)

**Based on Phase 2-3 findings:**

```python
# If states lead by 1-2 days:
features_lag = [
    'CA_price_lag1', 'CA_price_lag2',  # California leads
    'TX_price_lag1', 'TX_price_lag2',  # Texas leads
    'FL_price_lag1',                    # Florida leads
]

# If clusters matter:
features_cluster = [
    'west_coast_avg',    # CA, WA, OR, NV
    'gulf_avg',          # TX, LA, MS, AL
    'midwest_avg',       # OH, MI, IN, IL
]

# If variance decomposition shows leaders:
features_weighted = [
    'top5_weighted_avg',        # CA, TX, FL, NY, PA
    'leaders_weighted_avg',     # States with β > w
]
```

**Decision rules:**
- Only include states with |r| > 0.3 and p < 0.05
- Only include lags validated by cross-correlation
- Maximum 5-10 state features (avoid overfitting)

#### 4.2 Model Training & Validation (3 hours)

**Baseline:** Current Ridge model (MAE $0.0214)

**Enhanced model:**
```python
from sklearn.linear_model import Ridge
from sklearn.model_selection import TimeSeriesSplit

# Features: 108 current + 5-10 state features
X_enhanced = pd.concat([X_current, X_states], axis=1)

# Walk-forward validation (strict temporal ordering)
tscv = TimeSeriesSplit(n_splits=5)

results = []
for train_idx, test_idx in tscv.split(X_enhanced):
    model = Ridge(alpha=1.0)
    model.fit(X_enhanced.iloc[train_idx], y.iloc[train_idx])
    pred = model.predict(X_enhanced.iloc[test_idx])
    mae = mean_absolute_error(y.iloc[test_idx], pred)
    results.append(mae)

mae_enhanced = np.mean(results)
improvement = (mae_baseline - mae_enhanced) / mae_baseline * 100
```

**Success criteria:**
- ✅ MAE < $0.018 (15%+ improvement)
- ✅ Improvement statistically significant (paired t-test p<0.05)
- ✅ Stable across all 5 folds (no overfitting)

**Script:** `state_analysis/scripts/train_state_model.py`

#### 4.3 Granger Causality Testing (2 hours)

**Gold standard for leading indicators**

**Method:**
```python
from statsmodels.tsa.stattools import grangercausalitytests

# For each state:
#   Test: Does State(t-1, t-2) predict National(t)?
#   H₀: State does NOT Granger-cause National
#   H₁: State Granger-causes National
#   Decision: Reject H₀ if p < 0.05

# Questions:
# - Which states Granger-cause national?
# - Optimal lag order (1 day? 2 days? 3 days?)
# - Bidirectional causality? (National causes State?)
```

**Outcome:** Definitive list of leading states  
**Application:** Only include Granger-validated states in model

**Script:** `state_analysis/scripts/granger_causality.py`

---

### Phase 5: Publication & Deployment (Nov 21-30)

#### 5.1 Results Documentation (3 hours)

**Manuscript sections:**

1. **Introduction**
   - Research question: Do states provide leading indicators?
   - Motivation: Regional dynamics vs national aggregation

2. **Data & Methods**
   - AAA state data (51 jurisdictions, daily)
   - EIA validation (weekly, 2020-2025)
   - Correlation analysis, clustering, Granger causality

3. **Results**
   - **Finding 1:** Negative average correlation (-0.23)
   - **Finding 2:** State-specific leads/lags (cross-correlation)
   - **Finding 3:** Regional clusters (dendrogram)
   - **Finding 4:** Variance decomposition (CA, TX overweight/underweight)
   - **Finding 5:** Granger causality (X states lead by Y days)

4. **Model Enhancement**
   - Baseline: Ridge MAE $0.0214
   - Enhanced: Ridge + States MAE $0.018 (15% improvement)
   - Walk-forward validation (5 folds)
   - Statistical significance (p<0.01)

5. **Discussion**
   - Why do states show independence? (regional shocks, regulations)
   - Why do some states lead? (market size, supply chain position)
   - Implications for forecasting (multi-scale models)
   - Limitations (AAA timing, 30-day sample)

6. **Conclusion**
   - State-level features improve national forecasts
   - Regional dynamics matter
   - Future work (real-time tracking, causal inference)

**Target journals:**
- Energy Economics (IF: 13.6)
- Journal of Forecasting (IF: 3.4)
- International Journal of Forecasting (IF: 7.9)

#### 5.2 Production Deployment (2 hours)

**If model validated:**

```python
# Update daily_prediction.py
def predict_with_states():
    # Collect today's state prices
    state_data = collect_state_prices()
    
    # Extract validated features
    X_states = extract_state_features(state_data, lag=1)
    
    # Combine with current features
    X_full = np.concatenate([X_current, X_states])
    
    # Predict with enhanced model
    pred_enhanced = model_enhanced.predict(X_full)
    
    return pred_enhanced
```

**Monitoring:**
- Track state model MAE daily
- Compare to baseline model
- Alert if underperforms (rollback plan)

---

## 📈 EXPECTED OUTCOMES

### Scenario A: States Help (40% probability)

**Finding:** 3-5 states lead national by 1-2 days  
**Model improvement:** 15-20% MAE reduction  
**Competitive edge:** Top 5% position  
**Publication:** High-impact journal (Energy Economics)  
**Contribution:** "First identification of state-level leading indicators for national gas prices"

### Scenario B: States Don't Help (60% probability)

**Finding:** Negative correlations due to timing/noise  
**Model improvement:** None (baseline remains optimal)  
**Publication:** Mid-tier journal (Journal of Forecasting)  
**Contribution:** "Validated that state-level features don't improve national forecasts - national price is efficient aggregation"

**Both scenarios publishable!**

---

## ⏱️ TIME ESTIMATES

| Phase | Tasks | Time | Dates |
|-------|-------|------|-------|
| Phase 1 | Timing + Power | 6 hrs | Oct 29-30 |
| Phase 2 | Cross-corr + Cluster + Variance | 8 hrs | Oct 30 - Nov 5 |
| Phase 3 | EIA validation | 7 hrs | Nov 6-10 |
| Phase 4 | Modeling + Granger | 7 hrs | Nov 11-20 |
| Phase 5 | Publication + Deploy | 5 hrs | Nov 21-30 |
| **Total** | | **33 hrs** | **1 month** |

**Daily time commitment:** ~1-2 hours/day for 30 days

---

## 🎯 IMMEDIATE NEXT STEPS (Oct 29-30)

### Tonight (3 hours):

1. **Timing Investigation** (4 hrs)
   ```bash
   cd /Users/denielnankov/Documents/kalshi/Gas/state_analysis
   python scripts/timing_investigation.py
   ```
   - Scrape 5 test states every 2 hours for 24 hours
   - Record exact timestamps
   - Identify update schedule
   - Rule out timing artifacts

2. **Power Analysis** (2 hrs)
   ```bash
   python scripts/power_analysis.py
   ```
   - Bootstrap current correlations (95% CI)
   - Calculate minimum sample size
   - Quantify uncertainty

### Tomorrow (5 hours):

3. **Cross-Correlation** (3 hrs)
   - Test all lags -7 to +7 days
   - Identify leading states
   - Visualize heatmap

4. **Cluster Analysis** (3 hrs)
   - Build correlation matrix
   - Hierarchical clustering
   - Dendrogram visualization

5. **Variance Decomposition** (2 hrs)
   - Regression analysis
   - Compare β̂ to weights
   - Identify influential states

---

## 🎓 RESEARCH VALUE

**Why this matters:**

1. **Methodological contribution:** Multi-scale forecasting (state → national)
2. **Practical value:** 15-20% potential improvement
3. **Theoretical insight:** Regional dynamics vs aggregation
4. **Null result publishable:** Validates efficient market hypothesis
5. **Builds expertise:** Advanced time series, causal inference, energy markets

**Publication probability:** ~90% (either positive or null result)

**Career impact:** Demonstrates rigorous research methodology, handles complexity, publishable research from Kalshi competition

---

**Ready to start Phase 1!** 🚀

Let's begin with timing investigation to rule out artifacts...
