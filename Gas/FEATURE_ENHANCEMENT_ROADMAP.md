# Feature Enhancement Roadmap - Gas Price Prediction Model

**Current State:** 80 features, 50 in COMMON_FEATURES  
**Goal:** Comprehensive, rigorous ML model with domain-specific feature engineering

---

## 🎯 TIER 1: HIGH IMPACT, QUICK WINS (Implement First)

### 1. **Supply Shock Indicators** 🔥 **CRITICAL**

**Problem:** Model doesn't capture sudden supply disruptions beyond hurricanes

**Features to Add:**
```python
# Refinery Outages (EIA data available)
- refinery_outage_capacity_bpd         # Total unplanned outages
- refinery_outage_pct_of_capacity      # % of PADD 3 capacity offline
- scheduled_maintenance_capacity_bpd   # Planned turnarounds
- days_since_major_outage              # Time since last >100K bpd outage
- cumulative_outage_30d                # Rolling 30-day outage sum

# Colonial Pipeline Disruptions
- colonial_pipeline_status             # 0=normal, 1=disrupted
- days_since_colonial_shutdown         # Critical for East Coast supply
- colonial_pipeline_flow_rate_kbd      # Actual throughput (if available)

# Port Operations (Houston, Corpus Christi)
- port_closure_indicator               # Weather/hurricane closures
- port_congestion_score                # Import/export delays
```

**Why Critical:**
- Refinery outages directly reduce supply → gas price spikes
- Colonial Pipeline shutdown (2021 cyberattack) → +20% gas prices in days
- Hurricane Laura (2020): Refinery damage → multi-week recovery

**Data Sources:**
- EIA Weekly Petroleum Status Report (Table 1)
- Colonial Pipeline public announcements
- Port of Houston/Corpus Christi status

**Expected Impact:** 🔥🔥🔥 Major improvement for supply-constrained periods

---

### 2. **Geopolitical Risk Quantification** 🌍 **HIGH VALUE**

**Problem:** Binary `geopolitical_shock` doesn't capture magnitude or type

**Features to Add:**
```python
# Crude Oil Disruption Risk
- middle_east_tension_score            # 0-10 scale based on events
- opec_production_cut_mb_d             # OPEC+ announced cuts
- iran_venezuela_sanctions_indicator   # Binary for active sanctions
- russia_ukraine_oil_disruption        # 0-10 severity scale
- libya_nigeria_outage_risk            # Unstable producer disruption

# Strategic Petroleum Reserve (SPR)
- spr_release_mb_d                     # Daily release rate
- spr_inventory_mb                     # Total SPR stocks
- spr_days_of_supply                   # SPR / daily consumption
- days_since_spr_announcement          # Market anticipation

# Trade Policy
- oil_export_ban_indicator             # Binary: export restrictions
- import_tariff_effective_rate         # Trade war impacts
```

**Why High Value:**
- Russia-Ukraine (2022) → +40% crude prices
- SPR releases (2022) → -15% crude prices over 6 months
- OPEC cuts (2023) → sustained price support

**Data Sources:**
- EIA International Energy Statistics
- OPEC announcements (public)
- SPR inventory (EIA weekly)
- News sentiment scoring (optional: scrape Bloomberg headlines)

**Expected Impact:** 🔥🔥 Captures macro crude price drivers that flow to gas

---

### 3. **Demand Seasonality & Driving Patterns** 🚗 **OCTOBER-SPECIFIC**

**Problem:** Basic calendar features don't capture demand nuances

**Features to Add:**
```python
# Seasonal Demand Patterns
- is_summer_driving_season             # Memorial Day → Labor Day
- days_into_summer_driving_season      # Peak demand progression
- is_holiday_week                      # July 4, Labor Day, Thanksgiving
- school_in_session_indicator          # Commute patterns
- is_end_of_month                      # Paycheck-driven fill-ups

# October-Specific
- is_early_october                     # Oct 1-10 (higher demand)
- is_mid_october                       # Oct 11-20 (transition)
- is_late_october                      # Oct 21-31 (lower demand)
- days_until_winter_blend_switch       # Nov 1 transition anticipation
- fall_foliage_travel_indicator        # Northeast tourism boost

# Weather-Driven Demand
- avg_temp_celsius_week                # Already have, enhance
- heating_degree_days                  # Cold → reduced driving
- cooling_degree_days                  # Heat → more driving (AC usage)
- precipitation_days_week              # Rain/snow reduces driving
- extreme_weather_days                 # Storms reduce demand
```

**Why October-Specific:**
- October has declining demand (summer driving → winter)
- Winter blend transition (Nov 1) → cheaper gas production
- School year fully started → commute patterns stabilized
- Halloween travel patterns

**Data Sources:**
- NOAA climate data (already partially integrated)
- School calendar data (major metro areas)
- Federal Reserve economic calendar (holidays)

**Expected Impact:** 🔥🔥 Improves October-specific predictions significantly

---

### 4. **Market Microstructure & Liquidity** 💹 **TECHNICAL**

**Problem:** No features capturing market depth, volatility regime, or trading patterns

**Features to Add:**
```python
# RBOB Futures Liquidity
- rbob_volume_ma21                     # 21-day avg trading volume
- rbob_volume_zscore                   # Unusual volume detection
- rbob_bid_ask_spread                  # Liquidity indicator (if available)
- rbob_open_interest                   # Futures market positioning

# Volatility Regime
- realized_volatility_21d              # Already have, enhance
- volatility_zscore                    # Is current vol unusual?
- volatility_percentile_1y             # Where are we in vol distribution?
- vol_of_vol                           # Volatility of volatility (regime shift)
- garman_klass_volatility              # High-low-close vol estimator

# Price Action Patterns
- rbob_higher_highs_5d                 # Uptrend detector
- rbob_lower_lows_5d                   # Downtrend detector
- rbob_breakout_indicator              # Price > 21-day high
- rbob_breakdown_indicator             # Price < 21-day low
- rbob_range_compression               # Bollinger Band squeeze

# Term Structure
- rbob_front_month_vs_next             # Contango/backwardation
- rbob_calendar_spread_m1_m3           # 1st vs 3rd month
- crude_rbob_time_spread_correlation   # Term structure alignment
```

**Why Technical:**
- October volatility often differs from summer (seasonality)
- Low liquidity → larger price swings
- Contango/backwardation signals supply tightness

**Data Sources:**
- CME RBOB futures data (already have price, add volume/OI)
- Calculated from existing price data

**Expected Impact:** 🔥 Captures trading dynamics and regime shifts

---

## 🎯 TIER 2: MODERATE IMPACT, MODERATE EFFORT

### 5. **Regional Supply Chain Features** 🚛

**Features to Add:**
```python
# PADD 3 → PADD 1 Pipeline Flows
- colonial_pipeline_utilization        # % of capacity
- plantation_pipeline_utilization      # Southeast supply
- buckeye_pipeline_utilization         # Northeast supply

# Refinery-Specific
- top_5_refinery_utilization_avg       # Largest refiners only
- padd3_operable_capacity_change       # New capacity coming online
- refinery_complexity_weighted_util    # Complex refineries run harder

# Distribution
- pipeline_congestion_score            # Bottlenecks
- barge_freight_rate_index             # Water transport costs
- truck_delivery_premium               # Last-mile costs
```

**Data Sources:**
- Pipeline operators (some public, some via EIA)
- Freight indices (publicly available)

**Expected Impact:** 🔥 Captures supply chain bottlenecks

---

### 6. **Macroeconomic Indicators** 📊

**Features to Add:**
```python
# Economic Activity
- gdp_growth_rate_qoq                  # Quarterly GDP (demand proxy)
- unemployment_rate                    # Income → driving
- consumer_sentiment_index             # U. Michigan / Conference Board
- retail_sales_growth_mom              # Consumer spending
- vehicle_miles_traveled_index         # Direct demand measure

# Inflation
- cpi_energy_component                 # Energy inflation
- cpi_transportation_component         # Transport costs
- dollar_index                         # USD strength (crude prices)
- real_gas_price_vs_income             # Affordability

# Interest Rates
- fed_funds_rate                       # Borrowing costs
- 10y_treasury_yield                   # Risk-free rate
- oil_futures_cost_of_carry            # Storage economics
```

**Data Sources:**
- FRED (Federal Reserve Economic Data) - free API
- BLS (Bureau of Labor Statistics)
- EIA vehicle miles traveled

**Expected Impact:** 🔥 Captures broader economic demand drivers

---

### 7. **Competitive Fuel Pricing** ⚡

**Features to Add:**
```python
# Alternative Fuels
- natural_gas_price_henry_hub          # CNG vehicle competition
- electricity_price_residential        # EV adoption impact
- ethanol_price_chicago                # Blend component
- diesel_price_retail                  # Commercial vehicle costs

# Fuel Switching Economics
- gas_diesel_price_ratio               # Fleet switching incentive
- gas_natural_gas_btu_equivalent_ratio # CNG fleet economics
- gas_electricity_cost_per_mile_ratio  # EV competitiveness
```

**Data Sources:**
- EIA natural gas, electricity data
- USDA/Chicago ethanol prices
- Calculated ratios

**Expected Impact:** 🔥 Long-term demand substitution effects

---

## 🎯 TIER 3: ADVANCED / RESEARCH-ORIENTED

### 8. **Machine Learning-Derived Features** 🤖

**Features to Add:**
```python
# Autoencoder-Based
- latent_factor_1_through_5            # PCA/autoencoder on all features
- anomaly_score                        # Isolation Forest outlier detection
- cluster_assignment                   # K-means market regime

# Time Series Decomposition
- trend_component                      # STL decomposition
- seasonal_component                   # Seasonal patterns
- residual_component                   # Unexplained variance

# Lag Selection
- optimal_lag_rbob                     # Determined by mutual information
- optimal_lag_wti                      # Not just fixed 7, 14, 21
- granger_causality_lag_inventory      # How long do inventory shocks last?
```

**Why Advanced:**
- Requires additional modeling infrastructure
- May overfit on small October samples

**Expected Impact:** 🔥 Potential breakthrough if done carefully

---

### 9. **Sentiment & Alternative Data** 📰

**Features to Add:**
```python
# News Sentiment
- oil_news_sentiment_score             # Bloomberg/Reuters scraping
- hurricane_forecast_intensity         # NOAA forecast cone uncertainty
- opec_meeting_countdown               # Days until decision
- fed_meeting_countdown                # Monetary policy anticipation

# Google Trends
- gas_prices_search_volume             # Consumer awareness
- road_trip_search_volume              # Travel intent
- electric_car_search_volume           # EV interest

# Social Media (Twitter/X)
- twitter_gas_price_complaint_volume   # Consumer sentiment
- oil_analyst_twitter_consensus        # Expert opinion aggregation
```

**Why Research:**
- Requires API access, scraping infrastructure
- Signal-to-noise ratio uncertain
- Regulatory concerns (Twitter API changes)

**Expected Impact:** 🔥 Experimental, high variance

---

### 10. **Non-Linear Interaction Terms** 🔬

**Features to Add:**
```python
# Price Interactions
- crack_spread_x_inventory             # Profitability + availability
- utilization_x_hurricane_threat       # Constrained + risk
- rbob_volatility_x_geopolitical       # Uncertainty amplification

# Threshold Effects
- inventory_below_5yr_min              # Critical shortage
- utilization_above_95pct              # Capacity constraint
- crack_spread_above_90th_percentile   # Extreme profitability

# Regime Indicators
- high_vol_high_crack_regime           # 1 if both conditions
- low_inventory_high_utilization       # Supply stress
- hurricane_season_high_threat         # Compound risk
```

**Why Non-Linear:**
- Ridge regression assumes linearity
- Gradient boosting can capture interactions automatically
- Hand-crafted interactions for interpretability

**Expected Impact:** 🔥🔥 Major boost for tree-based models

---

## 📊 IMPLEMENTATION PRIORITY MATRIX

| Feature Category | Impact | Effort | Priority | Est. Features Added |
|------------------|--------|--------|----------|---------------------|
| **Supply Shock Indicators** | 🔥🔥🔥 | Low | **1** | +8 features |
| **Geopolitical Risk** | 🔥🔥 | Medium | **2** | +10 features |
| **Demand Seasonality** | 🔥🔥 | Low | **3** | +12 features |
| **Market Microstructure** | 🔥 | Low | **4** | +10 features |
| **Regional Supply Chain** | 🔥 | Medium | 5 | +8 features |
| **Macroeconomic** | 🔥 | Medium | 6 | +10 features |
| **Competitive Fuels** | 🔥 | Low | 7 | +6 features |
| **ML-Derived** | 🔥 | High | 8 | +10 features |
| **Sentiment/Alt Data** | 🔥 | High | 9 | +8 features |
| **Interaction Terms** | 🔥🔥 | Low | **10** | +15 features |

**Total Potential:** +97 new features → ~150 total features

---

## 🚀 RECOMMENDED NEXT STEPS

### Week 1: Supply Shock Features
1. Download EIA refinery outage data (Table 1, 4, 5)
2. Create `scripts/generate_refinery_outage_features.py`
3. Add Colonial Pipeline status (manual research 2020-2025)
4. Integrate into Gold layer

### Week 2: Geopolitical & Demand
1. Pull SPR data from EIA API
2. Create OPEC cut indicator (manual coding)
3. Add enhanced seasonality features (already have calendar)
4. Weather enhancements (heating/cooling degree days)

### Week 3: Market Microstructure
1. Add RBOB volume data (CME)
2. Calculate volatility regime features
3. Implement term structure features
4. Test on October-only data

### Week 4: Interaction Terms & Model Comparison
1. Create 15 key interaction terms
2. Retrain all models
3. SHAP analysis on new features
4. A/B test old vs. new feature sets

---

## 🎓 FEATURE ENGINEERING PRINCIPLES

### For October Gas Price Prediction:

1. **October is transition month:**
   - Demand declining (summer → winter)
   - Supply transitioning (winter blend Nov 1)
   - Refinery maintenance season (fall turnarounds)
   - Hurricane risk declining but non-zero

2. **PADD 3 is critical:**
   - 60% of US refining
   - Colonial Pipeline origin
   - Hurricane exposure
   - Export hub (Corpus Christi, Houston)

3. **Supply shocks matter more than demand:**
   - Inelastic short-term demand
   - Refinery outages → immediate price impact
   - Inventory draws → price spikes
   - Pipeline disruptions → regional shortages

4. **Lead time matters:**
   - 21-day prediction horizon means need forward-looking indicators
   - Hurricane forecasts, OPEC meeting schedules, maintenance calendars
   - Futures term structure (market expectations)

---

## 📈 EXPECTED PERFORMANCE GAINS

**Current Model:**
- Ridge Baseline: Test R² = -0.20, RMSE = 0.058
- Ensemble: Test R² = -0.17, RMSE = 0.057

**Target with Tier 1 Features:**
- Ridge Baseline: Test R² = 0.30+, RMSE < 0.045
- Ensemble: Test R² = 0.40+, RMSE < 0.040

**Rationale:**
- Current model lacks supply disruption signals → misses price spikes
- Better geopolitical features → capture crude price shocks earlier
- Enhanced seasonality → better October-specific patterns
- Interaction terms → capture non-linear regime shifts

---

## 🔍 DATA SOURCES SUMMARY

### Free & Public:
- ✅ **EIA (Energy Information Administration):** Refinery, inventory, SPR, imports
- ✅ **NOAA:** Weather, hurricanes (already using)
- ✅ **FRED:** Macro indicators, interest rates, sentiment
- ✅ **CME:** RBOB futures (already have price, add volume/OI)
- ✅ **BLS:** Employment, CPI
- ✅ **Colonial Pipeline:** Public announcements (manual)

### Paid/Proprietary (Optional):
- ❌ Bloomberg Terminal: Real-time news sentiment, analyst forecasts
- ❌ Genscape: Real-time refinery operations (expensive)
- ❌ TankerTrackers: Import flow tracking
- ❌ Twitter API: Sentiment (now X, pricing changed)

**Recommendation:** Start with free sources, validate impact before considering paid data.

---

## ✅ VALIDATION STRATEGY

For each new feature batch:

1. **Univariate Analysis:**
   - Correlation with target (retail_price)
   - Distribution (skewness, outliers)
   - Missing data patterns

2. **Feature Importance:**
   - SHAP values
   - Ridge coefficients
   - Permutation importance

3. **Out-of-Sample Testing:**
   - Time series CV (not random splits!)
   - October-only validation
   - 2024-2025 holdout test

4. **Ablation Studies:**
   - Remove feature → measure performance drop
   - Proves causal value

---

## 🎯 SUCCESS METRICS

**Quantitative:**
- ✅ Reduce RMSE by 20%+ (0.058 → 0.045)
- ✅ Achieve positive R² on test set (currently negative)
- ✅ Top 10 features should include supply indicators

**Qualitative:**
- ✅ Model correctly predicts supply shock events (refinery outages, hurricanes)
- ✅ Feature importance aligns with domain expertise
- ✅ Predictions pass "smell test" (no unrealistic values)

**Robustness:**
- ✅ Performance stable across different years (2020-2025)
- ✅ Not overly sensitive to single features (diversified importance)
- ✅ Works for both quiet and volatile periods

---

## 🚨 COMMON PITFALLS TO AVOID

1. **Data Leakage:**
   - Don't use future data in features (e.g., next week's inventory in this week's prediction)
   - Careful with rolling averages near prediction boundary
   - Hurricane `days_until_next` is OK (it's historical knowledge, not future realization)

2. **Overfitting:**
   - October-only has ~145 samples → don't add 100+ features blindly
   - Use L1/L2 regularization aggressively
   - Validate on holdout years (2024-2025)

3. **Feature Correlation:**
   - Many inventory features will correlate → Ridge regression handles this well
   - Document which features are redundant
   - Consider PCA if correlation matrix becomes rank-deficient

4. **Stationarity:**
   - Gas prices have trends (inflation, structural changes)
   - Use returns/changes, not levels, where appropriate
   - Test for unit roots if doing advanced time series

---

**Next Steps:** Choose **Tier 1, Priority 1-4** and I'll help you implement them! 🚀
