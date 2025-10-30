
STATE-ENHANCED MODEL VALIDATION REPORT
======================================

Date: 2025-10-29 21:54:28
Validation period: 2023-10-09 to 2025-10-27 (108 weeks)
Initial training: 80 weeks
Walk-forward testing: 108 predictions

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
  MAE:  $0.0078
  RMSE: $0.0098
  Features: 8 (national lags + MAs)

Enhanced Model (+ State lag features):
  MAE:  $0.0082
  RMSE: $0.0097
  Features: 20 (national + state lags)

IMPROVEMENT
-----------
MAE improvement:  -4.65%
RMSE improvement: +1.12%

Target: >10% MAE improvement
Status: ⚠️ TARGET MISSED

STATISTICAL SIGNIFICANCE
-------------------------
Paired t-test (baseline vs enhanced errors):
  t-statistic: -0.5899
  p-value: 0.556484
  Significance: ❌ NOT SIGNIFICANT (p>0.05)

ERROR DISTRIBUTION
------------------
Baseline errors:
  Mean: $0.0078
  Std:  $0.0060
  Median: $0.0066
  95th percentile: $0.0205

Enhanced errors:
  Mean: $0.0082
  Std:  $0.0052
  Median: $0.0082
  95th percentile: $0.0181

TOP 10 MOST IMPORTANT FEATURES
-------------------------------
         feature  coefficient
   national_lag1     0.218221
    national_ma4     0.117616
national_change1     0.058773
         TX_lag1     0.055718
   national_lag2     0.035575
    national_ma8     0.033279
         FL_lag1     0.021836
   national_ma12     0.016414
   national_lag3    -0.015433
          FL_ma8    -0.013171

GRANGER-VALIDATED STATE FEATURES
---------------------------------
feature  coefficient
TX_lag1     0.055718
FL_lag1     0.021836
NY_lag4    -0.009620
CA_lag3    -0.001379

DECISION CRITERIA
-----------------
❌ MAE improvement -4.65% < 10%
❌ Not statistically significant (p=0.5565)
✅ Enhanced MAE $0.0082 < target $0.0190

FINAL DECISION
--------------
📝 DOCUMENT AS RESEARCH

Model does not meet deployment criteria. Document as exploratory finding.


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


FILES GENERATED
---------------
- Validation plot: /Users/denielnankov/Documents/kalshi/Gas/results/state_enhanced_model_validation.png
- Detailed results: /Users/denielnankov/Documents/kalshi/Gas/results/state_enhanced_model_results.csv
- This report: /Users/denielnankov/Documents/kalshi/Gas/results/STATE_ENHANCED_MODEL_REPORT.md
