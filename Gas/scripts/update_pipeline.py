"""
Incremental Pipeline - Smart Updates

This is a FASTER alternative to run_medallion_pipeline.py.
Only rebuilds what's needed based on what's changed.

Usage:
    python scripts/update_pipeline.py              # Smart update (checks what's stale)
    python scripts/update_pipeline.py --full       # Full rebuild (all layers)
    python scripts/update_pipeline.py --gold-only  # Just rebuild Gold layer
    python scripts/update_pipeline.py --silver     # Bronze → Silver only
"""

import subprocess
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

SCRIPTS_DIR = Path(__file__).parent
INGESTION_DIR = Path(__file__).parent.parent / "src" / "ingestion"
DATA_DIR = Path(__file__).parent.parent / "data"


def get_latest_modification(directory: Path) -> datetime:
    """Get the most recent modification time in a directory"""
    if not directory.exists():
        return datetime.min
    
    files = list(directory.rglob("*.parquet")) + list(directory.rglob("*.csv"))
    if not files:
        return datetime.min
    
    return max(datetime.fromtimestamp(f.stat().st_mtime) for f in files)


def is_stale(source_dir: Path, target_dir: Path, max_age_hours: int = 24) -> bool:
    """Check if target needs rebuilding"""
    if not target_dir.exists():
        return True
    
    target_time = get_latest_modification(target_dir)
    
    # Check if target is older than max age
    age_hours = (datetime.now() - target_time).total_seconds() / 3600
    if age_hours > max_age_hours:
        return True
    
    # Check if source is newer than target
    if source_dir.exists():
        source_time = get_latest_modification(source_dir)
        if source_time > target_time:
            return True
    
    return False


def run_script(script_name: str, description: str, use_ingestion: bool = False) -> bool:
    """Run a Python script and return success status"""
    print("\n" + "=" * 80)
    print(f"🚀 {description}")
    print("=" * 80)
    
    script_dir = INGESTION_DIR if use_ingestion else SCRIPTS_DIR
    script_path = script_dir / script_name
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=False
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Script failed with exit code {e.returncode}")
        return False


def update_bronze() -> bool:
    """Download latest data to Bronze layer"""
    print("\n📥 UPDATING BRONZE LAYER (Raw Data)")
    print("-" * 80)
    
    bronze_scripts = [
        ("download_rbob_data_bronze.py", "Download RBOB/WTI futures"),
        ("download_retail_prices_bronze.py", "Download retail prices"),
        ("download_eia_data_bronze.py", "Download EIA data"),
    ]
    
    for script, desc in bronze_scripts:
        if not run_script(script, desc, use_ingestion=True):
            return False
    return True


def update_silver() -> bool:
    """Clean Bronze → Silver"""
    print("\n🧹 UPDATING SILVER LAYER (Cleaned Data)")
    print("-" * 80)
    
    silver_scripts = [
        ("clean_rbob_to_silver.py", "Clean RBOB/WTI"),
        ("clean_retail_to_silver.py", "Clean retail prices"),
        ("clean_eia_to_silver.py", "Clean EIA data"),
    ]
    
    for script, desc in silver_scripts:
        if not run_script(script, desc):
            return False
    return True


def update_gold() -> bool:
    """Build Silver → Gold"""
    print("\n⭐ UPDATING GOLD LAYER (Feature Engineering)")
    print("-" * 80)
    
    return run_script("build_gold_layer.py", "Build Gold Layer")


def smart_update(max_age_hours: int = 24) -> int:
    """Smart update: only rebuild what's stale"""
    print("\n" + "=" * 80)
    print("🧠 SMART PIPELINE UPDATE")
    print("=" * 80)
    print(f"\nChecking for stale data (max age: {max_age_hours} hours)...")
    
    bronze_dir = DATA_DIR / "bronze"
    silver_dir = DATA_DIR / "silver"
    gold_dir = DATA_DIR / "gold"
    
    # Check what needs updating
    needs_bronze = is_stale(Path(), bronze_dir, max_age_hours)
    needs_silver = is_stale(bronze_dir, silver_dir, max_age_hours) or needs_bronze
    needs_gold = is_stale(silver_dir, gold_dir, max_age_hours) or needs_silver
    
    print("\nStatus check:")
    print(f"  📦 Bronze: {'🔴 STALE' if needs_bronze else '✅ FRESH'}")
    print(f"  🪙 Silver: {'🔴 STALE' if needs_silver else '✅ FRESH'}")
    print(f"  ⭐ Gold:   {'🔴 STALE' if needs_gold else '✅ FRESH'}")
    
    if not (needs_bronze or needs_silver or needs_gold):
        print("\n✅ All layers are up-to-date! Nothing to do.")
        return 0
    
    print("\n" + "=" * 80)
    
    # Update what's needed
    if needs_bronze:
        if not update_bronze():
            return 1
    else:
        print("\n⏭️  SKIPPING Bronze (already fresh)")
    
    if needs_silver:
        if not update_silver():
            return 1
    else:
        print("\n⏭️  SKIPPING Silver (already fresh)")
    
    if needs_gold:
        if not update_gold():
            return 1
    else:
        print("\n⏭️  SKIPPING Gold (already fresh)")
    
    print("\n" + "=" * 80)
    print("✅ SMART UPDATE COMPLETE!")
    print("=" * 80)
    return 0


def full_rebuild() -> int:
    """Full rebuild: Bronze → Silver → Gold"""
    print("\n" + "=" * 80)
    print("🏗️  FULL PIPELINE REBUILD")
    print("=" * 80)
    print("\nRebuilding ALL layers from scratch...")
    print("=" * 80)
    
    if not update_bronze():
        return 1
    if not update_silver():
        return 1
    if not update_gold():
        return 1
    
    print("\n" + "=" * 80)
    print("✅ FULL REBUILD COMPLETE!")
    print("=" * 80)
    return 0


def gold_only() -> int:
    """Rebuild only Gold layer (assumes Silver is fresh)"""
    print("\n" + "=" * 80)
    print("⭐ GOLD LAYER REBUILD")
    print("=" * 80)
    print("\nRebuilding Gold layer from existing Silver data...")
    print("=" * 80)
    
    if not update_gold():
        return 1
    
    print("\n" + "=" * 80)
    print("✅ GOLD REBUILD COMPLETE!")
    print("=" * 80)
    return 0


def silver_only() -> int:
    """Update Bronze and Silver only (skip Gold)"""
    print("\n" + "=" * 80)
    print("🪙 BRONZE + SILVER UPDATE")
    print("=" * 80)
    print("\nUpdating Bronze and Silver layers...")
    print("=" * 80)
    
    if not update_bronze():
        return 1
    if not update_silver():
        return 1
    
    print("\n" + "=" * 80)
    print("✅ BRONZE + SILVER UPDATE COMPLETE!")
    print("=" * 80)
    print("\nNote: Gold layer was NOT rebuilt.")
    print("Run with --gold-only to rebuild Gold, or run smart update.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Smart incremental pipeline updates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/update_pipeline.py              # Smart update (default)
  python scripts/update_pipeline.py --full       # Full rebuild
  python scripts/update_pipeline.py --gold-only  # Just rebuild Gold
  python scripts/update_pipeline.py --silver     # Bronze + Silver only
  python scripts/update_pipeline.py --max-age 6  # Update if > 6 hours old
        """
    )
    
    parser.add_argument(
        "--full",
        action="store_true",
        help="Full rebuild of all layers (Bronze → Silver → Gold)"
    )
    
    parser.add_argument(
        "--gold-only",
        action="store_true",
        help="Rebuild only Gold layer (assumes Silver is fresh)"
    )
    
    parser.add_argument(
        "--silver",
        action="store_true",
        help="Update Bronze and Silver only (skip Gold)"
    )
    
    parser.add_argument(
        "--max-age",
        type=int,
        default=24,
        help="Max age in hours before data is considered stale (default: 24)"
    )
    
    args = parser.parse_args()
    
    # Run appropriate pipeline
    if args.full:
        return full_rebuild()
    elif args.gold_only:
        return gold_only()
    elif args.silver:
        return silver_only()
    else:
        return smart_update(args.max_age)


if __name__ == "__main__":
    sys.exit(main())
