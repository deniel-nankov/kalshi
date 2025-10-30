#!/bin/bash
#
# Complete Daily Workflow for Kalshi Competition
# 
# This script:
# 1. Validates yesterday's predictions (track_actuals.py)
# 2. Makes today's predictions (daily_prediction.py)
# 3. Regenerates all submission graphs
#
# Usage: ./scripts/daily_workflow.sh
#

set -e  # Exit on error

echo "================================================================================"
echo "🚀 KALSHI COMPETITION - DAILY WORKFLOW"
echo "================================================================================"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================================================"

cd /Users/denielnankov/Documents/kalshi/Gas

# Step 1: Validate Previous Predictions
echo ""
echo "📊 STEP 1: Validating Previous Predictions..."
echo "--------------------------------------------------------------------------------"
if /Users/denielnankov/Documents/kalshi/.venv/bin/python scripts/track_actuals.py; then
    echo "✅ Validation complete!"
else
    echo "⚠️  No new actuals available yet (EIA lag is 1-2 days)"
fi

# Step 2: Make Today's Prediction
echo ""
echo "🔮 STEP 2: Making Today's Prediction..."
echo "--------------------------------------------------------------------------------"
echo "y" | /Users/denielnankov/Documents/kalshi/.venv/bin/python scripts/daily_prediction.py
echo "✅ Prediction complete!"

# Step 3: Regenerate Graphs
echo ""
echo "📊 STEP 3: Regenerating Submission Graphs..."
echo "--------------------------------------------------------------------------------"
/Users/denielnankov/Documents/kalshi/.venv/bin/python scripts/create_submission_graphs.py
echo "✅ Graphs regenerated!"

# Step 4: Show Current Status
echo ""
echo "================================================================================"
echo "📋 CURRENT STATUS"
echo "================================================================================"

# Count predictions
TOTAL_PREDICTIONS=$(wc -l < data/real_time_tracking.csv)
TOTAL_PREDICTIONS=$((TOTAL_PREDICTIONS - 1))  # Subtract header

# Count validations (rows with actual_price)
VALIDATED=$(awk -F',' 'NR>1 && $6!="" {count++} END {print count+0}' data/real_time_tracking.csv)

echo "Total Predictions Made: $TOTAL_PREDICTIONS"
echo "Predictions Validated:  $VALIDATED"
echo "Pending Validation:     $((TOTAL_PREDICTIONS - VALIDATED))"
echo ""
echo "Progress: [$VALIDATED / 10] for competition submission"
echo ""

if [ $VALIDATED -ge 10 ]; then
    echo "🎉 READY TO SUBMIT! You have 10+ validated predictions!"
elif [ $VALIDATED -ge 5 ]; then
    echo "🔥 Halfway there! Keep running daily to reach 10 predictions."
else
    echo "📅 Keep running daily to collect more validation data."
fi

echo ""
echo "================================================================================"
echo "📁 OUTPUT LOCATIONS"
echo "================================================================================"
echo "Tracking Data:     data/real_time_tracking.csv"
echo "Graphs:            outputs/submission_graphs/"
echo "Submission Memo:   FORECAST_SUBMISSION_MEMO.md"
echo ""
echo "================================================================================"
echo "✅ DAILY WORKFLOW COMPLETE!"
echo "================================================================================"
echo ""
echo "💡 Next Steps:"
echo "   1. Check graphs in outputs/submission_graphs/"
echo "   2. Review tracking data: cat data/real_time_tracking.csv"
echo "   3. Run again tomorrow to collect more data"
echo ""
echo "🏆 Target: 10 validated predictions by Oct 29, 2025"
echo "================================================================================"
