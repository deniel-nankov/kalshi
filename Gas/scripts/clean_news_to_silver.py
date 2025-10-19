"""
Silver Layer: News Sentiment Cleaning and Daily Aggregation

This script transforms Bronze layer raw news data into clean, daily-aggregated
sentiment scores suitable for feature engineering.

Processes:
1. Load all Bronze layer news data
2. Apply improved sentiment analysis (VADER for financial text)
3. Remove duplicates
4. Aggregate to daily level (mean sentiment, article count, confidence)
5. Forward-fill missing days
6. Save to Silver layer with validation report

Usage:
    python scripts/clean_news_to_silver.py [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD]
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze" / "news"
SILVER_DIR = PROJECT_ROOT / "data" / "silver" / "news"
SILVER_DIR.mkdir(parents=True, exist_ok=True)

VALIDATION_DIR = PROJECT_ROOT / "data" / "validation"
VALIDATION_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# SENTIMENT ANALYSIS
# ============================================================================

class EnhancedSentimentAnalyzer:
    """
    Enhanced sentiment analysis for financial news
    
    Uses VADER with financial keyword adjustments for better accuracy
    """
    
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        
        # Financial-specific keyword adjustments
        # VADER default scores need adjustment for financial context
        self.financial_boosts = {
            # Strongly positive
            'surge': 0.3, 'soar': 0.3, 'rally': 0.3, 'jump': 0.2,
            'spike': 0.2, 'boost': 0.2, 'gain': 0.15, 'rise': 0.15,
            'strong': 0.15, 'growth': 0.15, 'increase': 0.1, 'up': 0.1,
            'positive': 0.1, 'bullish': 0.3, 'optimistic': 0.2,
            
            # Strongly negative
            'crash': -0.4, 'plunge': -0.3, 'collapse': -0.3, 'slump': -0.3,
            'tumble': -0.25, 'fall': -0.15, 'drop': -0.15, 'decline': -0.15,
            'weak': -0.15, 'loss': -0.15, 'decrease': -0.1, 'down': -0.1,
            'negative': -0.1, 'bearish': -0.3, 'pessimistic': -0.2,
            'concern': -0.15, 'worry': -0.15, 'fear': -0.2,
            
            # Context-specific (oil/energy)
            'shortage': -0.2, 'surplus': -0.1, 'glut': -0.2,
            'supply': 0.0, 'demand': 0.0,  # Neutral until context
            'opec': 0.0, 'production': 0.0,  # Neutral
        }
    
    def analyze(self, text: str) -> dict:
        """
        Analyze sentiment of financial news text
        
        Args:
            text: News headline or summary
            
        Returns:
            dict with sentiment_score, confidence, label
        """
        if pd.isna(text) or not text:
            return {
                'sentiment_score': 0.0,
                'confidence': 0.0,
                'label': 'neutral'
            }
        
        # Get VADER scores
        vader_scores = self.vader.polarity_scores(text)
        base_compound = vader_scores['compound']
        
        # Apply financial keyword adjustments
        text_lower = text.lower()
        adjustment = 0.0
        boost_count = 0
        
        for keyword, boost in self.financial_boosts.items():
            if keyword in text_lower:
                adjustment += boost
                boost_count += 1
        
        # Limit adjustment impact
        if boost_count > 0:
            adjustment = adjustment / boost_count  # Average adjustment
            adjustment = np.clip(adjustment, -0.3, 0.3)  # Cap at ±0.3
        
        # Combine VADER and financial adjustments (weighted)
        final_score = (0.7 * base_compound) + (0.3 * adjustment)
        final_score = np.clip(final_score, -1.0, 1.0)
        
        # Calculate confidence based on VADER's pos/neg balance
        pos = vader_scores['pos']
        neg = vader_scores['neg']
        neu = vader_scores['neu']
        
        # Higher confidence when clearly positive or negative
        confidence = 1.0 - neu  # Lower neutral = higher confidence
        confidence = np.clip(confidence, 0.0, 1.0)
        
        # Determine label
        if final_score > 0.05:
            label = 'positive'
        elif final_score < -0.05:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'sentiment_score': float(final_score),
            'confidence': float(confidence),
            'label': label
        }


# ============================================================================
# DATA PROCESSING
# ============================================================================

def load_bronze_data(start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """Load all Bronze layer news data"""
    print("\n" + "="*80)
    print("LOADING BRONZE LAYER DATA")
    print("="*80)
    
    parquet_files = list(BRONZE_DIR.glob("energy_news_raw_*.parquet"))
    
    if not parquet_files:
        print("❌ No Bronze layer files found!")
        return pd.DataFrame()
    
    print(f"📂 Found {len(parquet_files)} Bronze layer file(s)")
    
    # Load all files
    dfs = []
    for file in parquet_files:
        df = pd.read_parquet(file)
        dfs.append(df)
        print(f"   ✅ Loaded {file.name}: {len(df)} articles")
    
    # Combine
    combined = pd.concat(dfs, ignore_index=True)
    print(f"\n✅ Total articles loaded: {len(combined)}")
    
    # Filter by date if specified
    if start_date or end_date:
        combined['date'] = pd.to_datetime(combined['date'])
        if start_date:
            start = pd.to_datetime(start_date)
            combined = combined[combined['date'] >= start]
            print(f"   Filtered to >= {start_date}: {len(combined)} articles")
        if end_date:
            end = pd.to_datetime(end_date)
            combined = combined[combined['date'] <= end]
            print(f"   Filtered to <= {end_date}: {len(combined)} articles")
    
    return combined


def clean_and_deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicates and clean data"""
    print("\n" + "="*80)
    print("CLEANING AND DEDUPLICATION")
    print("="*80)
    
    initial_count = len(df)
    
    # Remove exact duplicates
    df = df.drop_duplicates()
    print(f"   Removed {initial_count - len(df)} exact duplicates")
    
    # Remove duplicates by date + headline
    df = df.drop_duplicates(subset=['date', 'headline'], keep='first')
    print(f"   Removed {initial_count - len(df)} headline duplicates")
    
    # Remove rows with null headlines
    null_headlines = df['headline'].isna().sum()
    if null_headlines > 0:
        df = df[df['headline'].notna()]
        print(f"   Removed {null_headlines} null headlines")
    
    print(f"\n✅ Clean articles: {len(df)}")
    return df


def apply_enhanced_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    """Apply enhanced VADER sentiment analysis"""
    print("\n" + "="*80)
    print("APPLYING ENHANCED SENTIMENT ANALYSIS")
    print("="*80)
    
    analyzer = EnhancedSentimentAnalyzer()
    
    # Analyze each headline
    print("   Analyzing headlines with VADER + financial keywords...")
    sentiments = df['headline'].apply(analyzer.analyze)
    
    # Extract results
    df['sentiment_score_enhanced'] = sentiments.apply(lambda x: x['sentiment_score'])
    df['sentiment_confidence'] = sentiments.apply(lambda x: x['confidence'])
    df['sentiment_label_enhanced'] = sentiments.apply(lambda x: x['label'])
    
    # Compare with original keyword-based scores
    if 'sentiment_score' in df.columns:
        diff = (df['sentiment_score_enhanced'] - df['sentiment_score']).abs().mean()
        print(f"   Average difference from keyword scores: {diff:.3f}")
    
    # Statistics
    print(f"\n📊 Enhanced Sentiment Statistics:")
    print(f"   Mean: {df['sentiment_score_enhanced'].mean():.3f}")
    print(f"   Std:  {df['sentiment_score_enhanced'].std():.3f}")
    print(f"   Min:  {df['sentiment_score_enhanced'].min():.3f}")
    print(f"   Max:  {df['sentiment_score_enhanced'].max():.3f}")
    print(f"   Avg Confidence: {df['sentiment_confidence'].mean():.3f}")
    
    # Distribution
    pos_count = (df['sentiment_label_enhanced'] == 'positive').sum()
    neu_count = (df['sentiment_label_enhanced'] == 'neutral').sum()
    neg_count = (df['sentiment_label_enhanced'] == 'negative').sum()
    
    print(f"\n📈 Label Distribution:")
    print(f"   Positive: {pos_count} ({pos_count/len(df)*100:.1f}%)")
    print(f"   Neutral:  {neu_count} ({neu_count/len(df)*100:.1f}%)")
    print(f"   Negative: {neg_count} ({neg_count/len(df)*100:.1f}%)")
    
    return df


def aggregate_to_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate to daily sentiment scores"""
    print("\n" + "="*80)
    print("AGGREGATING TO DAILY LEVEL")
    print("="*80)
    
    # Group by date
    daily = df.groupby('date').agg({
        'sentiment_score_enhanced': ['mean', 'std', 'min', 'max'],
        'sentiment_confidence': 'mean',
        'headline': 'count',  # Article count
        'api_source': lambda x: ','.join(x.unique())  # Sources used
    }).reset_index()
    
    # Flatten column names
    daily.columns = [
        'date',
        'sentiment_mean',
        'sentiment_std',
        'sentiment_min',
        'sentiment_max',
        'confidence_mean',
        'article_count',
        'sources'
    ]
    
    # Fill NaN std (single article days)
    daily['sentiment_std'] = daily['sentiment_std'].fillna(0.0)
    
    print(f"   Aggregated to {len(daily)} days")
    print(f"   Date range: {daily['date'].min()} to {daily['date'].max()}")
    print(f"   Avg articles per day: {daily['article_count'].mean():.1f}")
    print(f"   Days with <3 articles: {(daily['article_count'] < 3).sum()}")
    
    return daily


def forward_fill_missing_days(df: pd.DataFrame, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """Forward-fill missing days in date range"""
    print("\n" + "="*80)
    print("FORWARD-FILLING MISSING DAYS")
    print("="*80)
    
    # Determine date range
    if start_date:
        min_date = pd.to_datetime(start_date).date()
    else:
        min_date = df['date'].min()
    
    if end_date:
        max_date = pd.to_datetime(end_date).date()
    else:
        max_date = df['date'].max()
    
    print(f"   Target range: {min_date} to {max_date}")
    
    # Create complete date range
    all_dates = pd.date_range(start=min_date, end=max_date, freq='D')
    complete_df = pd.DataFrame({'date': all_dates.date})
    
    # Merge with existing data
    df_filled = complete_df.merge(df, on='date', how='left')
    
    # Forward-fill sentiment scores (carry last observation forward)
    df_filled['sentiment_mean'] = df_filled['sentiment_mean'].ffill()
    df_filled['sentiment_std'] = df_filled['sentiment_std'].fillna(0.0)
    df_filled['confidence_mean'] = df_filled['confidence_mean'].ffill()
    
    # Fill article count with 0 for missing days
    df_filled['article_count'] = df_filled['article_count'].fillna(0).astype(int)
    
    # Fill extreme values with mean for missing days
    df_filled['sentiment_min'] = df_filled['sentiment_min'].fillna(df_filled['sentiment_mean'])
    df_filled['sentiment_max'] = df_filled['sentiment_max'].fillna(df_filled['sentiment_mean'])
    
    # Fill sources
    df_filled['sources'] = df_filled['sources'].fillna('none')
    
    missing_days = (df_filled['article_count'] == 0).sum()
    print(f"   Filled {missing_days} missing days ({missing_days/len(df_filled)*100:.1f}%)")
    
    return df_filled


def save_silver_layer(df: pd.DataFrame, start_date: str, end_date: str) -> None:
    """Save cleaned data to Silver layer"""
    print("\n" + "="*80)
    print("SAVING TO SILVER LAYER")
    print("="*80)
    
    # Save main file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = SILVER_DIR / f"energy_news_sentiment_daily_{start_date}_{end_date}_{timestamp}.parquet"
    
    df.to_parquet(output_file, index=False)
    print(f"✅ Saved: {output_file}")
    print(f"   Rows: {len(df)}")
    print(f"   Columns: {list(df.columns)}")
    
    # Save metadata
    metadata = {
        'timestamp': timestamp,
        'start_date': str(start_date),
        'end_date': str(end_date),
        'total_days': len(df),
        'days_with_articles': int((df['article_count'] > 0).sum()),
        'total_articles': int(df['article_count'].sum()),
        'sentiment_statistics': {
            'mean': float(df['sentiment_mean'].mean()),
            'std': float(df['sentiment_mean'].std()),
            'min': float(df['sentiment_mean'].min()),
            'max': float(df['sentiment_mean'].max()),
        },
        'confidence_mean': float(df['confidence_mean'].mean()),
        'file_path': str(output_file)
    }
    
    metadata_file = SILVER_DIR / f"metadata_{timestamp}.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Saved metadata: {metadata_file}")


def generate_validation_report(df: pd.DataFrame) -> None:
    """Generate validation report"""
    print("\n" + "="*80)
    print("GENERATING VALIDATION REPORT")
    print("="*80)
    
    report = []
    
    # Date coverage
    report.append("="*60)
    report.append("SILVER LAYER VALIDATION REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("="*60)
    
    report.append("\n📅 DATE COVERAGE:")
    report.append(f"  Start: {df['date'].min()}")
    report.append(f"  End: {df['date'].max()}")
    report.append(f"  Total days: {len(df)}")
    report.append(f"  Days with articles: {(df['article_count'] > 0).sum()} ({(df['article_count'] > 0).mean()*100:.1f}%)")
    report.append(f"  Days with 0 articles: {(df['article_count'] == 0).sum()}")
    
    # Article counts
    report.append("\n📰 ARTICLE STATISTICS:")
    report.append(f"  Total articles: {df['article_count'].sum()}")
    report.append(f"  Avg per day: {df['article_count'].mean():.1f}")
    report.append(f"  Median per day: {df['article_count'].median():.0f}")
    report.append(f"  Min per day: {df['article_count'].min()}")
    report.append(f"  Max per day: {df['article_count'].max()}")
    
    # Sentiment statistics
    report.append("\n💭 SENTIMENT STATISTICS:")
    report.append(f"  Mean: {df['sentiment_mean'].mean():.3f}")
    report.append(f"  Std: {df['sentiment_mean'].std():.3f}")
    report.append(f"  Min: {df['sentiment_mean'].min():.3f}")
    report.append(f"  Max: {df['sentiment_mean'].max():.3f}")
    report.append(f"  25th percentile: {df['sentiment_mean'].quantile(0.25):.3f}")
    report.append(f"  75th percentile: {df['sentiment_mean'].quantile(0.75):.3f}")
    
    # Confidence
    report.append("\n🎯 CONFIDENCE STATISTICS:")
    report.append(f"  Mean: {df['confidence_mean'].mean():.3f}")
    report.append(f"  Min: {df['confidence_mean'].min():.3f}")
    report.append(f"  Max: {df['confidence_mean'].max():.3f}")
    
    # Distribution
    report.append("\n📊 SENTIMENT DISTRIBUTION:")
    very_pos = (df['sentiment_mean'] > 0.2).sum()
    pos = ((df['sentiment_mean'] > 0.05) & (df['sentiment_mean'] <= 0.2)).sum()
    neu = ((df['sentiment_mean'] >= -0.05) & (df['sentiment_mean'] <= 0.05)).sum()
    neg = ((df['sentiment_mean'] < -0.05) & (df['sentiment_mean'] >= -0.2)).sum()
    very_neg = (df['sentiment_mean'] < -0.2).sum()
    
    report.append(f"  Very Positive (>0.2): {very_pos} ({very_pos/len(df)*100:.1f}%)")
    report.append(f"  Positive (0.05-0.2): {pos} ({pos/len(df)*100:.1f}%)")
    report.append(f"  Neutral (-0.05 to 0.05): {neu} ({neu/len(df)*100:.1f}%)")
    report.append(f"  Negative (-0.2 to -0.05): {neg} ({neg/len(df)*100:.1f}%)")
    report.append(f"  Very Negative (<-0.2): {very_neg} ({very_neg/len(df)*100:.1f}%)")
    
    # Quality checks
    report.append("\n✅ QUALITY CHECKS:")
    
    # Check 1: No future dates
    today = datetime.now().date()
    future_dates = (df['date'] > today).sum()
    if future_dates == 0:
        report.append("  ✅ No future dates")
    else:
        report.append(f"  ❌ WARNING: {future_dates} future dates found!")
    
    # Check 2: Sentiment range
    if df['sentiment_mean'].min() >= -1.0 and df['sentiment_mean'].max() <= 1.0:
        report.append("  ✅ Sentiment scores in valid range [-1, +1]")
    else:
        report.append("  ❌ WARNING: Sentiment scores out of range!")
    
    # Check 3: Reasonable distribution
    if abs(df['sentiment_mean'].mean()) < 0.3:
        report.append("  ✅ Mean sentiment near neutral (reasonable)")
    else:
        report.append(f"  ⚠️  WARNING: Mean sentiment is biased ({df['sentiment_mean'].mean():.3f})")
    
    # Check 4: Coverage
    coverage = (df['article_count'] > 0).mean()
    if coverage > 0.9:
        report.append(f"  ✅ Excellent coverage ({coverage*100:.1f}%)")
    elif coverage > 0.7:
        report.append(f"  ⚠️  Good coverage ({coverage*100:.1f}%)")
    else:
        report.append(f"  ⚠️  WARNING: Low coverage ({coverage*100:.1f}%)")
    
    report.append("\n" + "="*60)
    
    # Print report
    report_text = "\n".join(report)
    print(report_text)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = VALIDATION_DIR / f"silver_validation_report_{timestamp}.txt"
    with open(report_file, 'w') as f:
        f.write(report_text)
    
    print(f"\n💾 Saved validation report: {report_file}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Process Bronze to Silver layer")
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("NEWS SENTIMENT: BRONZE → SILVER TRANSFORMATION")
    print("="*80)
    
    # Load Bronze data
    df = load_bronze_data(args.start_date, args.end_date)
    if df.empty:
        print("❌ No data to process!")
        return 1
    
    # Clean and deduplicate
    df = clean_and_deduplicate(df)
    
    # Apply enhanced sentiment
    df = apply_enhanced_sentiment(df)
    
    # Aggregate to daily
    daily_df = aggregate_to_daily(df)
    
    # Forward-fill missing days
    daily_df = forward_fill_missing_days(daily_df, args.start_date, args.end_date)
    
    # Save Silver layer
    start_date = str(daily_df['date'].min())
    end_date = str(daily_df['date'].max())
    save_silver_layer(daily_df, start_date, end_date)
    
    # Generate validation report
    generate_validation_report(daily_df)
    
    print("\n" + "="*80)
    print("✅ SILVER LAYER PROCESSING COMPLETE!")
    print("="*80)
    print("\n📊 Summary:")
    print(f"   Input articles: {len(df)}")
    print(f"   Output days: {len(daily_df)}")
    print(f"   Days with data: {(daily_df['article_count'] > 0).sum()}")
    print(f"   Avg sentiment: {daily_df['sentiment_mean'].mean():.3f}")
    print(f"   Avg confidence: {daily_df['confidence_mean'].mean():.3f}")
    
    print("\n🎯 Next steps:")
    print("   1. Review validation report in data/validation/")
    print("   2. Check Silver layer data in data/silver/news/")
    print("   3. Proceed to Gold layer feature engineering")
    print("   4. Run: python scripts/build_gold_layer.py (update with sentiment features)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
