#!/usr/bin/env python3
"""
DAILY STATE GAS PRICE COLLECTOR - SIDE PROJECT

Collects gas prices for all 50 states + DC from AAA Daily Fuel Gauge.
Runs daily at 9:30 AM EST (after AAA updates at 9 AM).

This is ISOLATED from the main Oct 31 forecast system.
All data saved to state_analysis/ directory only.

Usage:
    python state_analysis/scripts/collect_state_prices.py

Cron (9:30 AM daily):
    30 9 * * * cd /path/to/Gas && /path/to/.venv/bin/python state_analysis/scripts/collect_state_prices.py
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import requests
import re
from datetime import datetime
import time
import json

# Project structure
PROJECT_ROOT = Path(__file__).parent.parent.parent
STATE_PROJECT = PROJECT_ROOT / 'state_analysis'
DATA_DIR = STATE_PROJECT / 'data' / 'daily_snapshots'
DATA_DIR.mkdir(parents=True, exist_ok=True)

COMBINED_FILE = STATE_PROJECT / 'data' / 'historical_state_prices.csv'
LOG_FILE = STATE_PROJECT / 'data' / 'collection_log.txt'

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

# Gasoline consumption weights (% of US total, 2024 estimate)
CONSUMPTION_WEIGHTS = {
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

def log(message, level='INFO'):
    """Log to file and console"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] [{level}] {message}"
    print(log_msg)
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def scrape_state_price(state_code, retry=3):
    """
    Scrape AAA gas price for a specific state.
    
    Args:
        state_code: Two-letter state code (e.g., 'CA', 'TX')
        retry: Number of retry attempts
        
    Returns:
        float: Price in $/gallon, or None if failed
    """
    url = f"https://gasprices.aaa.com/?state={state_code}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    for attempt in range(retry):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Try multiple regex patterns to find price
            patterns = [
                # Pattern 1: State name followed by price
                rf'{STATES[state_code]}.*?\$(\d+\.\d{{2,3}})',
                # Pattern 2: "Regular" followed by price
                r'Regular.*?\$(\d+\.\d{2,3})',
                # Pattern 3: Any price pattern
                r'\$(\d+\.\d{3})',
                r'\$(\d+\.\d{2})',
                # Pattern 4: JSON data (if embedded)
                r'"price":\s*"?\$?(\d+\.\d{2,3})"?',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response.text, re.IGNORECASE)
                if match:
                    price = float(match.group(1))
                    # Sanity check (gas prices typically $2-$6/gal)
                    if 2.0 <= price <= 6.0:
                        return price
            
            # If no match, log HTML snippet for debugging
            if attempt == retry - 1:
                snippet = response.text[:500]
                log(f"   {state_code}: No price found. HTML snippet: {snippet[:100]}...", 'DEBUG')
            
        except requests.RequestException as e:
            if attempt == retry - 1:
                log(f"   {state_code}: Request failed after {retry} attempts: {e}", 'ERROR')
            time.sleep(2 ** attempt)  # Exponential backoff
        
        except Exception as e:
            log(f"   {state_code}: Unexpected error: {e}", 'ERROR')
            break
    
    return None

def calculate_national_average(state_prices):
    """
    Calculate volume-weighted national average from state prices.
    
    Args:
        state_prices: dict {state_code: price}
        
    Returns:
        dict: {'simple': simple_avg, 'weighted': weighted_avg}
    """
    prices = list(state_prices.values())
    
    # Simple average (all states equal weight)
    simple_avg = np.mean(prices)
    
    # Volume-weighted average
    total_weight = sum([CONSUMPTION_WEIGHTS.get(s, 1.0) for s in state_prices.keys()])
    weighted_avg = sum([
        price * CONSUMPTION_WEIGHTS.get(state, 1.0) / total_weight
        for state, price in state_prices.items()
    ])
    
    return {
        'simple': simple_avg,
        'weighted': weighted_avg,
        'n_states': len(state_prices)
    }

def main():
    """Main collection routine"""
    
    log("=" * 80)
    log("🗺️  STATE GAS PRICE COLLECTOR - SIDE PROJECT")
    log("=" * 80)
    
    today = datetime.now().strftime('%Y-%m-%d')
    log(f"Collection date: {today}")
    log(f"States to collect: {len(STATES)}")
    
    # ========================================================================
    # STEP 1: Scrape All States
    # ========================================================================
    log("\nSTEP 1: SCRAPING STATE PRICES")
    log("-" * 80)
    
    state_prices = {}
    failed_states = []
    
    for i, (state_code, state_name) in enumerate(STATES.items(), 1):
        log(f"   [{i:2d}/51] Scraping {state_code} ({state_name})...")
        
        price = scrape_state_price(state_code)
        
        if price:
            state_prices[state_code] = price
            log(f"      ✅ ${price:.3f}", 'SUCCESS')
        else:
            failed_states.append(state_code)
            log(f"      ❌ Failed", 'WARNING')
        
        # Rate limiting (be nice to AAA servers)
        if i < len(STATES):
            time.sleep(1.5)  # 1.5 seconds between requests
    
    success_rate = len(state_prices) / len(STATES) * 100
    log(f"\n✅ Successfully collected: {len(state_prices)}/51 states ({success_rate:.1f}%)")
    
    if failed_states:
        log(f"⚠️  Failed states: {', '.join(failed_states)}", 'WARNING')
    
    if len(state_prices) < 30:
        log("❌ ERROR: Less than 30 states collected. Aborting.", 'ERROR')
        return False
    
    # ========================================================================
    # STEP 2: Calculate National Average
    # ========================================================================
    log("\nSTEP 2: CALCULATE NATIONAL AVERAGE")
    log("-" * 80)
    
    national = calculate_national_average(state_prices)
    
    log(f"   Simple average: ${national['simple']:.3f}")
    log(f"   Volume-weighted: ${national['weighted']:.3f}")
    log(f"   Difference: ${abs(national['weighted'] - national['simple']):.3f}")
    
    # ========================================================================
    # STEP 3: Save Daily Snapshot
    # ========================================================================
    log("\nSTEP 3: SAVE DAILY SNAPSHOT")
    log("-" * 80)
    
    # Create snapshot DataFrame
    snapshot_records = []
    for state_code, price in state_prices.items():
        snapshot_records.append({
            'date': today,
            'state': state_code,
            'state_name': STATES[state_code],
            'price': price,
            'consumption_weight': CONSUMPTION_WEIGHTS.get(state_code, 1.0)
        })
    
    snapshot_df = pd.DataFrame(snapshot_records)
    
    # Save individual snapshot
    snapshot_file = DATA_DIR / f'state_prices_{today}.csv'
    snapshot_df.to_csv(snapshot_file, index=False)
    log(f"   ✅ Saved: {snapshot_file}")
    
    # ========================================================================
    # STEP 4: Update Combined Historical File
    # ========================================================================
    log("\nSTEP 4: UPDATE HISTORICAL FILE")
    log("-" * 80)
    
    # Load existing historical data (if exists)
    if COMBINED_FILE.exists():
        historical_df = pd.read_csv(COMBINED_FILE)
        historical_df['date'] = pd.to_datetime(historical_df['date']).dt.strftime('%Y-%m-%d')
        
        # Remove today's data if already exists (overwrite)
        historical_df = historical_df[historical_df['date'] != today]
        
        # Append today's data
        combined_df = pd.concat([historical_df, snapshot_df], ignore_index=True)
        
        days_collected = combined_df['date'].nunique()
        log(f"   Existing historical data: {len(historical_df)} records")
        log(f"   Added today: {len(snapshot_df)} records")
        log(f"   Total days collected: {days_collected}")
        
    else:
        combined_df = snapshot_df
        log(f"   New historical file created")
        log(f"   Records: {len(combined_df)}")
    
    # Sort by date and state
    combined_df = combined_df.sort_values(['date', 'state']).reset_index(drop=True)
    
    # Save
    combined_df.to_csv(COMBINED_FILE, index=False)
    log(f"   ✅ Saved: {COMBINED_FILE}")
    
    # ========================================================================
    # STEP 5: Save Summary Statistics
    # ========================================================================
    log("\nSTEP 5: SAVE SUMMARY STATISTICS")
    log("-" * 80)
    
    summary = {
        'date': today,
        'n_states_collected': len(state_prices),
        'n_states_failed': len(failed_states),
        'success_rate': success_rate,
        'simple_avg': national['simple'],
        'weighted_avg': national['weighted'],
        'min_price': min(state_prices.values()),
        'max_price': max(state_prices.values()),
        'min_state': min(state_prices, key=state_prices.get),
        'max_state': max(state_prices, key=state_prices.get),
        'price_spread': max(state_prices.values()) - min(state_prices.values()),
        'failed_states': ','.join(failed_states) if failed_states else 'none'
    }
    
    summary_file = STATE_PROJECT / 'data' / 'daily_summaries.json'
    
    # Load existing summaries
    if summary_file.exists():
        with open(summary_file, 'r') as f:
            summaries = json.load(f)
    else:
        summaries = []
    
    # Add today's summary
    summaries.append(summary)
    
    # Save
    with open(summary_file, 'w') as f:
        json.dump(summaries, f, indent=2)
    
    log(f"   ✅ Saved: {summary_file}")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    log("\n" + "=" * 80)
    log("✅ COLLECTION COMPLETE!")
    log("=" * 80)
    
    log(f"""
Summary for {today}:
  • States collected: {len(state_prices)}/51 ({success_rate:.1f}%)
  • National average: ${national['weighted']:.3f} (volume-weighted)
  • Price range: ${min(state_prices.values()):.3f} - ${max(state_prices.values()):.3f}
  • Cheapest: {min(state_prices, key=state_prices.get)} (${state_prices[min(state_prices, key=state_prices.get)]:.3f})
  • Most expensive: {max(state_prices, key=state_prices.get)} (${state_prices[max(state_prices, key=state_prices.get)]:.3f})
  
Files saved:
  • Daily snapshot: {snapshot_file}
  • Historical data: {COMBINED_FILE}
  • Summary stats: {summary_file}
  
Total days collected: {combined_df['date'].nunique()}

Next steps:
  • Need 30 days for analysis (currently: {combined_df['date'].nunique()})
  • Run correlation analysis after 30 days
  • Test leading indicators (Granger causality)
""")
    
    log("=" * 80)
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        log(f"FATAL ERROR: {e}", 'ERROR')
        import traceback
        log(traceback.format_exc(), 'ERROR')
        sys.exit(1)
