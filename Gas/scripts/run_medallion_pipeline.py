"""
Master Data Pipeline - Bronze → Silver → Gold

This orchestrates the full medallion architecture:
1. Download raw data to Bronze layer
2. Clean Bronze → Silver layer
3. Build Silver → Gold layer (feature engineering)
4. Validate each layer

Run this to execute the complete data pipeline.
"""

import os
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
INGESTION_DIR = Path(__file__).parent.parent / "src" / "ingestion"


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
        env = None
        if use_ingestion:
            src_root = INGESTION_DIR.parent
            existing = os.environ.get("PYTHONPATH", "")
            new_path = str(src_root)
            if existing:
                new_path = new_path + os.pathsep + existing
            env = {**os.environ, "PYTHONPATH": new_path}

        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=False,
            env=env,
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Script failed with exit code {e.returncode}")
        return False


def main():
    print("\n" + "=" * 80)
    print("🏗️  FULL MEDALLION PIPELINE: BRONZE → SILVER → GOLD")
    print("=" * 80)
    print("\nThis will:")
    print("  1. Download raw data to Bronze layer")
    print("  2. Clean data to Silver layer")
    print("  3. Build Gold layer (feature engineering)")
    print("  4. Validate all layers")
    print("\n" + "=" * 80)
    
    # Step 1: Download to Bronze
    print("\n📥 PHASE 1: DOWNLOADING RAW DATA TO BRONZE LAYER")
    print("-" * 80)
    
    bronze_scripts = [
        ("download_rbob_data_bronze.py", "Download RBOB/WTI futures to Bronze"),
        ("download_retail_prices_bronze.py", "Download retail prices to Bronze"),
        ("download_eia_data_bronze.py", "Download EIA data to Bronze"),
    ]
    
    for script, desc in bronze_scripts:
        if not run_script(script, desc, use_ingestion=True):
            print(f"\n❌ Pipeline failed at: {desc}")
            return 1
    
    # Step 2: Clean to Silver
    print("\n🧹 PHASE 2: CLEANING DATA TO SILVER LAYER")
    print("-" * 80)
    
    silver_scripts = [
        ("clean_rbob_to_silver.py", "Clean RBOB/WTI: Bronze → Silver"),
        ("clean_retail_to_silver.py", "Clean retail prices: Bronze → Silver"),
        ("clean_eia_to_silver.py", "Clean EIA data: Bronze → Silver"),
    ]
    
    for script, desc in silver_scripts:
        if not run_script(script, desc):
            print(f"\n❌ Pipeline failed at: {desc}")
            return 1
    
    # Step 3: Validate Silver
    print("\n✅ PHASE 3: VALIDATING SILVER LAYER")
    print("-" * 80)
    
    if not run_script("validate_silver_layer.py", "Validate Silver Layer"):
        print(f"\n⚠️  Silver layer validation issues detected")
        # Don't fail - just warn
    
    # Optional: Weather & Hurricane features
    print("\n🌦️  OPTIONAL PHASE: WEATHER & HURRICANE FEATURES")
    print("-" * 80)

    optional_scripts = [
        ("download_noaa_temp.py", "Download NOAA temperature anomalies"),
        ("process_hurricane_risk_october.py", "Process Gulf hurricane risk"),
    ]

    for script, desc in optional_scripts:
        if not run_script(script, desc):
            print(f"  ⚠️  Optional feature step skipped: {desc}")

    # Step 4: Build Gold
    print("\n⭐ PHASE 4: BUILDING GOLD LAYER")
    print("-" * 80)
    
    if not run_script("build_gold_layer.py", "Build Gold Layer (Feature Engineering)"):
        print(f"\n❌ Pipeline failed at: Build Gold Layer")
        return 1
    
    # Step 5: Validate Gold
    print("\n✅ PHASE 5: VALIDATING GOLD LAYER")
    print("-" * 80)
    
    if not run_script("validate_gold_layer.py", "Validate Gold Layer"):
        print(f"\n⚠️  Gold layer validation issues detected")
        # Don't fail - just warn
    
    # Success!
    print("\n" + "=" * 80)
    print("✅ FULL PIPELINE COMPLETE!")
    print("=" * 80)
    print("\nData layers created:")
    print("  📦 Bronze: Raw API responses")
    print("  🪙 Silver: Cleaned, validated data")
    print("  ⭐ Gold: Feature-engineered, model-ready data")
    print("\nNext steps:")
    print("  1. Review: Gas/data/silver/ and Gas/data/gold/")
    print("  2. Run: python train_models.py")
    print("  3. Run: python walk_forward_validation.py")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
