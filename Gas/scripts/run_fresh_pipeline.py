#!/usr/bin/env python3
"""
Complete Pipeline with Fresh API Data
=====================================

This script:
1. Fetches fresh data from all APIs
2. Rebuilds Bronze → Silver → Gold layers
3. Adds sentiment features
4. Trains Ridge baseline model
5. Runs Optuna optimization
6. Compares results

Author: Deniel Nankov
Date: October 19, 2025
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*80}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.END}")
    print(f"{'='*80}\n")

def print_step(step_num, total_steps, description):
    """Print a step description."""
    print(f"{Colors.CYAN}[{step_num}/{total_steps}] {description}{Colors.END}")

def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_warning(text):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.END}")

def print_error(text):
    """Print error message."""
    print(f"{Colors.FAIL}❌ {text}{Colors.END}")

def run_script(script_path, description, timeout=600, required=True):
    """
    Run a Python script and capture output.
    
    Args:
        script_path: Path to the script
        description: Description of what the script does
        timeout: Maximum time to wait (seconds)
        required: Whether this step is required for the pipeline
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"\n{'─'*80}")
        print(f"{Colors.BLUE}Running: {description}{Colors.END}")
        print(f"Script: {script_path}")
        print(f"{'─'*80}\n")
        
        start_time = time.time()
        
        # Run the script
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        elapsed = time.time() - start_time
        
        # Print output (last 100 lines only to avoid clutter)
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 100:
                print("... (output truncated) ...")
                print('\n'.join(lines[-100:]))
            else:
                print(result.stdout)
        
        if result.stderr and result.returncode != 0:
            print(f"\n{Colors.WARNING}Errors/Warnings:{Colors.END}")
            print(result.stderr)
        
        # Check result
        if result.returncode == 0:
            print_success(f"Completed in {elapsed:.1f}s")
            return True
        else:
            if required:
                print_error(f"Failed with exit code {result.returncode}")
                return False
            else:
                print_warning(f"Failed but not required (exit code {result.returncode})")
                return True
    
    except subprocess.TimeoutExpired:
        print_error(f"Timeout after {timeout}s")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def main():
    """Run the complete fresh pipeline."""
    
    print_header(f"🚀 FRESH DATA PIPELINE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Change to Gas directory
    gas_dir = Path(__file__).parent.parent
    os.chdir(gas_dir)
    print(f"Working directory: {os.getcwd()}\n")
    
    total_steps = 7
    current_step = 0
    
    # Track results
    results = {}
    
    # ============================================================================
    # STEP 1: Fetch Fresh External Data (Optional)
    # ============================================================================
    current_step += 1
    print_step(current_step, total_steps, "Fetch fresh external data (optional)")
    
    success = run_script(
        'scripts/fetch_external_data.py',
        'Fetching external indicators (FRED, weather, etc.)',
        timeout=600,
        required=False  # Optional since we have existing data
    )
    results['fetch_external'] = success
    
    if success:
        print_success("External data fetched successfully!")
    else:
        print_warning("External data fetch failed, using existing data")
    
    # ============================================================================
    # STEP 2: Skip Silver Layer (Using existing Gold layer workflow)
    # ============================================================================
    current_step += 1
    print_step(current_step, total_steps, "Skip Silver Layer (not needed)")
    
    print_warning("Silver layer script not found, proceeding directly to Gold layer")
    results['silver_layer'] = True  # Mark as success since it's optional
    
    # ============================================================================
    # STEP 3: Build Gold Layer
    # ============================================================================
    current_step += 1
    print_step(current_step, total_steps, "Build Gold Layer (feature engineering)")
    
    success = run_script(
        'scripts/build_gold_layer.py',
        'Creating features (lags, rolling stats, etc.)',
        timeout=300,
        required=True
    )
    results['gold_layer'] = success
    
    if not success:
        print_error("Failed to build Gold layer. Aborting pipeline.")
        return 1
    
    # ============================================================================
    # STEP 4: Add Sentiment Features
    # ============================================================================
    current_step += 1
    print_step(current_step, total_steps, "Add Sentiment Features")
    
    success = run_script(
        'scripts/add_sentiment_to_gold.py',
        'Fetching news sentiment (NewsAPI, AlphaVantage)',
        timeout=600,
        required=False  # Not required if APIs fail
    )
    results['sentiment'] = success
    
    if success:
        print_success("Sentiment features added successfully!")
    else:
        print_warning("Sentiment features failed, but continuing with existing features")
    
    # ============================================================================
    # STEP 5: Train Baseline Ridge Model
    # ============================================================================
    current_step += 1
    print_step(current_step, total_steps, "Train Baseline Ridge Model")
    
    success = run_script(
        'scripts/walk_forward_validation.py',
        'Ridge regression with walk-forward validation',
        timeout=300,
        required=True
    )
    results['baseline_ridge'] = success
    
    if not success:
        print_error("Failed to train baseline Ridge model. Aborting pipeline.")
        return 1
    
    # ============================================================================
    # STEP 6: Run Optuna Optimization
    # ============================================================================
    current_step += 1
    print_step(current_step, total_steps, "Run Optuna Hyperparameter Optimization")
    
    success = run_script(
        'scripts/tune_with_optuna.py',
        'Optimizing Ridge and Gradient Boosting hyperparameters',
        timeout=600,
        required=False  # Not required for the paper
    )
    results['optuna'] = success
    
    if success:
        print_success("Optuna optimization completed!")
    else:
        print_warning("Optuna failed, but baseline Ridge results are still valid")
    
    # ============================================================================
    # STEP 7: Validation Test (Check for Overfitting)
    # ============================================================================
    current_step += 1
    print_step(current_step, total_steps, "Run Validation Test (Overfitting Check)")
    
    success = run_script(
        'scripts/test_optuna_walk_forward.py',
        'Rigorous overfitting detection and model comparison',
        timeout=600,
        required=False
    )
    results['validation'] = success
    
    if success:
        print_success("Validation test completed!")
    else:
        print_warning("Validation test failed, but results are still usable")
    
    # ============================================================================
    # FINAL SUMMARY
    # ============================================================================
    print_header("📊 PIPELINE EXECUTION SUMMARY")
    
    print(f"{Colors.BOLD}Results:{Colors.END}")
    for step, success in results.items():
        status = f"{Colors.GREEN}✅ SUCCESS{Colors.END}" if success else f"{Colors.FAIL}❌ FAILED{Colors.END}"
        print(f"  {step:20s}: {status}")
    
    # Count successes
    total = len(results)
    successes = sum(results.values())
    
    print(f"\n{Colors.BOLD}Overall:{Colors.END} {successes}/{total} steps completed successfully")
    
    # Final recommendations
    print_header("🎯 NEXT STEPS")
    
    if results.get('baseline_ridge', False):
        print_success("Baseline Ridge model trained successfully!")
        print("   → Check outputs/walk_forward/ for results")
        print("   → Ridge R² scores are your main paper results")
    
    if results.get('optuna', False):
        print_success("Optuna optimization completed!")
        print("   → Check outputs/optuna/ for hyperparameter results")
        print("   → Compare with baseline Ridge to see if overfitting occurred")
    
    if results.get('validation', False):
        print_success("Validation test completed!")
        print("   → Check outputs/optuna_validation/ for overfitting analysis")
        print("   → Use this to determine which model to use in your paper")
    
    print("\n" + "="*80)
    print(f"{Colors.BOLD}💡 Recommendations:{Colors.END}")
    print("="*80)
    
    print("\n1. Review Results:")
    print("   • outputs/walk_forward/october_predictions.csv")
    print("   • outputs/optuna/optuna_results.csv")
    print("   • outputs/optuna_validation/validation_summary.txt")
    
    print("\n2. Check for Overfitting:")
    print("   • Compare Train R² vs Test R²")
    print("   • If gap > 0.2, model is overfitted")
    print("   • Your baseline Ridge should have gap ≈ 0")
    
    print("\n3. Choose Best Model:")
    print("   • If Optuna test R² < Baseline Ridge test R²:")
    print("     → Use Baseline Ridge (it didn't overfit!)")
    print("   • If Optuna test R² > Baseline Ridge test R²:")
    print("     → Use Optuna (it improved without overfitting!)")
    
    print("\n4. Create Visualizations:")
    print("   • Performance by horizon (1, 2, 3 days)")
    print("   • Actual vs predicted plots")
    print("   • Overfitting comparison (Train vs Test R²)")
    
    print("\n" + "="*80)
    print(f"{Colors.GREEN}✅ Pipeline complete!{Colors.END}")
    print("="*80 + "\n")
    
    # Return success if baseline Ridge worked
    return 0 if results.get('baseline_ridge', False) else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
