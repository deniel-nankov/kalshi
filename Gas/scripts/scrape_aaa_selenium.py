#!/usr/bin/env python3
"""
AAA Daily Fuel Gauge Scraper (with Selenium for JavaScript)

AAA's website likely renders prices via JavaScript, so we need a browser.
This uses Selenium with headless Chrome.
"""

import time
from datetime import datetime
from pathlib import Path
import pandas as pd

def scrape_aaa_with_selenium():
    """
    Use Selenium to scrape AAA (handles JavaScript)
    """
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
    except ImportError:
        print("❌ Selenium not installed. Install with: pip install selenium")
        return None
    
    print("🔍 Launching headless Chrome to scrape AAA...")
    
    # Setup headless Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"❌ Chrome driver error: {e}")
        print("💡 Install ChromeDriver: brew install chromedriver")
        return None
    
    try:
        # Navigate to AAA
        url = "https://gasprices.aaa.com/"
        print(f"   Loading {url}...")
        driver.get(url)
        
        # Wait for page to load (JavaScript to render)
        time.sleep(3)
        
        # Try multiple selectors
        selectors = [
            (By.CSS_SELECTOR, "span.price"),
            (By.CSS_SELECTOR, "div.price"),
            (By.XPATH, "//*[contains(text(), 'National Average')]/..//*[contains(text(), '$')]"),
            (By.XPATH, "//*[contains(@class, 'price')]"),
            (By.CSS_SELECTOR, "[class*='price']"),
        ]
        
        price = None
        for by, selector in selectors:
            try:
                element = driver.find_element(by, selector)
                text = element.text.strip()
                
                # Extract price from text
                import re
                match = re.search(r'\$?(\d+\.\d{2,3})', text)
                if match:
                    price = float(match.group(1))
                    print(f"   ✅ Found price: ${price:.3f}/gal (selector: {selector})")
                    break
            except:
                continue
        
        # If not found, try getting all text
        if not price:
            print("   ⚠️ Specific selectors failed, searching all page text...")
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            
            # Save for debugging
            with open('/tmp/aaa_page_text.txt', 'w') as f:
                f.write(page_text)
            print(f"   💾 Saved page text to /tmp/aaa_page_text.txt")
            
            # Look for price patterns
            import re
            # Find all dollar amounts with 3 decimal places (gas prices)
            matches = re.findall(r'\$(\d+\.\d{3})', page_text)
            
            if matches:
                # First one is usually national average
                price = float(matches[0])
                print(f"   ✅ Found price via text search: ${price:.3f}/gal")
                print(f"   All price-like values found: {matches[:5]}")
        
        # Take screenshot for debugging
        screenshot_path = '/tmp/aaa_screenshot.png'
        driver.save_screenshot(screenshot_path)
        print(f"   📸 Screenshot saved to {screenshot_path}")
        
        driver.quit()
        
        if price:
            return {
                'date': datetime.now().date(),
                'price': price,
                'source': 'AAA',
                'method': 'selenium'
            }
        else:
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        driver.quit()
        return None


def scrape_aaa_simple():
    """
    Simpler approach - just get the raw content and parse aggressively
    """
    import requests
    import re
    
    print("🔍 Simple scrape of AAA...")
    
    url = "https://gasprices.aaa.com/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        text = response.text
        
        # Save for inspection
        with open('/tmp/aaa_raw.html', 'w') as f:
            f.write(text)
        
        # Look for JSON data embedded in JavaScript
        json_pattern = r'var\s+\w+\s*=\s*(\{[^;]+\})'
        json_matches = re.findall(json_pattern, text)
        
        for match in json_matches:
            if 'price' in match.lower() or 'national' in match.lower():
                print(f"   Found potential data: {match[:100]}...")
        
        # Look for price patterns
        price_matches = re.findall(r'\$(\d+\.\d{3})', text)
        if price_matches:
            price = float(price_matches[0])
            print(f"   ✅ Found price: ${price:.3f}/gal")
            return {
                'date': datetime.now().date(),
                'price': price,
                'source': 'AAA',
                'method': 'regex'
            }
        
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


if __name__ == "__main__":
    print("=" * 80)
    print("📊 AAA SCRAPER (JavaScript-Aware)")
    print("=" * 80)
    
    # Try simple method first (faster)
    print("\n1️⃣ Trying simple HTTP request...")
    result = scrape_aaa_simple()
    
    # If that fails, use Selenium
    if not result:
        print("\n2️⃣ Trying Selenium (handles JavaScript)...")
        result = scrape_aaa_with_selenium()
    
    if result:
        print(f"\n✅ SUCCESS!")
        print(f"   Date: {result['date']}")
        print(f"   Price: ${result['price']:.3f}/gal")
        print(f"   Source: {result['source']}")
        
        # Save to CSV
        output_path = Path('/Users/denielnankov/Documents/kalshi/Gas/outputs/aaa_daily_prices.csv')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_path.exists():
            df = pd.read_csv(output_path)
            new_row = pd.DataFrame([result])
            df = pd.concat([df, new_row], ignore_index=True)
        else:
            df = pd.DataFrame([result])
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.drop_duplicates(subset=['date'], keep='last')
        df = df.sort_values('date')
        
        df.to_csv(output_path, index=False)
        print(f"\n💾 Saved to: {output_path}")
        print(f"   Total records: {len(df)}")
    else:
        print(f"\n❌ FAILED - Could not retrieve AAA price")
        print(f"\n💡 Manual alternatives:")
        print(f"   1. Visit https://gasprices.aaa.com/ and note the price")
        print(f"   2. Use RBOB futures conversion (already working!)")
        print(f"   3. Use EIA weekly data (official source)")
    
    print("=" * 80)
