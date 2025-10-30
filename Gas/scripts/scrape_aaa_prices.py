#!/usr/bin/env python3
"""
AAA Daily Fuel Gauge Scraper

Scrapes daily U.S. national average gas prices from AAA's website.
AAA publishes this data daily and it's the industry standard cited by news media.

Website: https://gasprices.aaa.com/
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import json
from pathlib import Path

def scrape_aaa_current_price():
    """
    Scrape current U.S. national average gas price from AAA
    
    Returns:
        dict: {'date': datetime, 'price': float, 'source': 'AAA'}
    """
    
    print("🔍 Scraping AAA Daily Fuel Gauge...")
    
    # AAA main page
    url = "https://gasprices.aaa.com/"
    
    # Headers to mimic a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        # Make request
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # AAA shows national average prominently
        # Look for common patterns in their HTML structure
        
        # Method 1: Look for price in specific div/span classes
        price_element = None
        
        # Try finding by class patterns AAA typically uses
        possible_selectors = [
            ('span', {'class': 'price'}),
            ('div', {'class': 'price-display'}),
            ('span', {'class': 'national-average'}),
            ('div', {'class': 'gasprices-price'}),
        ]
        
        for tag, attrs in possible_selectors:
            price_element = soup.find(tag, attrs)
            if price_element:
                break
        
        # Method 2: Search for price pattern in text
        if not price_element:
            # Look for text matching $X.XXX pattern
            import re
            price_pattern = r'\$(\d+\.\d{3})'
            
            # Search all text
            all_text = soup.get_text()
            matches = re.findall(price_pattern, all_text)
            
            if matches:
                # First match is usually the national average
                price_text = matches[0]
                price = float(price_text)
                
                result = {
                    'date': datetime.now().date(),
                    'price': price,
                    'source': 'AAA',
                    'method': 'regex'
                }
                
                print(f"   ✅ Found price: ${price:.3f}/gal (via regex)")
                return result
        
        # Method 3: Parse structured data (JSON-LD)
        script_tags = soup.find_all('script', {'type': 'application/ld+json'})
        for script in script_tags:
            try:
                data = json.loads(script.string)
                # Look for price in structured data
                if 'price' in str(data):
                    # Parse out price if found
                    pass
            except:
                pass
        
        # If price element found, extract text
        if price_element:
            price_text = price_element.get_text().strip()
            # Remove $ and convert to float
            price_text = price_text.replace('$', '').replace(',', '')
            price = float(price_text)
            
            result = {
                'date': datetime.now().date(),
                'price': price,
                'source': 'AAA',
                'method': 'element'
            }
            
            print(f"   ✅ Found price: ${price:.3f}/gal")
            return result
        
        # If we get here, try a more aggressive search
        print("   ⚠️ Standard selectors didn't work, trying comprehensive search...")
        
        # Save HTML for inspection
        debug_path = Path('/tmp/aaa_page.html')
        with open(debug_path, 'w') as f:
            f.write(str(soup.prettify()))
        print(f"   💾 Saved HTML to {debug_path} for inspection")
        
        # Search all text for price-like patterns
        import re
        text_content = soup.get_text()
        
        # Look for "national average" context
        lines = text_content.split('\n')
        for i, line in enumerate(lines):
            if 'national' in line.lower() and 'average' in line.lower():
                # Check surrounding lines for price
                context = '\n'.join(lines[max(0, i-3):min(len(lines), i+4)])
                price_matches = re.findall(r'\$?(\d+\.\d{3})', context)
                if price_matches:
                    price = float(price_matches[0])
                    result = {
                        'date': datetime.now().date(),
                        'price': price,
                        'source': 'AAA',
                        'method': 'context_search'
                    }
                    print(f"   ✅ Found price via context: ${price:.3f}/gal")
                    return result
        
        print(f"   ❌ Could not find price on page")
        print(f"   💡 Inspect {debug_path} to find correct selector")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {str(e)}")
        return None
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None


def scrape_aaa_api():
    """
    Try to access AAA's backend API directly (if they have one)
    
    Many sites load data via JSON API calls - check browser DevTools Network tab
    """
    
    print("\n🔍 Checking for AAA API endpoints...")
    
    # Common API patterns
    api_urls = [
        "https://gasprices.aaa.com/api/prices",
        "https://gasprices.aaa.com/api/national",
        "https://api.gasprices.aaa.com/v1/prices",
        "https://gasprices.aaa.com/state-gas-price-averages",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    
    for api_url in api_urls:
        try:
            response = requests.get(api_url, headers=headers, timeout=5)
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ Found API: {api_url}")
                    print(f"   Response keys: {list(data.keys()) if isinstance(data, dict) else 'List'}")
                    
                    # Save for inspection
                    with open('/tmp/aaa_api_response.json', 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"   💾 Saved to /tmp/aaa_api_response.json")
                    
                    return data
                except:
                    print(f"   ⚠️ {api_url} returned non-JSON")
        except:
            pass
    
    print(f"   ℹ️ No obvious API endpoints found")
    return None


def get_aaa_daily_price():
    """
    Main function to get AAA daily price - tries multiple methods
    
    Returns:
        dict: {'date': datetime, 'price': float, 'source': 'AAA'} or None
    """
    
    print("=" * 80)
    print("📊 AAA DAILY FUEL GAUGE SCRAPER")
    print("=" * 80)
    
    # Try API first (faster and more reliable)
    api_data = scrape_aaa_api()
    if api_data:
        # Parse price from API response
        # Structure depends on their API
        pass
    
    # Fall back to web scraping
    result = scrape_aaa_current_price()
    
    if result:
        print(f"\n✅ SUCCESS!")
        print(f"   Date: {result['date']}")
        print(f"   Price: ${result['price']:.3f}/gal")
        print(f"   Source: {result['source']}")
        print(f"   Method: {result.get('method', 'unknown')}")
    else:
        print(f"\n❌ Could not retrieve AAA price")
        print(f"   Manual check: https://gasprices.aaa.com/")
    
    print("=" * 80)
    return result


if __name__ == "__main__":
    # Test the scraper
    result = get_aaa_daily_price()
    
    if result:
        # Save to CSV
        output_path = Path('/Users/denielnankov/Documents/kalshi/Gas/outputs/aaa_daily_prices.csv')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Append to existing file or create new
        if output_path.exists():
            df = pd.read_csv(output_path)
            new_row = pd.DataFrame([result])
            df = pd.concat([df, new_row], ignore_index=True)
        else:
            df = pd.DataFrame([result])
        
        # Remove duplicates (same date)
        df['date'] = pd.to_datetime(df['date'])
        df = df.drop_duplicates(subset=['date'], keep='last')
        df = df.sort_values('date')
        
        df.to_csv(output_path, index=False)
        print(f"\n💾 Saved to: {output_path}")
        print(f"   Total records: {len(df)}")
