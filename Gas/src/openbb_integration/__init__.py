"""OpenBB Platform Integration Module"""
__version__ = "1.0.0"

from .config import OpenBBConfig, get_config, set_config
from .data_fetchers import OpenBBDataFetcher
from .energy import EnergyDataFetcher

__all__ = [
    "OpenBBConfig",
    "get_config", 
    "set_config",
    "OpenBBDataFetcher",
    "EnergyDataFetcher"
]
