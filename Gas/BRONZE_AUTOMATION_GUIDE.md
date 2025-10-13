# Bronze Data Automation Guide

## 🤖 Overview

Automate Bronze layer data downloads based on data source schedules:

- **EIA:** Updates Wednesday 10:30 AM ET (weekly)
- **RBOB Futures:** Updates Mon-Fri during market hours (9:30 AM - 4:00 PM ET)
- **Retail Prices:** Updates Monday mornings (weekly)

---

## 🚀 Quick Start

### One-Time Update
```bash
# Check for fresh data and download if needed
python scripts/automate_bronze.py
```

**Output:**
```
EIA: Data is fresh (last download: 2025-10-10)
RBOB: Market is closed, skipping update
Retail: Data is 5 days old (threshold: 7 days)

Summary:
  ⏭️  EIA: Skipped (data is fresh)
  ⏭️  RBOB: Skipped (market closed)
  ⏭️  RETAIL: Skipped (data is fresh)
```

### Force Update
```bash
# Download fresh data regardless of age
python scripts/automate_bronze.py --force
```

---

## 🔄 Daemon Mode (Continuous Updates)

### Run Interactively
```bash
# Check every hour (default)
python scripts/automate_bronze.py --daemon

# Check every 30 minutes
python scripts/automate_bronze.py --daemon --interval 1800

# Check every 15 minutes (for active trading)
python scripts/automate_bronze.py --daemon --interval 900
```

Press **Ctrl+C** to stop.

### Run as Background Process
```bash
# Start in background
nohup python scripts/automate_bronze.py --daemon > /dev/null 2>&1 &

# Save the PID for later
echo $! > /tmp/bronze_automation.pid

# Check if running
ps -p $(cat /tmp/bronze_automation.pid)

# Stop the process
kill $(cat /tmp/bronze_automation.pid)
```

---

## ⚙️ macOS System Service (launchd)

### Create Launch Agent

**1. Create the plist file:**
```bash
cat > ~/Library/LaunchAgents/com.kalshi.bronze-automation.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.kalshi.bronze-automation</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/Users/christianlee/Desktop/kalshi/.venv/bin/python</string>
        <string>/Users/christianlee/Desktop/kalshi/Gas/scripts/automate_bronze.py</string>
        <string>--daemon</string>
        <string>--interval</string>
        <string>3600</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/Users/christianlee/Desktop/kalshi/Gas</string>
    
    <key>StandardOutPath</key>
    <string>/Users/christianlee/Desktop/kalshi/Gas/logs/bronze_automation.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/christianlee/Desktop/kalshi/Gas/logs/bronze_automation_error.log</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>ProcessType</key>
    <string>Background</string>
</dict>
</plist>
EOF
```

**2. Load the service:**
```bash
launchctl load ~/Library/LaunchAgents/com.kalshi.bronze-automation.plist
```

**3. Check status:**
```bash
launchctl list | grep bronze-automation
```

**4. Start/Stop/Restart:**
```bash
# Stop
launchctl stop com.kalshi.bronze-automation

# Start
launchctl start com.kalshi.bronze-automation

# Restart (unload and reload)
launchctl unload ~/Library/LaunchAgents/com.kalshi.bronze-automation.plist
launchctl load ~/Library/LaunchAgents/com.kalshi.bronze-automation.plist
```

**5. Remove service:**
```bash
launchctl unload ~/Library/LaunchAgents/com.kalshi.bronze-automation.plist
rm ~/Library/LaunchAgents/com.kalshi.bronze-automation.plist
```

---

## 📊 Smart Scheduling Logic

### EIA Data (Weekly)
```
Last download: Monday, Oct 7
Next EIA update: Wednesday, Oct 9 @ 10:30 AM ET

Status on:
- Monday Oct 7:    ⏭️  Skip (just downloaded)
- Tuesday Oct 8:   ⏭️  Skip (not Wednesday yet)
- Wednesday Oct 9 (before 10:30 AM): ⏭️  Skip (not updated yet)
- Wednesday Oct 9 (after 10:30 AM):  ✅ Download (new data!)
- Thursday Oct 10: ⏭️  Skip (already have latest)
```

### RBOB Data (Hourly during market hours)
```
Market Hours: Mon-Fri 9:30 AM - 4:00 PM ET

Status:
- Monday 10:00 AM:  ✅ Download (market open, > 1 hour since last)
- Monday 10:30 AM:  ⏭️  Skip (< 1 hour since last)
- Monday 11:30 AM:  ✅ Download (> 1 hour since last)
- Saturday:         ⏭️  Skip (market closed)
- Monday 8:00 AM:   ⏭️  Skip (before market open)
```

### Retail Prices (Weekly)
```
Last download: Monday, Oct 7
Next retail update: Monday, Oct 14 @ 12:00 PM ET

Status on:
- Monday Oct 7:     ⏭️  Skip (just downloaded)
- Wednesday Oct 9:  ⏭️  Skip (not Monday yet)
- Monday Oct 14 (before 12 PM): ⏭️  Skip (not updated yet)
- Monday Oct 14 (after 12 PM):  ✅ Download (new data!)
```

---

## 📝 Logging

Logs are saved to: `Gas/logs/bronze_automation.log`

**View logs:**
```bash
# Tail the log file
tail -f logs/bronze_automation.log

# View last 50 lines
tail -n 50 logs/bronze_automation.log

# Search for errors
grep ERROR logs/bronze_automation.log
```

**Log format:**
```
2025-10-12 10:30:15 - bronze_automation - INFO - EIA: No previous download found
2025-10-12 10:30:16 - bronze_automation - INFO - Downloading EIA inventory/utilization data (attempt 1/3)
2025-10-12 10:30:45 - bronze_automation - INFO - ✅ Successfully downloaded EIA inventory/utilization data
```

---

## 🔔 Metadata Tracking

The script tracks download times in: `Gas/data/bronze/*_metadata.json`

**Example: `eia_metadata.json`**
```json
{
  "last_download": "2025-10-09T15:45:23.123456",
  "source": "eia"
}
```

This prevents redundant downloads and enables smart scheduling.

---

## 🛠️ Error Handling

### Automatic Retries
- Each download attempts **3 times**
- Exponential backoff: 30s, 60s, 90s
- 5-minute timeout per attempt

### Example:
```
Downloading RBOB/WTI futures data (attempt 1/3)
❌ Failed to download: Connection timeout
Retrying in 30 seconds...
Downloading RBOB/WTI futures data (attempt 2/3)
✅ Successfully downloaded RBOB/WTI futures data
```

### Daemon Resilience
If running as daemon, errors won't stop the service:
```
Error during update cycle: ConnectionError(...)
Next check at: 2025-10-12 11:30:00
Sleeping for 3600 seconds...
```

---

## 📋 Integration with Pipeline

### Option 1: Manual Trigger + Smart Pipeline
```bash
# Check for fresh Bronze data (runs quickly)
python scripts/automate_bronze.py

# Smart update (rebuilds Silver/Gold if Bronze changed)
python scripts/update_pipeline.py
```

### Option 2: Scheduled Full Pipeline
```bash
# In cron or launchd, run full pipeline daily
python scripts/automate_bronze.py --force
python scripts/update_pipeline.py --full
```

### Option 3: Daemon + On-Demand Processing
```bash
# Bronze daemon runs continuously
python scripts/automate_bronze.py --daemon &

# Process data when needed
python scripts/update_pipeline.py --silver  # Rebuild Silver from fresh Bronze
python scripts/update_pipeline.py --gold-only  # Just features
```

---

## 🎯 Recommended Setups

### For Active Trading (High Frequency)
```bash
# Check every 15 minutes during market hours
python scripts/automate_bronze.py --daemon --interval 900
```

### For Daily Analysis (Low Frequency)
```bash
# Check once per hour
python scripts/automate_bronze.py --daemon --interval 3600
```

### For Production (macOS Service)
```bash
# Set up launchd service (auto-starts on boot)
launchctl load ~/Library/LaunchAgents/com.kalshi.bronze-automation.plist
```

### For Manual Updates Only
```bash
# Add to daily workflow script
python scripts/automate_bronze.py
python scripts/update_pipeline.py
```

---

## 🔍 Monitoring

### Check Service Status
```bash
# Is daemon running?
ps aux | grep automate_bronze

# Check recent activity
tail -n 20 logs/bronze_automation.log

# Check for failures
grep "❌" logs/bronze_automation.log
```

### Health Check Script
```bash
#!/bin/bash
# health_check.sh

LOGFILE="logs/bronze_automation.log"
LAST_UPDATE=$(tail -n 100 "$LOGFILE" | grep "Successfully downloaded" | tail -1)

if [ -z "$LAST_UPDATE" ]; then
    echo "⚠️  No successful downloads found recently"
    exit 1
else
    echo "✅ Last successful download:"
    echo "$LAST_UPDATE"
    exit 0
fi
```

---

## ⚙️ Configuration

### Adjust Update Schedules

Edit `scripts/automate_bronze.py`:

```python
# Change EIA update day/time
EIA_UPDATE_DAY = 2      # 0=Monday, 2=Wednesday
EIA_UPDATE_HOUR = 15    # 15 = 3 PM (adjust for timezone)
EIA_UPDATE_MINUTE = 30

# Change RBOB market hours
RBOB_MARKET_OPEN_HOUR = 14   # 2 PM UTC ≈ 9:30 AM ET
RBOB_MARKET_CLOSE_HOUR = 21  # 9 PM UTC ≈ 4:00 PM ET

# Change retail update day
RETAIL_UPDATE_DAY = 0   # Monday
RETAIL_UPDATE_HOUR = 12 # Noon
```

### Adjust Data Freshness Thresholds

```python
# In should_update_eia():
if age_days >= 7:  # Change to 5 for more frequent updates

# In should_update_rbob():
if age_hours >= 1:  # Change to 0.5 for 30-minute updates

# In should_update_retail():
if age_days >= 7:  # Change to 5 for more frequent updates
```

---

## 🎓 Best Practices

### DO:
✅ Run daemon mode for automated updates  
✅ Monitor logs for failures  
✅ Use `--force` for testing or manual refreshes  
✅ Set up launchd for production  
✅ Check metadata files to verify last updates  

### DON'T:
❌ Run multiple daemons simultaneously (creates conflicts)  
❌ Force update too frequently (wastes API calls)  
❌ Ignore error logs (may indicate API issues)  
❌ Delete metadata files (breaks smart scheduling)  

---

## 📝 Summary

**One-Time Update:**
```bash
python scripts/automate_bronze.py
```

**Continuous Updates:**
```bash
python scripts/automate_bronze.py --daemon
```

**Production Service:**
```bash
launchctl load ~/Library/LaunchAgents/com.kalshi.bronze-automation.plist
```

**Check Logs:**
```bash
tail -f logs/bronze_automation.log
```

---

**Status:** ✅ Bronze automation ready  
**Dependencies:** None (uses existing download scripts)  
**Breaking Changes:** None  
**Next Step:** Set up daemon or launchd service
