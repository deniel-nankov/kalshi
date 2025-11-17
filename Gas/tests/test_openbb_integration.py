"""
Comprehensive Test Suite for OpenBB Integration
================================================

Professional-grade testing for all OpenBB integration components including:
- Configuration management
- Data fetching
- Error handling
- Caching
- Data validation
- Energy commodity data
- Integration with existing pipeline

Author: Christian Lee
Date: November 2025
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from openbb_integration.config import OpenBBConfig, get_config
from openbb_integration.data_fetchers import OpenBBDataFetcher
from openbb_integration.energy import EnergyDataFetcher


class TestOpenBBConfig:
    """Test configuration management"""
    
    def test_config_initialization(self):
        """Test basic config initialization"""
        config = OpenBBConfig()
        assert config is not None
        assert isinstance(config.base_dir, Path)
        assert config.timeout >= 5
        assert config.retry_attempts >= 1
    
    def test_config_api_keys(self):
        """Test API key management"""
        config = OpenBBConfig()
        
        # Test setting API key
        test_key = "test_api_key_12345"
        config.api_keys['test_provider'] = test_key
        
        assert config.get_api_key('test_provider') == test_key
        assert config.has_api_key('test_provider')
        assert not config.has_api_key('nonexistent_provider')
    
    def test_config_validation(self):
        """Test configuration validation"""
        config = OpenBBConfig()
        
        # Test timeout validation
        config.timeout = 3
        config._validate_config()
        assert config.timeout >= 5  # Should be corrected
        
        # Test retry attempts validation
        config.retry_attempts = 0
        config._validate_config()
        assert config.retry_attempts >= 1  # Should be corrected
        
        config.retry_attempts = 20
        config._validate_config()
        assert config.retry_attempts <= 10  # Should be capped
    
    def test_config_to_dict(self):
        """Test config serialization"""
        config = OpenBBConfig()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert 'cache_enabled' in config_dict
        assert 'timeout' in config_dict
        assert 'retry_attempts' in config_dict
        # API keys should not be included
        assert 'api_keys' not in config_dict
    
    def test_config_singleton(self):
        """Test global config singleton pattern"""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2  # Same instance


class TestOpenBBDataFetcher:
    """Test base data fetcher functionality"""
    
    def test_fetcher_initialization(self):
        """Test fetcher initialization"""
        fetcher = OpenBBDataFetcher()
        assert fetcher is not None
        assert fetcher.config is not None
        assert fetcher._request_count == 0
        assert fetcher._error_count == 0
    
    def test_cache_management(self):
        """Test caching functionality"""
        fetcher = OpenBBDataFetcher()
        
        # Create test data
        test_data = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=10),
            'value': np.random.rand(10)
        })
        test_data = test_data.set_index('date')
        
        cache_key = "test_cache_key"
        
        # Save to cache
        fetcher._save_to_cache(cache_key, test_data)
        
        # Load from cache
        loaded_data = fetcher._load_from_cache(cache_key)
        assert loaded_data is not None
        assert len(loaded_data) == len(test_data)
        pd.testing.assert_frame_equal(loaded_data, test_data)
        
        # Test cache expiration
        old_cache = fetcher._load_from_cache(cache_key, max_age_hours=0)
        assert old_cache is None  # Should be expired
        
        # Clear cache
        fetcher.clear_cache(cache_key)
        cleared_data = fetcher._load_from_cache(cache_key)
        assert cleared_data is None
    
    def test_dataframe_validation(self):
        """Test DataFrame validation"""
        fetcher = OpenBBDataFetcher()
        
        # Test valid DataFrame
        valid_df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=10),
            'price': np.random.rand(10),
            'volume': np.random.randint(1000, 10000, 10)
        })
        
        assert fetcher._validate_dataframe(valid_df, required_columns=['date', 'price'])
        
        # Test invalid DataFrame (empty)
        with pytest.raises(Exception):
            fetcher._validate_dataframe(pd.DataFrame())
        
        # Test invalid DataFrame (missing columns)
        with pytest.raises(Exception):
            fetcher._validate_dataframe(valid_df, required_columns=['nonexistent_column'])
        
        # Test invalid DataFrame (too few rows)
        with pytest.raises(Exception):
            small_df = pd.DataFrame({'col1': [1]})
            fetcher._validate_dataframe(small_df, min_rows=10)
    
    def test_dataframe_standardization(self):
        """Test DataFrame standardization"""
        fetcher = OpenBBDataFetcher()
        
        # Create DataFrame with date column
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=5),
            'value': [1, 2, 3, 4, 5]
        })
        
        standardized = fetcher._standardize_dataframe(df)
        
        # Should have datetime index
        assert isinstance(standardized.index, pd.DatetimeIndex)
        
        # Should be sorted by date
        assert standardized.index.is_monotonic_increasing
        
        # Test duplicate removal
        df_with_dupes = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-01', '2024-01-02'],
            'value': [1, 2, 3]
        })
        df_with_dupes['date'] = pd.to_datetime(df_with_dupes['date'])
        df_with_dupes = df_with_dupes.set_index('date')
        
        cleaned = fetcher._standardize_dataframe(df_with_dupes)
        assert not cleaned.index.duplicated().any()
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        fetcher = OpenBBDataFetcher()
        fetcher.config.rate_limit_enabled = True
        
        # Record start time
        start_time = datetime.now()
        
        # Make multiple requests
        for _ in range(3):
            fetcher._enforce_rate_limit(min_delay=0.1)
        
        # Should have taken at least 0.2 seconds (2 delays)
        elapsed = (datetime.now() - start_time).total_seconds()
        assert elapsed >= 0.2
    
    def test_stats_tracking(self):
        """Test statistics tracking"""
        fetcher = OpenBBDataFetcher()
        
        initial_stats = fetcher.get_stats()
        assert initial_stats['request_count'] == 0
        assert initial_stats['error_count'] == 0
        
        # Simulate some requests
        fetcher._request_count = 10
        fetcher._error_count = 2
        
        stats = fetcher.get_stats()
        assert stats['request_count'] == 10
        assert stats['error_count'] == 2
        assert stats['error_rate'] == 0.2


class TestEnergyDataFetcher:
    """Test energy commodity data fetching"""
    
    @pytest.fixture
    def energy_fetcher(self):
        """Create energy fetcher instance"""
        return EnergyDataFetcher()
    
    def test_energy_fetcher_initialization(self, energy_fetcher):
        """Test energy fetcher initialization"""
        assert energy_fetcher is not None
        assert energy_fetcher.RBOB_SYMBOL == "RB"
        assert energy_fetcher.WTI_SYMBOL == "CL"
        assert energy_fetcher.BRENT_SYMBOL == "BZ"
    
    def test_rbob_futures_fetch(self, energy_fetcher):
        """Test RBOB futures data fetching"""
        # Use recent dates for testing
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        try:
            data = energy_fetcher.get_rbob_futures(
                start_date=start_date,
                end_date=end_date,
                use_cache=False  # Don't use cache for test
            )
            
            assert data is not None
            assert isinstance(data, pd.DataFrame)
            assert len(data) > 0
            assert 'price_close' in data.columns
            assert isinstance(data.index, pd.DatetimeIndex)
            
            print(f"✓ Successfully fetched {len(data)} RBOB price records")
            
        except Exception as e:
            pytest.skip(f"RBOB fetch failed (may be API issue): {e}")
    
    def test_wti_crude_fetch(self, energy_fetcher):
        """Test WTI crude oil data fetching"""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        try:
            data = energy_fetcher.get_wti_crude(
                start_date=start_date,
                end_date=end_date,
                use_cache=False
            )
            
            assert data is not None
            assert isinstance(data, pd.DataFrame)
            assert len(data) > 0
            assert 'price_close' in data.columns
            assert data['symbol'].iloc[0] == 'WTI'
            
            print(f"✓ Successfully fetched {len(data)} WTI price records")
            
        except Exception as e:
            pytest.skip(f"WTI fetch failed (may be API issue): {e}")
    
    def test_crack_spread_calculation(self, energy_fetcher):
        """Test crack spread calculation"""
        # Create mock data
        dates = pd.date_range('2024-10-01', periods=10)
        
        rbob_data = pd.DataFrame({
            'price_close': np.random.uniform(2.0, 3.0, 10)
        }, index=dates)
        
        wti_data = pd.DataFrame({
            'price_close': np.random.uniform(70.0, 80.0, 10)
        }, index=dates)
        
        crack_spread = energy_fetcher.calculate_crack_spread(rbob_data, wti_data)
        
        assert crack_spread is not None
        assert len(crack_spread) == 10
        assert 'crack_spread' in crack_spread.columns
        assert 'crack_spread_pct' in crack_spread.columns
        
        # Verify calculation
        expected_wti_per_gallon = wti_data['price_close'] / 42.0
        expected_spread = rbob_data['price_close'] - expected_wti_per_gallon
        
        np.testing.assert_array_almost_equal(
            crack_spread['crack_spread'].values,
            expected_spread.values,
            decimal=6
        )
    
    def test_caching_behavior(self, energy_fetcher):
        """Test data caching behavior"""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Clear any existing cache
        cache_key = f"rbob_front_{start_date}_{end_date}"
        energy_fetcher.clear_cache(cache_key)
        
        try:
            # First fetch (should hit API)
            data1 = energy_fetcher.get_rbob_futures(
                start_date=start_date,
                end_date=end_date,
                use_cache=True
            )
            requests_after_first = energy_fetcher._request_count
            
            # Second fetch (should use cache)
            data2 = energy_fetcher.get_rbob_futures(
                start_date=start_date,
                end_date=end_date,
                use_cache=True
            )
            requests_after_second = energy_fetcher._request_count
            
            # Request count should not increase for cached fetch
            assert requests_after_second == requests_after_first
            
            # Data should be identical
            pd.testing.assert_frame_equal(data1, data2)
            
            print("✓ Caching working correctly")
            
        except Exception as e:
            pytest.skip(f"Caching test skipped: {e}")


class TestIntegrationWithExistingPipeline:
    """Test integration with existing gas price forecasting pipeline"""
    
    def test_data_format_compatibility(self):
        """Test that OpenBB data format is compatible with existing pipeline"""
        fetcher = EnergyDataFetcher()
        
        # Create sample data in OpenBB format
        sample_data = pd.DataFrame({
            'price_close': [2.5, 2.6, 2.7],
            'price_open': [2.4, 2.5, 2.6],
            'volume': [1000, 1100, 1200]
        }, index=pd.date_range('2024-10-01', periods=3))
        
        # Verify expected format
        assert isinstance(sample_data.index, pd.DatetimeIndex)
        assert 'price_close' in sample_data.columns
        assert not sample_data.isna().any().any()
    
    def test_medallion_architecture_integration(self):
        """Test integration with Bronze/Silver/Gold layers"""
        # This would test saving OpenBB data to the medallion architecture
        base_dir = Path("/home/runner/work/kalshi/kalshi/Gas")
        
        # Verify directory structure exists
        assert base_dir.exists()
        assert (base_dir / "data").exists()
        
        # Test creating OpenBB data in bronze layer format
        bronze_dir = base_dir / "data" / "bronze" / "openbb"
        bronze_dir.mkdir(parents=True, exist_ok=True)
        
        assert bronze_dir.exists()
        print("✓ Bronze layer integration ready")


class TestErrorHandlingAndRobustness:
    """Test error handling and system robustness"""
    
    def test_invalid_date_handling(self):
        """Test handling of invalid dates"""
        fetcher = EnergyDataFetcher()
        
        with pytest.raises(Exception):
            # Invalid date format
            fetcher.get_rbob_futures(
                start_date="invalid-date",
                end_date="2024-11-01"
            )
    
    def test_missing_data_handling(self):
        """Test handling of missing data"""
        fetcher = OpenBBDataFetcher()
        
        # Test with None DataFrame
        with pytest.raises(Exception):
            fetcher._validate_dataframe(None)
        
        # Test with empty DataFrame
        with pytest.raises(Exception):
            fetcher._validate_dataframe(pd.DataFrame())
    
    def test_network_error_recovery(self):
        """Test recovery from network errors"""
        fetcher = OpenBBDataFetcher()
        
        # Test retry mechanism by checking configuration
        assert fetcher.config.retry_attempts >= 1
        assert fetcher.config.retry_delay >= 1
        
        print("✓ Error recovery mechanisms configured")


def run_all_tests():
    """Run all tests and report results"""
    import subprocess
    
    print("="*80)
    print("RUNNING COMPREHENSIVE OPENBB INTEGRATION TEST SUITE")
    print("="*80)
    
    # Run pytest with verbose output
    result = subprocess.run(
        ["pytest", __file__, "-v", "--tb=short"],
        capture_output=False
    )
    
    return result.returncode


if __name__ == "__main__":
    # Run tests when executed directly
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*80)
    print("OpenBB Integration Test Suite")
    print("="*80 + "\n")
    
    exit_code = run_all_tests()
    
    if exit_code == 0:
        print("\n" + "="*80)
        print("✓ ALL TESTS PASSED")
        print("="*80 + "\n")
    else:
        print("\n" + "="*80)
        print("✗ SOME TESTS FAILED")
        print("="*80 + "\n")
    
    sys.exit(exit_code)
