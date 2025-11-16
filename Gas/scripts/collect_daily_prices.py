#!/usr/bin/env python3
"""
Complete Daily Gas Price Data Collection

Collects daily U.S. gas prices from multiple sources:
1. AAA Daily Fuel Gauge (scraping) - BEST for retail
2. EIA Weekly (API) - Official government data
3. RBOB Futures (yfinance) - Daily wholesale prices

Combines all sources for most complete daily dataset.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import re
import yfinance as yf
import os
from dotenv import load_dotenv

# Add project root
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
load_dotenv(project_root / '.env')

print("=" * 80)
print("📊 COMPLETE DAILY GAS PRICE DATA COLLECTION")
print("=" * 80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# ============================================================================
# 1. AAA Daily (Scraping)
# ============================================================================
print("\n1️⃣ AAA Daily Fuel Gauge (scraping)...")

def get_aaa_price():
    url = "https://gasprices.aaa.com/"
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        price_matches = re.findall(r'\$(\d+\.\d{3})', response.text)
        if price_matches:
            price = float(price_matches[0])
            print(f"   ✅ ${price:.3f}/gal (U.S. National Average)")
            return price
    except Exception as e:
        print(f"   ⚠️ Failed: {str(e)[:50]}")
    return None

aaa_price = get_aaa_price()

# ============================================================================
# 2. EIA Weekly (API)
# ============================================================================
print("\n2️⃣ EIA Weekly (official API)...")

def get_eia_weekly():
    eia_key = os.getenv('EIA_API_KEY')
    if not eia_key:
        print(f"   ⚠️ No EIA API key")
        return None
    
    url = "https://api.eia.gov/v2/petroleum/pri/gnd/data/"
    params = {
        'api_key': eia_key,
        'frequency': 'weekly',
        'data[0]': 'value',
        'facets[product][]': 'EPMR',  # Regular Gasoline
        'facets[duoarea][]': 'NUS',   # U.S. National
        'sort[0][column]': 'period',
        'sort[0][direction]': 'desc',
        'length': 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'response' in data and 'data' in data['response']:
                records = data['response']['data']
                if records:
                    latest = records[0]
                    price = float(latest['value'])
                    date = latest['period']
                    print(f"   ✅ ${price:.3f}/gal (Week ending {date})")
                    return {'price': price, 'date': date}
    except Exception as e:
        print(f"   ⚠️ Failed: {str(e)[:50]}")
    return None

eia_data = get_eia_weekly()

# ============================================================================
# 3. RBOB Futures (Yahoo Finance)
# ============================================================================
print("\n3️⃣ RBOB Gasoline Futures (yfinance)...")

def get_rbob_price():
    try:
        rbob = yf.download('RB=F', period='5d', progress=False)
        if not rbob.empty:
            latest_price = rbob['Close'].iloc[-1]
            latest_date = rbob.index[-1].strftime('%Y-%m-%d')
            
            # Convert to retail estimate (from earlier analysis)
            retail_est = latest_price + 1.152
            
            print(f"   ✅ RBOB: ${latest_price:.3f}/gal ({latest_date})")
            print(f"      → Retail estimate: ${retail_est:.3f}/gal")
            return {'rbob': latest_price, 'retail_est': retail_est, 'date': latest_date}
    except Exception as e:
        print(f"   ⚠️ Failed: {str(e)[:50]}")
    return None

rbob_data = get_rbob_price()

# ============================================================================
# 4. Combine and Analyze
# ============================================================================
print(f"\n{'=' * 80}")
print("📊 SUMMARY & COMPARISON")
print("=" * 80)

today = datetime.now().date()

prices = {}
if aaa_price:
    prices['AAA'] = aaa_price
if eia_data:
    prices['EIA'] = eia_data['price']
if rbob_data:
    prices['RBOB_Est'] = rbob_data['retail_est']

if prices:
    print(f"\nToday's Prices ({today}):")
    print(f"   {'Source':<15} {'Price':<12} {'Notes'}")
    print(f"   {'-'*50}")
    
    if 'AAA' in prices:
        print(f"   {'AAA':<15} ${prices['AAA']:.3f}/gal   Daily retail (scraped)")
    
    if 'EIA' in prices:
        eia_date = eia_data['date']
        days_old = (pd.Timestamp(today) - pd.Timestamp(eia_date)).days
        print(f"   {'EIA':<15} ${prices['EIA']:.3f}/gal   Weekly ({days_old} days old)")
    
    if 'RBOB_Est' in prices:
        rbob_date = rbob_data['date']
        print(f"   {'RBOB Est':<15} ${prices['RBOB_Est']:.3f}/gal   From futures ({rbob_date})")
    
    # Calculate consensus
    if len(prices) > 1:
        avg_price = np.mean(list(prices.values()))
        std_price = np.std(list(prices.values()))
        
        print(f"\n   {'Consensus':<15} ${avg_price:.3f}/gal   ± ${std_price:.3f}")
        
        # Differences
        if 'AAA' in prices and 'RBOB_Est' in prices:
            diff = abs(prices['AAA'] - prices['RBOB_Est'])
            print(f"\n   AAA vs RBOB Est: ${diff:.3f} difference")
        
        if 'AAA' in prices and 'EIA' in prices:
            diff = abs(prices['AAA'] - prices['EIA'])
            print(f"   AAA vs EIA: ${diff:.3f} difference")

# ============================================================================
# 5. Save to CSV
# ============================================================================
print(f"\n{'=' * 80}")
print("💾 SAVING DATA")
print("=" * 80)

output_dir = project_root / 'outputs'
output_dir.mkdir(parents=True, exist_ok=True)

# Create record
record = {
    'date': today,
    'aaa_price': aaa_price,
    'eia_price': eia_data['price'] if eia_data else None,
    'eia_date': eia_data['date'] if eia_data else None,
    'rbob_wholesale': rbob_data['rbob'] if rbob_data else None,
    'rbob_retail_est': rbob_data['retail_est'] if rbob_data else None,
    'rbob_date': rbob_data['date'] if rbob_data else None,
}

# Best estimate (prefer AAA > EIA > RBOB)
if aaa_price:
    record['best_estimate'] = aaa_price
    record['best_source'] = 'AAA'
elif eia_data:
    record['best_estimate'] = eia_data['price']
    record['best_source'] = 'EIA'
elif rbob_data:
    record['best_estimate'] = rbob_data['retail_est']
    record['best_source'] = 'RBOB'
else:
    record['best_estimate'] = None
    record['best_source'] = None

# Save to master file
master_path = output_dir / 'daily_gas_prices_all_sources.csv'

if master_path.exists():
    df = pd.read_csv(master_path)
    df['date'] = pd.to_datetime(df['date']).dt.date
    
    # Remove today if exists (update)
    df = df[df['date'] != today]
    
    # Append new record
    new_df = pd.DataFrame([record])
    df = pd.concat([df, new_df], ignore_index=True)
else:
    df = pd.DataFrame([record])

# Sort and save
df = df.sort_values('date')
df.to_csv(master_path, index=False)

print(f"\n✅ Saved to: {master_path}")
print(f"   Total days: {len(df)}")
print(f"   Date range: {df['date'].min()} to {df['date'].max()}")

# Show last 5 days
if len(df) >= 5:
    print(f"\n   Last 5 days:")
    print(f"\n   {'Date':<12} {'AAA':<8} {'EIA':<8} {'RBOB':<8} {'Best':<8}")
    print(f"   {'-'*50}")
    # Use itertuples() for better performance (5-10x faster than iterrows)
    for row in df.tail(5).itertuples(index=False):
        aaa = f"${row.aaa_price:.3f}" if pd.notna(row.aaa_price) else "—"
        eia = f"${row.eia_price:.3f}" if pd.notna(row.eia_price) else "—"
        rbob = f"${row.rbob_retail_est:.3f}" if pd.notna(row.rbob_retail_est) else "—"
        best = f"${row.best_estimate:.3f}" if pd.notna(row.best_estimate) else "—"
        print(f"   {row.date!s:<12} {aaa:<8} {eia:<8} {rbob:<8} {best:<8}")

# ============================================================================
# 6. Recommendations
# ============================================================================
print(f"\n{'=' * 80}")
print("💡 RECOMMENDATIONS")
print("=" * 80)

print(f"""
Data Quality Assessment:

1. AAA (Best for daily retail):
   ✓ Daily updates
   ✓ Industry standard
   ✓ What consumers actually see
   → Use as PRIMARY source

2. EIA (Best for validation):
   ✓ Official government data
   ✓ Most authoritative
   ✗ Weekly only (not daily)
   → Use to VALIDATE weekly

3. RBOB (Best for automation):
   ✓ Daily trading data
   ✓ API available (no scraping)
   ✗ Wholesale (not retail)
   → Use as BACKUP

Recommended Strategy:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   • Run this script daily (cron job)
   • Use AAA as primary daily price
   • Validate weekly against EIA
   • Use RBOB as fallback if AAA fails
   • Track all 3 for comparison/validation
""")

print("=" * 80)
print(f"\n✅ Data collection complete!")
print(f"   Run this daily to build historical dataset")
print(f"   Add to cron: 0 9 * * * /path/to/script")
print("=" * 80)
