#!/usr/bin/env python3
"""
AAA HISTORICAL DATA INVESTIGATOR
Run this AFTER Oct 31 submission to see if we can scrape past 30 days!

Usage:
    python state_analysis/scripts/investigate_aaa_history.py
"""

import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

print("="*70)
print("🔍 AAA HISTORICAL DATA INVESTIGATION")
print("="*70)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Purpose: Determine if AAA provides historical state-level data")
print("="*70)

def investigate_aaa_state_page(state_code, state_name):
    """Check what historical data is available for a state"""
    
    print(f"\n📍 {state_code} ({state_name})")
    print("-" * 60)
    
    # Try different URL patterns AAA might use
    urls_to_try = [
        f'https://gasprices.aaa.com/?state={state_code}',
        f'https://gasprices.aaa.com/state/{state_code.lower()}',
        f'https://gasprices.aaa.com/{state_code}',
    ]
    
    for url in urls_to_try:
        try:
            print(f"  Trying: {url}")
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text().lower()
                
                # Look for historical indicators
                findings = {
                    'url': url,
                    'status': 'SUCCESS',
                    'has_current': 'current' in text or 'today' in text,
                    'has_yesterday': 'yesterday' in text,
                    'has_week_ago': 'week ago' in text,
                    'has_month_ago': 'month ago' in text,
                    'has_year_ago': 'year ago' in text,
                    'has_chart': 'chart' in text or 'graph' in text,
                    'has_archive': 'archive' in text or 'history' in text or 'historical' in text,
                    'has_download': 'download' in text or 'export' in text or 'csv' in text,
                }
                
                # Try to find price tables or structured data
                tables = soup.find_all('table')
                findings['num_tables'] = len(tables)
                
                # Look for date patterns (might indicate historical data)
                date_patterns = [
                    r'\d{1,2}/\d{1,2}/\d{2,4}',  # 10/29/25 or 10/29/2025
                    r'\d{4}-\d{2}-\d{2}',        # 2025-10-29
                    r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}',  # Oct 29
                ]
                
                dates_found = []
                for pattern in date_patterns:
                    dates_found.extend(re.findall(pattern, text))
                findings['dates_found'] = len(dates_found)
                findings['sample_dates'] = list(set(dates_found))[:5]
                
                # Try to extract prices (AAA format: $X.XXX)
                price_pattern = r'\$\d\.\d{3}'
                prices = re.findall(price_pattern, response.text)  # Use raw HTML for accuracy
                findings['prices_found'] = len(prices)
                findings['unique_prices'] = len(set(prices))
                findings['sample_prices'] = list(set(prices))[:5]
                
                # Print findings
                print(f"  ✅ SUCCESS: {url}")
                print(f"     Current price: {'✅' if findings['has_current'] else '❌'}")
                print(f"     Yesterday: {'✅' if findings['has_yesterday'] else '❌'}")
                print(f"     Week ago: {'✅' if findings['has_week_ago'] else '❌'}")
                print(f"     Month ago: {'✅' if findings['has_month_ago'] else '❌'}")
                print(f"     Year ago: {'✅' if findings['has_year_ago'] else '❌'}")
                print(f"     Charts/Graphs: {'✅' if findings['has_chart'] else '❌'}")
                print(f"     Archive/History: {'✅' if findings['has_archive'] else '❌'}")
                print(f"     Download option: {'✅' if findings['has_download'] else '❌'}")
                print(f"     Tables found: {findings['num_tables']}")
                print(f"     Dates found: {findings['dates_found']}")
                if findings['sample_dates']:
                    print(f"     Sample dates: {', '.join(findings['sample_dates'][:3])}")
                print(f"     Prices found: {findings['prices_found']} ({findings['unique_prices']} unique)")
                if findings['sample_prices']:
                    print(f"     Sample prices: {', '.join(findings['sample_prices'][:3])}")
                
                return findings
            
            elif response.status_code == 404:
                print(f"  ❌ 404 Not Found")
            else:
                print(f"  ⚠️  Status {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"  ⏱️  Timeout (10s)")
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:50]}")
    
    return None

# Test on representative states (different regions, price levels)
test_states = [
    ('CA', 'California'),      # Highest price, West Coast
    ('OK', 'Oklahoma'),        # Lowest price, Central
    ('TX', 'Texas'),           # Large consumption, South
    ('NY', 'New York'),        # Northeast, high price
    ('FL', 'Florida'),         # Southeast, medium price
]

results = {}

print("\n" + "="*70)
print("TESTING 5 REPRESENTATIVE STATES")
print("="*70)

for state_code, state_name in test_states:
    result = investigate_aaa_state_page(state_code, state_name)
    if result:
        results[state_code] = result
    time.sleep(2)  # Rate limiting

# Summary Analysis
print("\n" + "="*70)
print("📊 SUMMARY ANALYSIS")
print("="*70)

if results:
    successful_states = len(results)
    print(f"\n✅ Successfully accessed: {successful_states}/5 states")
    
    # Count common features
    features = {
        'yesterday': sum(1 for r in results.values() if r['has_yesterday']),
        'week_ago': sum(1 for r in results.values() if r['has_week_ago']),
        'month_ago': sum(1 for r in results.values() if r['has_month_ago']),
        'year_ago': sum(1 for r in results.values() if r['has_year_ago']),
        'archive': sum(1 for r in results.values() if r['has_archive']),
        'download': sum(1 for r in results.values() if r['has_download']),
    }
    
    print("\nHistorical Data Availability:")
    for feature, count in features.items():
        pct = (count / successful_states) * 100
        status = "✅" if count == successful_states else "⚠️" if count > 0 else "❌"
        print(f"  {status} {feature.replace('_', ' ').title()}: {count}/{successful_states} states ({pct:.0f}%)")
    
    # Average prices and dates found
    avg_prices = sum(r['prices_found'] for r in results.values()) / successful_states
    avg_dates = sum(r['dates_found'] for r in results.values()) / successful_states
    
    print(f"\nData Richness:")
    print(f"  Average prices per page: {avg_prices:.1f}")
    print(f"  Average dates per page: {avg_dates:.1f}")
    
else:
    print("\n❌ No states successfully accessed!")

# Recommendations
print("\n" + "="*70)
print("💡 RECOMMENDATIONS")
print("="*70)

if not results:
    print("\n⚠️  All requests failed!")
    print("   • Check internet connection")
    print("   • Try from different network")
    print("   • AAA might be blocking automated requests")
    
elif any(r['has_archive'] or r['has_download'] for r in results.values()):
    print("\n🎉 EXCELLENT NEWS!")
    print("   • Some states have archive/download options")
    print("   • High probability of historical data access")
    print("   • Next step: Build historical scraper")
    print("\n📋 TODO:")
    print("   1. Investigate archive page structure")
    print("   2. Check if download requires authentication")
    print("   3. Build scraper for past 30 days")
    print("   4. Validate against current data")
    
elif any(r['has_yesterday'] and r['has_week_ago'] for r in results.values()):
    print("\n✅ GOOD NEWS!")
    print("   • States show Yesterday/Week Ago/Month Ago data")
    print("   • Can collect limited historical points (4 per state)")
    print("   • Total: ~200 historical records (51 states × 4 points)")
    print("\n📋 TODO:")
    print("   1. Update collect_state_prices.py to extract historical points")
    print("   2. Run once to get ~30-day snapshots")
    print("   3. Supplement with ongoing daily collection")
    print("   4. Will have partial dataset by Nov 10 (30-day coverage)")
    
elif any(r['prices_found'] > 1 for r in results.values()):
    print("\n⚠️  MIXED RESULTS")
    print("   • Multiple prices found but unclear if historical")
    print("   • Might be different fuel types (Regular/Premium/Diesel)")
    print("   • Need deeper investigation of page structure")
    print("\n📋 TODO:")
    print("   1. Save full HTML of one state page")
    print("   2. Manually inspect for date-price pairs")
    print("   3. Determine if prices are historical or fuel types")
    
else:
    print("\n❌ LIMITED DATA")
    print("   • State pages only show current prices")
    print("   • No historical data available via web scraping")
    print("   • Must collect forward from today")
    print("\n📋 TODO:")
    print("   1. Stick with daily collection plan (30 days forward)")
    print("   2. Check if AAA has public API or data portal")
    print("   3. Consider contacting AAA for historical access")
    print("   4. Alternative: Use EIA state-level data (weekly)")

print("\n" + "="*70)
print("🎯 NEXT STEPS")
print("="*70)

print("\n1. Review findings above")
print("2. If historical data available:")
print("   • Build historical scraper (4-6 hours)")
print("   • Collect past 30 days (one-time)")
print("   • Validate data quality")
print("3. If no historical data:")
print("   • Continue daily collection (already set up)")
print("   • Wait 30 days for analysis")
print("   • Consider alternative data sources")
print("\n4. Either way:")
print("   • Document findings in research log")
print("   • Update state analysis README")
print("   • Plan December analysis timeline")

print("\n" + "="*70)
print("Investigation complete! Check results above.")
print("="*70)
