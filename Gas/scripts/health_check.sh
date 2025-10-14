#!/bin/bash
# System Health Check
# Monitors data automation, forecasts, and system resources

# Determine project directory relative to script location
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
cd "$PROJECT_DIR"

echo "🏥 System Health Check - $(date)"
echo "=================================================="

EXIT_CODE=0

# Check 1: Data automation running?
echo ""
echo "📥 Data Automation Status:"
if pgrep -f "automate_bronze_silver.py" > /dev/null; then
    echo "  ✅ Process: RUNNING"
    PID=$(pgrep -f "automate_bronze_silver.py")
    echo "  📋 PID: $PID"
else
    echo "  ❌ Process: STOPPED"
    EXIT_CODE=1
fi

# Check 2: Recent Bronze updates?
echo ""
echo "📦 Bronze Layer Status:"
BRONZE_LOG="logs/bronze_silver_automation.log"
if [ -f "$BRONZE_LOG" ]; then
    LAST_SUCCESS=$(tail -100 "$BRONZE_LOG" | grep "Successfully downloaded" | tail -1)
    if [ -n "$LAST_SUCCESS" ]; then
        echo "  ✅ Recent update found"
        echo "  📝 $LAST_SUCCESS" | head -c 80
        echo "..."
    else
        echo "  ⚠️  No recent successful downloads"
        LAST_LINE=$(tail -1 "$BRONZE_LOG")
        echo "  📝 Last log: $LAST_LINE" | head -c 80
        echo "..."
    fi
    
    # Check for errors
    ERROR_COUNT=$(tail -100 "$BRONZE_LOG" | grep -c "ERROR" || true)
    if [ $ERROR_COUNT -gt 5 ]; then
        echo "  ⚠️  Found $ERROR_COUNT recent errors"
        EXIT_CODE=1
    fi
else
    echo "  ❌ Log file not found"
    EXIT_CODE=1
fi

# Check 3: Silver layer status
echo ""
echo "🪙 Silver Layer Status:"
SILVER_METADATA="data/silver/silver_processing_metadata.json"
if [ -f "$SILVER_METADATA" ]; then
    echo "  ✅ Metadata exists"
    LAST_PROCESSED=$(cat "$SILVER_METADATA" | python3 -c "import sys, json; print(json.load(sys.stdin).get('last_processed', 'unknown'))" 2>/dev/null || echo "unknown")
    echo "  📅 Last processed: $LAST_PROCESSED"
else
    echo "  ⚠️  No metadata found"
fi

# Check 4: Gold layer status
echo ""
echo "⭐ Gold Layer Status:"
GOLD_FILES=$(find data/gold -name "*.parquet" 2>/dev/null | wc -l)
if [ $GOLD_FILES -gt 0 ]; then
    echo "  ✅ Files found: $GOLD_FILES"
    NEWEST_GOLD=$(find data/gold -name "*.parquet" -type f -exec stat -f "%m %N" {} \; 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
    if [ -n "$NEWEST_GOLD" ]; then
        AGE_GOLD=$(( ($(date +%s) - $(stat -f %m "$NEWEST_GOLD" 2>/dev/null || echo 0)) / 3600 ))
        echo "  📅 Newest file age: $AGE_GOLD hours"
        if [ $AGE_GOLD -gt 48 ]; then
            echo "  ⚠️  Gold layer is stale (>48 hours)"
        fi
    fi
else
    echo "  ❌ No Gold files found"
    EXIT_CODE=1
fi

# Check 5: Recent forecast?
echo ""
echo "🔮 Forecast Status:"
FORECAST="outputs/final_forecast.json"
if [ -f "$FORECAST" ]; then
    AGE=$(( ($(date +%s) - $(stat -f %m "$FORECAST" 2>/dev/null || echo 0)) / 3600 ))
    if [ $AGE -lt 24 ]; then
        echo "  ✅ Forecast age: $AGE hours (fresh)"
    elif [ $AGE -lt 48 ]; then
        echo "  ⚠️  Forecast age: $AGE hours (getting stale)"
    else
        echo "  ❌ Forecast age: $AGE hours (stale)"
        EXIT_CODE=1
    fi
    
    # Check forecast content
    PRED_COUNT=$(cat "$FORECAST" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('predictions', [])))" 2>/dev/null || echo 0)
    echo "  📊 Predictions: $PRED_COUNT"
else
    echo "  ❌ No forecast found"
    EXIT_CODE=1
fi

# Check 6: Models exist?
echo ""
echo "🤖 Model Status:"
MODEL_DIR="outputs/models"
if [ -d "$MODEL_DIR" ]; then
    MODEL_COUNT=$(find "$MODEL_DIR" -name "*.pkl" 2>/dev/null | wc -l)
    echo "  ✅ Models found: $MODEL_COUNT"
    if [ $MODEL_COUNT -lt 2 ]; then
        echo "  ⚠️  Expected at least 2 models"
    fi
else
    echo "  ❌ Model directory not found"
    EXIT_CODE=1
fi

# Check 7: Disk space
echo ""
echo "💾 Disk Space:"
DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
DISK_AVAIL=$(df -h . | awk 'NR==2 {print $4}')
if [ $DISK_USAGE -lt 80 ]; then
    echo "  ✅ Usage: ${DISK_USAGE}% (Available: $DISK_AVAIL)"
elif [ $DISK_USAGE -lt 90 ]; then
    echo "  ⚠️  Usage: ${DISK_USAGE}% (Available: $DISK_AVAIL)"
else
    echo "  ❌ Usage: ${DISK_USAGE}% (Available: $DISK_AVAIL) - HIGH!"
    EXIT_CODE=1
fi

# Check 8: Log files size
echo ""
echo "📝 Log Files:"
LOG_SIZE=$(du -sh logs 2>/dev/null | cut -f1)
echo "  📂 Total size: ${LOG_SIZE:-N/A}"

# Final summary
echo ""
echo "=================================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Overall Status: HEALTHY"
else
    echo "⚠️  Overall Status: ISSUES DETECTED"
fi
echo "=================================================="

exit $EXIT_CODE
