"""
Kalshi Gas Price Markets - Direct API Access
=============================================

Successfully found gas price markets!
Series: KXAAAGASM
Format: KXAAAGASM-{YY}{MON}{DD}-{STRIKE}
Example: KXAAAGASM-25OCT31-3.05

This module uses direct HTTP requests (not SDK) to access Kalshi markets.
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd


class KalshiMarkets:
    """Direct HTTP access to Kalshi prediction markets"""
    
    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
    
    @staticmethod
    def get_gas_markets(month: str = "OCT", year: str = "25", status: str = "active") -> List[Dict]:
        """
        Get all gas price markets for a specific month.
        
        Parameters:
        -----------
        month : str
            Month abbreviation (OCT, NOV, DEC)
        year : str
            Two-digit year (25 for 2025)
        status : str
            Market status filter ('active', 'initialized', 'all')
            
        Returns:
        --------
        list : List of market dictionaries
        
        Example:
        --------
        >>> markets = KalshiMarkets.get_gas_markets("OCT", "25")
        >>> for m in markets:
        ...     print(f"${m['strike']}: {m['probability']}%")
        """
        url = f"{KalshiMarkets.BASE_URL}/markets"
        params = {"series_ticker": "KXAAAGASM", "limit": 200}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            markets = data.get('markets', [])
            
            # Filter for specific month
            month_pattern = f"{year}{month}"
            filtered = []
            
            for market in markets:
                ticker = market.get('ticker', '')
                market_status = market.get('status', '')
                
                # Check month and status
                if month_pattern in ticker:
                    if status == 'all' or market_status == status:
                        # Extract strike price
                        parts = ticker.split('-')
                        strike = parts[-1] if len(parts) >= 3 else 'N/A'
                        
                        filtered.append({
                            'ticker': ticker,
                            'strike': strike,
                            'strike_price': float(strike) if strike != 'N/A' else None,
                            'probability': market.get('last_price', 0),
                            'volume': market.get('volume', 0),
                            'status': market_status,
                            'close_time': market.get('close_time'),
                            'title': market.get('title')
                        })
            
            # Sort by strike price
            filtered.sort(key=lambda x: x['strike_price'] if x['strike_price'] else 0)
            
            return filtered
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching markets: {e}")
            return []
    
    @staticmethod
    def get_market_consensus(markets: List[Dict]) -> Dict:
        """
        Calculate implied market consensus from probability distribution.
        
        Parameters:
        -----------
        markets : list
            List of market dictionaries from get_gas_markets()
            
        Returns:
        --------
        dict : Market consensus statistics
            - expected_value: Weighted average expected price
            - median_strike: Strike closest to 50% probability
            - mode_strike: Strike with highest volume
            - total_volume: Sum of all volumes
            - prob_above_{strike}: Probability of price > strike
            
        Example:
        --------
        >>> markets = KalshiMarkets.get_gas_markets()
        >>> consensus = KalshiMarkets.get_market_consensus(markets)
        >>> print(f"Market expects: ${consensus['expected_value']:.3f}")
        """
        if not markets:
            return {}
        
        # Find median strike (closest to 50% probability)
        median_strike = None
        min_diff = float('inf')
        
        for m in markets:
            diff = abs(m['probability'] - 50)
            if diff < min_diff:
                min_diff = diff
                median_strike = m
        
        # Find mode strike (highest volume)
        mode_strike = max(markets, key=lambda x: x['volume'])
        
        # Calculate expected value
        # Using probability mass function approach
        expected = 0
        prev_prob = 100
        
        for m in markets:
            if m['strike_price']:
                strike = m['strike_price']
                prob = m['probability']
                
                # Probability mass in this range
                prob_mass = (prev_prob - prob) / 100.0
                expected += prob_mass * strike
                prev_prob = prob
        
        # Total volume
        total_volume = sum(m['volume'] for m in markets)
        
        # Create probability dict for key strikes
        prob_above = {}
        for m in markets:
            if m['strike_price']:
                key = f"prob_above_{m['strike']}"
                prob_above[key] = m['probability']
        
        return {
            'expected_value': round(expected, 3),
            'median_strike': median_strike['strike_price'] if median_strike else None,
            'median_prob': median_strike['probability'] if median_strike else None,
            'mode_strike': mode_strike['strike_price'],
            'mode_volume': mode_strike['volume'],
            'total_volume': total_volume,
            **prob_above
        }
    
    @staticmethod
    def compare_with_model(model_prediction: float, month: str = "OCT", year: str = "25") -> Dict:
        """
        Compare model prediction with Kalshi market consensus.
        
        Parameters:
        -----------
        model_prediction : float
            Your model's price prediction
        month : str
            Month to compare (OCT, NOV, etc.)
        year : str
            Year (25 for 2025)
            
        Returns:
        --------
        dict : Comparison statistics
            - model_prediction: Your prediction
            - market_consensus: Market expected value
            - difference: model - market
            - model_percentile: Where your prediction falls in market distribution
            - closest_strike: Strike price nearest to your prediction
            - closest_probability: Market probability at closest strike
            
        Example:
        --------
        >>> comparison = KalshiMarkets.compare_with_model(3.058, "OCT", "25")
        >>> print(f"Your model: ${comparison['model_prediction']}")
        >>> print(f"Market expects: ${comparison['market_consensus']}")
        >>> print(f"Difference: ${comparison['difference']}")
        """
        # Get markets
        markets = KalshiMarkets.get_gas_markets(month, year)
        
        if not markets:
            return {'error': 'No markets found'}
        
        # Get consensus
        consensus = KalshiMarkets.get_market_consensus(markets)
        
        # Find closest strike to model prediction
        closest = min(markets, key=lambda x: abs(x['strike_price'] - model_prediction) if x['strike_price'] else float('inf'))
        
        # Determine percentile
        # Find strikes above and below model prediction
        below = [m for m in markets if m['strike_price'] and m['strike_price'] < model_prediction]
        above = [m for m in markets if m['strike_price'] and m['strike_price'] >= model_prediction]
        
        # Interpolate probability
        if above and below:
            lower_strike = max(below, key=lambda x: x['strike_price'])
            upper_strike = min(above, key=lambda x: x['strike_price'])
            
            # Linear interpolation
            strike_range = upper_strike['strike_price'] - lower_strike['strike_price']
            pred_range = model_prediction - lower_strike['strike_price']
            weight = pred_range / strike_range if strike_range > 0 else 0
            
            prob_at_model = lower_strike['probability'] + weight * (upper_strike['probability'] - lower_strike['probability'])
        elif above:
            prob_at_model = above[0]['probability']
        elif below:
            prob_at_model = below[-1]['probability']
        else:
            prob_at_model = None
        
        return {
            'model_prediction': model_prediction,
            'market_consensus': consensus['expected_value'],
            'difference': round(model_prediction - consensus['expected_value'], 3),
            'model_percentile': prob_at_model,
            'closest_strike': closest['strike_price'],
            'closest_strike_ticker': closest['ticker'],
            'closest_probability': closest['probability'],
            'total_market_volume': consensus['total_volume'],
            'markets_analyzed': len(markets)
        }
    
    @staticmethod
    def print_market_snapshot(month: str = "OCT", year: str = "25"):
        """
        Print a formatted snapshot of current market prices.
        
        Parameters:
        -----------
        month : str
            Month abbreviation
        year : str
            Two-digit year
        """
        markets = KalshiMarkets.get_gas_markets(month, year)
        
        if not markets:
            print(f"❌ No active markets found for {month} {year}")
            return
        
        print("="*80)
        print(f"📊 KALSHI GAS PRICE MARKETS - {month} 20{year}")
        print("="*80)
        print()
        print(f"{'Strike':>8} | {'Prob':>5} | {'Volume':>12} | {'Ticker'}")
        print("-"*80)
        
        for m in markets:
            print(f"${m['strike']:>6} | {m['probability']:3d}%  | ${m['volume']:10,} | {m['ticker']}")
        
        print()
        print("="*80)
        print("💡 MARKET CONSENSUS")
        print("="*80)
        
        consensus = KalshiMarkets.get_market_consensus(markets)
        
        print(f"\nExpected value: ${consensus['expected_value']:.3f}")
        print(f"Median (50%):   ${consensus['median_strike']:.2f} (actual: {consensus['median_prob']}%)")
        print(f"Mode (volume):  ${consensus['mode_strike']:.2f} (${consensus['mode_volume']:,})")
        print(f"Total volume:   ${consensus['total_volume']:,}")
        print()
        print("="*80)


def test_markets():
    """Test market access and display current data"""
    
    print("\n" + "="*80)
    print("🧪 TESTING KALSHI MARKETS API")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()
    
    # Get October 2025 markets
    print("Fetching October 2025 gas price markets...")
    markets = KalshiMarkets.get_gas_markets("OCT", "25")
    
    if markets:
        print(f"✅ Found {len(markets)} active markets!\n")
        
        # Display snapshot
        KalshiMarkets.print_market_snapshot("OCT", "25")
        
        # Compare with model prediction
        model_pred = 3.058
        print("\n" + "="*80)
        print(f"🤖 MODEL vs MARKET COMPARISON")
        print("="*80)
        print()
        
        comparison = KalshiMarkets.compare_with_model(model_pred, "OCT", "25")
        
        print(f"Your Ridge model: ${comparison['model_prediction']:.3f}")
        print(f"Market consensus: ${comparison['market_consensus']:.3f}")
        print(f"Difference:       ${comparison['difference']:+.3f}")
        print()
        print(f"Market probability at your prediction: {comparison['model_percentile']:.1f}%")
        print(f"Closest strike: ${comparison['closest_strike']:.2f} ({comparison['closest_probability']}%)")
        print()
        
        if abs(comparison['difference']) < 0.05:
            print("✅ EXCELLENT! Your model aligns closely with market consensus!")
        elif abs(comparison['difference']) < 0.10:
            print("✅ GOOD! Your model is reasonably aligned with the market")
        else:
            print("⚠️ Your model differs significantly from market expectations")
        
        print()
        print("="*80)
        
        return True
    else:
        print("❌ No markets found")
        return False


if __name__ == "__main__":
    test_markets()
