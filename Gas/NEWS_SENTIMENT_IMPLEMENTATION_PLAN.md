# News Sentiment Analysis - Elite Implementation Plan

**Date:** October 18, 2025  
**Goal:** Add news sentiment features to improve R² from 0.086 → 0.25-0.30  
**Timeline:** 3-4 days  
**Quality Standard:** Production-grade with comprehensive testing

---

## 🎯 Implementation Strategy

### **Phase 1: API Selection & Setup (Day 1, Morning)**

**Primary Source:** NewsAPI.org
- ✅ Free tier: 100 requests/day
- ✅ Historical data: Up to 1 month back (free), 5 years (paid $449/month)
- ✅ Coverage: 80,000+ sources worldwide
- ✅ Rate limit: 500 requests/day (developer plan)

**Backup Source:** Finnhub.io
- ✅ Free tier: 60 calls/minute
- ✅ Company news endpoint with sentiment scores (pre-computed!)
- ✅ Energy sector coverage
- ✅ Rate limit: 60/min

**Tertiary Source:** AlphaVantage
- ✅ Free tier: 5 calls/minute, 500/day
- ✅ News sentiment API endpoint
- ✅ Ticker-based (XLE, XOM, CVX for energy sector)
- ✅ Provides sentiment scores + relevance

**Strategy:**
1. Use **Finnhub** as primary (has pre-computed sentiment, highest rate limit)
2. Use **AlphaVantage** as backup (also has sentiment scores)
3. Use **NewsAPI** for additional coverage + manual VADER scoring

---

### **Phase 2: Data Architecture (Day 1, Afternoon)**

```
📦 BRONZE LAYER (Raw API Responses)
├── data/bronze/news/
│   ├── finnhub_energy_news_raw_YYYYMMDD.parquet
│   ├── alphavantage_energy_sentiment_raw_YYYYMMDD.parquet
│   ├── newsapi_energy_articles_raw_YYYYMMDD.parquet
│   └── _metadata/
│       ├── api_call_log.json (track API usage)
│       └── data_quality_metrics.json

🪙 SILVER LAYER (Cleaned, Validated Sentiment)
├── data/silver/news/
│   ├── energy_news_sentiment_daily.parquet
│   │   Columns: date, source, headline, sentiment_score, 
│   │            confidence, relevance_score, article_count
│   └── sentiment_validation_report.csv

⭐ GOLD LAYER (Engineered Features)
├── data/gold/master_model_ready.parquet (existing)
│   NEW COLUMNS:
│   - news_sentiment_1d: Previous day sentiment
│   - news_sentiment_7d_avg: 7-day rolling average
│   - news_sentiment_14d_avg: 14-day rolling average
│   - news_sentiment_volatility_7d: 7-day rolling std
│   - news_volume_1d: Article count previous day
│   - news_volume_7d_avg: 7-day rolling article count
│   - sentiment_momentum_7d: Change in sentiment
│   - extreme_sentiment_flag: |sentiment| > 0.5
```

---

### **Phase 3: Implementation Plan**

#### **Step 1: API Client with Elite Robustness** ✅

**File:** `scripts/fetch_news_sentiment.py`

**Features:**
- ✅ Retry logic (10 attempts, exponential backoff)
- ✅ Rate limiting (respect API limits)
- ✅ API key rotation (if multiple keys available)
- ✅ Graceful fallback (Finnhub → AlphaVantage → NewsAPI)
- ✅ Comprehensive error handling
- ✅ Request/response logging
- ✅ API usage tracking (stay under limits)

**Validation:**
- ✅ Verify date ranges (no future data)
- ✅ Check for duplicates
- ✅ Validate sentiment scores (-1 to +1 range)
- ✅ Flag missing/null values
- ✅ Track data freshness

---

#### **Step 2: Sentiment Scoring Engine** ✅

**File:** `src/sentiment/sentiment_scorer.py`

**Methods:**

1. **Finnhub Sentiment** (Pre-computed, most reliable)
   ```python
   # Finnhub provides: sentiment = "positive" | "neutral" | "negative"
   # Convert to numerical: positive=+0.5, neutral=0, negative=-0.5
   ```

2. **AlphaVantage Sentiment** (Pre-computed with confidence)
   ```python
   # AlphaVantage provides: sentiment_score, relevance_score
   # Already numerical, just validate range
   ```

3. **VADER Sentiment** (For NewsAPI articles)
   ```python
   from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
   
   analyzer = SentimentIntensityAnalyzer()
   scores = analyzer.polarity_scores(headline + " " + snippet)
   sentiment = scores['compound']  # -1 to +1
   ```

4. **FinBERT Sentiment** (Optional, most accurate but slowest)
   ```python
   from transformers import BertTokenizer, BertForSequenceClassification
   
   # Pre-trained on financial news
   # Use for spot-checking accuracy
   ```

**Ensemble Strategy:**
- Weight by source reliability: Finnhub (0.4) + AlphaVantage (0.4) + NewsAPI/VADER (0.2)
- Require minimum 2 sources for high-confidence scores
- Flag low-confidence days (< 5 articles)

---

#### **Step 3: Comprehensive Test Suite** ✅

**File:** `tests/test_news_sentiment.py`

**Test Categories:**

1. **Unit Tests (API Calls)**
   ```python
   def test_finnhub_api_call():
       """Test Finnhub API returns valid data"""
       client = FinnhubNewsClient(api_key="test")
       news = client.fetch_company_news("XLE", "2024-01-01", "2024-01-02")
       assert len(news) > 0
       assert all('headline' in item for item in news)
       assert all('sentiment' in item for item in news)
   
   def test_api_retry_logic():
       """Test retry logic handles failures gracefully"""
       # Mock API failure, verify retries
   
   def test_rate_limiting():
       """Test rate limiter prevents exceeding API limits"""
       # Make 61 requests, verify last one is delayed
   ```

2. **Unit Tests (Sentiment Scoring)**
   ```python
   def test_vader_sentiment_positive():
       """Test VADER correctly identifies positive sentiment"""
       text = "Oil prices surge on strong demand outlook"
       score = vader_scorer.score(text)
       assert score > 0.3
   
   def test_vader_sentiment_negative():
       """Test VADER correctly identifies negative sentiment"""
       text = "Refinery fire causes major supply disruption"
       score = vader_scorer.score(text)
       assert score < -0.3
   
   def test_sentiment_score_range():
       """Test all sentiment scores are in valid range"""
       scores = [...multiple headlines...]
       assert all(-1 <= s <= 1 for s in scores)
   ```

3. **Integration Tests (End-to-End)**
   ```python
   def test_bronze_to_silver_pipeline():
       """Test complete data flow from API to silver layer"""
       # Fetch news → Clean → Validate → Save
       assert silver_file.exists()
       df = pd.read_parquet(silver_file)
       assert len(df) > 0
       assert df['sentiment_score'].notna().all()
   
   def test_silver_to_gold_pipeline():
       """Test sentiment features added to gold layer"""
       # Load silver → Engineer features → Merge to gold
       gold = pd.read_parquet("data/gold/master_model_ready.parquet")
       assert 'news_sentiment_7d_avg' in gold.columns
       assert 'news_volume_7d_avg' in gold.columns
   ```

4. **Data Validation Tests**
   ```python
   def test_no_future_data_leakage():
       """Verify no future data used in features"""
       gold = load_gold_layer()
       for idx in range(14, len(gold)):
           target_date = gold.loc[idx, 'date']
           sentiment_date = gold.loc[idx, 'news_sentiment_1d_date']
           assert sentiment_date < target_date
   
   def test_sentiment_correlation_realistic():
       """Test sentiment correlates with price changes (sanity check)"""
       gold = load_gold_layer()
       corr = gold['news_sentiment_7d_avg'].corr(gold['target'])
       assert -0.5 < corr < 0.5  # Should be moderate, not perfect
   
   def test_no_duplicates():
       """Verify no duplicate articles in dataset"""
       silver = load_silver_layer()
       assert silver.duplicated(subset=['date', 'headline']).sum() == 0
   ```

5. **Quality Assurance Tests**
   ```python
   def test_data_freshness():
       """Verify data is recent (within 7 days)"""
       silver = load_silver_layer()
       latest_date = silver['date'].max()
       assert (datetime.now().date() - latest_date).days <= 7
   
   def test_sufficient_coverage():
       """Verify sufficient articles per day (>5 minimum)"""
       silver = load_silver_layer()
       daily_counts = silver.groupby('date').size()
       assert (daily_counts >= 5).mean() > 0.90  # 90% of days have 5+ articles
   
   def test_sentiment_distribution():
       """Verify sentiment distribution is reasonable"""
       silver = load_silver_layer()
       # Should be mostly neutral with some pos/neg
       assert silver['sentiment_score'].abs().mean() < 0.3
       assert silver['sentiment_score'].std() > 0.1  # Has variance
   ```

---

#### **Step 4: Data Quality Validation** ✅

**File:** `scripts/validate_news_sentiment.py`

**Validation Checks:**

1. **Manual Spot-Checks**
   ```python
   def manual_validation_sample():
       """Generate sample for manual review"""
       silver = load_silver_layer()
       
       # Sample 50 articles: 10 very positive, 10 very negative, 30 neutral
       very_pos = silver[silver['sentiment_score'] > 0.5].sample(10)
       very_neg = silver[silver['sentiment_score'] < -0.5].sample(10)
       neutral = silver[silver['sentiment_score'].abs() < 0.2].sample(30)
       
       sample = pd.concat([very_pos, very_neg, neutral])
       sample[['date', 'headline', 'sentiment_score']].to_csv(
           'outputs/validation/news_sentiment_manual_review.csv'
       )
       print("Review: outputs/validation/news_sentiment_manual_review.csv")
   ```

2. **Statistical Validation**
   ```python
   def statistical_validation():
       """Run statistical tests on sentiment data"""
       silver = load_silver_layer()
       
       # Test 1: No extreme outliers (|z-score| > 5)
       z_scores = (silver['sentiment_score'] - silver['sentiment_score'].mean()) / silver['sentiment_score'].std()
       outliers = (z_scores.abs() > 5).sum()
       assert outliers < 10, f"Found {outliers} extreme outliers"
       
       # Test 2: Distribution roughly normal
       from scipy.stats import normaltest
       stat, pvalue = normaltest(silver['sentiment_score'])
       # Note: Financial sentiment may not be normal, just check not too skewed
       
       # Test 3: Correlation with price changes (lead-lag)
       gold = load_gold_with_sentiment()
       for lag in [1, 2, 3, 7]:
           corr = gold['news_sentiment_1d'].shift(lag).corr(gold['retail_price'].pct_change())
           print(f"Sentiment lag {lag} days → price change: {corr:.3f}")
   ```

3. **Event-Based Validation**
   ```python
   def validate_known_events():
       """Check sentiment captured known major events"""
       known_events = [
           ("2020-04-20", "negative", "Oil price crash, WTI negative"),
           ("2022-03-08", "negative", "Russia invades Ukraine"),
           ("2023-10-07", "negative", "Israel-Hamas war starts"),
           ("2024-03-15", "positive", "OPEC production increase")
       ]
       
       silver = load_silver_layer()
       for date, expected, description in known_events:
           actual = silver[silver['date'] == date]['sentiment_score'].mean()
           print(f"{date} ({description})")
           print(f"  Expected: {expected}, Actual: {actual:.2f}")
           
           # Flexible assertions (sentiment analysis isn't perfect)
           if expected == "negative":
               assert actual < 0, f"Failed to detect negative sentiment for {description}"
           elif expected == "positive":
               assert actual > 0, f"Failed to detect positive sentiment for {description}"
   ```

---

#### **Step 5: Feature Engineering (Gold Layer)** ✅

**File:** `scripts/build_gold_layer.py` (update existing)

**New Features:**

```python
# Load sentiment data
sentiment = pd.read_parquet("data/silver/news/energy_news_sentiment_daily.parquet")

# Ensure date alignment
sentiment = sentiment.rename(columns={'date': 'sentiment_date'})
gold = gold.merge(sentiment, left_on='date', right_on='sentiment_date', how='left')

# === SENTIMENT FEATURES (ALL PROPERLY LAGGED FOR 14-DAY HORIZON) ===

# 1. Raw sentiment (1-day lag for 14-day forecast = use t-15)
gold['news_sentiment_lag15'] = gold['sentiment_score'].shift(15)

# 2. Short-term averages (properly lagged)
gold['news_sentiment_7d_avg'] = gold['sentiment_score'].shift(15).rolling(7).mean()
gold['news_sentiment_14d_avg'] = gold['sentiment_score'].shift(15).rolling(14).mean()

# 3. Volatility (captures uncertainty)
gold['news_sentiment_volatility_7d'] = gold['sentiment_score'].shift(15).rolling(7).std()
gold['news_sentiment_volatility_14d'] = gold['sentiment_score'].shift(15).rolling(14).std()

# 4. Article volume (market attention)
gold['news_volume_lag15'] = gold['article_count'].shift(15)
gold['news_volume_7d_avg'] = gold['article_count'].shift(15).rolling(7).mean()

# 5. Momentum (change in sentiment)
gold['sentiment_momentum_7d'] = (
    gold['sentiment_score'].shift(15) - 
    gold['sentiment_score'].shift(22)
)

# 6. Extreme sentiment flags (binary)
gold['extreme_positive_sentiment'] = (gold['sentiment_score'].shift(15) > 0.5).astype(int)
gold['extreme_negative_sentiment'] = (gold['sentiment_score'].shift(15) < -0.5).astype(int)

# 7. Interaction with price features (captures divergence)
gold['sentiment_price_divergence'] = (
    gold['news_sentiment_7d_avg'] * gold['rbob_lag14']
)

# Forward fill NaNs (for days with no news)
sentiment_cols = [
    'news_sentiment_lag15', 'news_sentiment_7d_avg', 'news_sentiment_14d_avg',
    'news_sentiment_volatility_7d', 'news_sentiment_volatility_14d',
    'news_volume_lag15', 'news_volume_7d_avg', 'sentiment_momentum_7d',
    'extreme_positive_sentiment', 'extreme_negative_sentiment',
    'sentiment_price_divergence'
]

for col in sentiment_cols:
    if col in gold.columns:
        gold[col] = gold[col].fillna(method='ffill').fillna(0)
```

**Validation:**
```python
# Verify no leakage
assert all(gold['news_sentiment_lag15'].shift(-15).notna() == gold['sentiment_score'].notna())

# Verify features exist
assert all(col in gold.columns for col in sentiment_cols)

# Verify no future data
for col in sentiment_cols:
    # Check that feature values don't change when we remove future data
    test_idx = 100
    val_before = gold.loc[test_idx, col]
    gold_truncated = gold.iloc[:test_idx+1].copy()
    # Recalculate feature on truncated data
    # Should match original value
```

---

#### **Step 6: Integration & Testing** ✅

**File:** `scripts/run_pipeline.py` (update existing)

```python
# Add to Phase 1: Data Acquisition
steps.append((
    "1b. Fetch Energy News Sentiment (Finnhub, AlphaVantage)",
    [python, str(SCRIPT_DIR / "fetch_news_sentiment.py"),
     "--start-date", "2020-01-01",
     "--end-date", "2025-12-31"],
    True  # Allow failure - news is supplemental
))

# Add to Phase 3: Validation
steps.append((
    "12b. Validate News Sentiment Data",
    [python, str(SCRIPT_DIR / "validate_news_sentiment.py")],
    True  # Allow failure - validation is diagnostic
))
```

---

#### **Step 7: Model Retraining & Evaluation** ✅

**File:** `scripts/train_models_with_sentiment.py` (new)

```python
# Before sentiment (baseline)
baseline_features = COMMON_FEATURES  # 88 features

# After sentiment (enhanced)
sentiment_features = baseline_features + [
    'news_sentiment_lag15',
    'news_sentiment_7d_avg',
    'news_sentiment_14d_avg',
    'news_sentiment_volatility_7d',
    'news_volume_7d_avg',
    'sentiment_momentum_7d',
    'extreme_positive_sentiment',
    'extreme_negative_sentiment',
    'sentiment_price_divergence'
]  # 97 features total

# Train both models
results_baseline = train_all_models(df, features=baseline_features)
results_sentiment = train_all_models(df, features=sentiment_features)

# Compare
comparison = pd.DataFrame({
    'model': results_baseline.keys(),
    'r2_baseline': [r.metrics['test']['r2'] for r in results_baseline.values()],
    'r2_with_sentiment': [r.metrics['test']['r2'] for r in results_sentiment.values()],
    'r2_improvement': [
        r_sent.metrics['test']['r2'] - r_base.metrics['test']['r2']
        for r_base, r_sent in zip(results_baseline.values(), results_sentiment.values())
    ]
})

print(comparison)

# Expected improvement: R² +0.10-0.15
```

---

### **Phase 4: Monitoring & Documentation**

#### **File:** `scripts/monitor_news_sentiment_freshness.py`

```python
def check_data_freshness():
    """Monitor news sentiment data quality"""
    silver = pd.read_parquet("data/silver/news/energy_news_sentiment_daily.parquet")
    
    checks = {
        'latest_date': silver['date'].max(),
        'days_stale': (datetime.now().date() - silver['date'].max()).days,
        'avg_daily_articles': silver.groupby('date')['article_count'].sum().mean(),
        'days_with_no_news': (silver.groupby('date')['article_count'].sum() == 0).sum(),
        'sentiment_mean': silver['sentiment_score'].mean(),
        'sentiment_std': silver['sentiment_score'].std()
    }
    
    # Alerts
    if checks['days_stale'] > 7:
        print(f"⚠️  WARNING: News data is {checks['days_stale']} days stale!")
    
    if checks['avg_daily_articles'] < 5:
        print(f"⚠️  WARNING: Low article coverage ({checks['avg_daily_articles']:.1f} per day)")
    
    return checks
```

---

## 📊 Expected Outcomes

### **Performance Targets:**

| Metric | Baseline | With Sentiment | Target |
|--------|----------|----------------|--------|
| **Ridge R²** | 0.086 | → | **0.20-0.25** |
| **Ridge MAE** | $0.042 | → | **$0.035** |
| **GB R²** | 0.025 | → | **0.15-0.20** |

### **Data Quality Targets:**

- ✅ Historical coverage: 2020-01-01 to present (1,800+ days)
- ✅ Daily article count: >5 per day (95% of days)
- ✅ Sentiment accuracy: >80% on manual validation sample
- ✅ Data freshness: <7 days stale
- ✅ No temporal leakage: 100% of features properly lagged
- ✅ Test coverage: >90% (unit + integration tests)

---

## 🚀 Execution Checklist

### **Day 1: Setup & API Testing**
- [ ] Sign up for API keys (Finnhub, AlphaVantage, NewsAPI)
- [ ] Test API endpoints with sample requests
- [ ] Verify rate limits and historical data access
- [ ] Set up .env file for API keys
- [ ] Create Bronze layer directory structure
- [ ] Implement API client with retry logic

### **Day 2: Data Collection & Cleaning**
- [ ] Fetch historical news (2020-2025, ~1,800 days)
- [ ] Implement sentiment scoring (VADER + pre-computed)
- [ ] Clean and validate Bronze → Silver
- [ ] Run data quality checks
- [ ] Create validation reports

### **Day 3: Feature Engineering & Testing**
- [ ] Engineer 9 sentiment features
- [ ] Update build_gold_layer.py
- [ ] Run comprehensive test suite
- [ ] Validate no temporal leakage
- [ ] Manual spot-check sentiment accuracy

### **Day 4: Integration & Evaluation**
- [ ] Update run_pipeline.py
- [ ] Retrain all models with sentiment features
- [ ] Run walk-forward validation
- [ ] Compare R² before/after
- [ ] Document results and commit to GitHub

---

## ✅ Success Criteria

**Must Have:**
- ✅ R² improvement of at least +0.08 (from 0.086 → 0.166+)
- ✅ Zero temporal leakage (verified by detect_leakage.py)
- ✅ 95%+ test coverage
- ✅ Data validation passing all checks
- ✅ Documentation complete

**Nice to Have:**
- ✅ R² improvement of +0.15 (reaching 0.23+)
- ✅ Sentiment accuracy >85% on manual validation
- ✅ Real-time data updates (within 24 hours)

---

**Ready to begin implementation!** 🚀

Next step: Set up API keys and create the fetch_news_sentiment.py script with elite robustness.
