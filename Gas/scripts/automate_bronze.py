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


class DataSourceSchedule:
    """Data source update schedules"""
    
    # EIA updates: Wednesday 10:30 AM ET
    EIA_UPDATE_DAY = 2  # Wednesday (0 = Monday)
    EIA_UPDATE_HOUR = 15  # 10:30 AM ET = 15:30 UTC (approximate)
    EIA_UPDATE_MINUTE = 30
    
    # RBOB: Market hours Mon-Fri 9:30 AM - 4:00 PM ET
    RBOB_MARKET_OPEN_HOUR = 14  # 9:30 AM ET = ~14:30 UTC
    RBOB_MARKET_CLOSE_HOUR = 21  # 4:00 PM ET = ~21:00 UTC
    
    # Retail: Updates Monday morning with previous week data
    RETAIL_UPDATE_DAY = 0  # Monday
    RETAIL_UPDATE_HOUR = 12  # Noon ET = ~17:00 UTC
    
    @staticmethod
    def get_eia_update_time() -> datetime:
        """Get next EIA update time"""
        now = datetime.now()
        days_ahead = (DataSourceSchedule.EIA_UPDATE_DAY - now.weekday()) % 7
        if days_ahead == 0:
            # Today is Wednesday - check if update time has passed
            update_time = now.replace(
                hour=DataSourceSchedule.EIA_UPDATE_HOUR,
                minute=DataSourceSchedule.EIA_UPDATE_MINUTE,
                second=0,
                microsecond=0
            )
            if now >= update_time:
                days_ahead = 7  # Next week
        
        next_update = now + timedelta(days=days_ahead)
        next_update = next_update.replace(
            hour=DataSourceSchedule.EIA_UPDATE_HOUR,
            minute=DataSourceSchedule.EIA_UPDATE_MINUTE,
            second=0,
            microsecond=0
        )
        return next_update
    
    @staticmethod
    def is_market_hours() -> bool:
        """Check if it's currently market hours for RBOB"""
        now = datetime.now()
        # Market closed on weekends
        if now.weekday() >= 5:  # Saturday or Sunday
            return False
        
        # Check market hours
        hour = now.hour
        return DataSourceSchedule.RBOB_MARKET_OPEN_HOUR <= hour <= DataSourceSchedule.RBOB_MARKET_CLOSE_HOUR
    
    @staticmethod
    def get_retail_update_time() -> datetime:
        """Get next retail price update time"""
        now = datetime.now()
        days_ahead = (DataSourceSchedule.RETAIL_UPDATE_DAY - now.weekday()) % 7
        if days_ahead == 0:
            # Today is Monday - check if update time has passed
            update_time = now.replace(
                hour=DataSourceSchedule.RETAIL_UPDATE_HOUR,
                minute=0,
                second=0,
                microsecond=0
            )
            if now >= update_time:
                days_ahead = 7  # Next week
        
        next_update = now + timedelta(days=days_ahead)
        next_update = next_update.replace(
            hour=DataSourceSchedule.RETAIL_UPDATE_HOUR,
            minute=0,
            second=0,
            microsecond=0
        )
        return next_update


def get_last_download_time(source: str) -> Optional[datetime]:
    """Get the last download time for a data source"""
    metadata_file = BRONZE_DIR / f"{source}_metadata.json"
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


def save_download_time(source: str):
    """Save the download time for a data source"""
    metadata_file = BRONZE_DIR / f"{source}_metadata.json"
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        'last_download': datetime.now().isoformat(),
        'source': source
    }
    
    try:
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        logger.error(f"Could not save metadata for {source}: {e}")


def run_download_script(script_name: str, description: str, max_retries: int = 3) -> bool:
    """Run a download script with retries"""
    script_path = INGESTION_DIR / script_name
    
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False
    
    for attempt in range(1, max_retries + 1):
        logger.info(f"Downloading {description} (attempt {attempt}/{max_retries})")
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            logger.info(f"✅ Successfully downloaded {description}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout downloading {description}")
            if attempt < max_retries:
                wait_time = 30 * attempt  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to download {description}: {e.stderr}")
            if attempt < max_retries:
                wait_time = 30 * attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
    
    logger.error(f"❌ Failed to download {description} after {max_retries} attempts")
    return False


def should_update_eia(force: bool = False) -> bool:
    """Check if EIA data should be updated"""
    if force:
        return True
    
    last_download = get_last_download_time('eia')
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
    
    last_download = get_last_download_time('rbob')
    
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
    
    last_download = get_last_download_time('retail')
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
            save_download_time('eia')
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
            save_download_time('rbob')
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
            save_download_time('retail')
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
