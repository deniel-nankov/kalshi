#!/bin/bash
# Daily Tracking Routine
# Run this every morning to validate yesterday and predict today

echo "================================================================================"
echo "📅 DAILY GAS PRICE TRACKING ROUTINE"
echo "================================================================================"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================================================"
echo ""

# Navigate to project directory
cd /Users/denielnankov/Documents/kalshi/Gas

# Step 1: Validate yesterday's predictions
echo "Step 1: Validating yesterday's predictions..."
echo "--------------------------------------------------------------------------------"
/Users/denielnankov/Documents/kalshi/.venv/bin/python scripts/track_actuals.py
echo ""

# Step 2: Make today's prediction
echo "Step 2: Making today's prediction..."
echo "--------------------------------------------------------------------------------"
/Users/denielnankov/Documents/kalshi/.venv/bin/python scripts/daily_prediction.py <<EOF
y
EOF
echo ""

echo "================================================================================"
echo "✅ DAILY ROUTINE COMPLETE!"
echo "================================================================================"
echo ""
echo "Next Steps:"
echo "  1. Check data/real_time_tracking.csv for all predictions"
echo "  2. Run this script again tomorrow morning"
echo "  3. After 10 days, create visualizations for paper"
echo ""
echo "================================================================================"
