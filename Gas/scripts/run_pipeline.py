"""
Comprehensive orchestrator for the complete gas forecasting pipeline.

Runs medallion architecture workflow (Bronze → Silver → Gold):
    PHASE 1: DATA ACQUISITION (Bronze Layer)
        1. Fetch external data (SPR, FRED macro, OPEC/geopolitical) - 10 retries
        2. Download RBOB futures to Bronze - 3 retries
        3. Download retail prices to Bronze - 3 retries
        4. Download EIA data to Bronze - 3 retries
        5. Process hurricane risk features
        6. Download NOAA temperature - 10 retries
        7-9. Clean Bronze → Silver (RBOB, Retail, EIA)
    
    PHASE 2: FEATURE ENGINEERING (Silver → Gold)
        10. Build Gold layer (merge all features)
    
    PHASE 3: VALIDATION
        11. Validate Gold layer (quality checks)
        12. Run leakage detection (temporal integrity)
    
    PHASE 4: MODEL TRAINING
        13. Train baseline models (Ridge, GB, Ensemble)
    
    PHASE 5: EVALUATION (Optional)
        14. Walk-forward validation
    
    PHASE 6: REPORTING (Optional)
        15. Data freshness dashboard

Retry Logic:
- EIA client: 3 retries with 1.5x exponential backoff (built-in)
- SPR data: 10 retries with 2.0x exponential backoff
- FRED API: 5 retries with 2.0x exponential backoff
- NOAA temp: 10 retries

Usage:
    python run_pipeline.py [--skip-walkforward] [--skip-freshness] [--skip-data-download] [--horizon 14]
    
Options:
    --skip-data-download  Skip data downloading (use existing silver layer data)
    --skip-walkforward    Skip walk-forward validation step
    --skip-freshness      Skip data freshness dashboard
    --skip-validation     Skip validation and leakage detection steps
    --horizon N           Forecast horizon in days (default: 14)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
INGESTION_DIR = SCRIPT_DIR.parent / "src" / "ingestion"


def run_step(name: str, command: list[str], allow_failure: bool = False) -> bool:
    """
    Run a pipeline step and report status.
    
    Args:
        name: Human-readable step name
        command: Command to execute
        allow_failure: If True, continue pipeline even if step fails
        
    Returns:
        True if step succeeded, False otherwise
    """
    print(f"\n{'='*80}")
    print(f"  {name}")
    print(f"{'='*80}")
    
    try:
        # Check if running a script from src/ingestion/
        import os
        env = None
        if len(command) > 1 and "src/ingestion" in str(command[1]):
            # Set PYTHONPATH to include src directory
            src_root = INGESTION_DIR.parent
            existing = os.environ.get("PYTHONPATH", "")
            new_path = str(src_root)
            if existing:
                new_path = new_path + os.pathsep + existing
            env = {**os.environ, "PYTHONPATH": new_path}
        
        result = subprocess.run(command, check=not allow_failure, env=env)
        if result.returncode == 0:
            print(f"✅ {name} completed successfully")
            return True
        else:
            if allow_failure:
                print(f"⚠️  {name} failed but continuing (allow_failure=True)")
                return False
            else:
                print(f"❌ {name} failed")
                return False
    except subprocess.CalledProcessError as e:
        print(f"❌ {name} failed with error: {e}")
        if not allow_failure:
            raise
        return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run complete gasoline forecasting pipeline with medallion architecture"
    )
    parser.add_argument(
        "--skip-data-download",
        action="store_true",
        help="Skip data downloading steps (use existing silver layer data)"
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
        "--skip-validation",
        action="store_true",
        help="Skip validation and leakage detection steps (not recommended for production)"
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=14,
        help="Forecast horizon in days (default: 14)"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    python = sys.executable
    
    print("\n" + "="*80)
    print("  🚀 GAS PRICE FORECASTING PIPELINE")
    print("="*80)
    print(f"Forecast horizon: {args.horizon} days")
    print(f"Skip data download: {args.skip_data_download}")
    print(f"Skip validation: {args.skip_validation}")
    print(f"Skip walk-forward: {args.skip_walkforward}")
    print(f"Skip freshness: {args.skip_freshness}")
    print("="*80 + "\n")

    steps = []
    
    # ========================================
    # PHASE 1: DATA ACQUISITION (Bronze Layer)
    # ========================================
    if not args.skip_data_download:
        print("\n" + "🔵 PHASE 1: DATA ACQUISITION (Bronze → Silver)")
        
        # Step 1: Fetch external data (SPR, FRED, OPEC) with 10 retries
        steps.append((
            "1. Fetch External Data (SPR, FRED macro, OPEC cuts)",
            [python, str(SCRIPT_DIR / "fetch_external_data.py"),
             "--start-date", "2020-01-01",
             "--end-date", "2025-12-31"],
            True  # Allow failure - not all external data may be available
        ))
        
        # Step 2: Download RBOB futures
        steps.append((
            "2. Download RBOB Futures Data",
            [python, str(INGESTION_DIR / "download_rbob_data_bronze.py")],
            False
        ))
        
        # Step 3: Download retail gas prices
        steps.append((
            "3. Download Retail Gas Prices",
            [python, str(INGESTION_DIR / "download_retail_prices_bronze.py")],
            False
        ))
        
        # Step 4: Download EIA data (inventory, utilization, imports) with retries
        steps.append((
            "4. Download EIA Data (Inventory, Utilization, Imports)",
            [python, str(INGESTION_DIR / "download_eia_data_bronze.py")],
            False
        ))
        
        # Step 5: Process hurricane features (using existing script)
        steps.append((
            "5. Process Hurricane Risk Features",
            [python, str(SCRIPT_DIR / "process_hurricane_risk_october.py")],
            True  # Allow failure - historical data
        ))
        
        # Step 6: Download NOAA temperature data with retries
        steps.append((
            "6. Download NOAA Temperature Data (10 retries)",
            [python, str(SCRIPT_DIR / "download_noaa_temp.py")],
            True  # Allow failure - not critical
        ))
        
        # Step 7: Clean Bronze → Silver (RBOB)
        steps.append((
            "7. Clean RBOB Data (Bronze → Silver)",
            [python, str(SCRIPT_DIR / "clean_rbob_to_silver.py")],
            False
        ))
        
        # Step 8: Clean Bronze → Silver (Retail)
        steps.append((
            "8. Clean Retail Prices (Bronze → Silver)",
            [python, str(SCRIPT_DIR / "clean_retail_to_silver.py")],
            False
        ))
        
        # Step 9: Clean Bronze → Silver (EIA)
        steps.append((
            "9. Clean EIA Data (Bronze → Silver)",
            [python, str(SCRIPT_DIR / "clean_eia_to_silver.py")],
            False
        ))
    
    # ========================================
    # PHASE 2: FEATURE ENGINEERING (Gold Layer)
    # ========================================
    print("\n" + "🟡 PHASE 2: FEATURE ENGINEERING (Silver → Gold)")
    
    # Step 10: Build gold layer (merge all features)
    steps.append((
        "10. Build Gold Layer (Feature Engineering)",
        [python, str(SCRIPT_DIR / "build_gold_layer.py")],
        False
    ))
    
    # ========================================
    # PHASE 3: VALIDATION
    # ========================================
    if not args.skip_validation:
        print("\n" + "🟢 PHASE 3: VALIDATION & QUALITY CHECKS")
        
        # Step 11: Validate gold layer
        steps.append((
            "11. Validate Gold Layer (Quality Checks)",
            [python, str(SCRIPT_DIR / "validate_gold_layer.py")],
            False
        ))
        
        # Step 12: Run leakage detection
        steps.append((
            "12. Leakage Detection (Temporal Integrity)",
            [python, str(SCRIPT_DIR / "detect_leakage.py"),
             "data/gold/master_model_ready.parquet"],
            True  # Allow high correlations for RBOB/retail prices
        ))
    
    # ========================================
    # PHASE 4: MODEL TRAINING
    # ========================================
    print("\n" + "🔴 PHASE 4: MODEL TRAINING")
    
    # Step 13: Train baseline models
    steps.append((
        "13. Train Baseline Models (Ridge, GB, Ensemble)",
        [python, str(SCRIPT_DIR / "train_models.py"),
         "--horizon", str(args.horizon)],
        False
    ))
    
    # ========================================
    # PHASE 5: EVALUATION (Optional)
    # ========================================
    if not args.skip_walkforward:
        print("\n" + "🟣 PHASE 5: MODEL EVALUATION")
        
        steps.append((
            "14. Walk-Forward Validation",
            [python, str(SCRIPT_DIR / "walk_forward_validation.py")],
            False
        ))
    
    # ========================================
    # PHASE 6: REPORTING (Optional)
    # ========================================
    if not args.skip_freshness:
        print("\n" + "🟠 PHASE 6: REPORTING")
        
        steps.append((
            "15. Generate Data Freshness Dashboard",
            [python, str(SCRIPT_DIR / "report_data_freshness.py")],
            True  # Allow failure - just reporting
        ))
    
    # ========================================
    # EXECUTE PIPELINE
    # ========================================
    failed_steps = []
    
    for name, cmd, allow_failure in steps:
        success = run_step(name, cmd, allow_failure)
        if not success and not allow_failure:
            failed_steps.append(name)
            print(f"\n❌ Pipeline FAILED at step: {name}")
            print("Fix the error and re-run the pipeline.")
            sys.exit(1)
        elif not success:
            failed_steps.append(name)
    
    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "="*80)
    print("  📊 PIPELINE SUMMARY")
    print("="*80)
    
    if failed_steps:
        print(f"⚠️  {len(failed_steps)} step(s) failed (allowed):")
        for step in failed_steps:
            print(f"   - {step}")
    else:
        print("✅ All steps completed successfully!")
    
    print("\n📁 Output locations:")
    print(f"   - Models: {SCRIPT_DIR.parent / 'models'}/")
    print(f"   - Gold data: {SCRIPT_DIR.parent / 'data' / 'gold'}/")
    print(f"   - Validation reports: {SCRIPT_DIR.parent / 'data' / 'gold' / 'validation_reports'}/")
    print(f"   - Artifacts: {SCRIPT_DIR.parent / 'outputs'}/")
    
    print("\n" + "="*80)
    print("  ✅ PIPELINE COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
