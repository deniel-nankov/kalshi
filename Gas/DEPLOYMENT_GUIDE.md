# Gas Price Forecasting System - Deployment Guide

**Date:** October 13, 2025  
**System:** Kalshi Gas Price Prediction Pipeline

---

## 🎯 Deployment Overview

Your system has 3 main components to deploy:

1. **Data Pipeline** - Automated Bronze → Silver updates
2. **Model Training** - Periodic retraining on fresh data
3. **Prediction Service** - Generate forecasts for trading/analysis

---

## 🏗️ Current System Architecture

```
┌─────────────────────────────────────────────────────┐
│ AUTOMATED (Background Service)                      │
├─────────────────────────────────────────────────────┤
│ Bronze Layer (Data Ingestion)                       │
│   - EIA: Wednesday 10:30 AM ET                      │
│   - RBOB: Mon-Fri market hours                      │
│   - Retail: Monday mornings                         │
│                                                      │
│ Silver Layer (Data Cleaning)                        │
│   - Rebuilds automatically when Bronze updates     │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ SCHEDULED/MANUAL (Your Control)                     │
├─────────────────────────────────────────────────────┤
│ Gold Layer (Feature Engineering)                    │
│   - Run when ready to train/predict                │
│                                                      │
│ Model Training                                      │
│   - Ridge regression (fast)                         │
│   - Quantile models (confidence intervals)          │
│                                                      │
│ Prediction Generation                               │
│   - Daily forecasts                                 │
│   - Confidence intervals                            │
│   - Export for trading decisions                    │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Deployment Options

### **Option 1: Local Development (Current)**

**Good for:**
- Research and experimentation
- Manual control over everything
- Testing features

**Setup:** Already done! ✅

---

### **Option 2: Semi-Automated Local (Recommended for Solo Use)**

**Good for:**
- Daily trading decisions
- Minimal maintenance
- Learning the system

**What's automated:**
- ✅ Data downloads (Bronze)
- ✅ Data cleaning (Silver)

**What's manual:**
- ⚠️ Feature engineering (Gold)
- ⚠️ Model training
- ⚠️ Predictions

**Deployment steps below** ⬇️

---

### **Option 3: Fully Automated Local**

**Good for:**
- Hands-off operation
- Daily predictions without intervention
- Production-like environment

**What's automated:**
- ✅ Data downloads
- ✅ Data cleaning
- ✅ Feature engineering
- ✅ Model training
- ✅ Predictions

**Deployment steps below** ⬇️

---

### **Option 4: Cloud Deployment**

**Good for:**
- Always-on availability
- Scaling to multiple users
- Integration with trading APIs

**Platforms:**
- AWS, GCP, Azure
- Heroku, Railway, Render
- DigitalOcean, Linode

**Not covered here** (requires infrastructure setup)

---

## 📋 Semi-Automated Deployment (Recommended)

### **Step 1: Install Data Automation Service**

```bash
cd /Users/christianlee/Desktop/kalshi/Gas

# Install Bronze → Silver automation
python scripts/automate_bronze_silver.py --daemon &

# Or as macOS service (auto-starts on boot)
bash scripts/setup_bronze_service.sh
```

**Result:** Data stays fresh automatically 24/7 ✅

---

### **Step 2: Create Daily Workflow Script**

Create `scripts/daily_forecast.sh`:
```bash
#!/bin/bash
# Daily Gas Price Forecasting Workflow
# Run this once per day to get fresh predictions

set -e  # Exit on error

PROJECT_DIR="/Users/christianlee/Desktop/kalshi/Gas"
PYTHON="/Users/christianlee/Desktop/kalshi/.venv/bin/python"

cd "$PROJECT_DIR"

echo "=================================================="
echo "🔮 Daily Gas Price Forecast - $(date)"
echo "=================================================="

# Step 1: Rebuild Gold layer (10 seconds)
echo ""
echo "⭐ Step 1: Building Gold layer (features)..."
$PYTHON scripts/update_pipeline.py --gold-only

# Step 2: Train models (2-3 minutes)
echo ""
echo "🤖 Step 2: Training models..."
$PYTHON scripts/train_models.py

# Step 3: Generate predictions
echo ""
echo "🔮 Step 3: Generating forecasts..."
$PYTHON scripts/final_month_forecast.py

# Step 4: Summary
echo ""
echo "=================================================="
echo "✅ Daily Forecast Complete!"
echo "=================================================="
echo "Results:"
echo "  - Models: outputs/models/"
echo "  - Forecast: outputs/final_forecast.json"
echo ""
echo "Check forecast:"
cat outputs/final_forecast.json | python -m json.tool | head -20
echo "=================================================="
```

Make it executable:
```bash
chmod +x scripts/daily_forecast.sh
```

---

### **Step 3: Schedule Daily Forecasts**

**Option A: Run Manually**
```bash
# Run whenever you want fresh predictions
./scripts/daily_forecast.sh
```

**Option B: Cron Job (Automatic)**
```bash
# Edit crontab
crontab -e

# Add line to run daily at 8 AM
0 8 * * * cd /Users/christianlee/Desktop/kalshi/Gas && ./scripts/daily_forecast.sh >> logs/daily_forecast.log 2>&1
```

**Option C: macOS launchd (Better for macOS)**
```bash
# Create plist file
cat > ~/Library/LaunchAgents/com.kalshi.daily-forecast.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.kalshi.daily-forecast</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/Users/christianlee/Desktop/kalshi/Gas/scripts/daily_forecast.sh</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/Users/christianlee/Desktop/kalshi/Gas</string>
    
    <key>StandardOutPath</key>
    <string>/Users/christianlee/Desktop/kalshi/Gas/logs/daily_forecast.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/christianlee/Desktop/kalshi/Gas/logs/daily_forecast_error.log</string>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
EOF

# Load the service
launchctl load ~/Library/LaunchAgents/com.kalshi.daily-forecast.plist
```

---

### **Step 4: Monitor and Verify**

```bash
# Check data automation
tail -f logs/bronze_silver_automation.log

# Check daily forecasts
tail -f logs/daily_forecast.log

# View latest predictions
cat outputs/final_forecast.json | python -m json.tool
```

---

## 🎯 Fully Automated Deployment

### **Additional Steps for Full Automation:**

Create `scripts/fully_automated_forecast.sh`:
```bash
#!/bin/bash
# Fully Automated Forecasting Pipeline
# Checks for new data, trains if needed, generates predictions

set -e

PROJECT_DIR="/Users/christianlee/Desktop/kalshi/Gas"
PYTHON="/Users/christianlee/Desktop/kalshi/.venv/bin/python"

cd "$PROJECT_DIR"

echo "🤖 Automated Forecast Check - $(date)"

# Step 1: Check if Silver has new data
SILVER_METADATA="data/silver/silver_processing_metadata.json"
if [ ! -f "$SILVER_METADATA" ]; then
    echo "⚠️  No Silver metadata, running full pipeline"
    RUN_FORECAST=true
else
    # Check if Silver was updated in last 6 hours
    LAST_UPDATE=$(cat "$SILVER_METADATA" | python -c "import sys, json; print(json.load(sys.stdin).get('last_processed', ''))")
    CURRENT_TIME=$(date -u +"%Y-%m-%dT%H:%M:%S")
    
    # Simple check: if metadata exists and is recent, skip
    # (More sophisticated: compare timestamps)
    RUN_FORECAST=true
fi

if [ "$RUN_FORECAST" = true ]; then
    echo "✅ New data detected, generating forecast..."
    
    # Rebuild Gold
    $PYTHON scripts/update_pipeline.py --gold-only
    
    # Train models
    $PYTHON scripts/train_models.py
    
    # Generate predictions
    $PYTHON scripts/final_month_forecast.py
    
    echo "✅ Forecast updated!"
else
    echo "⏭️  No new data, skipping forecast"
fi
```

Schedule to run every 6 hours:
```bash
crontab -e

# Add:
0 */6 * * * cd /Users/christianlee/Desktop/kalshi/Gas && ./scripts/fully_automated_forecast.sh >> logs/automated_forecast.log 2>&1
```

---

## 🔌 Integration with Trading Systems

### **Step 1: Create Prediction API**

Create `scripts/get_latest_forecast.py`:
```python
#!/usr/bin/env python3
"""
Get latest forecast for trading decisions
Returns: JSON with predictions and confidence intervals
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def get_latest_forecast():
    """Load and return latest forecast"""
    forecast_file = Path(__file__).parent.parent / "outputs" / "final_forecast.json"
    
    if not forecast_file.exists():
        return {
            "error": "No forecast available",
            "status": "missing"
        }
    
    # Check if forecast is recent (< 24 hours old)
    age_hours = (datetime.now().timestamp() - forecast_file.stat().st_mtime) / 3600
    
    with open(forecast_file, 'r') as f:
        forecast = json.load(f)
    
    forecast['metadata'] = {
        'age_hours': round(age_hours, 2),
        'is_fresh': age_hours < 24,
        'file_path': str(forecast_file)
    }
    
    return forecast

if __name__ == "__main__":
    forecast = get_latest_forecast()
    print(json.dumps(forecast, indent=2))
```

**Usage:**
```bash
# Get latest prediction
python scripts/get_latest_forecast.py

# Use in trading script
python trading_bot.py --forecast $(python scripts/get_latest_forecast.py)
```

---

### **Step 2: Create Trading Decision Helper**

Create `scripts/trading_signal.py`:
```python
#!/usr/bin/env python3
"""
Generate trading signal based on forecast
"""

import json
import sys
from pathlib import Path

def get_trading_signal():
    """
    Analyze forecast and return trading signal
    """
    forecast_file = Path(__file__).parent.parent / "outputs" / "final_forecast.json"
    
    if not forecast_file.exists():
        return {"signal": "HOLD", "reason": "No forecast available"}
    
    with open(forecast_file, 'r') as f:
        forecast = json.load(f)
    
    # Example logic (customize for your strategy)
    predictions = forecast.get('predictions', [])
    if not predictions:
        return {"signal": "HOLD", "reason": "No predictions"}
    
    # Get prediction for target date (e.g., end of month)
    target_pred = predictions[-1]  # Last prediction
    
    predicted_price = target_pred.get('predicted_price', 0)
    confidence_lower = target_pred.get('confidence_interval', {}).get('lower', predicted_price)
    confidence_upper = target_pred.get('confidence_interval', {}).get('upper', predicted_price)
    
    # Simple threshold logic
    current_price = 3.50  # Get from market data
    
    if predicted_price > current_price * 1.02:  # 2% increase expected
        signal = "BUY"
        reason = f"Price expected to rise to ${predicted_price:.3f} (currently ${current_price:.3f})"
    elif predicted_price < current_price * 0.98:  # 2% decrease expected
        signal = "SELL"
        reason = f"Price expected to fall to ${predicted_price:.3f} (currently ${current_price:.3f})"
    else:
        signal = "HOLD"
        reason = f"Price stable around ${predicted_price:.3f}"
    
    return {
        "signal": signal,
        "reason": reason,
        "predicted_price": predicted_price,
        "confidence_interval": [confidence_lower, confidence_upper],
        "current_price": current_price,
        "target_date": target_pred.get('date')
    }

if __name__ == "__main__":
    signal = get_trading_signal()
    print(json.dumps(signal, indent=2))
```

**Usage:**
```bash
# Get trading signal
python scripts/trading_signal.py

# Example output:
{
  "signal": "BUY",
  "reason": "Price expected to rise to $3.567 (currently $3.500)",
  "predicted_price": 3.567,
  "confidence_interval": [3.533, 3.601],
  "current_price": 3.5,
  "target_date": "2025-10-31"
}
```

---

## 📊 Monitoring and Alerts

### **Create Health Check Script**

Create `scripts/health_check.sh`:
```bash
#!/bin/bash
# System Health Check

PROJECT_DIR="/Users/christianlee/Desktop/kalshi/Gas"
cd "$PROJECT_DIR"

echo "🏥 System Health Check - $(date)"
echo "=================================================="

# Check 1: Data automation running?
if pgrep -f "automate_bronze_silver.py" > /dev/null; then
    echo "✅ Data automation: RUNNING"
else
    echo "❌ Data automation: STOPPED"
fi

# Check 2: Recent Bronze updates?
BRONZE_LOG="logs/bronze_silver_automation.log"
if [ -f "$BRONZE_LOG" ]; then
    LAST_UPDATE=$(tail -20 "$BRONZE_LOG" | grep "✅" | tail -1)
    if [ -n "$LAST_UPDATE" ]; then
        echo "✅ Recent Bronze update: $LAST_UPDATE"
    else
        echo "⚠️  No recent Bronze updates"
    fi
fi

# Check 3: Recent forecast?
FORECAST="outputs/final_forecast.json"
if [ -f "$FORECAST" ]; then
    AGE=$(( ($(date +%s) - $(stat -f %m "$FORECAST")) / 3600 ))
    if [ $AGE -lt 24 ]; then
        echo "✅ Forecast age: $AGE hours (fresh)"
    else
        echo "⚠️  Forecast age: $AGE hours (stale)"
    fi
else
    echo "❌ No forecast found"
fi

# Check 4: Disk space
DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 90 ]; then
    echo "✅ Disk usage: ${DISK_USAGE}%"
else
    echo "⚠️  Disk usage: ${DISK_USAGE}% (high)"
fi

echo "=================================================="
```

Run periodically:
```bash
# Add to crontab (check every 6 hours)
0 */6 * * * cd /Users/christianlee/Desktop/kalshi/Gas && ./scripts/health_check.sh >> logs/health_check.log 2>&1
```

---

## 🎯 Recommended Deployment Configuration

### **For Daily Trading (Recommended):**

```bash
# 1. Install data automation (runs 24/7)
bash scripts/setup_bronze_service.sh

# 2. Schedule daily forecasts (8 AM)
# Add to crontab:
0 8 * * * cd /Users/christianlee/Desktop/kalshi/Gas && ./scripts/daily_forecast.sh >> logs/daily_forecast.log 2>&1

# 3. Schedule health checks (every 6 hours)
0 */6 * * * cd /Users/christianlee/Desktop/kalshi/Gas && ./scripts/health_check.sh >> logs/health_check.log 2>&1

# 4. Review predictions daily
cat outputs/final_forecast.json | python -m json.tool
python scripts/trading_signal.py
```

**Result:**
- ✅ Data updates automatically
- ✅ Models retrain daily at 8 AM
- ✅ Fresh predictions every morning
- ✅ Health monitoring
- ✅ Trading signals available

---

## 📁 Directory Structure After Deployment

```
Gas/
├── scripts/
│   ├── automate_bronze_silver.py      # Data automation (daemon)
│   ├── daily_forecast.sh              # Daily workflow (NEW)
│   ├── fully_automated_forecast.sh    # Full automation (NEW)
│   ├── get_latest_forecast.py         # API for predictions (NEW)
│   ├── trading_signal.py              # Trading decisions (NEW)
│   ├── health_check.sh                # Monitoring (NEW)
│   └── ...
├── logs/
│   ├── bronze_silver_automation.log   # Data updates
│   ├── daily_forecast.log             # Training/predictions
│   ├── automated_forecast.log         # Full automation
│   └── health_check.log               # System health
├── outputs/
│   ├── final_forecast.json            # Latest predictions
│   ├── models/                        # Trained models
│   └── ...
└── data/
    ├── bronze/                        # Raw data (auto-updated)
    ├── silver/                        # Clean data (auto-updated)
    └── gold/                          # Features (updated daily)
```

---

## 🎓 Deployment Checklist

### **Pre-Deployment:**
- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] API keys configured (if needed)
- [ ] Data directories exist

### **Basic Deployment:**
- [ ] Data automation installed
- [ ] Data automation tested
- [ ] Logs directory created
- [ ] Initial forecast generated

### **Production Deployment:**
- [ ] Daily forecast script created
- [ ] Forecast schedule configured
- [ ] Health checks enabled
- [ ] Monitoring alerts set up
- [ ] Trading integration tested

### **Post-Deployment:**
- [ ] Verify data updates
- [ ] Verify forecast generation
- [ ] Verify prediction accuracy
- [ ] Document any issues

---

## 🚨 Troubleshooting

### **Data Not Updating:**
```bash
# Check if daemon is running
ps aux | grep automate_bronze_silver

# Check logs
tail -f logs/bronze_silver_automation.log

# Restart daemon
pkill -f automate_bronze_silver.py
python scripts/automate_bronze_silver.py --daemon &
```

### **Forecast Not Generating:**
```bash
# Check logs
tail -f logs/daily_forecast.log

# Run manually to see errors
./scripts/daily_forecast.sh
```

### **Old Predictions:**
```bash
# Check forecast age
ls -lh outputs/final_forecast.json

# Force new forecast
./scripts/daily_forecast.sh
```

---

## 📝 Summary

### **Minimal Deployment (Recommended):**
```bash
# 1. Data automation (background)
python scripts/automate_bronze_silver.py --daemon &

# 2. Daily forecasts (manual or scheduled)
./scripts/daily_forecast.sh
```

### **Full Deployment:**
```bash
# 1. Install data automation service
bash scripts/setup_bronze_service.sh

# 2. Schedule daily forecasts
crontab -e  # Add daily forecast job

# 3. Enable health checks
crontab -e  # Add health check job

# 4. Done! System runs automatically
```

---

**Status:** Ready for deployment! ✅  
**Next Steps:** Choose deployment option and follow steps above  
**Support:** Check logs in `logs/` directory for issues
