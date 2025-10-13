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

# Show preview of forecast
if [ -f "outputs/final_forecast.json" ]; then
    echo "📊 Forecast Preview:"
    cat outputs/final_forecast.json | $PYTHON -m json.tool | head -20
    echo "..."
else
    echo "⚠️  Forecast file not found!"
fi

echo "=================================================="
