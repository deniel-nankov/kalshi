#!/usr/bin/env python3
"""
State-Level Gas Price Analysis

Research Questions:
1. Which states drive the national average most?
2. Do some states lead national prices (early indicators)?
3. Is there correlation between state increases → national increase?

Data Source: AAA state-level gas prices
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import re
import time

# Output
OUTPUT_DIR = Path(__file__).parent.parent / 'outputs' / 'state_analysis'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# All 50 US states + DC
STATES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia'
}

# Gasoline consumption by state (2024 estimate - thousand barrels per day)
STATE_CONSUMPTION = {
    'CA': 14.5, 'TX': 12.3, 'FL': 8.1, 'NY': 6.2, 'PA': 5.4,
    'IL': 4.9, 'OH': 4.7, 'NC': 4.3, 'GA': 4.2, 'MI': 4.0,
    'VA': 3.8, 'NJ': 3.6, 'TN': 3.4, 'IN': 3.2, 'AZ': 3.0,
    'MA': 2.8, 'WA': 2.7, 'MO': 2.6, 'WI': 2.5, 'MD': 2.4,
    'MN': 2.3, 'CO': 2.2, 'AL': 2.1, 'SC': 2.0, 'LA': 1.9,
    'KY': 1.8, 'OR': 1.7, 'OK': 1.6, 'CT': 1.5, 'IA': 1.4,
    'MS': 1.3, 'AR': 1.2, 'KS': 1.1, 'UT': 1.0, 'NV': 0.9,
    'NM': 0.8, 'NE': 0.8, 'WV': 0.7, 'ID': 0.7, 'HI': 0.6,
    'NH': 0.6, 'ME': 0.6, 'RI': 0.5, 'MT': 0.5, 'DE': 0.4,
    'SD': 0.4, 'ND': 0.4, 'AK': 0.3, 'VT': 0.3, 'WY': 0.3, 'DC': 0.1
}

print("=" * 80)
print("🗺️  STATE-LEVEL GAS PRICE ANALYSIS")
print("=" * 80)
print(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"States to analyze: {len(STATES)}")
print("\n" + "=" * 80)

# ============================================================================
# STEP 1: Scrape Current State Prices
# ============================================================================
print("\nSTEP 1: SCRAPE CURRENT STATE PRICES")
print("=" * 80)

def scrape_state_price(state_code):
    """Scrape AAA price for a specific state"""
    url = f"https://gasprices.aaa.com/?state={state_code}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Look for price pattern
        patterns = [
            rf'{STATES[state_code]}.*?\$(\d+\.\d{{2,3}})',  # "California $3.456"
            r'\$(\d+\.\d{2,3})',  # Any price
            r'Regular.*?\$(\d+\.\d{2,3})'  # "Regular $3.45"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response.text)
            if match:
                return float(match.group(1))
        
        return None
        
    except Exception as e:
        print(f"   ⚠️  {state_code}: {e}")
        return None

# Scrape all states
state_prices = {}
print("\n📡 Scraping AAA state prices (this takes ~2 minutes)...\n")

for i, (state_code, state_name) in enumerate(STATES.items(), 1):
    price = scrape_state_price(state_code)
    
    if price:
        state_prices[state_code] = price
        print(f"   [{i:2d}/51] {state_code} ({state_name:<20}): ${price:.3f}")
    else:
        print(f"   [{i:2d}/51] {state_code} ({state_name:<20}): ❌ Failed")
    
    # Rate limiting (don't hammer AAA)
    time.sleep(1)

print(f"\n✅ Successfully scraped: {len(state_prices)}/51 states")

# Save today's snapshot
today = datetime.now().strftime('%Y-%m-%d')
snapshot_df = pd.DataFrame([
    {'date': today, 'state': code, 'price': price}
    for code, price in state_prices.items()
])
snapshot_df.to_csv(OUTPUT_DIR / f'state_prices_{today}.csv', index=False)
print(f"💾 Saved: {OUTPUT_DIR / f'state_prices_{today}.csv'}")

# ============================================================================
# STEP 2: Calculate National Average (Volume-Weighted)
# ============================================================================
print("\n" + "=" * 80)
print("STEP 2: CALCULATE NATIONAL AVERAGE")
print("=" * 80)

# Simple average
simple_avg = np.mean(list(state_prices.values()))

# Volume-weighted average
total_consumption = sum([STATE_CONSUMPTION.get(s, 1.0) for s in state_prices.keys()])
weighted_avg = sum([
    price * STATE_CONSUMPTION.get(state, 1.0) / total_consumption
    for state, price in state_prices.items()
])

print(f"\n   Simple Average (all states equal): ${simple_avg:.3f}")
print(f"   Volume-Weighted Average: ${weighted_avg:.3f}")
print(f"   Difference: ${abs(weighted_avg - simple_avg):.3f}")

# ============================================================================
# STEP 3: Identify High-Impact States
# ============================================================================
print("\n" + "=" * 80)
print("STEP 3: WHICH STATES DRIVE NATIONAL AVERAGE?")
print("=" * 80)

# Calculate each state's contribution to national average
state_impacts = []

for state, price in state_prices.items():
    consumption = STATE_CONSUMPTION.get(state, 1.0)
    contribution = (price * consumption) / total_consumption
    impact_pct = (consumption / total_consumption) * 100
    
    state_impacts.append({
        'state': state,
        'price': price,
        'consumption': consumption,
        'contribution': contribution,
        'impact_pct': impact_pct
    })

impact_df = pd.DataFrame(state_impacts).sort_values('impact_pct', ascending=False)

print("\n   Top 10 States by Impact on National Average:\n")
print(f"   {'Rank':<6} {'State':<6} {'Price':<10} {'Consumption':<15} {'Impact %':<10}")
print("   " + "-" * 60)

for i, row in impact_df.head(10).iterrows():
    print(f"   {impact_df.index.get_loc(i)+1:<6} {row['state']:<6} "
          f"${row['price']:<9.3f} {row['consumption']:<15.1f} {row['impact_pct']:<9.2f}%")

top_10_impact = impact_df.head(10)['impact_pct'].sum()
print(f"\n   Top 10 states = {top_10_impact:.1f}% of national average")

# ============================================================================
# STEP 4: Price Distribution Analysis
# ============================================================================
print("\n" + "=" * 80)
print("STEP 4: PRICE DISTRIBUTION")
print("=" * 80)

prices = list(state_prices.values())
print(f"\n   Range: ${min(prices):.3f} - ${max(prices):.3f}")
print(f"   Spread: ${max(prices) - min(prices):.3f}")
print(f"   Median: ${np.median(prices):.3f}")
print(f"   Std Dev: ${np.std(prices):.3f}")

# Highest and lowest
impact_df_sorted_price = impact_df.sort_values('price', ascending=False)

print(f"\n   Top 5 Most Expensive:")
for _, row in impact_df_sorted_price.head(5).iterrows():
    print(f"      {row['state']}: ${row['price']:.3f} (Impact: {row['impact_pct']:.2f}%)")

print(f"\n   Top 5 Cheapest:")
for _, row in impact_df_sorted_price.tail(5).iterrows():
    print(f"      {row['state']}: ${row['price']:.3f} (Impact: {row['impact_pct']:.2f}%)")

# ============================================================================
# STEP 5: What-If Analysis
# ============================================================================
print("\n" + "=" * 80)
print("STEP 5: WHAT-IF ANALYSIS")
print("=" * 80)

print("\n   Question: If California increases $0.10, how much does national average increase?\n")

# Recalculate with CA +$0.10
ca_original = state_prices.get('CA', weighted_avg)
ca_new = ca_original + 0.10

new_weighted_avg = weighted_avg - (ca_original * STATE_CONSUMPTION['CA'] / total_consumption) + (ca_new * STATE_CONSUMPTION['CA'] / total_consumption)

ca_impact = new_weighted_avg - weighted_avg

print(f"      Original CA price: ${ca_original:.3f}")
print(f"      New CA price: ${ca_new:.3f} (+$0.10)")
print(f"      Original national: ${weighted_avg:.3f}")
print(f"      New national: ${new_weighted_avg:.3f}")
print(f"      National increase: ${ca_impact:.4f} ({(ca_impact/weighted_avg*100):.2f}%)")

# Same for Texas
tx_original = state_prices.get('TX', weighted_avg)
tx_new = tx_original + 0.10
new_weighted_avg_tx = weighted_avg - (tx_original * STATE_CONSUMPTION['TX'] / total_consumption) + (tx_new * STATE_CONSUMPTION['TX'] / total_consumption)
tx_impact = new_weighted_avg_tx - weighted_avg

print(f"\n   Question: If Texas increases $0.10, how much does national average increase?\n")
print(f"      Original TX price: ${tx_original:.3f}")
print(f"      New TX price: ${tx_new:.3f} (+$0.10)")
print(f"      National increase: ${tx_impact:.4f} ({(tx_impact/weighted_avg*100):.2f}%)")

# ============================================================================
# STEP 6: Leading Indicator Analysis (Requires Historical Data)
# ============================================================================
print("\n" + "=" * 80)
print("STEP 6: LEADING INDICATOR TEST")
print("=" * 80)

print("""
To test if states lead national average, we need:
  • 30+ days of historical state prices (all 50 states)
  • 30+ days of national average
  • Cross-correlation analysis at different lags
  
Example: Does California price on Monday predict national price on Tuesday?

Next steps:
  1. Run this script daily for 30 days → Build historical dataset
  2. Run Granger causality test: state(t-1) → national(t)
  3. Identify leading states (if any)
  
Current status: Only 1 day of data collected (today)
Needed: 29 more days to test leading indicators

Would you like to:
  a) Set up daily cron job to collect state prices automatically?
  b) Manually run this daily for next 30 days?
  c) Wait until after Oct 31 Kalshi deadline?
""")

# ============================================================================
# SAVE SUMMARY
# ============================================================================
impact_df.to_csv(OUTPUT_DIR / 'state_impact_analysis.csv', index=False)
print(f"\n💾 Saved full analysis: {OUTPUT_DIR / 'state_impact_analysis.csv'}")

print("\n" + "=" * 80)
print("✅ STATE ANALYSIS COMPLETE!")
print("=" * 80)

print(f"""
📊 Summary:
  • States scraped: {len(state_prices)}/51
  • National average (volume-weighted): ${weighted_avg:.3f}
  • Top driver: {impact_df.iloc[0]['state']} ({impact_df.iloc[0]['impact_pct']:.2f}% impact)
  • Price range: ${min(prices):.3f} - ${max(prices):.3f} (${max(prices)-min(prices):.3f} spread)
  
Key Findings:
  • Top 10 states = {top_10_impact:.1f}% of national average
  • CA +$0.10 → National +${ca_impact:.4f} ({(ca_impact/weighted_avg*100):.2f}%)
  • TX +$0.10 → National +${tx_impact:.4f} ({(tx_impact/weighted_avg*100):.2f}%)
  
Next Steps:
  • Collect 30 days of state data to test leading indicators
  • Run correlation analysis (which states move together?)
  • Test Granger causality (do states lead national?)

Files saved:
  • {OUTPUT_DIR / f'state_prices_{today}.csv'}
  • {OUTPUT_DIR / 'state_impact_analysis.csv'}
""")

print("=" * 80)
