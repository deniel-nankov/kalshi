"""
Data Leakage Detection Module

This module provides comprehensive checks to detect temporal data leakage
in time series forecasting pipelines. It catches bugs like the SPR release
calculation that used future information.

Key Principles:
1. Features at time t can only use data up to time t-horizon
2. Target at time t should predict t+horizon
3. Correlations between lagged features and targets should be modest (<0.50)
4. No feature should have perfect/near-perfect correlation with target

Author: Kalshi Gas Forecasting Team
Date: October 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import warnings
from pathlib import Path


class LeakageDetector:
    """
    Detects various forms of temporal data leakage in time series datasets.
    """
    
    def __init__(self, horizon: int = 14, correlation_threshold: float = 0.50):
        """
        Initialize leakage detector.
        
        Parameters:
        -----------
        horizon : int
            Forecast horizon in days (default: 14)
        correlation_threshold : float
            Maximum acceptable correlation between features and target (default: 0.50)
        """
        self.horizon = horizon
        self.correlation_threshold = correlation_threshold
        self.leakage_report = []
        
    def check_feature_target_correlation(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
        target_col: str
    ) -> Dict[str, float]:
        """
        Check if any features have suspiciously high correlation with target.
        
        High correlation (>0.50) often indicates data leakage, especially for
        lagged features in time series forecasting.
        
        Returns:
        --------
        Dict mapping feature names to correlation values (only suspicious ones)
        """
        suspicious_features = {}
        
        for feature in feature_cols:
            if feature not in df.columns:
                continue
                
            if df[feature].isna().all() or df[target_col].isna().all():
                continue
            
            # Skip non-numeric columns
            if not pd.api.types.is_numeric_dtype(df[feature]):
                continue
                
            corr = df[feature].corr(df[target_col])
            
            if abs(corr) > self.correlation_threshold:
                suspicious_features[feature] = corr
                self.leakage_report.append({
                    'test': 'feature_target_correlation',
                    'feature': feature,
                    'correlation': corr,
                    'threshold': self.correlation_threshold,
                    'status': 'SUSPICIOUS',
                    'message': f'Correlation {corr:.3f} exceeds threshold {self.correlation_threshold:.3f}'
                })
        
        return suspicious_features
    
    def check_future_information(
        self,
        df: pd.DataFrame,
        date_col: str = 'date'
    ) -> List[str]:
        """
        Check if dataset contains dates from the future.
        
        Returns:
        --------
        List of columns containing future dates
        """
        today = pd.Timestamp.today().normalize()
        future_dates = []
        
        # Check date index or column
        if date_col in df.columns or df.index.name == date_col:
            dates = df[date_col] if date_col in df.columns else df.index
            
            if pd.api.types.is_datetime64_any_dtype(dates):
                max_date = dates.max()
                
                if max_date > today:
                    future_dates.append(date_col)
                    self.leakage_report.append({
                        'test': 'future_information',
                        'feature': date_col,
                        'max_date': str(max_date.date()),
                        'today': str(today.date()),
                        'status': 'WARNING',
                        'message': f'Dataset contains future dates up to {max_date.date()}'
                    })
        
        return future_dates
    
    def check_perfect_predictions(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
        target_col: str,
        threshold: float = 0.95
    ) -> Dict[str, float]:
        """
        Detect features with near-perfect correlation (>0.95) to target.
        
        This is almost always data leakage - no real-world feature should
        predict a 14-day ahead target with >95% correlation.
        
        Returns:
        --------
        Dict of features with suspiciously high correlations
        """
        perfect_features = {}
        
        for feature in feature_cols:
            if feature not in df.columns:
                continue
                
            if df[feature].isna().all() or df[target_col].isna().all():
                continue
            
            # Skip non-numeric columns
            if not pd.api.types.is_numeric_dtype(df[feature]):
                continue
                
            corr = abs(df[feature].corr(df[target_col]))
            
            if corr > threshold:
                perfect_features[feature] = corr
                self.leakage_report.append({
                    'test': 'perfect_prediction',
                    'feature': feature,
                    'correlation': corr,
                    'threshold': threshold,
                    'status': 'CRITICAL',
                    'message': f'Near-perfect correlation {corr:.3f} - almost certainly data leakage!'
                })
        
        return perfect_features
    
    def check_diff_features(
        self,
        df: pd.DataFrame,
        feature_cols: List[str]
    ) -> List[str]:
        """
        Identify features that look like diff() calculations without proper lag.
        
        Features ending in '_change', '_diff', '_delta' are suspicious if they
        have very low variance or high correlation with target.
        
        Returns:
        --------
        List of suspicious diff-based features
        """
        suspicious_diffs = []
        diff_patterns = ['_change', '_diff', '_delta', '_release', '_growth']
        
        for feature in feature_cols:
            if feature not in df.columns:
                continue
                
            # Check if feature name suggests it's a diff
            is_diff_feature = any(pattern in feature.lower() for pattern in diff_patterns)
            
            if is_diff_feature:
                # Check if variance is suspiciously high (might be unlagged)
                variance = df[feature].var()
                
                if pd.notna(variance) and variance > 0:
                    # Calculate autocorrelation at lag=1
                    autocorr = df[feature].autocorr(lag=1)
                    
                    if pd.notna(autocorr) and abs(autocorr) < 0.1:
                        # Low autocorrelation in a diff feature is suspicious
                        # (properly lagged diffs should have some autocorrelation)
                        suspicious_diffs.append(feature)
                        self.leakage_report.append({
                            'test': 'diff_feature_check',
                            'feature': feature,
                            'autocorr_lag1': autocorr,
                            'status': 'WARNING',
                            'message': f'Diff feature with low autocorrelation - check if properly lagged'
                        })
        
        return suspicious_diffs
    
    def check_lag_consistency(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
        expected_lag: int
    ) -> Dict[str, int]:
        """
        Verify that features are properly lagged by expected horizon.
        
        Uses autocorrelation to estimate effective lag. Features should be
        lagged by at least `expected_lag` days.
        
        Returns:
        --------
        Dict mapping feature names to estimated lags (for suspicious features)
        """
        inconsistent_lags = {}
        
        for feature in feature_cols:
            if feature not in df.columns:
                continue
                
            if df[feature].isna().all():
                continue
            
            # Skip non-numeric columns
            if not pd.api.types.is_numeric_dtype(df[feature]):
                continue
            
            # Skip binary/categorical features
            if df[feature].nunique() <= 5:
                continue
                
            # Calculate cross-correlation with lagged versions of itself
            # to estimate effective lag
            max_autocorr = 0
            best_lag = 0
            
            for lag in range(1, min(expected_lag + 5, len(df) // 2)):
                try:
                    autocorr = df[feature].autocorr(lag=lag)
                    if pd.notna(autocorr) and abs(autocorr) > abs(max_autocorr):
                        max_autocorr = autocorr
                        best_lag = lag
                except:
                    continue
            
            # If best lag is significantly less than expected, flag it
            if best_lag < expected_lag - 3 and abs(max_autocorr) > 0.3:
                inconsistent_lags[feature] = best_lag
                self.leakage_report.append({
                    'test': 'lag_consistency',
                    'feature': feature,
                    'expected_lag': expected_lag,
                    'estimated_lag': best_lag,
                    'status': 'WARNING',
                    'message': f'Feature may be lagged by {best_lag} instead of {expected_lag}'
                })
        
        return inconsistent_lags
    
    def run_all_checks(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
        target_col: str,
        date_col: str = 'date'
    ) -> Dict:
        """
        Run all leakage detection checks and return comprehensive report.
        
        Returns:
        --------
        Dict with all test results and summary
        """
        print("=" * 80)
        print("DATA LEAKAGE DETECTION REPORT")
        print("=" * 80)
        print(f"\nDataset: {len(df)} rows, {len(feature_cols)} features")
        print(f"Target: {target_col}")
        print(f"Horizon: {self.horizon} days")
        print(f"Correlation threshold: {self.correlation_threshold}")
        print()
        
        # Clear previous report
        self.leakage_report = []
        
        # Run all checks
        print("🔍 Running leakage detection tests...")
        print()
        
        # Test 1: Feature-target correlations
        print("1️⃣  Checking feature-target correlations...")
        suspicious_corrs = self.check_feature_target_correlation(df, feature_cols, target_col)
        print(f"   Found {len(suspicious_corrs)} suspicious features")
        
        # Test 2: Future information
        print("2️⃣  Checking for future dates...")
        future_dates = self.check_future_information(df, date_col)
        print(f"   Found {len(future_dates)} columns with future dates")
        
        # Test 3: Perfect predictions
        print("3️⃣  Checking for near-perfect predictions...")
        perfect_preds = self.check_perfect_predictions(df, feature_cols, target_col)
        print(f"   Found {len(perfect_preds)} features with suspicious correlations >0.95")
        
        # Test 4: Diff features
        print("4️⃣  Checking diff-based features...")
        suspicious_diffs = self.check_diff_features(df, feature_cols)
        print(f"   Found {len(suspicious_diffs)} potentially unlagged diff features")
        
        # Test 5: Lag consistency
        print("5️⃣  Checking lag consistency...")
        inconsistent_lags = self.check_lag_consistency(df, feature_cols, self.horizon)
        print(f"   Found {len(inconsistent_lags)} features with inconsistent lags")
        
        # Summary
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        critical_issues = [r for r in self.leakage_report if r['status'] == 'CRITICAL']
        warnings = [r for r in self.leakage_report if r['status'] == 'WARNING']
        suspicious = [r for r in self.leakage_report if r['status'] == 'SUSPICIOUS']
        
        print(f"\n🚨 CRITICAL: {len(critical_issues)} issues (likely data leakage)")
        print(f"⚠️  WARNING: {len(warnings)} issues (investigate)")
        print(f"🔔 SUSPICIOUS: {len(suspicious)} issues (monitor)")
        
        if critical_issues:
            print("\n❌ CRITICAL ISSUES DETECTED:")
            for issue in critical_issues:
                print(f"   • {issue['feature']}: {issue['message']}")
        
        if warnings:
            print("\n⚠️  WARNINGS:")
            for issue in warnings[:5]:  # Show first 5
                print(f"   • {issue['feature']}: {issue['message']}")
            if len(warnings) > 5:
                print(f"   ... and {len(warnings) - 5} more")
        
        if suspicious:
            print("\n🔔 SUSPICIOUS FEATURES:")
            for issue in suspicious[:5]:  # Show first 5
                print(f"   • {issue['feature']}: {issue['message']}")
            if len(suspicious) > 5:
                print(f"   ... and {len(suspicious) - 5} more")
        
        # Final verdict
        print()
        print("=" * 80)
        if critical_issues:
            print("❌ VERDICT: DATA LEAKAGE DETECTED - DO NOT USE THIS DATASET")
        elif warnings:
            print("⚠️  VERDICT: POTENTIAL ISSUES - INVESTIGATE BEFORE TRAINING")
        elif suspicious:
            print("🔔 VERDICT: SOME SUSPICIOUS FEATURES - MONITOR CLOSELY")
        else:
            print("✅ VERDICT: NO LEAKAGE DETECTED - SAFE TO PROCEED")
        print("=" * 80)
        print()
        
        return {
            'suspicious_correlations': suspicious_corrs,
            'future_dates': future_dates,
            'perfect_predictions': perfect_preds,
            'suspicious_diffs': suspicious_diffs,
            'inconsistent_lags': inconsistent_lags,
            'full_report': self.leakage_report,
            'summary': {
                'critical': len(critical_issues),
                'warnings': len(warnings),
                'suspicious': len(suspicious),
                'total_issues': len(self.leakage_report)
            }
        }
    
    def save_report(self, output_path: str):
        """Save detailed leakage report to CSV."""
        report_df = pd.DataFrame(self.leakage_report)
        report_df.to_csv(output_path, index=False)
        print(f"📄 Detailed report saved to: {output_path}")


def quick_leakage_check(
    df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str,
    horizon: int = 14
) -> bool:
    """
    Quick leakage check - returns True if safe, False if leakage detected.
    
    Use this for fast validation in production pipelines.
    """
    detector = LeakageDetector(horizon=horizon)
    results = detector.run_all_checks(df, feature_cols, target_col)
    
    # Safe if no critical issues
    return results['summary']['critical'] == 0


# Example usage
if __name__ == "__main__":
    import sys
    
    # Check if file path provided
    if len(sys.argv) < 2:
        print("Usage: python detect_leakage.py <path_to_gold_dataset>")
        sys.exit(1)
    
    # Load dataset
    file_path = sys.argv[1]
    print(f"Loading dataset from: {file_path}")
    
    if file_path.endswith('.parquet'):
        df = pd.read_parquet(file_path)
    else:
        df = pd.read_csv(file_path, parse_dates=['date'])
    
    # Identify target column
    possible_targets = ['target', 'target_14d_pct', 'target_14d', 'gas_price_target']
    target_col = None
    for col in possible_targets:
        if col in df.columns:
            target_col = col
            break
    
    if target_col is None:
        print("ERROR: Could not find target column!")
        print(f"Available columns: {df.columns.tolist()}")
        sys.exit(1)
    
    print(f"Using target column: {target_col}\n")
    
    # Exclude non-feature columns
    exclude_cols = ['date', target_col, 'gas_price_actual', 'gas_price', 'Date']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Run detection
    detector = LeakageDetector(horizon=14, correlation_threshold=0.50)
    results = detector.run_all_checks(df, feature_cols, target_col)
    
    # Save report
    output_dir = Path(file_path).parent / 'validation_reports'
    output_dir.mkdir(exist_ok=True)
    
    report_path = output_dir / 'leakage_detection_report.csv'
    detector.save_report(str(report_path))
    
    # Exit with error code if leakage detected
    if results['summary']['critical'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
