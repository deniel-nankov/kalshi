"""
Automated Bronze → Silver Pipeline

This script automatically:
1. Checks for fresh Bronze data (smart scheduling)
2. Downloads new Bronze data when available
3. Automatically rebuilds Silver layer when Bronze is updated
4. Tracks processing state to avoid redundant rebuilds

Usage:
    # Run once (check Bronze, rebuild Silver if needed)
    python scripts/automate_bronze_silver.py
    
    # Run continuously with auto-processing
    python scripts/automate_bronze_silver.py --daemon
    
    # Run with custom check interval
    python scripts/automate_bronze_silver.py --daemon --interval 3600
    
    # Force update both layers
    python scripts/automate_bronze_silver.py --force
"""

import subprocess
import sys
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import json

# Import shared modules
from scheduling import DataSourceSchedule
from metadata import get_last_download_time, save_download_time
from script_runner import run_script_with_retry

# Setup paths
SCRIPTS_DIR = Path(__file__).parent
INGESTION_DIR = Path(__file__).parent.parent / "src" / "ingestion"
DATA_DIR = Path(__file__).parent.parent / "data"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
LOG_DIR = Path(__file__).parent.parent / "logs"

# Ensure directories exist
LOG_DIR.mkdir(exist_ok=True)
SILVER_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'bronze_silver_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('bronze_silver_automation')


# DataSourceSchedule now imported from scheduling.py
# get_last_download_time and save_download_time now imported from metadata.py
# run_script_with_retry now imported from script_runner.py


def get_last_processing_time(layer: str = 'silver') -> Optional[datetime]:
    """Get the last Silver processing time"""
    metadata_file = SILVER_DIR / f"{layer}_processing_metadata.json"
    if not metadata_file.exists():
        return None
    
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
            timestamp_str = metadata.get('last_processed')
            if timestamp_str:
                return datetime.fromisoformat(timestamp_str)
    except Exception as e:
        logger.warning(f"Could not read processing metadata: {e}")
    
    return None


# save_download_time now imported from metadata.py


def save_processing_time(layer: str = 'silver'):
    """Save the Silver processing time"""
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    metadata_file = SILVER_DIR / f"{layer}_processing_metadata.json"
    
    metadata = {
        'last_processed': datetime.now().isoformat(),
        'layer': layer,
        'bronze_sources_processed': {
            'eia': get_last_download_time('eia', BRONZE_DIR).isoformat() if get_last_download_time('eia', BRONZE_DIR) else None,
            'rbob': get_last_download_time('rbob', BRONZE_DIR).isoformat() if get_last_download_time('rbob', BRONZE_DIR) else None,
            'retail': get_last_download_time('retail', BRONZE_DIR).isoformat() if get_last_download_time('retail', BRONZE_DIR) else None,
        }
    }
    
    try:
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        logger.error(f"Could not save processing metadata: {e}")


def run_script(script_path: Path, description: str, max_retries: int = 3) -> bool:
    """Run a script with retries"""
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False
    
    for attempt in range(1, max_retries + 1):
        logger.info(f"{description} (attempt {attempt}/{max_retries})")
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            logger.info(f"✅ {description} - Success")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout: {description}")
            if attempt < max_retries:
                wait_time = 30 * attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed: {description} - {e.stderr[:200] if e.stderr else 'No error output'}")
            if attempt < max_retries:
                wait_time = 30 * attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
    
    logger.error(f"❌ {description} - Failed after {max_retries} attempts")
    return False


def should_update_eia(force: bool = False) -> bool:
    """Check if EIA data should be updated"""
    if force:
        return True
    
    last_download = get_last_download_time('eia', BRONZE_DIR)
    if last_download is None:
        logger.info("EIA: No previous download found")
        return True
    
    age_days = (datetime.now() - last_download).days
    if age_days >= 7:
        logger.info(f"EIA: Data is {age_days} days old (threshold: 7 days)")
        return True
    
    next_update = DataSourceSchedule.get_eia_update_time()
    if last_download < next_update <= datetime.now():
        logger.info(f"EIA: New data available")
        return True
    
    logger.info(f"EIA: Data is fresh")
    return False


def should_update_rbob(force: bool = False) -> bool:
    """Check if RBOB data should be updated"""
    if force:
        return True
    
    if not DataSourceSchedule.is_market_hours():
        logger.info("RBOB: Market is closed")
        return False
    
    last_download = get_last_download_time('rbob', BRONZE_DIR)
    if last_download is None:
        logger.info("RBOB: No previous download found")
        return True
    
    age_hours = (datetime.now() - last_download).total_seconds() / 3600
    if age_hours >= 1:
        logger.info(f"RBOB: Data is {age_hours:.1f} hours old")
        return True
    
    logger.info(f"RBOB: Data is fresh")
    return False


def should_update_retail(force: bool = False) -> bool:
    """Check if retail price data should be updated"""
    if force:
        return True
    
    last_download = get_last_download_time('retail', BRONZE_DIR)
    if last_download is None:
        logger.info("Retail: No previous download found")
        return True
    
    age_days = (datetime.now() - last_download).days
    if age_days >= 7:
        logger.info(f"Retail: Data is {age_days} days old (threshold: 7 days)")
        return True
    
    next_update = DataSourceSchedule.get_retail_update_time()
    if last_download < next_update <= datetime.now():
        logger.info(f"Retail: New data available")
        return True
    
    logger.info(f"Retail: Data is fresh")
    return False


def should_rebuild_silver(force: bool = False) -> bool:
    """Check if Silver layer needs rebuilding"""
    if force:
        return True
    
    last_silver_processing = get_last_processing_time('silver')
    if last_silver_processing is None:
        logger.info("Silver: No previous processing found")
        return True
    
    # Check if any Bronze source is newer than Silver
    bronze_sources = {
        'eia': get_last_download_time('eia', BRONZE_DIR),
        'rbob': get_last_download_time('rbob', BRONZE_DIR),
        'retail': get_last_download_time('retail', BRONZE_DIR)
    }
    
    for source, download_time in bronze_sources.items():
        if download_time and download_time > last_silver_processing:
            logger.info(f"Silver: {source.upper()} has new data (Bronze: {download_time}, Silver: {last_silver_processing})")
            return True
    
    logger.info("Silver: Up-to-date with Bronze")
    return False


def update_bronze_layer(force: bool = False) -> Dict[str, bool]:
    """Update Bronze layer with fresh data"""
    results = {}
    
    logger.info("=" * 80)
    logger.info("📥 BRONZE LAYER - Checking for updates")
    logger.info("=" * 80)
    
    # Check and update EIA
    if should_update_eia(force):
        success = run_script(
            INGESTION_DIR / "download_eia_data_bronze.py",
            "Download EIA data"
        )
        if success:
            save_download_time('eia', BRONZE_DIR)
        results['eia'] = success
    else:
        results['eia'] = None
    
    # Check and update RBOB
    if should_update_rbob(force):
        success = run_script(
            INGESTION_DIR / "download_rbob_data_bronze.py",
            "Download RBOB/WTI data"
        )
        if success:
            save_download_time('rbob', BRONZE_DIR)
        results['rbob'] = success
    else:
        results['rbob'] = None
    
    # Check and update Retail
    if should_update_retail(force):
        success = run_script(
            INGESTION_DIR / "download_retail_prices_bronze.py",
            "Download Retail prices"
        )
        if success:
            save_download_time('retail', BRONZE_DIR)
        results['retail'] = success
    else:
        results['retail'] = None
    
    return results


def update_silver_layer() -> bool:
    """Update Silver layer from Bronze"""
    logger.info("=" * 80)
    logger.info("🧹 SILVER LAYER - Processing from Bronze")
    logger.info("=" * 80)
    
    silver_scripts = [
        ("clean_rbob_to_silver.py", "Clean RBOB/WTI data"),
        ("clean_retail_to_silver.py", "Clean Retail prices"),
        ("clean_eia_to_silver.py", "Clean EIA data"),
    ]

    all_success = True
    for script_name, description in silver_scripts:
        success = run_script(SCRIPTS_DIR / script_name, description)
        if not success:
            all_success = False

    # Run optional Silver data scripts (PADD3 share, NOAA temp, hurricane risk)
    optional_scripts = [
        ("download_padd3_share.py", "Download PADD3 share (optional)"),
        ("download_noaa_temp.py", "Download NOAA temperature (optional)"),
        ("process_hurricane_risk_october.py", "Process hurricane risk for October (optional)")
    ]
    for script_name, description in optional_scripts:
        script_path = SCRIPTS_DIR / script_name
        if script_path.exists():
            run_script(script_path, description, max_retries=2)
        else:
            logger.info(f"Optional script not found: {script_path}")

    if all_success:
        save_processing_time('silver')
        logger.info("✅ Silver layer processing complete")
    else:
        logger.error("❌ Silver layer processing had failures")

    return all_success


def run_pipeline(force: bool = False) -> int:
    """Run the full Bronze → Silver pipeline"""
    logger.info("\n" + "=" * 80)
    logger.info("🤖 AUTOMATED BRONZE → SILVER PIPELINE")
    logger.info("=" * 80)
    
    # Step 1: Update Bronze
    bronze_results = update_bronze_layer(force)
    
    # Check if any Bronze sources were updated
    bronze_updated = any(r is True for r in bronze_results.values())
    
    # Log Bronze summary
    logger.info("\n" + "-" * 80)
    logger.info("📥 BRONZE SUMMARY:")
    for source, result in bronze_results.items():
        if result is True:
            logger.info(f"  ✅ {source.upper()}: Updated")
        elif result is False:
            logger.error(f"  ❌ {source.upper()}: Failed")
        else:
            logger.info(f"  ⏭️  {source.upper()}: Skipped (fresh)")
    logger.info("-" * 80)
    
    # Step 2: Check if Silver needs rebuilding
    if bronze_updated or should_rebuild_silver(force):
        logger.info("\n🔄 Bronze data changed - Rebuilding Silver layer...")
        silver_success = update_silver_layer()
        
        if not silver_success:
            logger.error("\n❌ Pipeline completed with Silver errors")
            return 1
    else:
        logger.info("\n⏭️  SILVER LAYER - Skipped (up-to-date with Bronze)")
    
    # Success summary
    logger.info("\n" + "=" * 80)
    logger.info("✅ PIPELINE COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Bronze updates: {sum(1 for r in bronze_results.values() if r is True)}")
    logger.info(f"Silver rebuilt: {'Yes' if bronze_updated or force else 'No (already up-to-date)'}")
    logger.info("=" * 80 + "\n")
    
    return 0


def run_daemon(check_interval: int = 3600):
    """Run as a daemon, checking periodically"""
    logger.info("=" * 80)
    logger.info("🤖 BRONZE → SILVER AUTOMATION DAEMON - Starting")
    logger.info("=" * 80)
    logger.info(f"Check interval: {check_interval} seconds ({check_interval/3600:.1f} hours)")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 80 + "\n")
    
    try:
        while True:
            try:
                run_pipeline(force=False)
            except Exception as e:
                logger.error(f"Error during pipeline cycle: {e}", exc_info=True)
            
            next_check = datetime.now() + timedelta(seconds=check_interval)
            logger.info(f"Next check at: {next_check.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Sleeping for {check_interval} seconds...\n")
            
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 80)
        logger.info("🤖 DAEMON - Stopped by user")
        logger.info("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Automated Bronze → Silver pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run once (check Bronze, rebuild Silver if needed)
  python scripts/automate_bronze_silver.py
  
  # Run continuously, checking every hour
  python scripts/automate_bronze_silver.py --daemon --interval 3600
  
  # Force update both layers
  python scripts/automate_bronze_silver.py --force
  
  # Run as background process
  nohup python scripts/automate_bronze_silver.py --daemon > /dev/null 2>&1 &

Benefits:
  - Bronze downloads only when data sources update
  - Silver automatically rebuilds when Bronze changes
  - No redundant processing
  - Full audit trail in logs
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
        help='Force update all layers regardless of freshness'
    )
    
    args = parser.parse_args()
    
    if args.daemon:
        run_daemon(args.interval)
    else:
        return run_pipeline(args.force)


if __name__ == "__main__":
    sys.exit(main())
