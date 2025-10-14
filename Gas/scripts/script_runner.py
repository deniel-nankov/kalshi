"""
Shared script execution utilities with retry logic.

This module provides functions to execute Python scripts with
timeout, retry logic, and exponential backoff for transient failures.
"""

from __future__ import annotations

import logging
import random
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def run_script_with_retry(
    script_path: Path,
    description: str,
    max_retries: int = 3,
    timeout: int = 300,
    add_jitter: bool = True
) -> bool:
    """
    Run a Python script with retry logic and timeout.
    
    Args:
        script_path: Path to the Python script to execute
        description: Human-readable description for logging
        max_retries: Maximum number of retry attempts (default: 3)
        timeout: Timeout in seconds for each attempt (default: 300 = 5 minutes)
        add_jitter: Add random jitter to backoff to prevent thundering herd (default: True)
        
    Returns:
        True if script succeeded, False if all retries failed
    """
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False
    
    for attempt in range(1, max_retries + 1):
        logger.info(f"Running {description} (attempt {attempt}/{max_retries})")
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            logger.info(f"✅ Successfully completed {description}")
            if result.stdout:
                logger.debug(f"Output: {result.stdout}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout running {description} (exceeded {timeout}s)")
            if attempt < max_retries:
                wait_time = _calculate_backoff(attempt, add_jitter)
                logger.info(f"Retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to run {description}: {e.stderr}")
            if attempt < max_retries:
                wait_time = _calculate_backoff(attempt, add_jitter)
                logger.info(f"Retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
        
        except Exception as e:
            logger.error(f"Unexpected error running {description}: {e}")
            if attempt < max_retries:
                wait_time = _calculate_backoff(attempt, add_jitter)
                logger.info(f"Retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
    
    logger.error(f"❌ Failed to complete {description} after {max_retries} attempts")
    return False


def _calculate_backoff(attempt: int, add_jitter: bool = True) -> float:
    """
    Calculate exponential backoff with optional jitter.
    
    Args:
        attempt: Current attempt number (1-indexed)
        add_jitter: Add random jitter to prevent thundering herd
        
    Returns:
        Wait time in seconds
    """
    base_wait = 30 * attempt  # 30s, 60s, 90s, ...
    
    if add_jitter:
        # Add ±20% jitter
        jitter_factor = 1 + (random.random() * 0.4 - 0.2)
        return base_wait * jitter_factor
    
    return base_wait
