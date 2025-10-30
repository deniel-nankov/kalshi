"""
Build State-Enhanced Model with Granger-Validated Features
==========================================================

Based on Granger causality results, build enhanced Ridge model with:
- TX(t-1): p<0.000001, F=56.8 (EXTREMELY STRONG)
- FL(t-1): p=0.000016, F=19.6 (VERY STRONG)
- CA(t-3): p=0.014, F=3.6 (SIGNIFICANT)
- NY(t-4): p=0.008, F=3.6 (SIGNIFICANT)

Methodology:
1. Walk-forward validation on 200 weeks
2. Compare to baseline Ridge (MAE $0.0214)
3. Target: >10% improvement (MAE <$0.019)
4. Statistical significance: paired t-test p<0.05
5. If validated: Deploy, else document

Expected Outcome:
TX/FL have F>20, should provide substantial improvement.
Conservative estimate: 5-15% MAE reduction.
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'state_analysis' / 'data'
RESULTS_DIR = BASE_DIR / 'results'
RESULTS_DIR.mkdir(exist_ok=True)

print("="*80)
print("BUILDING STATE-ENHANCED MODEL")
print("="*80)

# Load EIA weekly data
df_states = pd.read_csv(DATA_DIR / 'eia_state_prices_weekly.csv')
df_national = pd.read_csv(DATA_DIR / 'eia_national_average_weekly.csv')

# Convert dates
df_states['week'] = pd.to_datetime(df_states['date'])
df_national['week'] = pd.to_datetime(df_national['date'])

# Pivot
pivot = df_states.pivot(index='week', columns='state', values='price')
national_prices = df_national.set_index('week')['price']

# Align
common_weeks = pivot.index.intersection(national_prices.index)
pivot = pivot.loc[common_weeks].sort_index()
national_prices = national_prices.loc[common_weeks].sort_index()

n = len(common_weeks)

print(f"\n✅ Data loaded:")
print(f"   Weeks: {n}")
print(f"   Date range: {common_weeks[0].date()} to {common_weeks[-1].date()}")
print(f"   States: {', '.join(pivot.columns)}")

# Create lag features based on Granger results
print("\n" + "="*80)
print("FEATURE ENGINEERING")
print("="*80)

print("\nGranger-validated lag features:")
print("  • TX(t-1): p<0.000001, F=56.8")
print("  • FL(t-1): p=0.000016, F=19.6")
print("  • CA(t-3): p=0.014, F=3.6")
print("  • NY(t-4): p=0.008, F=3.6")

# Create feature matrix
features_df = pd.DataFrame(index=national_prices.index)

# Add state lags
features_df['TX_lag1'] = pivot['TX'].shift(1)
features_df['FL_lag1'] = pivot['FL'].shift(1)
features_df['CA_lag3'] = pivot['CA'].shift(3)
features_df['NY_lag4'] = pivot['NY'].shift(4)

# Also add national lags (baseline features)
for lag in [1, 2, 3, 4]:
    features_df[f'national_lag{lag}'] = national_prices.shift(lag)

# Add moving averages
for window in [4, 8, 12]:
    features_df[f'national_ma{window}'] = national_prices.rolling(window).mean()
    features_df[f'TX_ma{window}'] = pivot['TX'].rolling(window).mean()
    features_df[f'FL_ma{window}'] = pivot['FL'].rolling(window).mean()

# Add price changes
features_df['national_change1'] = national_prices.diff(1)
features_df['TX_change1'] = pivot['TX'].diff(1)
features_df['FL_change1'] = pivot['FL'].diff(1)

# Drop rows with NaN (from lags/windows)
max_lag = 12  # From MA12
features_df = features_df.iloc[max_lag:]
target = national_prices.iloc[max_lag:]

print(f"\n✅ Features created:")
print(f"   Total features: {len(features_df.columns)}")
print(f"   Samples after lag removal: {len(features_df)}")
print(f"   Features: {', '.join(features_df.columns[:8])}...")

# Remove any remaining NaN
mask = ~(features_df.isnull().any(axis=1) | target.isnull())
X = features_df[mask]
y = target[mask]

print(f"\n✅ Clean data:")
print(f"   Samples: {len(X)}")
print(f"   Training samples available: {len(X)}")

# Walk-forward validation
print("\n" + "="*80)
print("WALK-FORWARD VALIDATION")
print("="*80)

# Use 80 weeks for initial training, then walk forward
initial_train_size = 80
print(f"\nInitial training: {initial_train_size} weeks")
print(f"Testing: {len(X) - initial_train_size} weeks (walk-forward)")

# Storage for predictions
baseline_predictions = []
enhanced_predictions = []
actuals = []
dates = []

print("\nRunning walk-forward validation...")

for i in range(initial_train_size, len(X)):
    # Training data up to current point
    X_train = X.iloc[:i]
    y_train = y.iloc[:i]
    
    # Test point
    X_test = X.iloc[i:i+1]
    y_test = y.iloc[i]
    
    # Baseline model: National lags + MAs only
    baseline_features = [c for c in X.columns if 'national' in c]
    X_train_baseline = X_train[baseline_features]
    X_test_baseline = X_test[baseline_features]
    
    # Enhanced model: All features including state lags
    X_train_enhanced = X_train
    X_test_enhanced = X_test
    
    # Scale
    scaler_baseline = StandardScaler()
    X_train_baseline_scaled = scaler_baseline.fit_transform(X_train_baseline)
    X_test_baseline_scaled = scaler_baseline.transform(X_test_baseline)
    
    scaler_enhanced = StandardScaler()
    X_train_enhanced_scaled = scaler_enhanced.fit_transform(X_train_enhanced)
    X_test_enhanced_scaled = scaler_enhanced.transform(X_test_enhanced)
    
    # Train models
    model_baseline = Ridge(alpha=1.0)
    model_baseline.fit(X_train_baseline_scaled, y_train)
    
    model_enhanced = Ridge(alpha=1.0)
    model_enhanced.fit(X_train_enhanced_scaled, y_train)
    
    # Predict
    pred_baseline = model_baseline.predict(X_test_baseline_scaled)[0]
    pred_enhanced = model_enhanced.predict(X_test_enhanced_scaled)[0]
    
    # Store
    baseline_predictions.append(pred_baseline)
    enhanced_predictions.append(pred_enhanced)
    actuals.append(y_test)
    dates.append(X.index[i])
    
    if (i - initial_train_size) % 20 == 0:
        print(f"  Week {i - initial_train_size + 1}/{len(X) - initial_train_size}: " +
              f"Baseline MAE={abs(pred_baseline - y_test):.4f}, " +
              f"Enhanced MAE={abs(pred_enhanced - y_test):.4f}")

# Convert to arrays
baseline_predictions = np.array(baseline_predictions)
enhanced_predictions = np.array(enhanced_predictions)
actuals = np.array(actuals)

# Calculate errors
baseline_errors = np.abs(baseline_predictions - actuals)
enhanced_errors = np.abs(enhanced_predictions - actuals)

# Metrics
baseline_mae = baseline_errors.mean()
enhanced_mae = enhanced_errors.mean()
improvement = (baseline_mae - enhanced_mae) / baseline_mae * 100

baseline_rmse = np.sqrt(np.mean((baseline_predictions - actuals)**2))
enhanced_rmse = np.sqrt(np.mean((enhanced_predictions - actuals)**2))

# Statistical significance: paired t-test
t_stat, p_value = stats.ttest_rel(baseline_errors, enhanced_errors)

print("\n" + "="*80)
print("VALIDATION RESULTS")
print("="*80)

print(f"\n📊 Performance Metrics:")
print(f"   Baseline MAE:  ${baseline_mae:.4f}")
print(f"   Enhanced MAE:  ${enhanced_mae:.4f}")
print(f"   Improvement:   {improvement:+.2f}%")
print(f"")
print(f"   Baseline RMSE: ${baseline_rmse:.4f}")
print(f"   Enhanced RMSE: ${enhanced_rmse:.4f}")
print(f"   RMSE improvement: {(baseline_rmse - enhanced_rmse)/baseline_rmse*100:+.2f}%")

print(f"\n📈 Statistical Significance:")
print(f"   Paired t-test: t={t_stat:.4f}, p={p_value:.6f}")
if p_value < 0.05:
    print(f"   ✅ SIGNIFICANT (p<0.05): Enhancement is statistically significant!")
else:
    print(f"   ❌ NOT SIGNIFICANT (p>0.05): Enhancement not statistically significant")

print(f"\n🎯 Target Achievement:")
target_mae = 0.019
if enhanced_mae < target_mae:
    print(f"   ✅ TARGET MET: Enhanced MAE ${enhanced_mae:.4f} < ${target_mae:.4f}")
else:
    print(f"   ❌ TARGET MISSED: Enhanced MAE ${enhanced_mae:.4f} > ${target_mae:.4f}")

if improvement > 10:
    print(f"   ✅ IMPROVEMENT >10%: {improvement:.2f}%")
else:
    print(f"   ⚠️ IMPROVEMENT <10%: {improvement:.2f}%")

# Detailed analysis
print(f"\n📊 Error Distribution:")
print(f"   Baseline: mean=${baseline_mae:.4f}, std=${baseline_errors.std():.4f}, median=${np.median(baseline_errors):.4f}")
print(f"   Enhanced: mean=${enhanced_mae:.4f}, std=${enhanced_errors.std():.4f}, median=${np.median(enhanced_errors):.4f}")

# Feature importance
print(f"\n🔍 Feature Importance (Enhanced Model):")
# Train final model on all data for coefficient inspection
scaler_final = StandardScaler()
X_scaled = scaler_final.fit_transform(X)
model_final = Ridge(alpha=1.0)
model_final.fit(X_scaled, y)

# Get coefficients
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'coefficient': model_final.coef_
})
feature_importance['abs_coef'] = np.abs(feature_importance['coefficient'])
feature_importance = feature_importance.sort_values('abs_coef', ascending=False)

print("\nTop 10 features by absolute coefficient:")
print(feature_importance.head(10)[['feature', 'coefficient', 'abs_coef']].to_string(index=False))

# Check if state features are important
state_features = ['TX_lag1', 'FL_lag1', 'CA_lag3', 'NY_lag4']
state_importance = feature_importance[feature_importance['feature'].isin(state_features)]
print(f"\nGranger-validated state features:")
print(state_importance[['feature', 'coefficient', 'abs_coef']].to_string(index=False))

# Visualization
fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# 1. Time series comparison
ax = axes[0, 0]
plot_start = max(0, len(dates) - 52)  # Last year
ax.plot(dates[plot_start:], actuals[plot_start:], 'k-', linewidth=2, label='Actual', alpha=0.8)
ax.plot(dates[plot_start:], baseline_predictions[plot_start:], 'b--', linewidth=1.5, label='Baseline', alpha=0.7)
ax.plot(dates[plot_start:], enhanced_predictions[plot_start:], 'r--', linewidth=1.5, label='Enhanced', alpha=0.7)
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Price ($/gal)', fontsize=12)
ax.set_title(f'Predictions vs Actual (Last Year)\nEnhanced MAE: ${enhanced_mae:.4f} vs Baseline: ${baseline_mae:.4f}', 
             fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

# 2. Error comparison
ax = axes[0, 1]
ax.boxplot([baseline_errors, enhanced_errors], labels=['Baseline', 'Enhanced'])
ax.set_ylabel('Absolute Error ($/gal)', fontsize=12)
ax.set_title(f'Error Distribution\nImprovement: {improvement:+.2f}% (p={p_value:.4f})', 
             fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

# 3. Scatter: Baseline vs Actual
ax = axes[1, 0]
ax.scatter(actuals, baseline_predictions, alpha=0.5, s=30)
ax.plot([actuals.min(), actuals.max()], [actuals.min(), actuals.max()], 'r--', linewidth=2)
ax.set_xlabel('Actual Price ($/gal)', fontsize=12)
ax.set_ylabel('Baseline Prediction ($/gal)', fontsize=12)
ax.set_title(f'Baseline Model\nMAE: ${baseline_mae:.4f}, RMSE: ${baseline_rmse:.4f}', 
             fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)

# 4. Scatter: Enhanced vs Actual
ax = axes[1, 1]
ax.scatter(actuals, enhanced_predictions, alpha=0.5, s=30, color='green')
ax.plot([actuals.min(), actuals.max()], [actuals.min(), actuals.max()], 'r--', linewidth=2)
ax.set_xlabel('Actual Price ($/gal)', fontsize=12)
ax.set_ylabel('Enhanced Prediction ($/gal)', fontsize=12)
ax.set_title(f'Enhanced Model (+ State Lags)\nMAE: ${enhanced_mae:.4f}, RMSE: ${enhanced_rmse:.4f}', 
             fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(RESULTS_DIR / 'state_enhanced_model_validation.png', dpi=300, bbox_inches='tight')
print(f"\n💾 Saved: {RESULTS_DIR / 'state_enhanced_model_validation.png'}")

# Save detailed results
results_df = pd.DataFrame({
    'date': dates,
    'actual': actuals,
    'baseline_prediction': baseline_predictions,
    'enhanced_prediction': enhanced_predictions,
    'baseline_error': baseline_errors,
    'enhanced_error': enhanced_errors,
    'improvement': baseline_errors - enhanced_errors
})

output_file = RESULTS_DIR / 'state_enhanced_model_results.csv'
results_df.to_csv(output_file, index=False)
print(f"💾 Saved: {output_file}")

# Create comprehensive report
report = f"""
STATE-ENHANCED MODEL VALIDATION REPORT
======================================

Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
Validation period: {dates[0].date()} to {dates[-1].date()} ({len(dates)} weeks)
Initial training: {initial_train_size} weeks
Walk-forward testing: {len(dates)} predictions

GRANGER-VALIDATED FEATURES
---------------------------
Based on 200-week Granger causality analysis:

1. TX(t-1): p<0.000001, F=56.8 (EXTREMELY STRONG)
2. FL(t-1): p=0.000016, F=19.6 (VERY STRONG)
3. CA(t-3): p=0.014, F=3.6 (SIGNIFICANT)
4. NY(t-4): p=0.008, F=3.6 (SIGNIFICANT)

PERFORMANCE METRICS
-------------------
Baseline Model (National features only):
  MAE:  ${baseline_mae:.4f}
  RMSE: ${baseline_rmse:.4f}
  Features: {len(baseline_features)} (national lags + MAs)

Enhanced Model (+ State lag features):
  MAE:  ${enhanced_mae:.4f}
  RMSE: ${enhanced_rmse:.4f}
  Features: {len(X.columns)} (national + state lags)

IMPROVEMENT
-----------
MAE improvement:  {improvement:+.2f}%
RMSE improvement: {(baseline_rmse - enhanced_rmse)/baseline_rmse*100:+.2f}%

Target: >10% MAE improvement
Status: {"✅ TARGET MET" if improvement > 10 else "⚠️ TARGET MISSED"}

STATISTICAL SIGNIFICANCE
-------------------------
Paired t-test (baseline vs enhanced errors):
  t-statistic: {t_stat:.4f}
  p-value: {p_value:.6f}
  Significance: {"✅ SIGNIFICANT (p<0.05)" if p_value < 0.05 else "❌ NOT SIGNIFICANT (p>0.05)"}

ERROR DISTRIBUTION
------------------
Baseline errors:
  Mean: ${baseline_mae:.4f}
  Std:  ${baseline_errors.std():.4f}
  Median: ${np.median(baseline_errors):.4f}
  95th percentile: ${np.percentile(baseline_errors, 95):.4f}

Enhanced errors:
  Mean: ${enhanced_mae:.4f}
  Std:  ${enhanced_errors.std():.4f}
  Median: ${np.median(enhanced_errors):.4f}
  95th percentile: ${np.percentile(enhanced_errors, 95):.4f}

TOP 10 MOST IMPORTANT FEATURES
-------------------------------
{feature_importance.head(10)[['feature', 'coefficient']].to_string(index=False)}

GRANGER-VALIDATED STATE FEATURES
---------------------------------
{state_importance[['feature', 'coefficient']].to_string(index=False)}

DECISION CRITERIA
-----------------
"""

# Decision logic
deploy = False
reason = []

if improvement > 10:
    reason.append("✅ MAE improvement >10%")
else:
    reason.append(f"❌ MAE improvement {improvement:.2f}% < 10%")

if p_value < 0.05:
    reason.append("✅ Statistically significant (p<0.05)")
else:
    reason.append(f"❌ Not statistically significant (p={p_value:.4f})")

if enhanced_mae < target_mae:
    reason.append(f"✅ Enhanced MAE ${enhanced_mae:.4f} < target ${target_mae:.4f}")
else:
    reason.append(f"⚠️ Enhanced MAE ${enhanced_mae:.4f} > target ${target_mae:.4f}")

# Final decision
if improvement > 10 and p_value < 0.05:
    deploy = True
    decision = "🎯 DEPLOY ENHANCED MODEL"
    explanation = "Model meets both criteria: >10% improvement AND statistical significance"
elif improvement > 5 and p_value < 0.05:
    deploy = True  
    decision = "⚠️ CONDITIONAL DEPLOY"
    explanation = "Model is statistically significant but improvement <10%. Deploy with monitoring."
else:
    deploy = False
    decision = "📝 DOCUMENT AS RESEARCH"
    explanation = "Model does not meet deployment criteria. Document as exploratory finding."

report += "\n".join(reason)
report += f"""

FINAL DECISION
--------------
{decision}

{explanation}

"""

if deploy:
    report += """
DEPLOYMENT PLAN
---------------
1. Update daily_prediction.py to include state lag features
2. Fetch weekly state prices from EIA (automated)
3. Generate predictions with enhanced model
4. Monitor performance for 2 weeks
5. If validation continues, make permanent

NEXT STEPS
----------
1. Integrate EIA state data fetching into daily pipeline
2. Update prediction script with state features
3. Deploy with A/B testing (baseline + enhanced in parallel)
4. Document performance improvement
"""
else:
    report += """
PUBLICATION STRATEGY
--------------------
Despite not meeting deployment criteria, this is PUBLICATION-QUALITY research:

Title: "When Granger Causality Doesn't Translate to Forecasting Gains: 
        State-Level Gas Prices as Leading Indicators"

Key findings:
1. 8/9 states show significant Granger causality (200-week analysis)
2. TX p<0.000001 (F=56.8), FL p=0.000016 (F=19.6)
3. But practical forecasting improvement: {improvement:.2f}%
4. Lesson: Statistical significance ≠ Practical significance

Contribution:
- Rigorous negative result with 200-week validation
- Demonstrates limits of Granger causality for forecasting
- Validates current national-level modeling approach

Target: Journal of Forecasting (IF=3.4)

NEXT STEPS
----------
1. Write manuscript with full methodology
2. Include all validation results
3. Discuss implications for commodity forecasting
4. Submit for peer review
"""

report += f"""

FILES GENERATED
---------------
- Validation plot: {RESULTS_DIR / 'state_enhanced_model_validation.png'}
- Detailed results: {output_file}
- This report: {RESULTS_DIR / 'STATE_ENHANCED_MODEL_REPORT.md'}
"""

report_file = RESULTS_DIR / 'STATE_ENHANCED_MODEL_REPORT.md'
report_file.write_text(report)
print(f"💾 Saved: {report_file}")

print("\n" + "="*80)
print("✅ STATE-ENHANCED MODEL VALIDATION COMPLETE!")
print("="*80)

print(f"\n{decision}")
print(f"\nKey Results:")
print(f"  • MAE improvement: {improvement:+.2f}%")
print(f"  • Statistical significance: p={p_value:.6f} {'✅' if p_value < 0.05 else '❌'}")
print(f"  • Baseline MAE: ${baseline_mae:.4f}")
print(f"  • Enhanced MAE: ${enhanced_mae:.4f}")

if deploy:
    print(f"\n🚀 READY FOR DEPLOYMENT!")
    print(f"   Next: Update daily_prediction.py with state features")
else:
    print(f"\n📝 DOCUMENT AS RESEARCH FINDING")
    print(f"   Still publication-quality: Granger vs Practical forecasting")

print("\n" + "="*80)
