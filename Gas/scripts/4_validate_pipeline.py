"""
Comprehensive Data Validation Pipeline

This script runs ALL validation checks across the medallion architecture:
- Bronze → Silver validation (data quality, schema, outliers)
- Silver → Gold validation (temporal consistency, feature engineering)
- Gold layer validation (leakage detection, feature integrity)

Generates detailed reports and fails with exit code 1 if critical issues found.

Author: Kalshi Gas Forecasting Team
Date: October 2025
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
import json

# Add scripts directory to path for imports
sys.path.append(str(Path(__file__).parent))
from detect_leakage import LeakageDetector

# Directories
PROJECT_ROOT = Path(__file__).parent.parent
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"
SILVER_DIR = PROJECT_ROOT / "data" / "silver"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"
VALIDATION_DIR = GOLD_DIR / "validation_reports"
VALIDATION_DIR.mkdir(parents=True, exist_ok=True)


class ValidationReport:
    """Track validation results across all stages."""
    
    def __init__(self):
        self.results = {
            'bronze_to_silver': [],
            'silver_to_gold': [],
            'gold_leakage': [],
            'summary': {}
        }
        self.critical_count = 0
        self.warning_count = 0
        
    def add_result(self, stage: str, test: str, status: str, message: str, details: Dict = None):
        """Add a validation result."""
        result = {
            'stage': stage,
            'test': test,
            'status': status,  # PASS, WARNING, CRITICAL
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.results[stage].append(result)
        
        if status == 'CRITICAL':
            self.critical_count += 1
        elif status == 'WARNING':
            self.warning_count += 1
    
    def print_summary(self):
        """Print validation summary."""
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        
        total_tests = sum(len(v) for v in self.results.values() if isinstance(v, list))
        
        print(f"\nTotal tests run: {total_tests}")
        print(f"🚨 CRITICAL issues: {self.critical_count}")
        print(f"⚠️  WARNINGS: {self.warning_count}")
        print(f"✅ PASSED: {total_tests - self.critical_count - self.warning_count}")
        
        # Print critical issues
        if self.critical_count > 0:
            print("\n" + "="*80)
            print("❌ CRITICAL ISSUES:")
            print("="*80)
            for stage_results in self.results.values():
                if isinstance(stage_results, list):
                    for result in stage_results:
                        if result['status'] == 'CRITICAL':
                            print(f"\n[{result['stage']}] {result['test']}")
                            print(f"   {result['message']}")
        
        # Print warnings
        if self.warning_count > 0:
            print("\n" + "="*80)
            print("⚠️  WARNINGS:")
            print("="*80)
            for stage_results in self.results.values():
                if isinstance(stage_results, list):
                    for result in stage_results:
                        if result['status'] == 'WARNING':
                            print(f"\n[{result['stage']}] {result['test']}")
                            print(f"   {result['message']}")
        
        # Final verdict
        print("\n" + "="*80)
        if self.critical_count > 0:
            print("❌ VERDICT: VALIDATION FAILED - CRITICAL ISSUES DETECTED")
            print("="*80)
            return False
        elif self.warning_count > 0:
            print("⚠️  VERDICT: VALIDATION PASSED WITH WARNINGS")
            print("="*80)
            return True
        else:
            print("✅ VERDICT: ALL VALIDATIONS PASSED")
            print("="*80)
            return True
    
    def save_report(self, filename: str = "validation_report.json"):
        """Save detailed validation report."""
        output_path = VALIDATION_DIR / filename
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Detailed report saved to: {output_path}")


def validate_silver_layer(report: ValidationReport):
    """Validate silver layer data quality."""
    print("\n" + "="*80)
    print("🔍 VALIDATING SILVER LAYER")
    print("="*80)
    
    silver_files = {
        'eia_retail_prices_cleaned.parquet': {'required_cols': ['date', 'retail_price'], 'min_rows': 200},
        'eia_inventory_weekly.parquet': {'required_cols': ['date', 'inventory_mbbl'], 'min_rows': 200},
        'eia_utilization_weekly.parquet': {'required_cols': ['date', 'utilization_pct'], 'min_rows': 200},
    }
    
    for filename, requirements in silver_files.items():
        filepath = SILVER_DIR / filename
        
        print(f"\n📋 Checking: {filename}")
        
        # Check file exists
        if not filepath.exists():
            report.add_result(
                'bronze_to_silver',
                f'file_exists_{filename}',
                'WARNING',
                f'File not found: {filename}'
            )
            continue
        
        # Load and validate
        try:
            df = pd.read_parquet(filepath)
            
            # Check row count
            if len(df) < requirements['min_rows']:
                report.add_result(
                    'bronze_to_silver',
                    f'row_count_{filename}',
                    'WARNING',
                    f'Only {len(df)} rows (expected >={requirements["min_rows"]})'
                )
            else:
                print(f"   ✓ Row count: {len(df)} rows")
            
            # Check required columns
            missing_cols = set(requirements['required_cols']) - set(df.columns)
            if missing_cols:
                report.add_result(
                    'bronze_to_silver',
                    f'schema_{filename}',
                    'CRITICAL',
                    f'Missing columns: {missing_cols}'
                )
            else:
                print(f"   ✓ Schema valid: {requirements['required_cols']}")
            
            # Check for nulls
            for col in requirements['required_cols']:
                if col in df.columns:
                    null_pct = df[col].isna().sum() / len(df) * 100
                    if null_pct > 5:
                        report.add_result(
                            'bronze_to_silver',
                            f'nulls_{filename}_{col}',
                            'WARNING',
                            f'{col} has {null_pct:.1f}% nulls (>5% threshold)'
                        )
                    else:
                        print(f"   ✓ {col}: {null_pct:.1f}% nulls")
            
            # Check date continuity
            if 'date' in df.columns:
                df_sorted = df.sort_values('date')
                gaps = df_sorted['date'].diff().dt.days
                max_gap = gaps.max()
                if pd.notna(max_gap) and max_gap > 30:
                    report.add_result(
                        'bronze_to_silver',
                        f'date_continuity_{filename}',
                        'WARNING',
                        f'Maximum gap: {max_gap} days (>30 day threshold)',
                        {'max_gap_days': int(max_gap)}
                    )
                else:
                    print(f"   ✓ Date continuity: max gap {max_gap} days")
        
        except Exception as e:
            report.add_result(
                'bronze_to_silver',
                f'load_error_{filename}',
                'CRITICAL',
                f'Failed to load: {str(e)}'
            )


def validate_gold_layer(report: ValidationReport):
    """Validate gold layer feature engineering."""
    print("\n" + "="*80)
    print("🔍 VALIDATING GOLD LAYER")
    print("="*80)
    
    gold_file = GOLD_DIR / "master_model_ready.parquet"
    
    if not gold_file.exists():
        report.add_result(
            'silver_to_gold',
            'gold_file_exists',
            'CRITICAL',
            f'Gold layer file not found: {gold_file}'
        )
        return
    
    print(f"\n📋 Loading: {gold_file.name}")
    df = pd.read_parquet(gold_file)
    
    print(f"   Rows: {len(df)}")
    print(f"   Columns: {len(df.columns)}")
    
    # Check for target column
    if 'target' not in df.columns:
        report.add_result(
            'silver_to_gold',
            'target_exists',
            'CRITICAL',
            'Target column not found in gold dataset'
        )
        return
    else:
        print(f"   ✓ Target column present")
    
    # Check target statistics
    target_nulls = df['target'].isna().sum()
    if target_nulls > 0:
        report.add_result(
            'silver_to_gold',
            'target_nulls',
            'CRITICAL',
            f'Target has {target_nulls} null values'
        )
    else:
        print(f"   ✓ Target has no nulls")
    
    # Check for suspicious columns that shouldn't be features
    suspicious_cols = ['retail_price', 'gas_price', 'gas_price_actual']
    found_suspicious = [col for col in suspicious_cols if col in df.columns]
    
    if found_suspicious:
        report.add_result(
            'silver_to_gold',
            'suspicious_features',
            'WARNING',
            f'Found potentially leaky features: {found_suspicious}',
            {'features': found_suspicious}
        )
        print(f"   ⚠️  Suspicious unlagged features found: {found_suspicious}")
    else:
        print(f"   ✓ No suspicious unlagged price features")
    
    # Check feature null percentages
    feature_cols = [col for col in df.columns if col not in ['date', 'target', 'gas_price_actual']]
    high_null_features = []
    
    for col in feature_cols:
        null_pct = df[col].isna().sum() / len(df) * 100
        if null_pct > 10:
            high_null_features.append((col, null_pct))
    
    if high_null_features:
        report.add_result(
            'silver_to_gold',
            'feature_nulls',
            'WARNING',
            f'{len(high_null_features)} features have >10% nulls',
            {'features': [(col, f"{pct:.1f}%") for col, pct in high_null_features[:10]]}
        )
        print(f"   ⚠️  {len(high_null_features)} features with >10% nulls")
    else:
        print(f"   ✓ All features have <10% nulls")


def validate_leakage(report: ValidationReport):
    """Run comprehensive leakage detection on gold layer."""
    print("\n" + "="*80)
    print("🔍 RUNNING LEAKAGE DETECTION")
    print("="*80)
    
    gold_file = GOLD_DIR / "master_model_ready.parquet"
    
    if not gold_file.exists():
        report.add_result(
            'gold_leakage',
            'gold_file_missing',
            'CRITICAL',
            'Cannot run leakage detection - gold file missing'
        )
        return
    
    df = pd.read_parquet(gold_file)
    
    # Find target column
    if 'target' not in df.columns:
        report.add_result(
            'gold_leakage',
            'target_missing',
            'CRITICAL',
            'Cannot run leakage detection - target column missing'
        )
        return
    
    # Get COMMON_FEATURES from baseline_models.py
    # This ensures we only check features actually used in training
    try:
        sys.path.append(str(PROJECT_ROOT / "src" / "models"))
        from baseline_models import COMMON_FEATURES
        
        feature_cols = COMMON_FEATURES
        print(f"\n   Using {len(feature_cols)} features from COMMON_FEATURES")
        
    except Exception as e:
        # Fallback: use all numeric columns except target
        print(f"\n   ⚠️  Could not load COMMON_FEATURES, using all numeric columns")
        feature_cols = [col for col in df.columns 
                       if col not in ['date', 'target', 'gas_price_actual', 'gas_price']
                       and pd.api.types.is_numeric_dtype(df[col])]
    
    # Run leakage detector
    detector = LeakageDetector(horizon=14, correlation_threshold=0.50)
    results = detector.run_all_checks(df, feature_cols, 'target')
    
    # Add leakage results to report
    if results['summary']['critical'] > 0:
        report.add_result(
            'gold_leakage',
            'critical_leakage',
            'CRITICAL',
            f"{results['summary']['critical']} features have critical leakage (correlation >0.95)",
            {'features': list(results['perfect_predictions'].keys())}
        )
    
    if results['summary']['warnings'] > 10:  # Only flag if many warnings
        report.add_result(
            'gold_leakage',
            'lag_warnings',
            'WARNING',
            f"{results['summary']['warnings']} features have potential lag issues"
        )
    
    if results['summary']['suspicious'] > 15:  # Only flag if many suspicious
        report.add_result(
            'gold_leakage',
            'high_correlations',
            'WARNING',
            f"{results['summary']['suspicious']} features have high correlations (>0.50)",
            {'features': list(results['suspicious_correlations'].keys())[:10]}
        )
    
    # Save detailed leakage report
    detector.save_report(str(VALIDATION_DIR / 'leakage_detection_report.csv'))


def main():
    """Run complete validation pipeline."""
    print("="*80)
    print("🏗️  COMPREHENSIVE PIPELINE VALIDATION")
    print("="*80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project: {PROJECT_ROOT}")
    print("="*80)
    
    report = ValidationReport()
    
    try:
        # Stage 1: Validate Silver Layer
        validate_silver_layer(report)
        
        # Stage 2: Validate Gold Layer
        validate_gold_layer(report)
        
        # Stage 3: Leakage Detection
        validate_leakage(report)
        
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Print summary
    success = report.print_summary()
    
    # Save detailed report
    report.save_report()
    
    # Exit with appropriate code
    if not success:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
