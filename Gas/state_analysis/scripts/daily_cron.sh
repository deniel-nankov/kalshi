#!/bin/bash
#
# Daily State Gas Price Collection - Cron Job Helper
#
# This script is designed to run from cron at 9:30 AM daily
# It collects gas prices for all 50 states + DC and logs results
#
# Usage (in crontab):
#   30 9 * * * /Users/denielnankov/Documents/kalshi/Gas/state_analysis/scripts/daily_cron.sh
#

# Paths
PROJECT_DIR="/Users/denielnankov/Documents/kalshi/Gas"
VENV_PYTHON="/Users/denielnankov/Documents/kalshi/.venv/bin/python"
SCRIPT="${PROJECT_DIR}/state_analysis/scripts/collect_state_prices.py"
CRON_LOG="${PROJECT_DIR}/state_analysis/data/cron.log"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Log start
echo "========================================" >> "$CRON_LOG"
echo "Starting collection: $(date)" >> "$CRON_LOG"

# Run collection
"$VENV_PYTHON" "$SCRIPT" >> "$CRON_LOG" 2>&1

# Log completion
EXIT_CODE=$?
echo "Completed: $(date) (exit code: $EXIT_CODE)" >> "$CRON_LOG"
echo "========================================" >> "$CRON_LOG"

# Exit with same code as Python script
exit $EXIT_CODE
