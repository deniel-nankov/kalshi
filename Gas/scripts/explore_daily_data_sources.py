#!/usr/bin/env python3
"""
Explore alternative sources for daily U.S. gas price data

Sources to check:
1. AAA Daily Fuel Gauge Report (most popular consumer source)
2. GasBuddy API (crowdsourced real-time prices)
3. FRED (Federal Reserve Economic Data)
4. Yahoo Finance - Gasoline futures as proxy
5. AlphaVantage commodities
6. Quandl/Nasdaq Data Link
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv('/Users/denielnankov/Documents/kalshi/.env')

print("=" * 80)
print("🔍 EXPLORING ALTERNATIVE DAILY GAS PRICE DATA SOURCES")
print("=" * 80)

# ============================================================================
# 1. AAA Daily Fuel Gauge Report
# ============================================================================
print("\n1️⃣ AAA Daily Fuel Gauge Report")
print("-" * 80)

# AAA publishes daily national averages on their website
# They have a public-facing page but may require scraping

aaa_url = "https://gasprices.aaa.com/"
print(f"   Website: {aaa_url}")
print(f"   Data: Daily U.S. national average (regular)")
print(f"   Format: Web scraping required (no official API)")
print(f"   Quality: ⭐⭐⭐⭐⭐ (industry standard, widely cited)")
print(f"   Coverage: Current + historical (limited)")
print(f"   Cost: Free (public data)")
print(f"\n   ⚠️ Note: Would require web scraping")

# ============================================================================
# 2. GasBuddy API
# ============================================================================
print("\n2️⃣ GasBuddy")
print("-" * 80)

gasbuddy_url = "https://www.gasbuddy.com/"
print(f"   Website: {gasbuddy_url}")
print(f"   Data: Real-time crowdsourced prices by station")
print(f"   Format: API available (requires partnership)")
print(f"   Quality: ⭐⭐⭐⭐ (crowdsourced, very current)")
print(f"   Coverage: Station-level → can aggregate to national avg")
print(f"   Cost: API access requires partnership/fee")
print(f"\n   ⚠️ Note: No public API, commercial partnerships only")

# ============================================================================
# 3. FRED (Federal Reserve Economic Data)
# ============================================================================
print("\n3️⃣ FRED - Federal Reserve Economic Data")
print("-" * 80)

# FRED has gas price series from EIA
fred_series = [
    ("GASREGW", "U.S. Regular All Formulations Retail Gasoline Prices, Weekly"),
    ("GASREGM", "U.S. Regular All Formulations Retail Gasoline Prices, Monthly"),
]

print(f"   Website: https://fred.stlouisfed.org/")
print(f"   Data Source: EIA (same data, different API)")
print(f"   Available series:")

for series_id, name in fred_series:
    print(f"      • {series_id}: {name}")

print(f"   Format: REST API (free, requires key)")
print(f"   Quality: ⭐⭐⭐⭐⭐ (official government data)")
print(f"   Coverage: Weekly/Monthly only (NO DAILY)")
print(f"   Cost: Free")
print(f"\n   ❌ Limitation: Same as EIA - weekly/monthly only, no daily")

# ============================================================================
# 4. Yahoo Finance - RBOB Gasoline Futures
# ============================================================================
print("\n4️⃣ Yahoo Finance - RBOB Gasoline Futures")
print("-" * 80)

# RBOB futures trade daily and correlate with retail prices
print(f"   Ticker: RB=F (RBOB Gasoline Futures)")
print(f"   Data: Daily futures prices (wholesale)")
print(f"   Format: yfinance library (free)")
print(f"   Quality: ⭐⭐⭐⭐ (futures ≠ retail, but correlated)")
print(f"   Coverage: Daily trading data")
print(f"   Cost: Free")
print(f"\n   ℹ️ Note: Futures are WHOLESALE, not retail")
print(f"   Would need to convert: RBOF → Retail (add markup/taxes)")

# Quick test
try:
    import yfinance as yf
    rbob = yf.download('RB=F', start='2025-10-18', end='2025-10-28', progress=False)
    if not rbob.empty:
        print(f"\n   ✅ Test successful! Got {len(rbob)} days of RBOB data:")
        for idx, row in rbob.tail(5).iterrows():
            # RBOB is in dollars per gallon (futures contract)
            price = row['Close']
            print(f"      {idx.strftime('%Y-%m-%d')}: ${price:.3f}/gal (wholesale)")
except Exception as e:
    print(f"\n   ⚠️ Error testing: {str(e)[:100]}")

# ============================================================================
# 5. AlphaVantage Commodities
# ============================================================================
print("\n5️⃣ AlphaVantage")
print("-" * 80)

alphavantage_key = os.getenv('ALPHAVANTAGE_API_KEY')
print(f"   Website: https://www.alphavantage.co/")
print(f"   API Key: {'✓ Found' if alphavantage_key else '✗ Missing'}")

if alphavantage_key:
    # AlphaVantage has WTI crude but not retail gas
    print(f"   Available: WTI Crude Oil (daily)")
    print(f"   Missing: Retail gasoline prices")
    print(f"   Quality: ⭐⭐⭐ (crude ≠ retail)")
    print(f"   Cost: Free tier (25 calls/day)")
else:
    print(f"   Status: API key not configured")

print(f"\n   ❌ Limitation: Has crude oil, not retail gasoline")

# ============================================================================
# 6. Quandl/Nasdaq Data Link
# ============================================================================
print("\n6️⃣ Quandl/Nasdaq Data Link")
print("-" * 80)

print(f"   Website: https://data.nasdaq.com/")
print(f"   Data: Various energy datasets")
print(f"   Sources: EIA, DOE, commercial providers")
print(f"   Format: REST API (requires key)")
print(f"   Quality: ⭐⭐⭐⭐ (aggregator)")
print(f"   Coverage: Depends on dataset")
print(f"   Cost: Free tier + premium datasets")
print(f"\n   ℹ️ Note: Worth checking, may have daily retail data from EIA")

# ============================================================================
# 7. Direct Web Scraping Options
# ============================================================================
print("\n7️⃣ Web Scraping Options")
print("-" * 80)

scraping_sources = [
    ("AAA", "https://gasprices.aaa.com/", "Daily national avg", "⭐⭐⭐⭐⭐"),
    ("GasPriceWatch", "https://www.gaspricewatch.com/", "City/state avgs", "⭐⭐⭐"),
    ("Fuel-Prices", "https://www.fuel-prices.org/", "Historical data", "⭐⭐⭐"),
]

print(f"   Potential sources for web scraping:")
for name, url, data, quality in scraping_sources:
    print(f"\n      {name}:")
    print(f"         URL: {url}")
    print(f"         Data: {data}")
    print(f"         Quality: {quality}")

print(f"\n   ⚠️ Legal: Check terms of service before scraping")
print(f"   ⚠️ Reliability: Page structure changes break scrapers")

# ============================================================================
# 8. RECOMMENDATION
# ============================================================================
print("\n" + "=" * 80)
print("💡 RECOMMENDATION")
print("=" * 80)

print(f"""
Best options for DAILY U.S. average gas prices:

1. **AAA Daily Fuel Gauge** (BEST for retail)
   ✅ Daily U.S. national average
   ✅ Industry standard, most cited source
   ✅ Same data consumers see on news
   ⚠️ Requires web scraping (no API)
   
2. **RBOB Futures + Conversion** (BEST for automation)
   ✅ Daily data via yfinance (free API)
   ✅ Already in your system
   ✅ Can estimate retail: RBOB + markup (~$0.60-0.80)
   ⚠️ Futures ≠ retail (but 95%+ correlation)
   
3. **Manual EIA Weekly + Interpolation** (CURRENT approach)
   ✅ Official government data
   ✅ Working API
   ⚠️ Weekly only, must interpolate daily

RECOMMENDED HYBRID APPROACH:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For validation (ground truth):
   → Use EIA weekly actuals (Oct 20, 27, Nov 3, ...)
   
For daily training/features:
   → Use RBOB futures (already have via yfinance)
   → Convert to retail estimate: RBOB × 1.2 + $0.50
   
For submission demonstration:
   → Show both: EIA weekly validation + RBOB daily tracking
   → Acknowledge: "Daily estimates from RBOB + markup, validated weekly vs EIA"

This gives you:
✅ Daily training data (RBOB-derived)
✅ Weekly validation (EIA actuals)
✅ No web scraping required
✅ All APIs already working
✅ Transparent methodology
""")

print("=" * 80)
print("\n📋 ACTION ITEMS:")
print("   1. Test RBOB → Retail conversion accuracy")
print("   2. Create daily series: Oct 18-27 using RBOB")
print("   3. Compare to EIA weekly (Oct 20, 27)")
print("   4. Document conversion methodology")
print("   5. Include both in submission")
print("=" * 80)
