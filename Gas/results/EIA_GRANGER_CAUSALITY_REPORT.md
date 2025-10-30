
EIA GRANGER CAUSALITY ANALYSIS - 200 WEEKS
===========================================

Date: 2025-10-29 21:48:58
Data: 2022-01-03 to 2025-10-27 (200 weeks)
States tested: 9
Lags tested: 1, 2, 3, 4 weeks
Significance level: α=0.05

METHODOLOGY
-----------
Granger causality tests whether State(t-k) provides predictive information
for National(t) beyond National's own history.

Null Hypothesis (H0): State does NOT Granger-cause National
Alternative (H1): State DOES Granger-cause National

Test: F-test comparing models:
- Restricted: National(t) = α + Σ β_i·National(t-i) + ε
- Full: National(t) = α + Σ β_i·National(t-i) + Σ γ_i·State(t-i) + ε

If p<0.05: Reject H0 → State provides predictive value
If p>0.05: Accept H0 → State doesn't add predictive information

OVERALL RESULTS
---------------
States tested: 9
States with significant causality: 8/9 (88.9%)

Mean minimum p-value: 0.0337
Median minimum p-value: 0.0078
Min p-value (best): 0.000000 (TX)

DETAILED RESULTS BY LAG
-----------------------

Lag 1 week:
  Significant: 4/9 states (44.4%)
  Mean p-value: 0.1524
  Significant states: TX, FL, WA, MN

Lag 2 week:
  Significant: 5/9 states (55.6%)
  Mean p-value: 0.1427
  Significant states: TX, FL, WA, NY, CA

Lag 3 week:
  Significant: 5/9 states (55.6%)
  Mean p-value: 0.1505
  Significant states: TX, FL, NY, CA, MA

Lag 4 week:
  Significant: 6/9 states (66.7%)
  Mean p-value: 0.1499
  Significant states: TX, FL, OH, NY, CA, MA


ALL STATES RANKED
-----------------
state  consumption_weight  best_lag        min_p  any_significant
   TX               0.094         1 1.734176e-12             True
   FL               0.062         1 1.556815e-05             True
   WA               0.024         1 1.448721e-03             True
   OH               0.036         4 7.760235e-03             True
   NY               0.047         4 7.773138e-03             True
   CA               0.111         3 1.405985e-02             True
   MN               0.020         1 3.335364e-02             True
   MA               0.025         3 3.697613e-02             True
   CO               0.018         1 2.018190e-01            False

HIGH-CONSUMPTION STATES (Top 4 = 31.4%)
----------------------------------------

CA (11.1% of national):
  Best lag: 3 weeks
  Minimum p-value: 0.014060
  Significant: YES
  
  Lag breakdown:
    Lag 1: F=1.611, p=0.205891 ✗
    Lag 2: F=3.427, p=0.034476 ✓
    Lag 3: F=3.626, p=0.014060 ✓
    Lag 4: F=3.080, p=0.017406 ✓

TX (9.4% of national):
  Best lag: 1 weeks
  Minimum p-value: 0.000000
  Significant: YES
  
  Lag breakdown:
    Lag 1: F=56.812, p=0.000000 ✓
    Lag 2: F=10.331, p=0.000055 ✓
    Lag 3: F=6.820, p=0.000217 ✓
    Lag 4: F=5.175, p=0.000563 ✓

FL (6.2% of national):
  Best lag: 1 weeks
  Minimum p-value: 0.000016
  Significant: YES
  
  Lag breakdown:
    Lag 1: F=19.636, p=0.000016 ✓
    Lag 2: F=6.662, p=0.001594 ✓
    Lag 3: F=5.125, p=0.001974 ✓
    Lag 4: F=4.369, p=0.002117 ✓

NY (4.7% of national):
  Best lag: 4 weeks
  Minimum p-value: 0.007773
  Significant: YES
  
  Lag breakdown:
    Lag 1: F=1.492, p=0.223329 ✗
    Lag 2: F=3.443, p=0.033940 ✓
    Lag 3: F=3.452, p=0.017657 ✓
    Lag 4: F=3.576, p=0.007773 ✓


INTERPRETATION
--------------

🎯 POSITIVE RESULT: STRONG GRANGER CAUSALITY DETECTED

Finding: 8/9 states (88.9%) show significant causality.

Interpretation:
- Majority of states provide predictive information
- State-level features may improve forecast accuracy
- Leading dynamics exist despite high synchronous correlation

NEXT STEPS:
1. Extract significant lag features
2. Enhance Ridge model with state lags
3. Walk-forward validation with 200 weeks
4. Require >10% out-of-sample MAE improvement
5. If validated: Deploy enhanced model
6. If not: Document as exploratory finding


STATISTICAL POWER
-----------------
With n=200 weeks and 4 lags:
- Degrees of freedom: 192 (adequate)
- Power to detect medium effects (f²=0.15): >90%
- F-critical (α=0.05, df1=4, df2≈192): ~2.4

Sample size is SUFFICIENT for reliable Granger tests.

CONCLUSION
----------

Strong evidence of Granger causality in majority of states.
State-level features warrant model enhancement testing.

POSITIVE RESULT - PROCEED TO MODEL ENHANCEMENT


FILES
-----
- Results: /Users/denielnankov/Documents/kalshi/Gas/results/eia_granger_causality_results.csv
- Full report: /Users/denielnankov/Documents/kalshi/Gas/results/EIA_GRANGER_CAUSALITY_REPORT.md
