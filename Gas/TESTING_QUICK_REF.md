# News Sentiment Testing - Quick Reference

**Quick commands for testing the news sentiment implementation**

---

## 🚀 Setup (5 minutes)

### 1. Get API Keys

**Finnhub (Primary):**
```
1. Visit: https://finnhub.io/register
2. Sign up (email + password)
3. Copy API key
4. Rate limit: 60 calls/minute (free)
```

**AlphaVantage (Backup):**
```
1. Visit: https://www.alphavantage.co/support/#api-key
2. Enter email, get instant key
3. Copy API key
4. Rate limit: 5 calls/minute (free)
```

### 2. Update .env

```bash
# Edit file
nano /Users/denielnankov/Documents/kalshi/.env

# Add your keys (replace placeholders):
FINNHUB_API_KEY=your_finnhub_key_here
ALPHAVANTAGE_API_KEY=your_alphavantage_key_here
```

---

## ✅ Verification Tests (3 steps)

### Step 1: Test Bronze Layer (Fast - 2 min)

```bash
cd /Users/denielnankov/Documents/kalshi/Gas

# Fetch one month of data
python scripts/fetch_news_sentiment.py \
  --start-date 2024-12-01 \
  --end-date 2024-12-31
```

**Expected Output:**
```
✅ Fetched 1,247 articles from Finnhub (XLE, XOM, CVX)
✅ Fetched 342 articles from AlphaVantage (CRUDE OIL)
✅ Total: 1,589 articles
✅ Date range: 2024-12-01 to 2024-12-31
✅ Saved to: data/bronze/news/energy_news_raw_20241201_20241231_*.parquet
✅ Validation passed: No future dates, sentiment scores valid
```

### Step 2: Run Validation (Fast - 1 min)

```bash
python scripts/validate_news_sentiment.py --sample-size 50
```

**Expected Output:**
```
📂 Loading: energy_news_raw_20241201_20241231_*.parquet
✅ Loaded 1,589 articles

🔍 DATA QUALITY CHECKS
   ✓ headline: 0 nulls (0.0%)
   ✓ sentiment_score: 0 nulls (0.0%)
   Duplicate articles: 12 (0.8%)
   Date coverage: 31 / 31 days (100%)
   Articles per day: 51.3 ± 12.4

📊 SENTIMENT DISTRIBUTION
   Mean: 0.032 ✅
   Std Dev: 0.241 ✅
   Very Positive (>0.5): 87 (5.5%)
   Positive (0.2-0.5): 412 (25.9%)
   Neutral (-0.2 to 0.2): 894 (56.3%)
   Negative (-0.5 to -0.2): 178 (11.2%)
   Very Negative (<-0.5): 18 (1.1%)

✅ Generated 50 articles for manual review
💾 Saved to: data/validation/manual_review_sample_*.csv
```

### Step 3: Run Automated Tests (Fast - 30 sec)

```bash
pip install pytest  # If not already installed

pytest tests/test_news_sentiment.py -v
```

**Expected Output:**
```
tests/test_news_sentiment.py::TestRetryLogic::test_retry_success_first_attempt PASSED
tests/test_news_sentiment.py::TestRetryLogic::test_retry_success_after_failures PASSED
tests/test_news_sentiment.py::TestRetryLogic::test_retry_exhausts_attempts PASSED
...
tests/test_news_sentiment.py::TestQualityAssurance::test_article_volume_reasonable PASSED

========================= 26 passed in 2.43s =========================
```

---

## 📊 Expected Results Summary

**If all 3 steps pass:**

| Check | Status | Expected Value |
|-------|--------|----------------|
| Articles Fetched | ✅ | 500-2000 (for 1 month) |
| Date Coverage | ✅ | >95% |
| Sentiment Mean | ✅ | -0.1 to 0.1 (near neutral) |
| Sentiment Std | ✅ | 0.15-0.35 (reasonable variance) |
| Duplicates | ✅ | <5% |
| Null Values | ✅ | <1% |
| Automated Tests | ✅ | 26/26 passing |

**✅ If all checks pass → Ready for Day 2 (Silver layer)**

---

## 🔧 Troubleshooting

### ❌ Problem: "API key invalid"

**Solution:**
```bash
# Verify key in .env
cat /Users/denielnankov/Documents/kalshi/.env | grep FINNHUB

# Should show: FINNHUB_API_KEY=<your-actual-key>
# NOT: FINNHUB_API_KEY=your_finnhub_key_here
```

### ❌ Problem: "No data fetched"

**Solution:**
```bash
# Test API endpoint manually
python -c "
import requests
import os
from dotenv import load_dotenv
load_dotenv()

key = os.getenv('FINNHUB_API_KEY')
url = f'https://finnhub.io/api/v1/company-news?symbol=XLE&from=2024-12-01&to=2024-12-31&token={key}'
response = requests.get(url)
print(f'Status: {response.status_code}')
print(f'Articles: {len(response.json())}')
"

# Expected: Status: 200, Articles: 50-200
```

### ❌ Problem: Tests failing

**Check Python version:**
```bash
python --version
# Must be 3.8+
```

**Check dependencies:**
```bash
pip install pandas numpy requests python-dotenv pytest
```

---

## 🏃 Quick Historical Data Fetch (30-60 min)

**Once verification passes, fetch full historical data:**

```bash
# Fetch 5 years of news (2020-2025)
python scripts/fetch_news_sentiment.py \
  --start-date 2020-01-01 \
  --end-date 2025-01-31

# This will:
# - Fetch ~50,000-100,000 articles
# - Take 30-60 minutes (rate limiting)
# - Save to data/bronze/news/
# - Create metadata for monitoring
```

**Then validate:**
```bash
python scripts/validate_news_sentiment.py --sample-size 100
```

---

## 📋 Manual Review (Optional, Day 1)

**To verify sentiment accuracy:**

```bash
# 1. Open generated sample
open data/validation/manual_review_sample_*.csv

# 2. For each row:
#    - Read headline
#    - Fill 'manual_sentiment': positive/neutral/negative
#    - Fill 'correct': yes/no (does automated score match?)
#    - Add any notes

# 3. Save file

# 4. Calculate accuracy
python scripts/validate_news_sentiment.py \
  --check-accuracy data/validation/manual_review_sample_*.csv

# Expected accuracy: >85%
```

---

## ✅ Day 1 Complete Checklist

Before proceeding to Day 2:

- [ ] API keys obtained (Finnhub + AlphaVantage)
- [ ] API keys added to .env file
- [ ] Bronze layer test successful (Step 1) ✅
- [ ] Validation shows good data quality (Step 2) ✅
- [ ] All automated tests pass (Step 3) ✅
- [ ] Historical data fetched (2020-2025) [OPTIONAL for Day 1]
- [ ] Manual review started (20+ articles) [OPTIONAL for Day 1]

**If all required items checked → Ready for Day 2! 🚀**

---

## 📞 Next Steps

**Day 2: Silver Layer**
- Create `scripts/clean_news_to_silver.py`
- Daily aggregation
- Duplicate removal
- Forward-fill missing days
- Validation report

**Day 3: Feature Engineering + Testing**
- Add 9 sentiment features to Gold layer
- Run leakage detection
- Full integration tests

**Day 4: Model Retraining**
- Update run_pipeline.py
- Retrain models with sentiment
- Compare R² before/after
- Document results

**Expected Timeline:** 2-3 more days → +0.10-0.15 R² improvement

---

**Need Help?** Check `TEST_FRAMEWORK_COMPLETE.md` for detailed documentation
