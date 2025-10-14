"""
Automated Bronze Data Updater

This script runs in the background and automatically downloads fresh data
to the Bronze layer based on data source schedules.

Data Source Update Times:
- EIA: Updates Wednesday 10:30 AM ET (weekly)
- RBOB Futures: Updates continuously during market hours (Mon-Fri 9:30 AM - 4:00 PM ET)
- Retail Prices: Updates Monday mornings (weekly, previous week data)

Usage:
    # Run once (check and update if needed)
    python scripts/automate_bronze.py
    
    # Run continuously with smart scheduling
    python scripts/automate_bronze.py --daemon
    
    # Run with custom check interval
    python scripts/automate_bronze.py --daemon --interval 3600  # Check every hour
    
    # Force update regardless of freshness
    python scripts/automate_bronze.py --force
"""

import subprocess
import sys
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
import json

# Import shared modules
from scheduling import DataSourceSchedule
from metadata import get_last_download_time, save_download_time
from script_runner import run_script_with_retry

# Setup paths
INGESTION_DIR = Path(__file__).parent.parent / "src" / "ingestion"
DATA_DIR = Path(__file__).parent.parent / "data"
BRONZE_DIR = DATA_DIR / "bronze"
LOG_DIR = Path(__file__).parent.parent / "logs"

# Ensure log directory exists
LOG_DIR.mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'bronze_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('bronze_automation')


# DataSourceSchedule now imported from scheduling.py
# metadata functions now imported from metadata.py
# script runner now imported from script_runner.py


def run_download_script(script_name: str, description: str, max_retries: int = 3) -> bool:
    """Run a download script with retries - wrapper around shared script_runner module"""
    script_path = INGESTION_DIR / script_name
    return run_script_with_retry(script_path, description, max_retries=max_retries, timeout=300)


def should_update_eia(force: bool = False) -> bool:
    """Check if EIA data should be updated"""
    if force:
        return True
    
    last_download = get_last_download_time('eia', BRONZE_DIR)
    if last_download is None:
        logger.info("EIA: No previous download found")
        return True
    
    # Check if it's been more than 7 days
    age_days = (datetime.now() - last_download).days
    if age_days >= 7:
        logger.info(f"EIA: Data is {age_days} days old (threshold: 7 days)")
        return True
    
    # Check if we're past Wednesday update time
    next_update = DataSourceSchedule.get_eia_update_time()
    if last_download < next_update <= datetime.now():
        logger.info(f"EIA: New data available (last: {last_download.date()}, update: {next_update.date()})")
        return True
    
    logger.info(f"EIA: Data is fresh (last download: {last_download})")
    return False


def should_update_rbob(force: bool = False) -> bool:
    """Check if RBOB data should be updated"""
    if force:
        return True
    
    last_download = get_last_download_time('rbob', BRONZE_DIR)
    
    # Update during market hours
    if not DataSourceSchedule.is_market_hours():
        logger.info("RBOB: Market is closed, skipping update")
        return False
    
    if last_download is None:
        logger.info("RBOB: No previous download found")
        return True
    
    # Update if it's been more than 1 hour during market hours
    age_hours = (datetime.now() - last_download).total_seconds() / 3600
    if age_hours >= 1:
        logger.info(f"RBOB: Data is {age_hours:.1f} hours old")
        return True
    
    logger.info(f"RBOB: Data is fresh (last download: {last_download})")
    return False


def should_update_retail(force: bool = False) -> bool:
    """Check if retail price data should be updated"""
    if force:
        return True
    
    last_download = get_last_download_time('retail', BRONZE_DIR)
    if last_download is None:
        logger.info("Retail: No previous download found")
        return True
    
    # Check if it's been more than 7 days
    age_days = (datetime.now() - last_download).days
    if age_days >= 7:
        logger.info(f"Retail: Data is {age_days} days old (threshold: 7 days)")
        return True
    
    # Check if we're past Monday update time
    next_update = DataSourceSchedule.get_retail_update_time()
    if last_download < next_update <= datetime.now():
        logger.info(f"Retail: New data available (last: {last_download.date()}, update: {next_update.date()})")
        return True
    
    logger.info(f"Retail: Data is fresh (last download: {last_download})")
    return False


def update_bronze_layer(force: bool = False) -> Dict[str, bool]:
    """Update Bronze layer with fresh data"""
    results = {}
    
    logger.info("=" * 80)
    logger.info("BRONZE LAYER AUTOMATION - Checking for updates")
    logger.info("=" * 80)
    
    # Check and update EIA data
    if should_update_eia(force):
        success = run_download_script(
            "download_eia_data_bronze.py",
            "EIA inventory/utilization data"
        )
        if success:
            save_download_time('eia', BRONZE_DIR)
        results['eia'] = success
    else:
        results['eia'] = None  # Skipped
    
    # Check and update RBOB data
    if should_update_rbob(force):
        success = run_download_script(
            "download_rbob_data_bronze.py",
            "RBOB/WTI futures data"
        )
        if success:
            save_download_time('rbob', BRONZE_DIR)
        results['rbob'] = success
    else:
        results['rbob'] = None  # Skipped
    
    # Check and update Retail data
    if should_update_retail(force):
        success = run_download_script(
            "download_retail_prices_bronze.py",
            "Retail gasoline prices"
        )
        if success:
            save_download_time('retail', BRONZE_DIR)
        results['retail'] = success
    else:
        results['retail'] = None  # Skipped
    
    logger.info("=" * 80)
    logger.info("BRONZE LAYER AUTOMATION - Summary")
    logger.info("=" * 80)
    
    for source, result in results.items():
        if result is True:
            logger.info(f"  ✅ {source.upper()}: Updated successfully")
        elif result is False:
            logger.error(f"  ❌ {source.upper()}: Update failed")
        else:
            logger.info(f"  ⏭️  {source.upper()}: Skipped (data is fresh)")
    
    return results


def run_daemon(check_interval: int = 3600):
    """Run as a daemon, checking periodically for updates"""
    logger.info("=" * 80)
    logger.info("BRONZE AUTOMATION DAEMON - Starting")
    logger.info("=" * 80)
    logger.info(f"Check interval: {check_interval} seconds ({check_interval/3600:.1f} hours)")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 80)
    
    try:
        while True:
            try:
                update_bronze_layer(force=False)
            except Exception as e:
                logger.error(f"Error during update cycle: {e}", exc_info=True)
            
            # Calculate next check time
            next_check = datetime.now() + timedelta(seconds=check_interval)
            logger.info(f"\nNext check at: {next_check.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Sleeping for {check_interval} seconds...")
            
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 80)
        logger.info("BRONZE AUTOMATION DAEMON - Stopped by user")
        logger.info("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Automated Bronze layer data updates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run once (check and update if needed)
  python scripts/automate_bronze.py
  
  # Run continuously, checking every hour
  python scripts/automate_bronze.py --daemon --interval 3600
  
  # Force update all sources
  python scripts/automate_bronze.py --force
  
  # Run as background process
  nohup python scripts/automate_bronze.py --daemon > /dev/null 2>&1 &

Data Source Schedules:
  - EIA: Wednesday 10:30 AM ET (weekly)
  - RBOB: Mon-Fri 9:30 AM - 4:00 PM ET (hourly during market hours)
  - Retail: Monday morning (weekly)
        """
    )
    
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run continuously as a daemon'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=3600,
        help='Check interval in seconds (default: 3600 = 1 hour)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force update all sources regardless of freshness'
    )
    
    args = parser.parse_args()
    
    if args.daemon:
        run_daemon(args.interval)
    else:
        results = update_bronze_layer(args.force)
        
        # Exit code: 0 if all successful, 1 if any failed
        failed = [s for s, r in results.items() if r is False]
        if failed:
            logger.error(f"Some updates failed: {', '.join(failed)}")
            return 1
        
        return 0


if __name__ == "__main__":
    sys.exit(main())
