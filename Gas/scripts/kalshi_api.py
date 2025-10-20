"""
Kalshi API Integration for Gas Price Predictions
================================================

Authenticates with Kalshi API using official SDK and fetches gas price market data.

Author: Gas Price Forecasting System
Date: October 19, 2025
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from kalshi_python import KalshiClient

# Load environment
load_dotenv('/Users/denielnankov/Documents/kalshi/.env')


class KalshiAPI:
    """Kalshi API client using official SDK"""
    
    def __init__(self, api_id=None, private_key_path=None, private_key_str=None):
        """
        Initialize Kalshi API client
        
        Parameters:
        -----------
        api_id : str
            Kalshi API ID (member ID)
        private_key_path : str
            Path to private key file (optional)
        private_key_str : str
            Private key as string (optional)
        """
        self.api_id = api_id or os.getenv('KALSHI_API_ID')
        
        # Save private key to temporary file if provided as string
        if private_key_str:
            key_path = Path('/tmp/kalshi_key.pem')
            key_path.write_text(private_key_str)
            private_key_path = str(key_path)
        
        self.private_key_path = private_key_path
        
        # Initialize Kalshi client
        from kalshi_python import Configuration
        config = Configuration(
            host="https://api.elections.kalshi.com/trade-api/v2"
        )
        self.client = KalshiClient(configuration=config)
        
        # Authenticate using RSA keys
        self.client.set_kalshi_auth(
            key_id=self.api_id,
            private_key_path=self.private_key_path
        )
        
        print(f"✅ Kalshi API initialized & authenticated")
        print(f"   API ID: {self.api_id[:8]}...{self.api_id[-8:]}")
    
    def search_markets(self, query=None, limit=20, status="open"):
        """
        Search for markets
        
        Parameters:
        -----------
        query : str
            Search term (optional)
        limit : int
            Maximum results to return
        status : str
            Market status ('open', 'closed', etc.')
            
        Returns:
        --------
        list : List of market dictionaries
        """
        print(f"\n🔍 Searching for markets...")
        if query:
            print(f"   Query: '{query}'")
        
        try:
            # Get markets using SDK
            response = self.client.get_markets(limit=limit, status=status)
            
            # SDK returns the response dict directly
            markets = response.markets if hasattr(response, 'markets') else []
            print(f"   Found {len(markets)} markets")
            
            # Convert to dict format
            markets_list = []
            for m in markets:
                if hasattr(m, 'to_dict'):
                    markets_list.append(m.to_dict())
                else:
                    markets_list.append(m)
            
            # Filter by query if provided
            if query:
                query_lower = query.lower()
                filtered = [m for m in markets_list if 
                           query_lower in str(m.get('title', '')).lower() or
                           query_lower in str(m.get('ticker', '')).lower()]
                print(f"   Filtered to {len(filtered)} matching '{query}'")
                return filtered
            
            return markets_list
            
        except Exception as e:
            print(f"   ❌ Error searching markets: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_market(self, ticker):
        """
        Get details for a specific market
        
        Parameters:
        -----------
        ticker : str
            Market ticker symbol
            
        Returns:
        --------
        dict : Market details
        """
        try:
            response = self.client.get_market(ticker=ticker)
            if hasattr(response, 'market'):
                market = response.market
                return market.to_dict() if hasattr(market, 'to_dict') else market
            return response
        except Exception as e:
            print(f"   ❌ Error getting market {ticker}: {str(e)}")
            return None
    
    def get_gas_price_prediction(self):
        """
        Get current gas price prediction from Kalshi markets
        
        Returns:
        --------
        dict : {
            'date': datetime,
            'kalshi_price': float,
            'market_ticker': str,
            'market_title': str,
            'last_price': float,
            'volume': int,
            'close_date': str
        } or None if no gas markets found
        """
        print(f"\n📊 Fetching gas price prediction from Kalshi...")
        
        # Search for gas-related markets
        markets = self.search_markets(query="gas", limit=50)
        
        # Also try gasoline
        if not markets:
            markets = self.search_markets(query="gasoline", limit=50)
        
        # Also try fuel
        if not markets:
            markets = self.search_markets(query="fuel", limit=50)
        
        if not markets:
            print(f"   ⚠️ No gas/gasoline/fuel markets found")
            print(f"\n   Let's see what markets are available...")
            all_markets = self.search_markets(limit=100)
            
            # Show categories
            if all_markets:
                categories = {}
                for m in all_markets:
                    cat = m.get('category', 'unknown')
                    categories[cat] = categories.get(cat, 0) + 1
                
                print(f"\n   Available market categories:")
                for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
                    print(f"      - {cat}: {count} markets")
                
                # Show sample titles
                print(f"\n   Sample market titles:")
                for m in all_markets[:5]:
                    print(f"      - {m.get('title', 'Unknown')}")
            
            return None
        
        # Use the first relevant market
        market = markets[0]
        ticker = market.get('ticker')
        
        print(f"\n   📈 Found market: {market.get('title')}")
        print(f"   Ticker: {ticker}")
        
        # Get full market details
        full_market = self.get_market(ticker)
        
        if full_market:
            result = {
                'date': datetime.now(),
                'market_ticker': ticker,
                'market_title': full_market.get('title'),
                'last_price': full_market.get('last_price', 0) / 100,  # Convert cents to dollars
                'kalshi_price': full_market.get('last_price', 0) / 100,
                'volume': full_market.get('volume', 0),
                'open_interest': full_market.get('open_interest', 0),
                'close_date': full_market.get('close_time'),
                'yes_bid': full_market.get('yes_bid', 0) / 100 if full_market.get('yes_bid') else None,
                'yes_ask': full_market.get('yes_ask', 0) / 100 if full_market.get('yes_ask') else None,
            }
            
            print(f"   Current price: ${result['kalshi_price']:.3f}")
            print(f"   Volume: {result['volume']:,}")
            if result['yes_bid']:
                print(f"   Bid/Ask: ${result['yes_bid']:.3f} / ${result['yes_ask']:.3f}")
            
            return result
        
        return None


def test_kalshi_connection():
    """Test Kalshi API connection and search for gas markets"""
    
    print("="*80)
    print("🧪 TESTING KALSHI API CONNECTION")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # API credentials
    api_id = "e7573856-4751-449f-8a15-f6c8df7dc502"
    private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAyF2N7pPA85UyXSHKCRoUwEoauWXEikQ43q3DXbGEhjWgQkww
TZeJ/h1582vVaMvyxBc0zuiC4eClMjiDJ7xY7XTBuiiYHwBz1URKS+gYwsiQh8Tu
szwwjYmqBu0XInTfOOJAjP4iiEHzUtVZ6zYhD6XtHWIEUaLNeVQChz26+bclCol3
t4GNRaN3Bmv88aLCPlsiLmsGlEU8jfhPFn9QGNBEV5+gzETnUjv1jEkvcbbsZxSI
/oArK3xoPMjcNqHJou8vxQcCyhA9CyA2qYwFP2YYyGUX5/tlqHK4unrnMjQbDkKm
YlZ6v1CUT3TQ0mtghob/N7mgkFPGjPH7qInU8wIDAQABAoIBAQCsmisSQqYNL5Fb
OShZ/uWxYCT1YP2WPn7fFMEfjTSkiL2tXwSdUtXE2o+bamFFDavr0DHlq9ZTzrmA
Mb6KFG5m4BWi0CV7T2B5b4KxMRdjdHNNAhC+xjLtOpIFtWggfp1s2zrQOnx09Jsv
2CrFvLNuT3mbvjwKNzzaL8ydxEe1pM5+Z9MWyU7rZB0LqDHApwhn8/8DRAPPc6l3
zuup0KDtWuid2TbGrNIaZJDBgYseKKhJ3WRNRwUOsRTINJoLUaztVWr/AT486bcq
hXf9oqcPcv7o+0Y7sP5E+jDCcgjf1FyfbGLsO9++seMqnB3G2F13sMKUqzOd7lOZ
j8TkQUCBAoGBAP82aDXooid043RO2ye7rIy8KqZK6hhxtAim5AEJNHzBTV/Nwy1d
BvwnA5WXoTXb0MOgFGBwCp2KfnNdjBK+SebbWtvabFFO4ewnPsYdeLXcO+EQm2wA
iUpIx5KrQqD5/lgcw2R4b05QELgVHpnXIsrfnqyAg0mv/Xq6pmXq+PUpAoGBAMj7
0tJNRlK/y53xeY4tr/ACHXGW8o0LbOwrUBJyclqf1A0qDD3kQIbnygJDb/GbLaFP
qbiPbG/3J/LMZ2aw2DFuOIxE8ttHj3HYip6j0wH2+v5iPS2PMIwXsd64QOSXoOaV
5UFLT0SL5m5vqnIrrydWF7B28PEnNi9YZHowUMC7AoGBAIcLzDMSiZOlZ6KpA5DP
32uNOmhKZftPV3voi+f8bfjB9OaIJAqCGmsdXekvlk/ApISP1Zh+US+yFF2Jl9Bn
PwXY9wg1WXHg8u2air4c5D4fbtQWjJem5P8Y6fozg4tZHfyUI9SrYgKnnWE7U7kG
PVPq5rTTQCWi6deiouB1aQ2ZAoGAbfK1Ji735ZTewwyyvsDnmpjNmrJFBjvV3mzj
ZPQO8ty0mG8EO2d+lU6ACDT0LGwDzldSNZDgdW/z/rMrbdYYrxHpBXNCmArRwin/
y0E70btXG4qKhT3sBPeBaqHJfkQk1X/y5oFYX9tYt9mGmOak7xP96Z9nt8UHs2bb
sKx1wLkCgYBVJsFDkouwi5+AXxIpyneilDkL68njVn75Ics+kEr52GZg6oHiOLzV
fxUy320wRWUTYUgtKUPIoyUPdqr01KpLwM/R6CvnVivOlNsOSYh1WGNg6vZ6hOAT
zWpj83BeZ0aoo/9TX6ajlmn7mJBRHKj6GkKEgFfm41+fLUOBaKBsyQ==
-----END RSA PRIVATE KEY-----"""
    
    try:
        # Initialize API client
        print("\n📡 Initializing Kalshi API client...")
        api = KalshiAPI(api_id=api_id, private_key_str=private_key)
        
        # Search for gas price markets
        prediction = api.get_gas_price_prediction()
        
        if prediction:
            print("\n" + "="*80)
            print("✅ KALSHI API TEST SUCCESSFUL!")
            print("="*80)
            print(f"\nMarket: {prediction['market_title']}")
            print(f"Ticker: {prediction['market_ticker']}")
            print(f"Current prediction: ${prediction['kalshi_price']:.3f}")
            print(f"Volume: {prediction['volume']:,}")
            print(f"Close date: {prediction['close_date']}")
            print("\n✅ Ready to start collecting daily predictions!")
            return True
        else:
            print("\n" + "="*80)
            print("⚠️ NO GAS PRICE MARKETS FOUND")
            print("="*80)
            print("\nKalshi may not have active gas price markets at this time.")
            print("This is expected - Kalshi focuses on political and economic events.")
            print("\n💡 Alternative approach:")
            print("   We can track EIA prices in real-time and compare with our predictions")
            print("   This gives us the same validation without needing Kalshi markets")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_kalshi_connection()
