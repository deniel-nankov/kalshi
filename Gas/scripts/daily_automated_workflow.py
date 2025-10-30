#!/usr/bin/env python3
"""
DAILY AUTOMATED WORKFLOW - Production Ready

This script runs the complete daily workflow:
1. Scrape latest AAA price
2. Fetch EIA weekly (if Monday)
3. Collect RBOB futures
4. Update training data
5. Make next-day prediction
6. Validate previous prediction
7. Save results to tracking file

Schedule this to run daily at 9:30 AM EST (after AAA updates at 9 AM)

Usage:
    python scripts/daily_automated_workflow.py

Cron example (9:30 AM daily):
    30 9 * * * /path/to/.venv/bin/python /path/to/scripts/daily_automated_workflow.py
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import requests
import re
import json
import yfinance as yf

# Add project root
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Paths
GOLD_PATH = project_root / 'data' / 'gold' / 'master_model_ready.parquet'
DAILY_TRACKING_PATH = project_root / 'outputs' / 'daily_tracking_automated.csv'
DAILY_PRICES_PATH = project_root / 'outputs' / 'daily_prices_automated.csv'
LOG_DIR = project_root / 'outputs' / 'automation_logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Log file
today = datetime.now().strftime('%Y%m%d')
LOG_FILE = LOG_DIR / f'workflow_{today}.log'

def log(message, level='INFO'):
    """Log to file and console"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] [{level}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def scrape_aaa_price():
    """Scrape latest AAA national average gas price"""
    log("Scraping AAA Daily Fuel Gauge...")
    
    url = "https://gasprices.aaa.com/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Try multiple regex patterns
        patterns = [
            r'\$(\d+\.\d{3})',  # $3.038
            r'National Average.*?\$(\d+\.\d{2,3})',
            r'Regular.*?\$(\d+\.\d{2,3})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response.text)
            if match:
                price = float(match.group(1))
                log(f"✅ AAA price: ${price:.3f}/gal", 'SUCCESS')
                return price
        
        log("Could not find price in AAA HTML", 'WARNING')
        return None
        
    except Exception as e:
        log(f"AAA scraping failed: {e}", 'ERROR')
        return None

def fetch_eia_price():
    """Fetch latest EIA weekly price (if available)"""
    log("Checking EIA weekly data...")
    
    # EIA only publishes on Mondays
    if datetime.now().weekday() != 0:  # 0 = Monday
        log("Not Monday, skipping EIA (weekly release)", 'INFO')
        return None
    
    api_key = os.environ.get('EIA_API_KEY')
    if not api_key:
        log("No EIA API key found", 'WARNING')
        return None
    
    try:
        url = "https://api.eia.gov/v2/petroleum/pri/gnd/data/"
        params = {
            'api_key': api_key,
            'frequency': 'weekly',
            'data[0]': 'value',
            'facets[product][]': 'EPMR',  # Regular gasoline
            'facets[area][]': 'NUS',  # National US
            'sort[0][column]': 'period',
            'sort[0][direction]': 'desc',
            'offset': 0,
            'length': 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if 'data' in data and len(data['data']) > 0:
            latest = data['data'][0]
            price = float(latest['value'])
            date = latest['period']
            log(f"✅ EIA price: ${price:.3f}/gal ({date})", 'SUCCESS')
            return price
        
        log("No EIA data available", 'WARNING')
        return None
        
    except Exception as e:
        log(f"EIA fetch failed: {e}", 'ERROR')
        return None

def fetch_rbob_price():
    """Fetch latest RBOB futures price"""
    log("Fetching RBOB futures...")
    
    try:
        rbob = yf.Ticker('RB=F')
        hist = rbob.history(period='5d')
        
        if len(hist) > 0:
            latest = hist['Close'].iloc[-1]
            log(f"✅ RBOB futures: ${latest:.3f}/gal", 'SUCCESS')
            return latest
        
        log("No RBOB data available", 'WARNING')
        return None
        
    except Exception as e:
        log(f"RBOB fetch failed: {e}", 'ERROR')
        return None

def save_daily_price(date, aaa_price, eia_price, rbob_price):
    """Save daily price collection to CSV"""
    
    record = {
        'date': date.strftime('%Y-%m-%d'),
        'aaa_price': aaa_price,
        'eia_price': eia_price,
        'rbob_price': rbob_price,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Load existing or create new
    if DAILY_PRICES_PATH.exists():
        df = pd.read_csv(DAILY_PRICES_PATH)
        df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    else:
        df = pd.DataFrame([record])
    
    df.to_csv(DAILY_PRICES_PATH, index=False)
    log(f"✅ Saved to {DAILY_PRICES_PATH}")

def make_prediction(current_date, latest_price):
    """Make prediction for tomorrow"""
    log(f"Making prediction for {(current_date + timedelta(days=1)).strftime('%Y-%m-%d')}...")
    
    # Load gold layer
    gold_df = pd.read_parquet(GOLD_PATH)
    gold_df['date'] = pd.to_datetime(gold_df['date'])
    
    # Load all daily prices
    if DAILY_PRICES_PATH.exists():
        daily_df = pd.read_csv(DAILY_PRICES_PATH)
        daily_df['date'] = pd.to_datetime(daily_df['date'])
        
        # Add new daily prices to gold layer
        latest_gold_date = gold_df['date'].max()
        new_daily = daily_df[daily_df['date'] > latest_gold_date]
        
        for _, row in new_daily.iterrows():
            new_row = gold_df.iloc[-1:].copy()
            new_row['date'] = row['date']
            
            # Use AAA price if available, else EIA
            if pd.notna(row['aaa_price']):
                new_row['retail_price'] = row['aaa_price']
            elif pd.notna(row['eia_price']):
                new_row['retail_price'] = row['eia_price']
            else:
                continue  # Skip if no price
            
            gold_df = pd.concat([gold_df, new_row], ignore_index=True)
    
    # Prepare features
    target_col = 'retail_price'
    exclude_cols = ['date', 'Date', target_col]
    feature_cols = [col for col in gold_df.columns 
                    if col not in exclude_cols and gold_df[col].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    # Train model
    X = gold_df[feature_cols].values
    y = gold_df[target_col].values
    
    imputer = SimpleImputer(strategy='mean')
    scaler = StandardScaler()
    model = Ridge(alpha=1.0)
    
    X_imputed = imputer.fit_transform(X)
    X_scaled = scaler.fit_transform(X_imputed)
    model.fit(X_scaled, y)
    
    r2 = model.score(X_scaled, y)
    
    # Predict tomorrow
    last_features = gold_df[feature_cols].iloc[-1:].values
    X_pred = imputer.transform(last_features)
    X_pred_scaled = scaler.transform(X_pred)
    prediction = model.predict(X_pred_scaled)[0]
    
    log(f"   Training: {len(gold_df)} samples, R²={r2:.6f}")
    log(f"   Prediction: ${prediction:.3f}/gal")
    
    return prediction, r2, len(gold_df)

def validate_yesterday(current_date, actual_price):
    """Validate yesterday's prediction"""
    log("Validating yesterday's prediction...")
    
    if not DAILY_TRACKING_PATH.exists():
        log("No tracking file yet, skipping validation")
        return
    
    df = pd.read_csv(DAILY_TRACKING_PATH)
    df['target_date'] = pd.to_datetime(df['target_date'])
    
    yesterday = current_date - timedelta(days=1)
    yesterday_pred = df[df['target_date'] == yesterday]
    
    if len(yesterday_pred) > 0:
        pred = yesterday_pred.iloc[-1]
        predicted = pred['prediction']
        error = predicted - actual_price
        abs_error = abs(error)
        pct_error = (abs_error / actual_price) * 100
        
        log(f"   Yesterday ({yesterday.strftime('%Y-%m-%d')}):")
        log(f"      Predicted: ${predicted:.3f}")
        log(f"      Actual: ${actual_price:.3f}")
        log(f"      Error: ${error:+.3f} ({pct_error:.2f}%)")
        
        # Update tracking file with actual
        df.loc[df['target_date'] == yesterday, 'actual'] = actual_price
        df.loc[df['target_date'] == yesterday, 'error'] = error
        df.loc[df['target_date'] == yesterday, 'abs_error'] = abs_error
        df.loc[df['target_date'] == yesterday, 'pct_error'] = pct_error
        df.to_csv(DAILY_TRACKING_PATH, index=False)
        
    else:
        log(f"   No prediction found for {yesterday.strftime('%Y-%m-%d')}")

def save_prediction(target_date, prediction, r2, samples):
    """Save prediction to tracking file"""
    
    record = {
        'prediction_date': datetime.now().strftime('%Y-%m-%d'),
        'target_date': target_date.strftime('%Y-%m-%d'),
        'prediction': prediction,
        'training_r2': r2,
        'training_samples': samples,
        'actual': None,
        'error': None,
        'abs_error': None,
        'pct_error': None
    }
    
    if DAILY_TRACKING_PATH.exists():
        df = pd.read_csv(DAILY_TRACKING_PATH)
        df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    else:
        df = pd.DataFrame([record])
    
    df.to_csv(DAILY_TRACKING_PATH, index=False)
    log(f"✅ Saved prediction to {DAILY_TRACKING_PATH}")

def main():
    """Main workflow"""
    
    log("=" * 80)
    log("🤖 DAILY AUTOMATED GAS PRICE FORECASTING")
    log("=" * 80)
    
    current_date = datetime.now().date()
    tomorrow = current_date + timedelta(days=1)
    
    log(f"Current date: {current_date.strftime('%Y-%m-%d')}")
    log(f"Target date: {tomorrow.strftime('%Y-%m-%d')}")
    
    # STEP 1: Collect today's data
    log("\n" + "-" * 80)
    log("STEP 1: COLLECT TODAY'S DATA")
    log("-" * 80)
    
    aaa_price = scrape_aaa_price()
    eia_price = fetch_eia_price()
    rbob_price = fetch_rbob_price()
    
    if aaa_price is None:
        log("❌ CRITICAL: No AAA price available", 'ERROR')
        sys.exit(1)
    
    save_daily_price(current_date, aaa_price, eia_price, rbob_price)
    
    # STEP 2: Validate yesterday's prediction
    log("\n" + "-" * 80)
    log("STEP 2: VALIDATE YESTERDAY")
    log("-" * 80)
    
    validate_yesterday(current_date, aaa_price)
    
    # STEP 3: Make tomorrow's prediction
    log("\n" + "-" * 80)
    log("STEP 3: PREDICT TOMORROW")
    log("-" * 80)
    
    prediction, r2, samples = make_prediction(current_date, aaa_price)
    save_prediction(tomorrow, prediction, r2, samples)
    
    # SUMMARY
    log("\n" + "=" * 80)
    log("✅ WORKFLOW COMPLETE")
    log("=" * 80)
    
    log(f"""
Summary:
    • Today ({current_date.strftime('%Y-%m-%d')}): ${aaa_price:.3f}/gal (AAA)
    • Tomorrow ({tomorrow.strftime('%Y-%m-%d')}): ${prediction:.3f}/gal (predicted)
    • Model: {samples} samples, R²={r2:.6f}
    • Outputs: {DAILY_PRICES_PATH}, {DAILY_TRACKING_PATH}
    
Next run: Tomorrow at 9:30 AM
    """)
    
    log("=" * 80)

if __name__ == '__main__':
    import os
    try:
        main()
    except Exception as e:
        log(f"FATAL ERROR: {e}", 'ERROR')
        import traceback
        log(traceback.format_exc(), 'ERROR')
        sys.exit(1)
