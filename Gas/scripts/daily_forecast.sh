#!/bin/bash
# Daily Gas Price Forecasting Workflow
# Run this once per day to get fresh predictions

set -e  # Exit on error

# Determine project directory relative to script location
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Determine Python interpreter: use virtualenv if available, otherwise system python
if [ -n "$VIRTUAL_ENV" ]; then
    PYTHON="$VIRTUAL_ENV/bin/python"
elif [ -f "$PROJECT_DIR/../.venv/bin/python" ]; then
    PYTHON="$PROJECT_DIR/../.venv/bin/python"
else
    PYTHON="$(which python3 || which python)"
fi

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

# Show preview of forecast
if [ -f "outputs/final_forecast.json" ]; then
    echo "📊 Forecast Preview:"
    cat outputs/final_forecast.json | $PYTHON -m json.tool | head -20
    echo "..."
else
    echo "⚠️  Forecast file not found!"
fi

echo "=================================================="
