"""
Manual Validation Script for News Sentiment Data

This script helps verify the accuracy and quality of news sentiment data by:
1. Loading Bronze layer news data
2. Sampling articles for manual review
3. Checking against known major events
4. Generating validation reports

Usage:
    python scripts/validate_news_sentiment.py --sample-size 50
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import sys


# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze" / "news"
VALIDATION_DIR = PROJECT_ROOT / "data" / "validation"
VALIDATION_DIR.mkdir(parents=True, exist_ok=True)


# Known major events for validation
KNOWN_EVENTS = [
    {
        'date': '2020-04-20',
        'event': 'WTI Crude Oil Price Goes Negative',
        'expected_sentiment': 'very_negative',
        'keywords': ['negative', 'crash', 'collapse', 'historic']
    },
    {
        'date': '2020-03-09',
        'event': 'Oil Price War (Russia-Saudi Arabia)',
        'expected_sentiment': 'very_negative',
        'keywords': ['price war', 'saudi', 'russia', 'crash', 'plunge']
    },
    {
        'date': '2022-03-08',
        'event': 'Russia Invades Ukraine - Oil Surge',
        'expected_sentiment': 'negative',
        'keywords': ['russia', 'ukraine', 'war', 'invasion', 'surge', 'spike']
    },
    {
        'date': '2022-03-23',
        'event': 'Biden Announces Strategic Reserve Release',
        'expected_sentiment': 'mixed',
        'keywords': ['biden', 'strategic', 'reserve', 'release']
    },
    {
        'date': '2023-10-07',
        'event': 'Israel-Hamas War Begins',
        'expected_sentiment': 'negative',
        'keywords': ['israel', 'hamas', 'middle east', 'conflict', 'surge']
    },
    {
        'date': '2024-03-22',
        'event': 'Russia Terror Attack Disrupts Oil Market',
        'expected_sentiment': 'negative',
        'keywords': ['russia', 'terror', 'attack', 'moscow']
    }
]


def load_latest_bronze_data():
    """Load most recent Bronze layer news data"""
    if not BRONZE_DIR.exists():
        print(f"❌ Bronze directory not found: {BRONZE_DIR}")
        print("   Please run fetch_news_sentiment.py first.")
        return None
    
    # Find most recent file
    parquet_files = list(BRONZE_DIR.glob("energy_news_raw_*.parquet"))
    if not parquet_files:
        print(f"❌ No Bronze layer news files found in {BRONZE_DIR}")
        return None
    
    latest_file = max(parquet_files, key=lambda p: p.stat().st_mtime)
    print(f"📂 Loading: {latest_file.name}")
    
    df = pd.read_parquet(latest_file)
    print(f"✅ Loaded {len(df)} articles")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    
    return df


def check_known_events(df):
    """Check if known major events appear in data with correct sentiment"""
    print("\n" + "="*80)
    print("KNOWN EVENT VALIDATION")
    print("="*80)
    
    results = []
    
    for event in KNOWN_EVENTS:
        event_date = pd.to_datetime(event['date']).date()
        
        # Get articles within ±2 days of event
        date_mask = (df['date'] >= event_date - timedelta(days=2)) & \
                    (df['date'] <= event_date + timedelta(days=2))
        event_articles = df[date_mask].copy()
        
        if len(event_articles) == 0:
            print(f"\n⚠️  {event['event']} ({event['date']})")
            print(f"    NO ARTICLES FOUND within ±2 days")
            results.append({
                'event': event['event'],
                'date': event['date'],
                'found': False,
                'article_count': 0,
                'avg_sentiment': None
            })
            continue
        
        # Check for keyword matches
        keyword_matches = []
        for keyword in event['keywords']:
            matches = event_articles[
                event_articles['headline'].str.lower().str.contains(keyword, na=False)
            ]
            keyword_matches.extend(matches.index)
        
        keyword_matches = event_articles.loc[list(set(keyword_matches))]
        
        # Calculate sentiment
        avg_sentiment = event_articles['sentiment_score'].mean()
        keyword_sentiment = keyword_matches['sentiment_score'].mean() if len(keyword_matches) > 0 else None
        
        # Display results
        print(f"\n{'='*80}")
        print(f"📅 {event['event']} ({event['date']})")
        print(f"   Expected: {event['expected_sentiment']}")
        print(f"   Found: {len(event_articles)} articles (±2 days)")
        print(f"   Keyword matches: {len(keyword_matches)}")
        print(f"   Average sentiment: {avg_sentiment:.3f}")
        if keyword_sentiment is not None:
            print(f"   Keyword sentiment: {keyword_sentiment:.3f}")
        
        # Show sample headlines
        print(f"\n   Sample headlines:")
        for idx, row in event_articles.head(5).iterrows():
            sentiment_label = "📈" if row['sentiment_score'] > 0.2 else "📉" if row['sentiment_score'] < -0.2 else "➡️"
            print(f"   {sentiment_label} [{row['date']}] ({row['sentiment_score']:+.2f}) {row['headline'][:80]}")
        
        results.append({
            'event': event['event'],
            'date': event['date'],
            'found': True,
            'article_count': len(event_articles),
            'keyword_matches': len(keyword_matches),
            'avg_sentiment': avg_sentiment,
            'keyword_sentiment': keyword_sentiment
        })
    
    # Save results
    results_df = pd.DataFrame(results)
    results_file = VALIDATION_DIR / f"known_events_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    results_df.to_csv(results_file, index=False)
    print(f"\n💾 Saved validation results to: {results_file}")
    
    return results_df


def generate_manual_review_sample(df, sample_size=50):
    """Generate stratified sample for manual review"""
    print("\n" + "="*80)
    print(f"GENERATING MANUAL REVIEW SAMPLE ({sample_size} articles)")
    print("="*80)
    
    # Stratify by sentiment
    very_positive = df[df['sentiment_score'] > 0.5]
    positive = df[(df['sentiment_score'] > 0.2) & (df['sentiment_score'] <= 0.5)]
    neutral = df[(df['sentiment_score'] >= -0.2) & (df['sentiment_score'] <= 0.2)]
    negative = df[(df['sentiment_score'] < -0.2) & (df['sentiment_score'] >= -0.5)]
    very_negative = df[df['sentiment_score'] < -0.5]
    
    # Sample proportionally
    n_very_pos = min(len(very_positive), max(5, int(sample_size * 0.1)))
    n_pos = min(len(positive), max(10, int(sample_size * 0.2)))
    n_neu = min(len(neutral), max(20, int(sample_size * 0.4)))
    n_neg = min(len(negative), max(10, int(sample_size * 0.2)))
    n_very_neg = min(len(very_negative), max(5, int(sample_size * 0.1)))
    
    sample_parts = []
    if len(very_positive) > 0:
        sample_parts.append(very_positive.sample(n=n_very_pos, random_state=42))
    if len(positive) > 0:
        sample_parts.append(positive.sample(n=n_pos, random_state=42))
    if len(neutral) > 0:
        sample_parts.append(neutral.sample(n=n_neu, random_state=42))
    if len(negative) > 0:
        sample_parts.append(negative.sample(n=n_neg, random_state=42))
    if len(very_negative) > 0:
        sample_parts.append(very_negative.sample(n=n_very_neg, random_state=42))
    
    sample = pd.concat(sample_parts)
    
    # Add manual validation columns
    sample = sample.copy()
    sample['manual_sentiment'] = ''
    sample['correct'] = ''
    sample['notes'] = ''
    
    # Save
    sample_file = VALIDATION_DIR / f"manual_review_sample_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    sample.to_csv(sample_file, index=False)
    
    print(f"\n✅ Generated {len(sample)} articles for manual review")
    print(f"   Very Positive (>0.5): {n_very_pos}")
    print(f"   Positive (0.2-0.5): {n_pos}")
    print(f"   Neutral (-0.2 to 0.2): {n_neu}")
    print(f"   Negative (-0.5 to -0.2): {n_neg}")
    print(f"   Very Negative (<-0.5): {n_very_neg}")
    print(f"\n💾 Saved to: {sample_file}")
    print("\n📝 Instructions:")
    print("   1. Open the CSV file")
    print("   2. Read each headline")
    print("   3. Fill in 'manual_sentiment': positive/neutral/negative")
    print("   4. Fill in 'correct': yes/no")
    print("   5. Add any notes")
    print("   6. Save and analyze with calculate_accuracy()")
    
    return sample


def analyze_sentiment_distribution(df):
    """Analyze sentiment score distribution"""
    print("\n" + "="*80)
    print("SENTIMENT DISTRIBUTION ANALYSIS")
    print("="*80)
    
    sentiment_scores = df['sentiment_score']
    
    print(f"\n📊 Statistics:")
    print(f"   Count: {len(sentiment_scores)}")
    print(f"   Mean: {sentiment_scores.mean():.3f}")
    print(f"   Median: {sentiment_scores.median():.3f}")
    print(f"   Std Dev: {sentiment_scores.std():.3f}")
    print(f"   Min: {sentiment_scores.min():.3f}")
    print(f"   Max: {sentiment_scores.max():.3f}")
    
    print(f"\n📈 Distribution:")
    print(f"   Very Positive (>0.5): {(sentiment_scores > 0.5).sum()} ({(sentiment_scores > 0.5).mean()*100:.1f}%)")
    print(f"   Positive (0.2-0.5): {((sentiment_scores > 0.2) & (sentiment_scores <= 0.5)).sum()} ({((sentiment_scores > 0.2) & (sentiment_scores <= 0.5)).mean()*100:.1f}%)")
    print(f"   Neutral (-0.2 to 0.2): {((sentiment_scores >= -0.2) & (sentiment_scores <= 0.2)).sum()} ({((sentiment_scores >= -0.2) & (sentiment_scores <= 0.2)).mean()*100:.1f}%)")
    print(f"   Negative (-0.5 to -0.2): {((sentiment_scores < -0.2) & (sentiment_scores >= -0.5)).sum()} ({((sentiment_scores < -0.2) & (sentiment_scores >= -0.5)).mean()*100:.1f}%)")
    print(f"   Very Negative (<-0.5): {(sentiment_scores < -0.5).sum()} ({(sentiment_scores < -0.5).mean()*100:.1f}%)")
    
    # Check for anomalies
    print(f"\n🔍 Anomaly Checks:")
    if sentiment_scores.mean() > 0.3 or sentiment_scores.mean() < -0.3:
        print(f"   ⚠️  WARNING: Mean sentiment is strongly biased ({sentiment_scores.mean():.3f})")
    else:
        print(f"   ✅ Mean sentiment is reasonable (near neutral)")
    
    if sentiment_scores.std() < 0.1:
        print(f"   ⚠️  WARNING: Very low variance ({sentiment_scores.std():.3f}) - lack of diversity")
    elif sentiment_scores.std() > 0.6:
        print(f"   ⚠️  WARNING: Very high variance ({sentiment_scores.std():.3f}) - check for errors")
    else:
        print(f"   ✅ Variance is reasonable")
    
    extreme_count = ((sentiment_scores > 0.8) | (sentiment_scores < -0.8)).sum()
    extreme_pct = extreme_count / len(sentiment_scores) * 100
    if extreme_pct > 10:
        print(f"   ⚠️  WARNING: High percentage of extreme scores ({extreme_pct:.1f}%)")
    else:
        print(f"   ✅ Extreme scores are rare ({extreme_pct:.1f}%)")


def check_data_quality(df):
    """Check data quality metrics"""
    print("\n" + "="*80)
    print("DATA QUALITY CHECKS")
    print("="*80)
    
    print(f"\n🔍 Completeness:")
    for col in df.columns:
        null_count = df[col].isna().sum()
        null_pct = null_count / len(df) * 100
        if null_pct > 0:
            status = "⚠️" if null_pct > 10 else "✓"
            print(f"   {status} {col}: {null_count} nulls ({null_pct:.1f}%)")
    
    print(f"\n🔍 Duplicates:")
    dup_count = df.duplicated(subset=['date', 'headline']).sum()
    dup_pct = dup_count / len(df) * 100
    print(f"   Duplicate articles: {dup_count} ({dup_pct:.1f}%)")
    if dup_pct > 5:
        print(f"   ⚠️  WARNING: High duplicate rate")
    
    print(f"\n🔍 Date Coverage:")
    date_range = (df['date'].max() - df['date'].min()).days
    unique_dates = df['date'].nunique()
    coverage_pct = unique_dates / date_range * 100 if date_range > 0 else 0
    print(f"   Date range: {df['date'].min()} to {df['date'].max()} ({date_range} days)")
    print(f"   Unique dates: {unique_dates} ({coverage_pct:.1f}% coverage)")
    
    # Articles per day
    articles_per_day = df.groupby('date').size()
    print(f"   Articles per day: {articles_per_day.mean():.1f} ± {articles_per_day.std():.1f}")
    print(f"   Min: {articles_per_day.min()}, Max: {articles_per_day.max()}")
    
    days_with_zero = date_range - unique_dates
    if days_with_zero > date_range * 0.1:
        print(f"   ⚠️  WARNING: {days_with_zero} days with no articles ({days_with_zero/date_range*100:.1f}%)")
    
    print(f"\n🔍 API Sources:")
    if 'api_source' in df.columns:
        source_counts = df['api_source'].value_counts()
        for source, count in source_counts.items():
            pct = count / len(df) * 100
            print(f"   {source}: {count} ({pct:.1f}%)")


def calculate_manual_review_accuracy(validation_file):
    """Calculate accuracy from completed manual review"""
    if not Path(validation_file).exists():
        print(f"❌ Validation file not found: {validation_file}")
        return None
    
    df = pd.read_csv(validation_file)
    
    # Count completed reviews
    completed = df[df['manual_sentiment'].notna() & (df['manual_sentiment'] != '')]
    
    if len(completed) == 0:
        print("❌ No manual reviews completed yet")
        return None
    
    print("\n" + "="*80)
    print(f"MANUAL REVIEW ACCURACY")
    print("="*80)
    print(f"\n📊 Reviews completed: {len(completed)} / {len(df)}")
    
    # Calculate accuracy
    correct = completed[completed['correct'].str.lower().str.strip() == 'yes']
    accuracy = len(correct) / len(completed) * 100
    
    print(f"\n✅ Accuracy: {accuracy:.1f}%")
    print(f"   Correct: {len(correct)}")
    print(f"   Incorrect: {len(completed) - len(correct)}")
    
    # Breakdown by sentiment category
    print(f"\n📈 Accuracy by Category:")
    for category in ['Very Positive', 'Positive', 'Neutral', 'Negative', 'Very Negative']:
        # Define sentiment ranges
        if category == 'Very Positive':
            mask = completed['sentiment_score'] > 0.5
        elif category == 'Positive':
            mask = (completed['sentiment_score'] > 0.2) & (completed['sentiment_score'] <= 0.5)
        elif category == 'Neutral':
            mask = (completed['sentiment_score'] >= -0.2) & (completed['sentiment_score'] <= 0.2)
        elif category == 'Negative':
            mask = (completed['sentiment_score'] < -0.2) & (completed['sentiment_score'] >= -0.5)
        else:  # Very Negative
            mask = completed['sentiment_score'] < -0.5
        
        category_reviews = completed[mask]
        if len(category_reviews) > 0:
            category_correct = category_reviews[category_reviews['correct'].str.lower().str.strip() == 'yes']
            category_accuracy = len(category_correct) / len(category_reviews) * 100
            print(f"   {category}: {category_accuracy:.1f}% ({len(category_correct)}/{len(category_reviews)})")
    
    return accuracy


def main():
    parser = argparse.ArgumentParser(description="Validate news sentiment data")
    parser.add_argument('--sample-size', type=int, default=50,
                        help='Number of articles to sample for manual review')
    parser.add_argument('--check-accuracy', type=str,
                        help='Path to completed manual review CSV to calculate accuracy')
    
    args = parser.parse_args()
    
    if args.check_accuracy:
        calculate_manual_review_accuracy(args.check_accuracy)
        return 0
    
    # Load data
    df = load_latest_bronze_data()
    if df is None:
        return 1
    
    # Run validation checks
    check_data_quality(df)
    analyze_sentiment_distribution(df)
    check_known_events(df)
    generate_manual_review_sample(df, sample_size=args.sample_size)
    
    print("\n" + "="*80)
    print("✅ VALIDATION COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Review the generated validation files in data/validation/")
    print("2. Complete manual review of sample articles")
    print("3. Run: python scripts/validate_news_sentiment.py --check-accuracy <file>")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
