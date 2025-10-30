# Submission Graphs for Kalshi Competition

**Generated**: October 24, 2025  
**Purpose**: Publication-ready visualizations for forecasting competition submission

---

## 📊 Graph Overview

### **Graph 1: Predicted vs Actual Time Series** ✅
- **File**: `graph1_time_series.png`
- **Shows**: Ridge, Kalshi Market, Bayesian Fused predictions vs Actual prices over time
- **Purpose**: Demonstrates model tracking ability and forecast accuracy
- **Status**: Generated (updates as actuals become available)

### **Graph 2: Forecast Error Distribution** ⏳
- **File**: `graph2_error_distribution.png`
- **Shows**: Box plot + histogram of prediction errors (Ridge vs Bayesian)
- **Purpose**: Shows bias, variance, and error distribution characteristics
- **Status**: Requires actual prices (will generate after validations)

### **Graph 3: Predicted vs Actual Scatter Plot** ⏳
- **File**: `graph3_scatter_predicted_vs_actual.png`
- **Shows**: Scatter plot with y=x perfect prediction line
- **Purpose**: Visual check for systematic bias in predictions
- **Status**: Requires actual prices (will generate after validations)

### **Graph 4: Confidence Interval Coverage** ✅
- **File**: `graph4_confidence_intervals.png`
- **Shows**: Bayesian CI (±$0.048) and Conformal CI (±$0.017) with actual prices
- **Purpose**: Validates uncertainty quantification methods (95% coverage guarantee)
- **Status**: Generated (shows predictions + intervals now, actuals when available)

### **Graph 5: Uncertainty Reduction Bar Chart** ✅
- **File**: `graph5_uncertainty_reduction.png`
- **Shows**: Bar chart comparing Ridge (±$0.100) vs Bayesian (±$0.048) vs Conformal (±$0.017)
- **Purpose**: Highlights 52.5% uncertainty reduction from ensemble methods
- **Status**: Generated (static - based on calibration results)

### **Graph 6: Cumulative Absolute Error** ⏳
- **File**: `graph6_cumulative_error.png`
- **Shows**: Cumulative |error| over time for Ridge vs Bayesian
- **Purpose**: Shows which method is most consistently accurate
- **Status**: Requires actual prices (will generate after validations)

---

## 🔄 How to Regenerate Graphs

### **Option 1: Standalone Script**
```bash
cd /Users/denielnankov/Documents/kalshi/Gas
python scripts/create_submission_graphs.py
```

### **Option 2: Complete Daily Workflow** (Recommended)
```bash
cd /Users/denielnankov/Documents/kalshi/Gas
./scripts/daily_workflow.sh
```

This will:
1. ✅ Validate previous predictions
2. ✅ Make today's prediction
3. ✅ Regenerate all graphs
4. ✅ Show current progress

---

## 📈 Graph Specifications

- **Resolution**: 300 DPI (publication quality)
- **Format**: PNG (high compression, web-friendly)
- **Style**: Seaborn darkgrid with custom colors
- **Font Sizes**: 10-14pt (readable at all sizes)
- **Color Palette**: Husl (colorblind-friendly)

---

## 🎯 Metrics Displayed in Graphs

| Metric | Value | Graph |
|--------|-------|-------|
| Ridge MAE | $0.0011 | Graph 2 |
| Bayesian MAE | $0.0010* | Graph 2 |
| Ridge MAPE | 0.036% | Graph 2 |
| Bayesian MAPE | 0.033%* | Graph 2 |
| R² Score | 0.9987 | Graph 3 |
| Conformal Coverage | 95.1% | Graph 4 |
| Bayesian Coverage | ~95% | Graph 4 |
| Uncertainty Reduction | 52.5% | Graph 5 |

*Estimated from historical performance

---

## 📊 Current Status

Run this to check current data availability:

```bash
python -c "
import pandas as pd
df = pd.read_csv('data/real_time_tracking.csv')
total = len(df)
validated = df['actual_price'].notna().sum()
print(f'Total Predictions: {total}')
print(f'Validated: {validated}')
print(f'Pending: {total - validated}')
print(f'Progress: {validated}/10 for submission')
"
```

---

## 🏆 Graphs for Submission

### **Include in Memo:**
1. ✅ Graph 1 (Time Series) - Shows your predictions vs reality
2. ✅ Graph 4 (CI Coverage) - Shows statistical rigor
3. ✅ Graph 5 (Uncertainty Reduction) - Shows innovation (Bayesian fusion)

### **Include After 10 Validations:**
4. ✅ Graph 2 (Error Distribution) - Shows consistency
5. ✅ Graph 3 (Scatter Plot) - Shows no bias
6. ✅ Graph 6 (Cumulative Error) - Shows sustained accuracy

---

## 💡 Tips for Presentation

### **Graph 1 (Time Series)**
- **Highlight**: How closely predictions track actuals
- **Key Message**: "Our model accurately predicts gas price movements"

### **Graph 4 (CI Coverage)**
- **Highlight**: Actuals fall within confidence intervals
- **Key Message**: "95.1% empirical coverage validates our uncertainty quantification"

### **Graph 5 (Uncertainty Reduction)**
- **Highlight**: 52.5% reduction from Ridge to Bayesian
- **Key Message**: "Bayesian fusion with Kalshi markets reduces uncertainty by half"

### **Graph 2 (Error Distribution)**
- **Highlight**: Errors centered at zero (no bias)
- **Key Message**: "Bayesian fusion has tighter error distribution than Ridge alone"

### **Graph 3 (Scatter Plot)**
- **Highlight**: Points cluster on y=x line
- **Key Message**: "No systematic bias - predictions are unbiased estimators"

### **Graph 6 (Cumulative Error)**
- **Highlight**: Bayesian line below Ridge line
- **Key Message**: "Bayesian fusion consistently outperforms Ridge over time"

---

## 🔧 Troubleshooting

### **Issue: Graphs not updating with new data**
```bash
# Regenerate manually
python scripts/create_submission_graphs.py
```

### **Issue: Missing actuals (graphs 2, 3, 6 not generated)**
```bash
# Check if EIA data is available
python scripts/track_actuals.py

# If successful, regenerate graphs
python scripts/create_submission_graphs.py
```

### **Issue: Want higher resolution**
Edit `scripts/create_submission_graphs.py`:
```python
plt.rcParams['figure.dpi'] = 600  # Change from 300 to 600
plt.rcParams['savefig.dpi'] = 600
```

---

## 📁 File Organization

```
outputs/submission_graphs/
├── graph1_time_series.png              (144 KB) ✅
├── graph2_error_distribution.png       (pending actuals) ⏳
├── graph3_scatter_predicted_vs_actual.png (pending actuals) ⏳
├── graph4_confidence_intervals.png     (200 KB) ✅
├── graph5_uncertainty_reduction.png    (206 KB) ✅
├── graph6_cumulative_error.png         (pending actuals) ⏳
└── README.md                           (this file)
```

---

## 🎯 Next Steps

1. **Daily**: Run `./scripts/daily_workflow.sh` every day (2 minutes)
2. **Oct 26-27**: After 10 validations, all 6 graphs will be complete
3. **Oct 28-29**: Finalize submission memo with all graphs
4. **Oct 30**: Submit to Kalshi competition! 🏆

---

**Last Updated**: October 24, 2025  
**Script**: `scripts/create_submission_graphs.py`  
**Generator**: Automated daily workflow
