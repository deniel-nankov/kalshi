"""
Add News Sentiment Features to Gold Layer

This script loads the existing Gold layer data and adds 9 properly-lagged
sentiment features from the Silver layer news sentiment data.

All features use 15-day lag to prevent temporal leakage for 14-day forecast horizon.

Features Added:
1. news_sentiment_lag15: Sentiment 15 days before (direct lag)
2. news_sentiment_7d_avg: 7-day average sentiment (lagged)
3. news_sentiment_14d_avg: 14-day average sentiment (lagged)
4. news_sentiment_volatility_7d: 7-day sentiment volatility (lagged)
5. news_sentiment_volatility_14d: 14-day sentiment volatility (lagged)
6. news_volume_lag15: Article count 15 days before
7. news_volume_7d_avg: 7-day average article count (lagged)
8. sentiment_momentum_7d: Change in sentiment (lagged)
9. extreme_sentiment_flag: Binary flag for extreme sentiment (|score| > 0.3)

Usage:
    python scripts/add_sentiment_to_gold.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SILVER_NEWS_DIR = PROJECT_ROOT / "data" / "silver" / "news"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"

# Constants
FORECAST_HORIZON = 14  # Days ahead we're forecasting
SAFE_LAG = FORECAST_HORIZON + 1  # 15 days to be safe


def load_silver_sentiment() -> pd.DataFrame:
    """Load Silver layer news sentiment data"""
    print("\n" + "="*80)
    print("LOADING SILVER LAYER SENTIMENT DATA")
    print("="*80)
    
    # Find latest Silver sentiment file
    sentiment_files = list(SILVER_NEWS_DIR.glob("energy_news_sentiment_daily_*.parquet"))
    
    if not sentiment_files:
        print("❌ No Silver layer sentiment files found!")
        print(f"   Expected location: {SILVER_NEWS_DIR}")
        return pd.DataFrame()
    
    latest_file = max(sentiment_files, key=lambda p: p.stat().st_mtime)
    print(f"📂 Loading: {latest_file.name}")
    
    df = pd.read_parquet(latest_file)
    df['date'] = pd.to_datetime(df['date'])
    
    print(f"✅ Loaded {len(df)} days of sentiment data")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    
    return df


def load_existing_gold() -> pd.DataFrame:
    """Load existing Gold layer data"""
    print("\n" + "="*80)
    print("LOADING EXISTING GOLD LAYER")
    print("="*80)
    
    gold_file = GOLD_DIR / "master_model_ready.parquet"
    
    if not gold_file.exists():
        print(f"❌ Gold layer file not found: {gold_file}")
        print("   Please run build_gold_layer.py first!")
        return pd.DataFrame()
    
    df = pd.read_parquet(gold_file)
    df['date'] = pd.to_datetime(df['date'])
    
    print(f"✅ Loaded Gold layer: {len(df)} rows × {len(df.columns)} columns")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Existing features: {len(df.columns)}")
    
    return df


def engineer_sentiment_features(sentiment_df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer sentiment features with proper 15-day lag
    
    All features are lagged by 15 days to prevent temporal leakage
    for 14-day forecast horizon.
    """
    print("\n" + "="*80)
    print("ENGINEERING SENTIMENT FEATURES")
    print("="*80)
    
    df = sentiment_df.copy()
    df = df.sort_values('date').set_index('date')
    
    print(f"   Forecast horizon: {FORECAST_HORIZON} days")
    print(f"   Safe lag: {SAFE_LAG} days")
    print(f"   Preventing temporal leakage...")
    
    # 1. Direct lagged sentiment (15 days before)
    df['news_sentiment_lag15'] = df['sentiment_mean'].shift(SAFE_LAG)
    print(f"   ✓ news_sentiment_lag15 (direct lag)")
    
    # 2. Rolling averages (on lagged data)
    df['news_sentiment_7d_avg'] = df['sentiment_mean'].shift(SAFE_LAG).rolling(7, min_periods=1).mean()
    df['news_sentiment_14d_avg'] = df['sentiment_mean'].shift(SAFE_LAG).rolling(14, min_periods=1).mean()
    print(f"   ✓ news_sentiment_7d_avg, news_sentiment_14d_avg (rolling averages)")
    
    # 3. Volatility measures (on lagged data)
    df['news_sentiment_volatility_7d'] = df['sentiment_mean'].shift(SAFE_LAG).rolling(7, min_periods=2).std()
    df['news_sentiment_volatility_14d'] = df['sentiment_mean'].shift(SAFE_LAG).rolling(14, min_periods=2).std()
    print(f"   ✓ news_sentiment_volatility_7d, news_sentiment_volatility_14d (volatility)")
    
    # 4. Article volume (lagged)
    df['news_volume_lag15'] = df['article_count'].shift(SAFE_LAG)
    df['news_volume_7d_avg'] = df['article_count'].shift(SAFE_LAG).rolling(7, min_periods=1).mean()
    print(f"   ✓ news_volume_lag15, news_volume_7d_avg (article volume)")
    
    # 5. Sentiment momentum (change in 7d avg)
    df['sentiment_momentum_7d'] = df['news_sentiment_7d_avg'] - df['news_sentiment_14d_avg']
    print(f"   ✓ sentiment_momentum_7d (momentum)")
    
    # 6. Extreme sentiment flag (binary: |sentiment| > 0.3)
    df['extreme_sentiment_flag'] = (df['news_sentiment_lag15'].abs() > 0.3).astype(int)
    print(f"   ✓ extreme_sentiment_flag (binary indicator)")
    
    # Keep only date and new features
    feature_cols = [
        'news_sentiment_lag15',
        'news_sentiment_7d_avg',
        'news_sentiment_14d_avg',
        'news_sentiment_volatility_7d',
        'news_sentiment_volatility_14d',
        'news_volume_lag15',
        'news_volume_7d_avg',
        'sentiment_momentum_7d',
        'extreme_sentiment_flag'
    ]
    
    df = df[feature_cols].reset_index()
    
    print(f"\n✅ Created {len(feature_cols)} sentiment features")
    print(f"   Total rows: {len(df)}")
    print(f"   Non-null rows: {df[feature_cols].notna().all(axis=1).sum()}")
    
    return df


def merge_with_gold(gold_df: pd.DataFrame, sentiment_features: pd.DataFrame) -> pd.DataFrame:
    """Merge sentiment features with Gold layer"""
    print("\n" + "="*80)
    print("MERGING SENTIMENT FEATURES WITH GOLD LAYER")
    print("="*80)
    
    print(f"   Gold layer: {len(gold_df)} rows")
    print(f"   Sentiment features: {len(sentiment_features)} rows")
    
    # Merge on date
    merged = gold_df.merge(sentiment_features, on='date', how='left')
    
    # Get list of sentiment columns before checking matches
    sentiment_cols = [col for col in sentiment_features.columns if col != 'date']
    
    # Count matches (check first sentiment column)
    if sentiment_cols and sentiment_cols[0] in merged.columns:
        matched = merged[sentiment_cols[0]].notna().sum()
        print(f"   ✓ Matched dates: {matched} / {len(gold_df)} ({matched/len(gold_df)*100:.1f}%)")
    
    # Fill missing sentiment values
    for col in sentiment_cols:
        if col in merged.columns:
            null_count = merged[col].isna().sum()
            if null_count > 0:
                # Fill with 0 for neutral sentiment, or forward-fill
                if 'sentiment' in col or 'momentum' in col:
                    merged[col] = merged[col].fillna(0.0)  # Neutral sentiment
                elif 'volume' in col:
                    merged[col] = merged[col].fillna(0.0)  # No articles
                elif 'flag' in col:
                    merged[col] = merged[col].fillna(0)  # No extreme sentiment
                else:
                    merged[col] = merged[col].fillna(0.0)
                
                print(f"   ⚠️  Filled {null_count} nulls in {col}")
    
    print(f"\n✅ Final dataset: {len(merged)} rows × {len(merged.columns)} columns")
    print(f"   Added {len(sentiment_cols)} sentiment features")
    
    return merged


def validate_no_leakage(df: pd.DataFrame, feature_col: str, target_col: str = 'target') -> None:
    """
    Validate that sentiment features don't leak future information
    
    For 14-day forecast, features at day T should only use data from day T-15 or earlier
    """
    print("\n" + "="*80)
    print(f"TEMPORAL LEAKAGE VALIDATION: {feature_col}")
    print("="*80)
    
    # Check correlation between feature and future target
    # For proper 14-day forecast, correlation should be with target 14 days ahead
    df_clean = df[[feature_col, target_col]].dropna()
    
    if len(df_clean) < 30:
        print("   ⚠️  Insufficient data for validation")
        return
    
    # Correlation with current target
    corr_current = df_clean[feature_col].corr(df_clean[target_col])
    
    # Correlation with target 14 days ahead (what we're forecasting)
    df_clean['target_14d_ahead'] = df_clean[target_col].shift(-14)
    df_clean = df_clean.dropna()
    
    if len(df_clean) > 0:
        corr_future = df_clean[feature_col].corr(df_clean['target_14d_ahead'])
        
        print(f"   Correlation with current target: {corr_current:+.3f}")
        print(f"   Correlation with target +14d ahead: {corr_future:+.3f}")
        
        # Validation: Future correlation should not be suspiciously higher
        if abs(corr_future) > abs(corr_current) * 1.5:
            print(f"   ⚠️  WARNING: Feature may have temporal leakage!")
            print(f"      Future correlation is {abs(corr_future)/abs(corr_current):.1f}x higher")
        else:
            print(f"   ✅ No temporal leakage detected")
    else:
        print("   ⚠️  Insufficient overlapping data")


def save_enhanced_gold(df: pd.DataFrame) -> None:
    """Save Gold layer with sentiment features"""
    print("\n" + "="*80)
    print("SAVING ENHANCED GOLD LAYER")
    print("="*80)
    
    # Save master_model_ready with sentiment
    output_file = GOLD_DIR / "master_model_ready.parquet"
    backup_file = GOLD_DIR / "master_model_ready_no_sentiment.parquet"
    
    # Backup original if it exists
    if output_file.exists():
        import shutil
        shutil.copy(output_file, backup_file)
        print(f"   💾 Backed up original to: {backup_file.name}")
    
    df.to_parquet(output_file, index=False)
    print(f"✅ Saved: {output_file}")
    print(f"   Rows: {len(df)}")
    print(f"   Columns: {len(df.columns)}")
    
    # Also update master_daily and master_october if they exist
    for filename in ["master_daily.parquet", "master_october.parquet"]:
        input_file = GOLD_DIR / filename
        if input_file.exists():
            df_subset = pd.read_parquet(input_file)
            df_subset['date'] = pd.to_datetime(df_subset['date'])
            
            # Get sentiment features
            sentiment_cols = [col for col in df.columns if 'sentiment' in col or 'news_volume' in col or 'extreme_sentiment' in col]
            sentiment_data = df[['date'] + sentiment_cols]
            
            # Merge
            df_subset = df_subset.merge(sentiment_data, on='date', how='left')
            
            # Fill nulls
            for col in sentiment_cols:
                if col in df_subset.columns:
                    if 'sentiment' in col or 'momentum' in col:
                        df_subset[col] = df_subset[col].fillna(0.0)
                    elif 'volume' in col:
                        df_subset[col] = df_subset[col].fillna(0.0)
                    elif 'flag' in col:
                        df_subset[col] = df_subset[col].fillna(0)
            
            df_subset.to_parquet(input_file, index=False)
            print(f"   ✓ Updated: {filename}")


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("NEWS SENTIMENT: GOLD LAYER ENHANCEMENT")
    print("="*80)
    
    # Load data
    sentiment_df = load_silver_sentiment()
    if sentiment_df.empty:
        print("❌ Cannot proceed without sentiment data!")
        return 1
    
    gold_df = load_existing_gold()
    if gold_df.empty:
        print("❌ Cannot proceed without Gold layer data!")
        return 1
    
    # Engineer features
    sentiment_features = engineer_sentiment_features(sentiment_df)
    
    # Merge
    enhanced_gold = merge_with_gold(gold_df, sentiment_features)
    
    # Validate no leakage
    validate_no_leakage(enhanced_gold, 'news_sentiment_lag15', 'target')
    
    # Save
    save_enhanced_gold(enhanced_gold)
    
    print("\n" + "="*80)
    print("✅ SENTIMENT FEATURES SUCCESSFULLY ADDED TO GOLD LAYER!")
    print("="*80)
    print("\n📊 Summary:")
    print(f"   Original features: {len(gold_df.columns)}")
    print(f"   New sentiment features: 9")
    print(f"   Total features: {len(enhanced_gold.columns)}")
    print(f"   Rows: {len(enhanced_gold)}")
    print(f"   Forecast horizon: {FORECAST_HORIZON} days (properly lagged)")
    
    print("\n🎯 Next steps:")
    print("   1. Run leakage detection: python scripts/detect_leakage.py")
    print("   2. Retrain models: python scripts/run_pipeline.py")
    print("   3. Compare R² before/after")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
