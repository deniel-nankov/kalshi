"""
OpenBB Energy Data Fetcher
===========================

Specialized module for fetching energy commodity data using OpenBB Platform.
Focuses on petroleum products critical for gas price forecasting.

Features:
    - RBOB gasoline futures data
    - WTI and Brent crude oil prices
    - Natural gas prices
    - Heating oil and diesel
    - Energy product spreads (crack spreads, basis)
    - NYMEX and ICE futures data
    - Real-time and historical data
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from .data_fetchers import OpenBBDataFetcher, OpenBBError
from .config import OpenBBConfig

logger = logging.getLogger(__name__)


class EnergyDataFetcher(OpenBBDataFetcher):
    """
    Fetch energy commodity data from OpenBB Platform
    
    Provides access to petroleum products, natural gas, and related
    energy commodities with built-in caching and error handling.
    """
    
    # Common energy symbols
    RBOB_SYMBOL = "RB"  # RBOB Gasoline futures
    WTI_SYMBOL = "CL"  # WTI Crude Oil futures
    BRENT_SYMBOL = "BZ"  # Brent Crude Oil futures
    NATURAL_GAS_SYMBOL = "NG"  # Natural Gas futures
    HEATING_OIL_SYMBOL = "HO"  # Heating Oil futures
    
    def __init__(self, config: Optional[OpenBBConfig] = None):
        """
        Initialize energy data fetcher
        
        Args:
            config: OpenBB configuration
        """
        super().__init__(config)
        logger.info("Initialized EnergyDataFetcher")
    
    def get_rbob_futures(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        contract: str = "front",
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Get RBOB gasoline futures prices
        
        RBOB (Reformulated Blendstock for Oxygenate Blending) is the
        primary wholesale gasoline benchmark in the US.
        
        Args:
            start_date: Start date (YYYY-MM-DD), defaults to 1 year ago
            end_date: End date (YYYY-MM-DD), defaults to today
            contract: Contract type ('front', 'second', or specific month)
            use_cache: Whether to use cached data
        
        Returns:
            DataFrame with RBOB futures data including:
                - open, high, low, close prices ($/gallon)
                - volume
                - open interest
        """
        # Set default dates
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        cache_key = f"rbob_{contract}_{start_date}_{end_date}"
        
        # Try cache first
        if use_cache:
            cached_data = self._load_from_cache(cache_key, max_age_hours=24)
            if cached_data is not None:
                return cached_data
        
        try:
            # Fetch from OpenBB using yfinance provider
            logger.info(f"Fetching RBOB futures from {start_date} to {end_date}")
            
            # RBOB futures ticker symbol
            symbol = f"{self.RBOB_SYMBOL}=F"  # Yahoo Finance futures format
            
            data = self._fetch_with_retry(
                self.obb.equity.price.historical,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                provider="yfinance"
            )
            
            # Validate and standardize
            self._validate_dataframe(
                data,
                required_columns=['close'],
                min_rows=1
            )
            
            # Rename columns to standard format
            data = data.rename(columns={
                'open': 'price_open',
                'high': 'price_high',
                'low': 'price_low',
                'close': 'price_close',
                'volume': 'volume'
            })
            
            # Add metadata
            data['symbol'] = 'RBOB'
            data['contract'] = contract
            data['unit'] = 'USD_per_gallon'
            
            # Save to cache
            if use_cache:
                self._save_to_cache(cache_key, data)
            
            logger.info(f"Fetched {len(data)} RBOB price records")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching RBOB futures: {e}")
            raise OpenBBError(f"Failed to fetch RBOB futures: {e}")
    
    def get_wti_crude(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Get WTI crude oil futures prices
        
        West Texas Intermediate (WTI) is the primary US crude oil benchmark.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            use_cache: Whether to use cached data
        
        Returns:
            DataFrame with WTI crude prices
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        cache_key = f"wti_{start_date}_{end_date}"
        
        if use_cache:
            cached_data = self._load_from_cache(cache_key, max_age_hours=24)
            if cached_data is not None:
                return cached_data
        
        try:
            logger.info(f"Fetching WTI crude from {start_date} to {end_date}")
            
            symbol = f"{self.WTI_SYMBOL}=F"
            
            data = self._fetch_with_retry(
                self.obb.equity.price.historical,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                provider="yfinance"
            )
            
            self._validate_dataframe(data, required_columns=['close'], min_rows=1)
            
            data = data.rename(columns={
                'open': 'price_open',
                'high': 'price_high',
                'low': 'price_low',
                'close': 'price_close',
                'volume': 'volume'
            })
            
            data['symbol'] = 'WTI'
            data['unit'] = 'USD_per_barrel'
            
            if use_cache:
                self._save_to_cache(cache_key, data)
            
            logger.info(f"Fetched {len(data)} WTI price records")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching WTI crude: {e}")
            raise OpenBBError(f"Failed to fetch WTI crude: {e}")
    
    def get_brent_crude(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Get Brent crude oil futures prices
        
        Brent Crude is the international oil benchmark.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            use_cache: Whether to use cached data
        
        Returns:
            DataFrame with Brent crude prices
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        cache_key = f"brent_{start_date}_{end_date}"
        
        if use_cache:
            cached_data = self._load_from_cache(cache_key, max_age_hours=24)
            if cached_data is not None:
                return cached_data
        
        try:
            logger.info(f"Fetching Brent crude from {start_date} to {end_date}")
            
            symbol = f"{self.BRENT_SYMBOL}=F"
            
            data = self._fetch_with_retry(
                self.obb.equity.price.historical,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                provider="yfinance"
            )
            
            self._validate_dataframe(data, required_columns=['close'], min_rows=1)
            
            data = data.rename(columns={
                'open': 'price_open',
                'high': 'price_high',
                'low': 'price_low',
                'close': 'price_close',
                'volume': 'volume'
            })
            
            data['symbol'] = 'BRENT'
            data['unit'] = 'USD_per_barrel'
            
            if use_cache:
                self._save_to_cache(cache_key, data)
            
            logger.info(f"Fetched {len(data)} Brent price records")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching Brent crude: {e}")
            raise OpenBBError(f"Failed to fetch Brent crude: {e}")
    
    def calculate_crack_spread(
        self,
        rbob_data: pd.DataFrame,
        wti_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate the crack spread (RBOB - WTI)
        
        The crack spread represents the refining margin - the profit
        refiners make converting crude oil to gasoline.
        
        Args:
            rbob_data: RBOB gasoline prices DataFrame
            wti_data: WTI crude prices DataFrame
        
        Returns:
            DataFrame with crack spread values
        """
        try:
            # Merge on date index
            merged = pd.merge(
                rbob_data[['price_close']].rename(columns={'price_close': 'rbob_price'}),
                wti_data[['price_close']].rename(columns={'price_close': 'wti_price'}),
                left_index=True,
                right_index=True,
                how='inner'
            )
            
            # Convert WTI from $/barrel to $/gallon (42 gallons per barrel)
            merged['wti_price_per_gallon'] = merged['wti_price'] / 42.0
            
            # Calculate crack spread
            merged['crack_spread'] = merged['rbob_price'] - merged['wti_price_per_gallon']
            
            # Calculate percentage spread
            merged['crack_spread_pct'] = (
                (merged['crack_spread'] / merged['wti_price_per_gallon']) * 100
            )
            
            result = merged[['rbob_price', 'wti_price_per_gallon', 'crack_spread', 'crack_spread_pct']]
            
            logger.info(f"Calculated crack spread for {len(result)} periods")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating crack spread: {e}")
            raise OpenBBError(f"Failed to calculate crack spread: {e}")
    
    def get_all_energy_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Get all energy commodity data in one call
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            use_cache: Whether to use cached data
        
        Returns:
            Dictionary with DataFrames for each commodity:
                - 'rbob': RBOB gasoline futures
                - 'wti': WTI crude oil
                - 'brent': Brent crude oil
                - 'crack_spread': Calculated crack spread
        """
        logger.info("Fetching all energy commodity data")
        
        result = {}
        
        # Fetch each commodity
        try:
            result['rbob'] = self.get_rbob_futures(start_date, end_date, use_cache=use_cache)
        except Exception as e:
            logger.error(f"Failed to fetch RBOB: {e}")
            result['rbob'] = None
        
        try:
            result['wti'] = self.get_wti_crude(start_date, end_date, use_cache=use_cache)
        except Exception as e:
            logger.error(f"Failed to fetch WTI: {e}")
            result['wti'] = None
        
        try:
            result['brent'] = self.get_brent_crude(start_date, end_date, use_cache=use_cache)
        except Exception as e:
            logger.error(f"Failed to fetch Brent: {e}")
            result['brent'] = None
        
        # Calculate crack spread if we have both RBOB and WTI
        if result['rbob'] is not None and result['wti'] is not None:
            try:
                result['crack_spread'] = self.calculate_crack_spread(
                    result['rbob'],
                    result['wti']
                )
            except Exception as e:
                logger.error(f"Failed to calculate crack spread: {e}")
                result['crack_spread'] = None
        
        logger.info("Completed fetching all energy data")
        return result


if __name__ == "__main__":
    # Test energy data fetcher
    logging.basicConfig(level=logging.INFO)
    
    fetcher = EnergyDataFetcher()
    
    # Test RBOB fetch
    print("\nFetching RBOB futures...")
    rbob = fetcher.get_rbob_futures(
        start_date="2024-10-01",
        end_date="2024-11-01"
    )
    print(f"RBOB data shape: {rbob.shape}")
    print(rbob.head())
    
    # Test WTI fetch
    print("\nFetching WTI crude...")
    wti = fetcher.get_wti_crude(
        start_date="2024-10-01",
        end_date="2024-11-01"
    )
    print(f"WTI data shape: {wti.shape}")
    print(wti.head())
    
    # Test crack spread calculation
    print("\nCalculating crack spread...")
    crack_spread = fetcher.calculate_crack_spread(rbob, wti)
    print(f"Crack spread shape: {crack_spread.shape}")
    print(crack_spread.head())
    
    # Test stats
    print(f"\nFetcher stats: {fetcher.get_stats()}")
