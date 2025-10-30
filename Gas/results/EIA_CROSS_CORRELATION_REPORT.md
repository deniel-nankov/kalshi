
EIA CROSS-CORRELATION ANALYSIS - 200 WEEKS
===========================================

Date: 2025-10-29 21:47:11
Data: 2022-01-03 to 2025-10-27 (200 weeks)
States: 9
Lag range: -10 to +10 weeks

INTERPRETATION
--------------
- Lag < 0: State LEADS national (potential predictor)
- Lag = 0: Synchronous (moves together)
- Lag > 0: State LAGS national (follower)

SUMMARY STATISTICS
------------------
Mean best correlation:     0.938
Mean synchronous (lag=0):  0.937
Mean improvement:          0.0015

States with best lag ≠ 0:  3/9
Mean absolute best lag:    0.33 weeks

CLASSIFICATION
--------------
Leading states (lag < 0):     2
Synchronous states (lag = 0): 6
Lagging states (lag > 0):     1

ALL STATES RANKED
-----------------
state  consumption_weight  best_lag   best_r   lag0_r  improvement
   MN               0.020         0 0.984594 0.984594     0.000000
   TX               0.094        -1 0.975052 0.970454     0.004597
   NY               0.047         0 0.969398 0.969398     0.000000
   MA               0.025         0 0.963945 0.963945     0.000000
   FL               0.062        -1 0.948157 0.946308     0.001849
   OH               0.036         0 0.944476 0.944476     0.000000
   CO               0.018         0 0.908006 0.908006     0.000000
   CA               0.111         0 0.905529 0.905529     0.000000
   WA               0.024         1 0.843922 0.837018     0.006904

HIGH-CONSUMPTION STATES (Top 4 = 31.4%)
----------------------------------------

CA (11.1% of national):
  Classification: SYNCHRONOUS
  Best lag: 0 weeks
  Best r: 0.906
  Lag=0 r: 0.906
  Improvement: 0.0000 (0.00%)

TX (9.4% of national):
  Classification: LEADS
  Best lag: -1 weeks
  Best r: 0.975
  Lag=0 r: 0.970
  Improvement: 0.0046 (0.47%)

FL (6.2% of national):
  Classification: LEADS
  Best lag: -1 weeks
  Best r: 0.948
  Lag=0 r: 0.946
  Improvement: 0.0018 (0.20%)

NY (4.7% of national):
  Classification: SYNCHRONOUS
  Best lag: 0 weeks
  Best r: 0.969
  Lag=0 r: 0.969
  Improvement: 0.0000 (0.00%)


KEY FINDINGS
------------
1. Mean improvement from optimal lag: 0.0015 (0.16%)
2. 6 states are synchronous (lag=0 is best)
3. 2 states lead, 1 states lag
4. Maximum improvement: 0.0069 (WA)

INTERPRETATION
--------------

✅ MINIMAL LEAD/LAG STRUCTURE DETECTED

Mean improvement from optimal lag is <1%, indicating:
- States move SYNCHRONOUSLY with national average
- No systematic leading or lagging dynamics
- States aggregate to national without predictive lead
- Validates aggregation hypothesis

CONCLUSION: State prices do NOT provide leading indicators.
They simply compose the national average in real-time.

This is a NEGATIVE but RIGOROUS result suitable for publication:
"200-week analysis shows state gas prices aggregate to national
average without systematic lead/lag structure (mean lag improvement
{df_results['improvement'].mean():.4f}, {df_results['improvement'].mean()/df_results['lag0_r'].mean()*100:.2f}%)."


NEXT STEPS
----------
1. Granger causality tests (GOLD STANDARD)
   - Test if states Granger-cause national prices
   - Requires p<0.05 for causal claim
   
2. If Granger p>0.05: Document null result (publishable!)
3. If Granger p<0.05: Consider model enhancement

FILES
-----
- Results: /Users/denielnankov/Documents/kalshi/Gas/results/eia_cross_correlation_results.csv
- Lag profiles: /Users/denielnankov/Documents/kalshi/Gas/results/eia_cross_correlation_200weeks.png
- Heatmap: /Users/denielnankov/Documents/kalshi/Gas/results/eia_cross_correlation_heatmap.png
