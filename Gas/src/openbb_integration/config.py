"""
OpenBB Configuration Management
================================

Handles all OpenBB Platform configuration, API keys, authentication,
and credential management with security best practices.

Features:
    - Secure API key management
    - Environment-based configuration
    - Multiple provider support
    - Credential validation
    - Rate limit configuration
    - Timeout and retry settings
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class OpenBBConfig:
    """
    OpenBB Platform Configuration
    
    Manages all configuration for OpenBB data providers with security
    and best practices built in.
    
    Attributes:
        base_dir: Base directory for configuration files
        api_keys: Dictionary of API keys for various providers
        cache_enabled: Whether to enable data caching
        cache_dir: Directory for cache storage
        rate_limit_enabled: Whether to enforce rate limits
        timeout: Request timeout in seconds
        retry_attempts: Number of retry attempts for failed requests
        retry_delay: Delay between retries in seconds
    """
    
    base_dir: Path = field(default_factory=lambda: Path("/home/runner/work/kalshi/kalshi/Gas"))
    api_keys: Dict[str, str] = field(default_factory=dict)
    cache_enabled: bool = True
    cache_dir: Path = field(default_factory=lambda: Path("/tmp/openbb_cache"))
    rate_limit_enabled: bool = True
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 2
    
    # Provider-specific settings
    fred_api_key: Optional[str] = None
    polygon_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None
    benzinga_api_key: Optional[str] = None
    intrinio_api_key: Optional[str] = None
    
    def __post_init__(self):
        """Initialize configuration after dataclass creation"""
        self._load_from_env()
        self._validate_config()
        self._setup_cache()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Load API keys from environment
        env_mappings = {
            'FRED_API_KEY': 'fred_api_key',
            'POLYGON_API_KEY': 'polygon_api_key',
            'ALPHA_VANTAGE_API_KEY': 'alpha_vantage_api_key',
            'BENZINGA_API_KEY': 'benzinga_api_key',
            'INTRINIO_API_KEY': 'intrinio_api_key',
        }
        
        for env_var, attr_name in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                setattr(self, attr_name, value)
                self.api_keys[env_var.replace('_API_KEY', '').lower()] = value
                logger.info(f"Loaded {env_var} from environment")
        
        # Load from .env file if exists
        env_file = self.base_dir / ".env"
        if env_file.exists():
            self._load_from_env_file(env_file)
    
    def _load_from_env_file(self, env_file: Path):
        """Load configuration from .env file"""
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        
                        if 'API_KEY' in key:
                            provider = key.replace('_API_KEY', '').lower()
                            self.api_keys[provider] = value
                            logger.info(f"Loaded {key} from .env file")
        except Exception as e:
            logger.warning(f"Error loading .env file: {e}")
    
    def _validate_config(self):
        """Validate configuration settings"""
        # Ensure timeout is reasonable
        if self.timeout < 5:
            logger.warning("Timeout too low, setting to minimum 5 seconds")
            self.timeout = 5
        
        # Validate retry attempts
        if self.retry_attempts < 1:
            logger.warning("Retry attempts must be at least 1")
            self.retry_attempts = 1
        
        if self.retry_attempts > 10:
            logger.warning("Too many retry attempts, capping at 10")
            self.retry_attempts = 10
    
    def _setup_cache(self):
        """Setup cache directory"""
        if self.cache_enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Cache directory: {self.cache_dir}")
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a specific provider
        
        Args:
            provider: Provider name (e.g., 'fred', 'polygon')
        
        Returns:
            API key if available, None otherwise
        """
        return self.api_keys.get(provider.lower())
    
    def has_api_key(self, provider: str) -> bool:
        """
        Check if API key is configured for provider
        
        Args:
            provider: Provider name
        
        Returns:
            True if API key is available
        """
        return provider.lower() in self.api_keys
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary (excluding sensitive data)
        
        Returns:
            Configuration dictionary
        """
        return {
            'base_dir': str(self.base_dir),
            'cache_enabled': self.cache_enabled,
            'cache_dir': str(self.cache_dir),
            'rate_limit_enabled': self.rate_limit_enabled,
            'timeout': self.timeout,
            'retry_attempts': self.retry_attempts,
            'retry_delay': self.retry_delay,
            'configured_providers': list(self.api_keys.keys())
        }
    
    def save_config(self, filepath: Optional[Path] = None):
        """
        Save configuration to JSON file (excluding API keys)
        
        Args:
            filepath: Path to save configuration, defaults to base_dir/openbb_config.json
        """
        if filepath is None:
            filepath = self.base_dir / "openbb_config.json"
        
        config_dict = self.to_dict()
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        logger.info(f"Configuration saved to {filepath}")
    
    @classmethod
    def load_config(cls, filepath: Optional[Path] = None) -> 'OpenBBConfig':
        """
        Load configuration from JSON file
        
        Args:
            filepath: Path to configuration file
        
        Returns:
            OpenBBConfig instance
        """
        if filepath is None:
            filepath = Path("/home/runner/work/kalshi/kalshi/Gas/openbb_config.json")
        
        if not filepath.exists():
            logger.info("No configuration file found, using defaults")
            return cls()
        
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        
        # Create config with loaded values
        config = cls()
        for key, value in config_dict.items():
            if key in ['base_dir', 'cache_dir']:
                setattr(config, key, Path(value))
            elif key != 'configured_providers':  # Skip this meta field
                setattr(config, key, value)
        
        logger.info(f"Configuration loaded from {filepath}")
        return config
    
    def __repr__(self) -> str:
        """String representation (safe, no API keys)"""
        return (
            f"OpenBBConfig("
            f"providers={len(self.api_keys)}, "
            f"cache_enabled={self.cache_enabled}, "
            f"timeout={self.timeout}s)"
        )


# Global configuration instance
_global_config: Optional[OpenBBConfig] = None


def get_config() -> OpenBBConfig:
    """
    Get global OpenBB configuration instance (singleton pattern)
    
    Returns:
        OpenBBConfig instance
    """
    global _global_config
    if _global_config is None:
        _global_config = OpenBBConfig()
    return _global_config


def set_config(config: OpenBBConfig):
    """
    Set global OpenBB configuration instance
    
    Args:
        config: OpenBBConfig instance to use globally
    """
    global _global_config
    _global_config = config
    logger.info("Global configuration updated")


if __name__ == "__main__":
    # Test configuration
    logging.basicConfig(level=logging.INFO)
    
    config = OpenBBConfig()
    print(config)
    print(f"Configuration: {config.to_dict()}")
    
    # Save configuration
    config.save_config()
    print("Configuration saved successfully")
