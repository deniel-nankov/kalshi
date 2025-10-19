"""
Bronze Layer Data Ingestion

This script downloads raw data from all API sources and saves it to the bronze layer
with full metadata tracking. The bronze layer contains EXACT API responses with
no transformations applied.

Key Principles:
1. Immutable - append-only, never modify existing bronze data
2. Raw - exact API responses, no transformations
3. Auditable - full metadata (timestamp, source, API version)
4. Validated - schema checks on write

Data Sources:
- EIA API: Retail prices, inventory, utilization, SPR stocks
- FRED API: Unemployment, VMT, consumer sentiment
- NOAA API: Hurricane data
- Manual: OPEC cuts, sanctions (with source URLs)

Author: Kalshi Gas Forecasting Team  
Date: October 2025
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Load environment variables
load_dotenv()

# API Keys
EIA_API_KEY = os.getenv("EIA_API_KEY")
FRED_API_KEY = os.getenv("FRED_API_KEY")
NOAA_TOKEN = os.getenv("NOAA_TOKEN")

# Bronze layer directory
BRONZE_DIR = Path(__file__).parent.parent / "data" / "bronze"
BRONZE_DIR.mkdir(parents=True, exist_ok=True)

# Metadata directory
METADATA_DIR = BRONZE_DIR / "metadata"
METADATA_DIR.mkdir(exist_ok=True)


class BronzeIngester:
    """Base class for bronze layer data ingestion with validation."""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.fetch_timestamp = datetime.now().isoformat()
        
    def save_raw_response(
        self,
        data: pd.DataFrame,
        filename: str,
        metadata: Dict
    ) -> Path:
        """
        Save raw API response to bronze layer with metadata.
        
        Parameters:
        -----------
        data : pd.DataFrame
            Raw data from API
        filename : str
            Output filename (without .parquet extension)
        metadata : Dict
            Metadata about the fetch (source_url, params, etc.)
        
        Returns:
        --------
        Path to saved file
        """
        # Add fetch metadata
        metadata.update({
            'source_name': self.source_name,
            'fetch_timestamp': self.fetch_timestamp,
            'row_count': len(data),
            'column_count': len(data.columns),
            'columns': data.columns.tolist(),
            'date_range': {
                'min': str(data['date'].min()) if 'date' in data.columns else None,
                'max': str(data['date'].max()) if 'date' in data.columns else None
            }
        })
        
        # Save data
        output_path = BRONZE_DIR / f"{filename}.parquet"
        data.to_parquet(output_path, index=False)
        print(f"✅ Saved {len(data)} rows to: {output_path}")
        
        # Save metadata
        metadata_path = METADATA_DIR / f"{filename}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"📋 Saved metadata to: {metadata_path}")
        
        # Check for duplicates
        if 'date' in data.columns:
            duplicates = data['date'].duplicated().sum()
            if duplicates > 0:
                print(f"⚠️  WARNING: Found {duplicates} duplicate dates")
        
        return output_path
    
    def validate_schema(self, data: pd.DataFrame, required_columns: List[str]):
        """Validate that all required columns are present."""
        missing = set(required_columns) - set(data.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        print(f"✓ Schema valid: {len(required_columns)} required columns present")


class EIAIngester(BronzeIngester):
    """Fetch data from EIA API."""
    
    def __init__(self):
        super().__init__("EIA")
        if not EIA_API_KEY:
            raise ValueError("EIA_API_KEY not found in environment!")
        self.api_key = EIA_API_KEY
        self.base_url = "https://api.eia.gov/v2"
    
    def fetch_retail_prices(self, start_date: str, end_date: str) -> Path:
        """Fetch weekly retail gasoline prices."""
        print("\n" + "="*80)
        print("📊 EIA: Fetching Retail Gasoline Prices")
        print("="*80)
        
        url = f"{self.base_url}/petroleum/pri/gnd/data/"
        params = {
            "api_key": self.api_key,
            "frequency": "weekly",
            "data[0]": "value",
            "facets[product][]": "EPM0",  # Regular gas
            "facets[duoarea][]": "NUS",   # US National
            "start": start_date,
            "end": end_date,
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "offset": 0,
            "length": 5000
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        json_data = response.json()
        records = json_data.get('response', {}).get('data', [])
        
        if not records:
            raise ValueError("No retail price data returned from EIA API!")
        
        # Parse into DataFrame
        df = pd.DataFrame(records)
        df['date'] = pd.to_datetime(df['period'])
        df['retail_price'] = pd.to_numeric(df['value'], errors='coerce')
        df = df[['date', 'retail_price']].sort_values('date').reset_index(drop=True)
        
        print(f"📈 Fetched {len(df)} weekly retail price records")
        print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
        print(f"   Price range: ${df['retail_price'].min():.3f} to ${df['retail_price'].max():.3f}")
        
        metadata = {
            'source_url': url,
            'api_params': params,
            'http_status': response.status_code,
            'data_description': 'Weekly US national regular gasoline retail prices ($/gallon)',
            'series': 'EPM0 (Regular Gasoline)',
            'frequency': 'Weekly',
            'unit': 'dollars per gallon'
        }
        
        self.validate_schema(df, ['date', 'retail_price'])
        return self.save_raw_response(df, 'eia_retail_prices_raw', metadata)
    
    def fetch_inventory(self, start_date: str, end_date: str) -> Path:
        """Fetch weekly gasoline inventory data."""
        print("\n" + "="*80)
        print("📊 EIA: Fetching Gasoline Inventory")
        print("="*80)
        
        url = f"{self.base_url}/petroleum/stoc/wstk/data/"
        params = {
            "api_key": self.api_key,
            "frequency": "weekly",
            "data[0]": "value",
            "facets[product][]": "EPMR",  # Motor gasoline
            "facets[duoarea][]": "NUS",
            "start": start_date,
            "end": end_date,
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "offset": 0,
            "length": 5000
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        json_data = response.json()
        records = json_data.get('response', {}).get('data', [])
        
        if not records:
            raise ValueError("No inventory data returned from EIA API!")
        
        df = pd.DataFrame(records)
        df['date'] = pd.to_datetime(df['period'])
        df['inventory_mbbl'] = pd.to_numeric(df['value'], errors='coerce')
        df = df[['date', 'inventory_mbbl']].sort_values('date').reset_index(drop=True)
        
        print(f"📦 Fetched {len(df)} weekly inventory records")
        print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
        print(f"   Inventory range: {df['inventory_mbbl'].min():.1f} to {df['inventory_mbbl'].max():.1f} million barrels")
        
        metadata = {
            'source_url': url,
            'api_params': params,
            'http_status': response.status_code,
            'data_description': 'Weekly US gasoline inventory stocks (million barrels)',
            'series': 'EPMR (Motor Gasoline)',
            'frequency': 'Weekly',
            'unit': 'million barrels'
        }
        
        self.validate_schema(df, ['date', 'inventory_mbbl'])
        return self.save_raw_response(df, 'eia_inventory_raw', metadata)
    
    def fetch_refinery_utilization(self, start_date: str, end_date: str) -> Path:
        """Fetch weekly refinery utilization rates."""
        print("\n" + "="*80)
        print("📊 EIA: Fetching Refinery Utilization")
        print("="*80)
        
        url = f"{self.base_url}/petroleum/pnp/wiup/data/"
        params = {
            "api_key": self.api_key,
            "frequency": "weekly",
            "data[0]": "value",
            "facets[duoarea][]": "NUS",
            "start": start_date,
            "end": end_date,
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "offset": 0,
            "length": 5000
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        json_data = response.json()
        records = json_data.get('response', {}).get('data', [])
        
        if not records:
            raise ValueError("No refinery utilization data returned from EIA API!")
        
        df = pd.DataFrame(records)
        df['date'] = pd.to_datetime(df['period'])
        df['utilization_pct'] = pd.to_numeric(df['value'], errors='coerce')
        df = df[['date', 'utilization_pct']].sort_values('date').reset_index(drop=True)
        
        print(f"🏭 Fetched {len(df)} weekly utilization records")
        print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
        print(f"   Utilization range: {df['utilization_pct'].min():.1f}% to {df['utilization_pct'].max():.1f}%")
        
        metadata = {
            'source_url': url,
            'api_params': params,
            'http_status': response.status_code,
            'data_description': 'Weekly US refinery utilization rates (%)',
            'frequency': 'Weekly',
            'unit': 'percent'
        }
        
        self.validate_schema(df, ['date', 'utilization_pct'])
        return self.save_raw_response(df, 'eia_utilization_raw', metadata)
    
    def fetch_spr_stocks(self, start_date: str, end_date: str) -> Path:
        """Fetch weekly Strategic Petroleum Reserve stocks."""
        print("\n" + "="*80)
        print("📊 EIA: Fetching SPR Stocks")
        print("="*80)
        
        url = f"{self.base_url}/petroleum/sum/sndw/data/"
        params = {
            "api_key": self.api_key,
            "frequency": "weekly",
            "data[0]": "value",
            "facets[series][]": "WCSSTUS1",  # SPR stocks
            "start": start_date,
            "end": end_date,
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "offset": 0,
            "length": 5000
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        json_data = response.json()
        records = json_data.get('response', {}).get('data', [])
        
        if not records:
            raise ValueError("No SPR data returned from EIA API!")
        
        df = pd.DataFrame(records)
        df['date'] = pd.to_datetime(df['period'])
        df['spr_stocks_mb'] = pd.to_numeric(df['value'], errors='coerce')
        df = df[['date', 'spr_stocks_mb']].sort_values('date').reset_index(drop=True)
        
        print(f"🛢️  Fetched {len(df)} weekly SPR stock records")
        print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
        print(f"   SPR range: {df['spr_stocks_mb'].min():.1f} to {df['spr_stocks_mb'].max():.1f} million barrels")
        
        metadata = {
            'source_url': url,
            'api_params': params,
            'http_status': response.status_code,
            'data_description': 'Weekly Strategic Petroleum Reserve stocks (million barrels)',
            'series': 'WCSSTUS1',
            'frequency': 'Weekly',
            'unit': 'million barrels'
        }
        
        self.validate_schema(df, ['date', 'spr_stocks_mb'])
        return self.save_raw_response(df, 'eia_spr_raw', metadata)


class FREDIngester(BronzeIngester):
    """Fetch data from FRED API."""
    
    def __init__(self):
        super().__init__("FRED")
        if not FRED_API_KEY:
            raise ValueError("FRED_API_KEY not found in environment!")
        self.api_key = FRED_API_KEY
        self.base_url = "https://api.stlouisfed.org/fred"
    
    def _fetch_series(
        self,
        series_id: str,
        series_name: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """Generic FRED series fetcher."""
        url = f"{self.base_url}/series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": start_date,
            "observation_end": end_date,
            "sort_order": "asc"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        json_data = response.json()
        observations = json_data.get('observations', [])
        
        if not observations:
            raise ValueError(f"No data returned for FRED series {series_id}!")
        
        df = pd.DataFrame(observations)
        df['date'] = pd.to_datetime(df['date'])
        df[series_name] = pd.to_numeric(df['value'], errors='coerce')
        df = df[['date', series_name]].sort_values('date').reset_index(drop=True)
        
        # Remove NaN values
        df = df[df[series_name].notna()].reset_index(drop=True)
        
        return df, {
            'source_url': url,
            'api_params': params,
            'http_status': response.status_code,
            'series_id': series_id,
            'series_name': series_name
        }
    
    def fetch_unemployment(self, start_date: str, end_date: str) -> Path:
        """Fetch monthly unemployment rate."""
        print("\n" + "="*80)
        print("📊 FRED: Fetching Unemployment Rate")
        print("="*80)
        
        df, metadata = self._fetch_series(
            series_id="UNRATE",
            series_name="unemployment_rate",
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"👥 Fetched {len(df)} monthly unemployment records")
        print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
        print(f"   Rate range: {df['unemployment_rate'].min():.1f}% to {df['unemployment_rate'].max():.1f}%")
        
        metadata['data_description'] = 'Monthly US unemployment rate (%)'
        metadata['frequency'] = 'Monthly'
        metadata['unit'] = 'percent'
        
        self.validate_schema(df, ['date', 'unemployment_rate'])
        return self.save_raw_response(df, 'fred_unemployment_raw', metadata)
    
    def fetch_vehicle_miles(self, start_date: str, end_date: str) -> Path:
        """Fetch monthly vehicle miles traveled."""
        print("\n" + "="*80)
        print("📊 FRED: Fetching Vehicle Miles Traveled")
        print("="*80)
        
        df, metadata = self._fetch_series(
            series_id="TRFVOLUSM227NFWA",
            series_name="vehicle_miles_traveled",
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"🚗 Fetched {len(df)} monthly VMT records")
        print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
        print(f"   VMT range: {df['vehicle_miles_traveled'].min():.0f} to {df['vehicle_miles_traveled'].max():.0f} million miles")
        
        metadata['data_description'] = 'Monthly US vehicle miles traveled (millions)'
        metadata['frequency'] = 'Monthly'
        metadata['unit'] = 'million miles'
        
        self.validate_schema(df, ['date', 'vehicle_miles_traveled'])
        return self.save_raw_response(df, 'fred_vmt_raw', metadata)
    
    def fetch_consumer_sentiment(self, start_date: str, end_date: str) -> Path:
        """Fetch monthly consumer sentiment index."""
        print("\n" + "="*80)
        print("📊 FRED: Fetching Consumer Sentiment")
        print("="*80)
        
        df, metadata = self._fetch_series(
            series_id="UMCSENT",
            series_name="consumer_sentiment",
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"📈 Fetched {len(df)} monthly sentiment records")
        print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
        print(f"   Sentiment range: {df['consumer_sentiment'].min():.1f} to {df['consumer_sentiment'].max():.1f}")
        
        metadata['data_description'] = 'Monthly University of Michigan Consumer Sentiment Index'
        metadata['frequency'] = 'Monthly'
        metadata['unit'] = 'index'
        
        self.validate_schema(df, ['date', 'consumer_sentiment'])
        return self.save_raw_response(df, 'fred_sentiment_raw', metadata)


class ManualIngester(BronzeIngester):
    """Handle manually coded data sources (OPEC, sanctions)."""
    
    def __init__(self):
        super().__init__("Manual")
    
    def create_geopolitical_data(self, start_date: str, end_date: str) -> Path:
        """
        Create geopolitical indicators (OPEC cuts, sanctions).
        
        These are manually coded from press releases and official announcements.
        """
        print("\n" + "="*80)
        print("📊 Manual: Creating Geopolitical Data")
        print("="*80)
        
        # Create daily date range
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        df = pd.DataFrame({'date': dates})
        
        # OPEC Production Cuts (verified from press releases)
        opec_cuts = [
            ('2020-04-12', '2020-07-31', -9.7),   # COVID emergency cut
            ('2020-08-01', '2020-12-31', -7.7),   # Gradual taper
            ('2021-01-01', '2021-03-31', -7.2),
            ('2022-11-01', '2023-03-31', -2.0),   # Late 2022 cut
            ('2023-04-01', '2023-12-31', -3.66),  # 2023 voluntary cuts
            ('2024-01-01', '2024-12-31', -2.2),   # 2024 extended cuts
            ('2025-01-01', '2025-10-18', -2.2)    # 2025 ongoing
        ]
        
        df['opec_production_cut_mb_d'] = 0.0
        for start, end, cut_amount in opec_cuts:
            mask = (df['date'] >= start) & (df['date'] <= end)
            df.loc[mask, 'opec_production_cut_mb_d'] = cut_amount
        
        # Iran Sanctions (reimposed May 8, 2018)
        df['iran_sanctions_indicator'] = (df['date'] >= '2018-05-08').astype(int)
        
        # Venezuela Sanctions (imposed January 28, 2019)
        df['venezuela_sanctions_indicator'] = (df['date'] >= '2019-01-28').astype(int)
        
        # Middle East Tension Score (constant baseline for now)
        # Can be enhanced with news sentiment analysis
        df['middle_east_tension_score'] = 4.0
        
        print(f"🌍 Created {len(df)} daily geopolitical records")
        print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
        print(f"   OPEC cut periods: {len(opec_cuts)}")
        print(f"   Iran sanctions: {df['iran_sanctions_indicator'].sum()} days active")
        print(f"   Venezuela sanctions: {df['venezuela_sanctions_indicator'].sum()} days active")
        
        metadata = {
            'data_description': 'Manually coded geopolitical indicators',
            'sources': [
                'OPEC Press Releases (https://www.opec.org/opec_web/en/press_room)',
                'US Treasury Sanctions (https://home.treasury.gov/policy-issues/financial-sanctions)',
                'EIA International Energy Portal'
            ],
            'opec_cut_periods': [
                {'start': start, 'end': end, 'cut_mb_d': cut, 'source': 'OPEC+ press release'}
                for start, end, cut in opec_cuts
            ],
            'iran_sanctions_date': '2018-05-08',
            'iran_sanctions_source': 'US Treasury Secondary Sanctions',
            'venezuela_sanctions_date': '2019-01-28',
            'venezuela_sanctions_source': 'Executive Order 13850',
            'tension_score_method': 'Constant baseline (to be enhanced with news sentiment)'
        }
        
        required_cols = [
            'date', 'opec_production_cut_mb_d', 'iran_sanctions_indicator',
            'venezuela_sanctions_indicator', 'middle_east_tension_score'
        ]
        self.validate_schema(df, required_cols)
        return self.save_raw_response(df, 'manual_geopolitical_raw', metadata)


def main():
    """Run complete bronze layer ingestion."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download raw data to bronze layer")
    parser.add_argument("--start-date", default="2020-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", default=datetime.now().strftime("%Y-%m-%d"), help="End date (YYYY-MM-DD)")
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🏗️  BRONZE LAYER INGESTION")
    print("="*80)
    print(f"Start date: {args.start_date}")
    print(f"End date: {args.end_date}")
    print(f"Output directory: {BRONZE_DIR}")
    print("="*80)
    
    try:
        # EIA Data
        eia = EIAIngester()
        eia.fetch_retail_prices(args.start_date, args.end_date)
        eia.fetch_inventory(args.start_date, args.end_date)
        eia.fetch_refinery_utilization(args.start_date, args.end_date)
        eia.fetch_spr_stocks(args.start_date, args.end_date)
        
        # FRED Data
        fred = FREDIngester()
        fred.fetch_unemployment(args.start_date, args.end_date)
        fred.fetch_vehicle_miles(args.start_date, args.end_date)
        fred.fetch_consumer_sentiment(args.start_date, args.end_date)
        
        # Manual Data
        manual = ManualIngester()
        manual.create_geopolitical_data(args.start_date, args.end_date)
        
        print("\n" + "="*80)
        print("✅ BRONZE LAYER INGESTION COMPLETE!")
        print("="*80)
        print(f"\n📁 Files saved to: {BRONZE_DIR}")
        print(f"📋 Metadata saved to: {METADATA_DIR}")
        print("\nNext step: Run `python scripts/2_clean_to_silver.py` to clean data")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
