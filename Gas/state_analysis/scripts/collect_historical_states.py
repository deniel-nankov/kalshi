#!/usr/bin/env python3
"""
HISTORICAL STATE GAS PRICE COLLECTOR

Scrapes historical state gas prices from AAA (Yesterday, Week Ago, Month Ago, Year Ago).
This gives us ~30 days of backdated data to analyze state-level patterns!

Usage:
    python state_analysis/scripts/collect_historical_states.py

This will collect:
- 51 states × 4 time points = 204 historical records
- Dates: Today, Yesterday, Week Ago (~Oct 22), Month Ago (~Sep 29)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import time
import json

# Project structure
PROJECT_ROOT = Path(__file__).parent.parent.parent
STATE_PROJECT = PROJECT_ROOT / 'state_analysis'
DATA_DIR = STATE_PROJECT / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

HISTORICAL_FILE = STATE_PROJECT / 'data' / 'historical_state_prices.csv'
LOG_FILE = STATE_PROJECT / 'data' / 'historical_collection_log.txt'

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

# State consumption weights (EIA data, % of national)
STATE_WEIGHTS = {
    'CA': 0.111, 'TX': 0.094, 'FL': 0.062, 'NY': 0.047, 'PA': 0.041,
    'OH': 0.036, 'IL': 0.035, 'NC': 0.034, 'GA': 0.032, 'MI': 0.031,
    'VA': 0.028, 'NJ': 0.027, 'IN': 0.026, 'TN': 0.024, 'WA': 0.023,
    'AZ': 0.022, 'MO': 0.021, 'MD': 0.020, 'WI': 0.019, 'MN': 0.019,
    'CO': 0.018, 'SC': 0.017, 'AL': 0.017, 'LA': 0.016, 'KY': 0.015,
    'OR': 0.014, 'OK': 0.013, 'CT': 0.012, 'IA': 0.012, 'MS': 0.011,
    'AR': 0.011, 'KS': 0.010, 'NV': 0.010, 'UT': 0.009, 'NM': 0.009,
    'NE': 0.008, 'WV': 0.007, 'ID': 0.007, 'HI': 0.004, 'NH': 0.004,
    'ME': 0.004, 'MT': 0.004, 'RI': 0.003, 'DE': 0.003, 'SD': 0.003,
    'ND': 0.003, 'AK': 0.002, 'VT': 0.002, 'WY': 0.002, 'DC': 0.002
}

def log(message):
    """Log to console and file"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def scrape_state_historical_prices(state_code, state_name):
    """
    Scrape historical prices for a state from AAA.
    Returns dict with: current, yesterday, week_ago, month_ago, year_ago
    """
    url = f'https://gasprices.aaa.com/?state={state_code}'
    
    try:
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        if response.status_code != 200:
            log(f"  ❌ {state_code}: HTTP {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for price data in tables
        # AAA typically uses a table structure like:
        # Current Avg. | $X.XXX
        # Yesterday Avg. | $X.XXX
        # Week Ago Avg. | $X.XXX
        # Month Ago Avg. | $X.XXX
        # Year Ago Avg. | $X.XXX
        
        prices = {}
        
        # Strategy 1: Find price table with time labels
        text = soup.get_text()
        
        # Extract all prices (format: $X.XXX)
        all_prices = re.findall(r'\$(\d\.\d{3})', response.text)
        
        # Look for specific patterns in HTML
        patterns = {
            'current': [
                r'Current\s+Avg[^$]*\$(\d\.\d{3})',
                r'Today[^$]*\$(\d\.\d{3})',
                r'current[^$]*\$(\d\.\d{3})',
            ],
            'yesterday': [
                r'Yesterday\s+Avg[^$]*\$(\d\.\d{3})',
                r'Yesterday[^$]*\$(\d\.\d{3})',
                r'yesterday[^$]*\$(\d\.\d{3})',
            ],
            'week_ago': [
                r'Week\s+Ago\s+Avg[^$]*\$(\d\.\d{3})',
                r'Week\s+Ago[^$]*\$(\d\.\d{3})',
                r'week ago[^$]*\$(\d\.\d{3})',
            ],
            'month_ago': [
                r'Month\s+Ago\s+Avg[^$]*\$(\d\.\d{3})',
                r'Month\s+Ago[^$]*\$(\d\.\d{3})',
                r'month ago[^$]*\$(\d\.\d{3})',
            ],
            'year_ago': [
                r'Year\s+Ago\s+Avg[^$]*\$(\d\.\d{3})',
                r'Year\s+Ago[^$]*\$(\d\.\d{3})',
                r'year ago[^$]*\$(\d\.\d{3})',
            ],
        }
        
        # Try each pattern
        html_lower = response.text.lower()
        for time_label, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, html_lower, re.IGNORECASE)
                if matches:
                    # Take first match
                    price = float(matches[0])
                    if 2.0 <= price <= 7.0:  # Sanity check
                        prices[time_label] = price
                        break
        
        # Validate we got at least current price
        if 'current' not in prices:
            log(f"  ⚠️  {state_code}: Could not extract current price")
            # Fallback: try to find any reasonable price
            if all_prices:
                for p_str in all_prices:
                    p = float(p_str)
                    if 2.0 <= p <= 7.0:
                        prices['current'] = p
                        log(f"  ℹ️  {state_code}: Using fallback current = ${p:.3f}")
                        break
        
        if not prices:
            log(f"  ❌ {state_code}: No valid prices found")
            return None
        
        # Log what we found
        found = [k for k in ['current', 'yesterday', 'week_ago', 'month_ago', 'year_ago'] if k in prices]
        log(f"  ✅ {state_code}: Found {len(found)}/5 points: {', '.join(found)}")
        
        return prices
        
    except requests.exceptions.Timeout:
        log(f"  ⏱️  {state_code}: Timeout (15s)")
        return None
    except Exception as e:
        log(f"  ❌ {state_code}: Error - {str(e)[:100]}")
        return None

def estimate_dates():
    """Estimate dates for historical points"""
    today = datetime.now()
    return {
        'current': today.strftime('%Y-%m-%d'),
        'yesterday': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
        'week_ago': (today - timedelta(days=7)).strftime('%Y-%m-%d'),
        'month_ago': (today - timedelta(days=30)).strftime('%Y-%m-%d'),
        'year_ago': (today - timedelta(days=365)).strftime('%Y-%m-%d'),
    }

def main():
    log("="*70)
    log("HISTORICAL STATE GAS PRICE COLLECTION")
    log("="*70)
    log(f"Collecting: Current, Yesterday, Week Ago, Month Ago, Year Ago")
    log(f"States: {len(STATES)}")
    log(f"Expected records: {len(STATES)} states × ~4 points = ~204 records")
    log("="*70)
    
    # Estimate dates
    dates = estimate_dates()
    log(f"\nEstimated dates:")
    for label, date in dates.items():
        log(f"  {label}: {date}")
    
    # Collect data
    log("\n" + "="*70)
    log("COLLECTING STATE PRICES")
    log("="*70)
    
    all_records = []
    successful_states = 0
    failed_states = []
    
    for i, (state_code, state_name) in enumerate(STATES.items(), 1):
        log(f"\n[{i}/{len(STATES)}] {state_code} ({state_name})")
        
        prices = scrape_state_historical_prices(state_code, state_name)
        
        if prices:
            successful_states += 1
            
            # Create records for each time point
            weight = STATE_WEIGHTS.get(state_code, 0.001)
            
            for time_label in ['current', 'yesterday', 'week_ago', 'month_ago', 'year_ago']:
                if time_label in prices:
                    all_records.append({
                        'date': dates[time_label],
                        'state': state_code,
                        'state_name': state_name,
                        'price': prices[time_label],
                        'consumption_weight': weight,
                        'time_label': time_label,
                    })
        else:
            failed_states.append(state_code)
        
        # Rate limiting
        if i < len(STATES):
            time.sleep(1.5)
    
    # Create DataFrame
    df = pd.DataFrame(all_records)
    
    log("\n" + "="*70)
    log("COLLECTION SUMMARY")
    log("="*70)
    log(f"States collected: {successful_states}/{len(STATES)}")
    log(f"Failed states: {len(failed_states)}")
    if failed_states:
        log(f"  Failed: {', '.join(failed_states)}")
    log(f"Total records: {len(df)}")
    log(f"Records per state (avg): {len(df)/successful_states:.1f}")
    
    # Calculate national averages for each time point
    log("\n" + "="*70)
    log("NATIONAL AVERAGES (VOLUME-WEIGHTED)")
    log("="*70)
    
    for time_label in ['current', 'yesterday', 'week_ago', 'month_ago', 'year_ago']:
        subset = df[df['time_label'] == time_label]
        if len(subset) > 0:
            simple_avg = subset['price'].mean()
            weighted_avg = (subset['price'] * subset['consumption_weight']).sum() / subset['consumption_weight'].sum()
            log(f"{time_label:12s}: ${weighted_avg:.3f} (weighted), ${simple_avg:.3f} (simple), n={len(subset)}")
    
    # Price range analysis
    log("\n" + "="*70)
    log("PRICE RANGES BY TIME PERIOD")
    log("="*70)
    
    for time_label in ['current', 'week_ago', 'month_ago']:
        subset = df[df['time_label'] == time_label]
        if len(subset) > 0:
            log(f"\n{time_label.upper()}:")
            log(f"  Range: ${subset['price'].min():.3f} - ${subset['price'].max():.3f}")
            log(f"  Spread: ${subset['price'].max() - subset['price'].min():.3f}")
            log(f"  Std Dev: ${subset['price'].std():.3f}")
            
            # Top 5 and Bottom 5
            top5 = subset.nlargest(5, 'price')[['state', 'price']]
            bottom5 = subset.nsmallest(5, 'price')[['state', 'price']]
            
            log(f"  Highest: {', '.join([f'{row.state} ${row.price:.3f}' for _, row in top5.iterrows()])}")
            log(f"  Lowest: {', '.join([f'{row.state} ${row.price:.3f}' for _, row in bottom5.iterrows()])}")
    
    # Save to CSV
    output_file = STATE_PROJECT / 'data' / 'historical_state_snapshot.csv'
    df.to_csv(output_file, index=False)
    log(f"\n✅ Saved {len(df)} records to: {output_file}")
    
    # Also append to main historical file
    if HISTORICAL_FILE.exists():
        existing = pd.read_csv(HISTORICAL_FILE)
        # Remove duplicates (same date + state)
        combined = pd.concat([existing, df], ignore_index=True)
        combined = combined.drop_duplicates(subset=['date', 'state'], keep='last')
        combined = combined.sort_values(['date', 'state'])
        combined.to_csv(HISTORICAL_FILE, index=False)
        log(f"✅ Updated main historical file: {HISTORICAL_FILE}")
        log(f"   Total unique records: {len(combined)}")
    else:
        df_sorted = df.sort_values(['date', 'state'])
        df_sorted.to_csv(HISTORICAL_FILE, index=False)
        log(f"✅ Created main historical file: {HISTORICAL_FILE}")
    
    # Summary stats
    log("\n" + "="*70)
    log("DATASET SUMMARY")
    log("="*70)
    log(f"Unique dates: {df['date'].nunique()}")
    log(f"Unique states: {df['state'].nunique()}")
    log(f"Date range: {df['date'].min()} to {df['date'].max()}")
    log(f"Average records per date: {len(df)/df['date'].nunique():.1f}")
    
    # Check if we have enough for analysis
    unique_dates = df['date'].nunique()
    if unique_dates >= 4:
        log("\n✅ SUCCESS! We have ~30 days of coverage (4 time points)")
        log("   Ready for:")
        log("   • Correlation analysis (states vs national)")
        log("   • Price change analysis (week-over-week, month-over-month)")
        log("   • Regional trend identification")
        log("\n⚠️  NOTE: For Granger causality (leading indicators), we need:")
        log("   • Daily data (not just 4 snapshots)")
        log("   • Minimum 30 consecutive days")
        log("   • Continue daily collection for full analysis")
    else:
        log(f"\n⚠️  Limited data: Only {unique_dates} time points")
        log("   Continue daily collection for full 30-day dataset")
    
    log("\n" + "="*70)
    log("COLLECTION COMPLETE!")
    log("="*70)

if __name__ == '__main__':
    main()
