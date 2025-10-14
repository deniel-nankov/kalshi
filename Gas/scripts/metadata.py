"""
Shared metadata utilities for tracking download times.

This module provides functions to save and retrieve metadata about
data source downloads, particularly the timestamp of the last successful download.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def get_last_download_time(source: str, bronze_dir: Path) -> Optional[datetime]:
    """
    Get the last download time for a data source.
    
    Args:
        source: Name of the data source (e.g., 'eia_inventory', 'rbob')
        bronze_dir: Path to the bronze data directory
        
    Returns:
        datetime of last download, or None if not found
    """
    metadata_file = bronze_dir / f"{source}_metadata.json"
    if not metadata_file.exists():
        return None
    
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
            timestamp_str = metadata.get('last_download')
            if timestamp_str:
                return datetime.fromisoformat(timestamp_str)
    except Exception as e:
        logger.warning(f"Could not read metadata for {source}: {e}")
    
    return None


def save_download_time(source: str, bronze_dir: Path) -> None:
    """
    Save the download time for a data source.
    
    Args:
        source: Name of the data source (e.g., 'eia_inventory', 'rbob')
        bronze_dir: Path to the bronze data directory
    """
    metadata_file = bronze_dir / f"{source}_metadata.json"
    bronze_dir.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        'last_download': datetime.now().isoformat(),
        'source': source
    }
    
    try:
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        logger.error(f"Could not save metadata for {source}: {e}")
