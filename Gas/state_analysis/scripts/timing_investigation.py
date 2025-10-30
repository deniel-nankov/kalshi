"""
Timing Investigation: AAA State Update Schedule Analysis

Goal: Determine if negative state-national correlations are due to timing artifacts
      (i.e., AAA updates different states at different times of day)

Method: Scrape key states every 2 hours for 24 hours, record exact timestamps
        of price changes to identify update schedule

Author: Research Team
Date: October 29, 2025
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import pandas as pd
import time
import json
from pathlib import Path

# Test states (representative sample)
TEST_STATES = {
    'CA': 'California',      # West Coast, 11.1% weight
    'TX': 'Texas',           # Gulf, 9.4% weight
    'FL': 'Florida',         # Southeast, 6.2% weight
    'NY': 'New York',        # Northeast, 4.7% weight
    'IL': 'Illinois',        # Midwest, 3.5% weight
}

# Base URL for AAA state pages
BASE_URL = "https://gasprices.aaa.com/state-gas-price-averages/"


def extract_state_price(state_abbr: str) -> dict:
    """
    Extract current gas price and all displayed time points for a state
    
    Returns dict with:
        - timestamp: when scraped
        - state: state abbreviation
        - current: current price
        - yesterday: yesterday price (if available)
        - week_ago: week ago price (if available)
        - month_ago: month ago price (if available)
        - success: bool
    """
    url = BASE_URL
    
    try:
        # Make request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find table rows
        rows = soup.find_all('tr')
        
        # Extract prices for this state
        state_data = {
            'timestamp': datetime.now().isoformat(),
            'state': state_abbr,
            'current': None,
            'yesterday': None,
            'week_ago': None,
            'month_ago': None,
            'year_ago': None,
            'success': False,
        }
        
        for row in rows:
            # Check if this row is for our state
            cells = row.find_all('td')
            if not cells:
                continue
                
            # First cell should contain state name
            state_cell = cells[0].get_text(strip=True)
            if state_abbr.lower() in state_cell.lower() or TEST_STATES.get(state_abbr, '').lower() in state_cell.lower():
                # Extract all prices from this row
                # Typical structure: State | Current | Yesterday | Week Ago | Month Ago | Year Ago
                if len(cells) >= 2:
                    state_data['current'] = cells[1].get_text(strip=True).replace('$', '')
                if len(cells) >= 3:
                    state_data['yesterday'] = cells[2].get_text(strip=True).replace('$', '')
                if len(cells) >= 4:
                    state_data['week_ago'] = cells[3].get_text(strip=True).replace('$', '')
                if len(cells) >= 5:
                    state_data['month_ago'] = cells[4].get_text(strip=True).replace('$', '')
                if len(cells) >= 6:
                    state_data['year_ago'] = cells[5].get_text(strip=True).replace('$', '')
                
                state_data['success'] = True
                break
        
        return state_data
        
    except Exception as e:
        print(f"❌ Error scraping {state_abbr}: {e}")
        return {
            'timestamp': datetime.now().isoformat(),
            'state': state_abbr,
            'current': None,
            'yesterday': None,
            'week_ago': None,
            'month_ago': None,
            'year_ago': None,
            'success': False,
            'error': str(e),
        }


def extract_national_price() -> dict:
    """
    Extract national average gas price
    """
    url = BASE_URL
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for "National Average" or "U.S. Average"
        national_data = {
            'timestamp': datetime.now().isoformat(),
            'entity': 'National',
            'current': None,
            'yesterday': None,
            'week_ago': None,
            'month_ago': None,
            'year_ago': None,
            'success': False,
        }
        
        # Try to find national average in table
        rows = soup.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if not cells:
                continue
            
            text = cells[0].get_text(strip=True).lower()
            if 'national' in text or 'u.s.' in text or 'average' in text:
                if len(cells) >= 2:
                    national_data['current'] = cells[1].get_text(strip=True).replace('$', '')
                if len(cells) >= 3:
                    national_data['yesterday'] = cells[2].get_text(strip=True).replace('$', '')
                if len(cells) >= 4:
                    national_data['week_ago'] = cells[3].get_text(strip=True).replace('$', '')
                if len(cells) >= 5:
                    national_data['month_ago'] = cells[4].get_text(strip=True).replace('$', '')
                if len(cells) >= 6:
                    national_data['year_ago'] = cells[5].get_text(strip=True).replace('$', '')
                
                national_data['success'] = True
                break
        
        return national_data
        
    except Exception as e:
        print(f"❌ Error scraping national: {e}")
        return {
            'timestamp': datetime.now().isoformat(),
            'entity': 'National',
            'current': None,
            'success': False,
            'error': str(e),
        }


def run_timing_check():
    """
    Run a single timing check for all test states + national
    """
    timestamp = datetime.now()
    print(f"\n{'='*60}")
    print(f"🕐 Timing Check: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    results = []
    
    # Scrape national
    print(f"\n📊 National Average:")
    national_data = extract_national_price()
    if national_data['success']:
        print(f"   Current: ${national_data['current']}")
        print(f"   Yesterday: ${national_data.get('yesterday', 'N/A')}")
        print(f"   Week Ago: ${national_data.get('week_ago', 'N/A')}")
        print(f"   Month Ago: ${national_data.get('month_ago', 'N/A')}")
    results.append(national_data)
    
    # Scrape states
    for state_abbr, state_name in TEST_STATES.items():
        print(f"\n🏛️  {state_name} ({state_abbr}):")
        state_data = extract_state_price(state_abbr)
        
        if state_data['success']:
            print(f"   Current: ${state_data['current']}")
            print(f"   Yesterday: ${state_data.get('yesterday', 'N/A')}")
            print(f"   Week Ago: ${state_data.get('week_ago', 'N/A')}")
            print(f"   Month Ago: ${state_data.get('month_ago', 'N/A')}")
        else:
            print(f"   ❌ Failed to extract")
        
        results.append(state_data)
        time.sleep(1)  # Be polite
    
    return results


def run_24hour_monitoring(interval_hours: int = 2):
    """
    Run timing checks every N hours for 24 hours
    
    Args:
        interval_hours: Hours between checks (default 2)
    """
    output_dir = Path('state_analysis/outputs')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / 'timing_monitoring.json'
    
    all_results = []
    checks_remaining = 24 // interval_hours + 1  # +1 for initial check
    
    print(f"\n{'='*60}")
    print(f"🔬 24-HOUR TIMING INVESTIGATION")
    print(f"{'='*60}")
    print(f"Interval: Every {interval_hours} hours")
    print(f"Total checks: {checks_remaining}")
    print(f"Duration: 24 hours")
    print(f"Output: {output_file}")
    print(f"{'='*60}\n")
    
    for i in range(checks_remaining):
        check_num = i + 1
        print(f"\n{'='*60}")
        print(f"CHECK {check_num}/{checks_remaining}")
        print(f"{'='*60}")
        
        # Run check
        results = run_timing_check()
        all_results.extend(results)
        
        # Save after each check (in case of interruption)
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\n✅ Check {check_num} complete. Results saved to {output_file}")
        
        # Wait for next check (unless this is the last one)
        if i < checks_remaining - 1:
            wait_seconds = interval_hours * 3600
            next_check = datetime.now() + timedelta(seconds=wait_seconds)
            print(f"\n⏰ Next check in {interval_hours} hours at {next_check.strftime('%H:%M:%S')}")
            print(f"   (You can stop with Ctrl+C)")
            time.sleep(wait_seconds)
    
    print(f"\n{'='*60}")
    print(f"✅ 24-HOUR MONITORING COMPLETE!")
    print(f"{'='*60}")
    print(f"Total records collected: {len(all_results)}")
    print(f"Output file: {output_file}")
    
    return all_results


def analyze_timing_results(results_file: str = 'state_analysis/outputs/timing_monitoring.json'):
    """
    Analyze timing monitoring results to identify update patterns
    """
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    df = pd.DataFrame(results)
    
    print(f"\n{'='*60}")
    print(f"📊 TIMING ANALYSIS RESULTS")
    print(f"{'='*60}\n")
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    
    # Group by state/national
    for entity in df['state'].unique():
        if pd.isna(entity):
            continue
            
        entity_df = df[df['state'] == entity].copy()
        
        print(f"\n{entity}:")
        print(f"  Total checks: {len(entity_df)}")
        print(f"  Successful: {entity_df['success'].sum()}")
        
        # Check if current price changed
        if 'current' in entity_df.columns:
            entity_df['current_numeric'] = pd.to_numeric(entity_df['current'], errors='coerce')
            price_changes = entity_df['current_numeric'].diff().abs()
            num_changes = (price_changes > 0.001).sum()  # Changed by more than $0.001
            
            if num_changes > 0:
                change_times = entity_df[price_changes > 0.001]['timestamp'].tolist()
                print(f"  Price changes detected: {num_changes}")
                print(f"  Change times: {[t.strftime('%H:%M') for t in change_times]}")
            else:
                print(f"  Price changes detected: 0 (stable)")
    
    print(f"\n{'='*60}")
    print(f"INTERPRETATION:")
    print(f"{'='*60}")
    print(f"If all states change at same time → Correlations are REAL")
    print(f"If states change at different times → Timing artifacts (need lag adjustment)")
    print(f"{'='*60}\n")


def run_quick_test():
    """
    Quick test: Single scrape of all states to verify functionality
    """
    print(f"\n{'='*60}")
    print(f"🧪 QUICK TEST: Single Scrape")
    print(f"{'='*60}\n")
    
    results = run_timing_check()
    
    # Save results
    output_dir = Path('state_analysis/outputs')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'timing_quick_test.json'
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Quick test complete!")
    print(f"Results saved to: {output_file}")
    print(f"\nTo run 24-hour monitoring, use: run_24hour_monitoring(interval_hours=2)")
    
    return results


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--24hour':
        # Run 24-hour monitoring
        interval = 2  # hours
        if len(sys.argv) > 2:
            interval = int(sys.argv[2])
        
        run_24hour_monitoring(interval_hours=interval)
    
    elif len(sys.argv) > 1 and sys.argv[1] == '--analyze':
        # Analyze existing results
        results_file = 'state_analysis/outputs/timing_monitoring.json'
        if len(sys.argv) > 2:
            results_file = sys.argv[2]
        
        analyze_timing_results(results_file)
    
    else:
        # Run quick test
        print("\nUsage:")
        print("  Quick test:      python timing_investigation.py")
        print("  24-hour monitor: python timing_investigation.py --24hour [interval_hours]")
        print("  Analyze results: python timing_investigation.py --analyze [results_file]")
        print("\nRunning quick test...\n")
        
        run_quick_test()
