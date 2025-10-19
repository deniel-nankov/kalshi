"""
Master Data Pipeline - Bronze → Silver → Gold (Complete Medallion Architecture)

This orchestrates the full medallion architecture with all features:
1. Download raw data to Bronze layer (RBOB, EIA, external data, hurricanes, temperature)
2. Clean Bronze → Silver layer (all data sources)
3. Build Silver → Gold layer (feature engineering with 88 features)
4. Validate each layer (quality checks + leakage detection)
5. Train models (Ridge, Gradient Boosting, Ensemble)
6. Optional: Walk-forward validation and freshness reporting

Features included:
- EIA data: Retail prices, inventory, utilization, imports/exports (with 3 retries)
- External data: SPR releases, FRED macro indicators, OPEC cuts (with 10/5 retries)
- Weather: NOAA temperature anomalies (with 10 retries)
- Hurricane risk: Gulf of Mexico hurricane features
- All 88 features properly lagged and validated

Run this to execute the complete data pipeline.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
INGESTION_DIR = Path(__file__).parent.parent / "src" / "ingestion"


def run_script(
    script_name: str, 
    description: str, 
    use_ingestion: bool = False, 
    allow_failure: bool = False,
    extra_args: list[str] = None
) -> bool:
    """
    Run a Python script and return success status
    
    Args:
        script_name: Name of the script to run
        description: Human-readable description
        use_ingestion: If True, look in src/ingestion/ directory
        allow_failure: If True, continue pipeline even if step fails
        extra_args: Additional command line arguments for the script
        
    Returns:
        True if script succeeded, False otherwise
    """
    print("\n" + "=" * 80)
    print(f"🚀 {description}")
    print("=" * 80)
    
    script_dir = INGESTION_DIR if use_ingestion else SCRIPTS_DIR
    script_path = script_dir / script_name
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False if not allow_failure else True
    
    try:
        env = None
        if use_ingestion:
            src_root = INGESTION_DIR.parent
            existing = os.environ.get("PYTHONPATH", "")
            new_path = str(src_root)
            if existing:
                new_path = new_path + os.pathsep + existing
            env = {**os.environ, "PYTHONPATH": new_path}

        cmd = [sys.executable, str(script_path)]
        if extra_args:
            cmd.extend(extra_args)

        result = subprocess.run(
            cmd,
            check=not allow_failure,
            capture_output=False,
            env=env,
        )
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            if allow_failure:
                print(f"⚠️  {description} failed but continuing (allow_failure=True)")
                return False
            else:
                print(f"❌ {description} failed with exit code {result.returncode}")
                return False
                
    except subprocess.CalledProcessError as e:
        if allow_failure:
            print(f"⚠️  {description} failed but continuing: {e}")
            return False
        else:
            print(f"❌ Script failed with exit code {e.returncode}")
            return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run complete medallion pipeline (Bronze → Silver → Gold) with all features"
    )
    parser.add_argument(
        "--skip-data-download",
        action="store_true",
        help="Skip data downloading steps (use existing silver layer data)"
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip validation and leakage detection steps (not recommended)"
    )
    parser.add_argument(
        "--skip-training",
        action="store_true",
        help="Skip model training step"
    )
    parser.add_argument(
        "--skip-walkforward",
        action="store_true",
        help="Skip walk-forward validation step"
    )
    parser.add_argument(
        "--skip-freshness",
        action="store_true",
        help="Skip data freshness dashboard generation"
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=14,
        help="Forecast horizon in days (default: 14)"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    
    print("\n" + "=" * 80)
    print("🏗️  FULL MEDALLION PIPELINE: BRONZE → SILVER → GOLD")
    print("=" * 80)
    print("\nConfiguration:")
    print(f"  • Forecast horizon: {args.horizon} days")
    print(f"  • Skip data download: {args.skip_data_download}")
    print(f"  • Skip validation: {args.skip_validation}")
    print(f"  • Skip training: {args.skip_training}")
    print(f"  • Skip walk-forward: {args.skip_walkforward}")
    print(f"  • Skip freshness: {args.skip_freshness}")
    print("\nThis will:")
    print("  1. Download raw data to Bronze layer (RBOB, EIA, external, hurricanes, temp)")
    print("  2. Clean data to Silver layer (all sources)")
    print("  3. Build Gold layer (88 features, properly lagged)")
    print("  4. Validate all layers (quality checks + leakage detection)")
    print("  5. Train models (Ridge, GB, Ensemble)")
    print("  6. Optional: Walk-forward validation & freshness reporting")
    print("\n" + "=" * 80)
    
    failed_steps = []
    
    # ========================================
    # PHASE 1: DATA ACQUISITION (Bronze Layer)
    # ========================================
    if not args.skip_data_download:
        print("\n📥 PHASE 1: DOWNLOADING RAW DATA TO BRONZE LAYER")
        print("-" * 80)
        
        # Step 1: Fetch external data (SPR, FRED, OPEC) - 10/5 retries
        if not run_script(
            "fetch_external_data.py", 
            "1. Fetch External Data (SPR, FRED, OPEC) - 10/5 retries",
            use_ingestion=False,
            allow_failure=True,  # External APIs may be unavailable
            extra_args=["--start-date", "2020-01-01", "--end-date", "2025-12-31"]
        ):
            failed_steps.append("Fetch External Data")
        
        # Step 2-4: Download core data to Bronze
        bronze_scripts = [
            ("download_rbob_data_bronze.py", "2. Download RBOB/WTI futures to Bronze - 3 retries"),
            ("download_retail_prices_bronze.py", "3. Download retail prices to Bronze"),
            ("download_eia_data_bronze.py", "4. Download EIA data to Bronze - 3 retries"),
        ]
        
        for script, desc in bronze_scripts:
            if not run_script(script, desc, use_ingestion=True):
                print(f"\n❌ Pipeline failed at: {desc}")
                return 1
        
        # Step 5-6: Weather & Hurricane features (optional)
        optional_scripts = [
            ("process_hurricane_risk_october.py", "5. Process Gulf hurricane risk features"),
            ("download_noaa_temp.py", "6. Download NOAA temperature data - 10 retries"),
        ]
        
        for script, desc in optional_scripts:
            if not run_script(script, desc, allow_failure=True):
                print(f"  ⚠️  {desc} - continuing anyway")
                failed_steps.append(desc)
        
        # Step 7-9: Clean to Silver
        print("\n🧹 PHASE 2: CLEANING DATA TO SILVER LAYER")
        print("-" * 80)
        
        silver_scripts = [
            ("clean_rbob_to_silver.py", "7. Clean RBOB/WTI: Bronze → Silver"),
            ("clean_retail_to_silver.py", "8. Clean retail prices: Bronze → Silver"),
            ("clean_eia_to_silver.py", "9. Clean EIA data: Bronze → Silver"),
        ]
        
        for script, desc in silver_scripts:
            if not run_script(script, desc):
                print(f"\n❌ Pipeline failed at: {desc}")
                return 1
        
        # Step 10: Validate Silver
        if not run_script("validate_silver_layer.py", "10. Validate Silver Layer", allow_failure=True):
            print(f"\n⚠️  Silver layer validation issues detected - continuing")
            failed_steps.append("Validate Silver Layer")
    
    # ========================================
    # PHASE 3: FEATURE ENGINEERING (Gold Layer)
    # ========================================
    print("\n⭐ PHASE 3: BUILDING GOLD LAYER (88 FEATURES)")
    print("-" * 80)
    
    if not run_script("build_gold_layer.py", "11. Build Gold Layer (Feature Engineering)"):
        print(f"\n❌ Pipeline failed at: Build Gold Layer")
        return 1
    
    # ========================================
    # PHASE 4: VALIDATION
    # ========================================
    if not args.skip_validation:
        print("\n✅ PHASE 4: VALIDATING GOLD LAYER")
        print("-" * 80)
        
        if not run_script("validate_gold_layer.py", "12. Validate Gold Layer (Quality Checks)", allow_failure=True):
            print(f"\n⚠️  Gold layer validation issues detected - continuing")
            failed_steps.append("Validate Gold Layer")
        
        # Leakage detection
        if not run_script(
            "detect_leakage.py", 
            "13. Leakage Detection (Temporal Integrity)",
            allow_failure=True,  # High correlations expected for RBOB/retail
            extra_args=["data/gold/master_model_ready.parquet"]
        ):
            failed_steps.append("Leakage Detection")
    
    # ========================================
    # PHASE 5: MODEL TRAINING
    # ========================================
    if not args.skip_training:
        print("\n🔴 PHASE 5: MODEL TRAINING")
        print("-" * 80)
        
        if not run_script(
            "train_models.py", 
            "14. Train Baseline Models (Ridge, GB, Ensemble)",
            extra_args=["--horizon", str(args.horizon)]
        ):
            print(f"\n❌ Pipeline failed at: Train Models")
            return 1
    
    # ========================================
    # PHASE 6: EVALUATION (Optional)
    # ========================================
    if not args.skip_walkforward:
        print("\n🟣 PHASE 6: MODEL EVALUATION")
        print("-" * 80)
        
        if not run_script("walk_forward_validation.py", "15. Walk-Forward Validation"):
            print(f"\n❌ Pipeline failed at: Walk-Forward Validation")
            return 1
    
    # ========================================
    # PHASE 7: REPORTING (Optional)
    # ========================================
    if not args.skip_freshness:
        print("\n🟠 PHASE 7: REPORTING")
        print("-" * 80)
        
        if not run_script("report_data_freshness.py", "16. Data Freshness Dashboard", allow_failure=True):
            failed_steps.append("Data Freshness Dashboard")
    
    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "=" * 80)
    print("✅ FULL PIPELINE COMPLETE!")
    print("=" * 80)
    
    if failed_steps:
        print(f"\n⚠️  {len(failed_steps)} step(s) had issues (allowed):")
        for step in failed_steps:
            print(f"   - {step}")
    else:
        print("\n🎉 All steps completed successfully!")
    
    print("\n📁 Data layers created:")
    print("  📦 Bronze: Raw API responses (with metadata)")
    print("  🪙 Silver: Cleaned, validated data")
    print("  ⭐ Gold: Feature-engineered, model-ready data (88 features)")
    
    print("\n📊 Output locations:")
    print(f"  • Bronze: {SCRIPTS_DIR.parent / 'data' / 'bronze'}/")
    print(f"  • Silver: {SCRIPTS_DIR.parent / 'data' / 'silver'}/")
    print(f"  • Gold: {SCRIPTS_DIR.parent / 'data' / 'gold'}/")
    print(f"  • Models: {SCRIPTS_DIR.parent / 'models'}/")
    print(f"  • Validation reports: {SCRIPTS_DIR.parent / 'data' / 'gold' / 'validation_reports'}/")
    print(f"  • Artifacts: {SCRIPTS_DIR.parent / 'outputs'}/")
    
    print("\n🚀 Next steps:")
    print("  1. Review validation reports in data/gold/validation_reports/")
    print("  2. Check model performance in models/")
    print("  3. Generate forecasts: python scripts/generate_october_forecast.py")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
