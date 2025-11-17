"""
OpenBB Core Data Fetchers
==========================

Base classes and core functionality for fetching data from OpenBB Platform.
Provides error handling, retry logic, caching, and data validation.

Features:
    - Automatic retry on failure with exponential backoff
    - Intelligent caching to minimize API calls
    - Data validation and quality checks
    - Rate limiting protection
    - Comprehensive error handling
    - Performance monitoring
"""

import time
import logging
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from functools import wraps
from openbb import obb

from .config import OpenBBConfig, get_config

logger = logging.getLogger(__name__)


class OpenBBError(Exception):
    """Base exception for OpenBB integration errors"""
    pass


class APIError(OpenBBError):
    """API request failed"""
    pass


class ValidationError(OpenBBError):
    """Data validation failed"""
    pass


class RateLimitError(OpenBBError):
    """Rate limit exceeded"""
    pass


def retry_on_failure(max_attempts: int = 3, delay: int = 2, backoff: float = 2.0):
    """
    Decorator for automatic retry with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Exponential backoff multiplier
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except RateLimitError as e:
                    logger.warning(f"Rate limit hit, attempt {attempt+1}/{max_attempts}")
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay * 2)  # Longer wait for rate limits
                        current_delay *= backoff
                except Exception as e:
                    logger.warning(
                        f"Attempt {attempt+1}/{max_attempts} failed: {str(e)}"
                    )
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            # All attempts failed
            raise APIError(
                f"Failed after {max_attempts} attempts: {str(last_exception)}"
            ) from last_exception
        
        return wrapper
    return decorator


class OpenBBDataFetcher:
    """
    Base class for OpenBB data fetching with professional-grade features
    
    Provides core functionality for all data fetchers including error handling,
    caching, retry logic, and data validation.
    
    Attributes:
        config: OpenBB configuration instance
        obb: OpenBB instance
        cache_enabled: Whether caching is enabled
        last_request_time: Timestamp of last API request (for rate limiting)
    """
    
    def __init__(self, config: Optional[OpenBBConfig] = None):
        """
        Initialize data fetcher
        
        Args:
            config: OpenBB configuration, uses global if None
        """
        self.config = config or get_config()
        self.obb = obb
        self.cache_enabled = self.config.cache_enabled
        self.last_request_time = 0
        self._request_count = 0
        self._error_count = 0
        
        logger.info(f"Initialized {self.__class__.__name__}")
    
    def _enforce_rate_limit(self, min_delay: float = 0.2):
        """
        Enforce rate limiting between requests
        
        Args:
            min_delay: Minimum delay between requests in seconds
        """
        if not self.config.rate_limit_enabled:
            return
        
        elapsed = time.time() - self.last_request_time
        if elapsed < min_delay:
            sleep_time = min_delay - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """
        Get cache file path for a given key
        
        Args:
            cache_key: Unique identifier for cached data
        
        Returns:
            Path to cache file
        """
        safe_key = cache_key.replace('/', '_').replace(' ', '_')
        return self.config.cache_dir / f"{safe_key}.parquet"
    
    def _load_from_cache(
        self,
        cache_key: str,
        max_age_hours: Optional[int] = None
    ) -> Optional[pd.DataFrame]:
        """
        Load data from cache if available and fresh
        
        Args:
            cache_key: Cache identifier
            max_age_hours: Maximum age of cached data in hours
        
        Returns:
            Cached DataFrame or None if not available/stale
        """
        if not self.cache_enabled:
            return None
        
        cache_path = self._get_cache_path(cache_key)
        if not cache_path.exists():
            return None
        
        try:
            # Check cache age
            if max_age_hours is not None:
                cache_age = time.time() - cache_path.stat().st_mtime
                max_age_seconds = max_age_hours * 3600
                
                if cache_age > max_age_seconds:
                    logger.debug(f"Cache expired for {cache_key} ({cache_age/3600:.1f}h old)")
                    return None
            
            # Load cached data
            df = pd.read_parquet(cache_path)
            logger.info(f"Loaded {len(df)} rows from cache: {cache_key}")
            return df
            
        except Exception as e:
            logger.warning(f"Error loading cache for {cache_key}: {e}")
            return None
    
    def _save_to_cache(self, cache_key: str, data: pd.DataFrame):
        """
        Save data to cache
        
        Args:
            cache_key: Cache identifier
            data: DataFrame to cache
        """
        if not self.cache_enabled or data is None or data.empty:
            return
        
        try:
            cache_path = self._get_cache_path(cache_key)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            data.to_parquet(cache_path)
            logger.debug(f"Saved {len(data)} rows to cache: {cache_key}")
        except Exception as e:
            logger.warning(f"Error saving cache for {cache_key}: {e}")
    
    def _validate_dataframe(
        self,
        df: pd.DataFrame,
        required_columns: Optional[List[str]] = None,
        min_rows: int = 1
    ) -> bool:
        """
        Validate DataFrame structure and content
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            min_rows: Minimum number of rows required
        
        Returns:
            True if valid
        
        Raises:
            ValidationError: If validation fails
        """
        if df is None:
            raise ValidationError("DataFrame is None")
        
        if df.empty:
            raise ValidationError("DataFrame is empty")
        
        if len(df) < min_rows:
            raise ValidationError(
                f"DataFrame has {len(df)} rows, minimum {min_rows} required"
            )
        
        if required_columns:
            missing_cols = set(required_columns) - set(df.columns)
            if missing_cols:
                raise ValidationError(
                    f"Missing required columns: {missing_cols}"
                )
        
        return True
    
    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize DataFrame format (dates, columns, index)
        
        Args:
            df: Input DataFrame
        
        Returns:
            Standardized DataFrame
        """
        if df is None or df.empty:
            return df
        
        # Make a copy to avoid modifying original
        df = df.copy()
        
        # Ensure datetime index if date column exists
        date_cols = [col for col in df.columns if 'date' in col.lower()]
        if date_cols and 'date' not in df.index.name.lower() if df.index.name else True:
            df[date_cols[0]] = pd.to_datetime(df[date_cols[0]])
            df = df.set_index(date_cols[0])
        
        # Sort by index if it's a datetime
        if isinstance(df.index, pd.DatetimeIndex):
            df = df.sort_index()
        
        # Remove duplicate indices
        if df.index.duplicated().any():
            logger.warning(f"Removing {df.index.duplicated().sum()} duplicate rows")
            df = df[~df.index.duplicated(keep='first')]
        
        return df
    
    @retry_on_failure(max_attempts=3, delay=2)
    def _fetch_with_retry(
        self,
        fetch_func: Callable,
        *args,
        **kwargs
    ) -> pd.DataFrame:
        """
        Fetch data with automatic retry and error handling
        
        Args:
            fetch_func: Function to call for fetching data
            *args: Positional arguments for fetch_func
            **kwargs: Keyword arguments for fetch_func
        
        Returns:
            DataFrame with fetched data
        
        Raises:
            APIError: If fetch fails after retries
        """
        self._enforce_rate_limit()
        self._request_count += 1
        
        try:
            result = fetch_func(*args, **kwargs)
            
            # Convert to DataFrame if needed
            if not isinstance(result, pd.DataFrame):
                if hasattr(result, 'to_df'):
                    result = result.to_df()
                elif hasattr(result, 'results'):
                    result = pd.DataFrame(result.results)
                else:
                    result = pd.DataFrame(result)
            
            return self._standardize_dataframe(result)
            
        except Exception as e:
            self._error_count += 1
            logger.error(f"Fetch error: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about fetcher usage
        
        Returns:
            Dictionary with usage statistics
        """
        return {
            'request_count': self._request_count,
            'error_count': self._error_count,
            'error_rate': self._error_count / max(self._request_count, 1),
            'cache_enabled': self.cache_enabled
        }
    
    def clear_cache(self, cache_key: Optional[str] = None):
        """
        Clear cache for specific key or all cache
        
        Args:
            cache_key: Specific cache to clear, or None for all
        """
        if cache_key:
            cache_path = self._get_cache_path(cache_key)
            if cache_path.exists():
                cache_path.unlink()
                logger.info(f"Cleared cache: {cache_key}")
        else:
            # Clear all cache
            if self.config.cache_dir.exists():
                for cache_file in self.config.cache_dir.glob("*.parquet"):
                    cache_file.unlink()
                logger.info("Cleared all cache")


if __name__ == "__main__":
    # Test data fetcher
    logging.basicConfig(level=logging.INFO)
    
    fetcher = OpenBBDataFetcher()
    print(f"Fetcher initialized: {fetcher}")
    print(f"Stats: {fetcher.get_stats()}")
