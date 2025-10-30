
EIA CORRELATION ANALYSIS - 200 WEEKS
====================================

Date: 2025-10-29 21:43:59
Data: 2022-01-03 to 2025-10-27 (200 weeks)
States: 9

SUMMARY STATISTICS
------------------
Mean correlation:    0.937
Median correlation:  0.946
Std deviation:       0.046
Range:              [0.837, 0.985]

Mean CI width:       ±0.017
Significant (p<0.05): 9/9 (100.0%)

TOP 5 STATES (Highest Correlation)
-----------------------------------
state        r       p_value  consumption_weight
   MN 0.984594 6.456489e-152               0.020
   TX 0.970454 3.211456e-124               0.094
   NY 0.969398 9.893450e-123               0.047
   MA 0.963945 8.470592e-116               0.025
   FL 0.946308  4.676952e-99               0.062

BOTTOM 5 STATES (Lowest Correlation)
-------------------------------------
state        r      p_value  consumption_weight
   FL 0.946308 4.676952e-99               0.062
   OH 0.944476 1.181920e-97               0.036
   CO 0.908006 9.638182e-77               0.018
   CA 0.905529 1.179588e-75               0.111
   WA 0.837018 9.517526e-54               0.024

HIGH-CONSUMPTION STATES (Top 4 = 31.4%)
----------------------------------------

CA (11.1% of national):
  r = 0.906 [0.877, 0.928]
  p-value = 0.0000 ✓ SIGNIFICANT
  R² = 0.820 (82.0% variance explained)

TX (9.4% of national):
  r = 0.970 [0.961, 0.978]
  p-value = 0.0000 ✓ SIGNIFICANT
  R² = 0.942 (94.2% variance explained)

FL (6.2% of national):
  r = 0.946 [0.930, 0.959]
  p-value = 0.0000 ✓ SIGNIFICANT
  R² = 0.895 (89.5% variance explained)

NY (4.7% of national):
  r = 0.969 [0.960, 0.977]
  p-value = 0.0000 ✓ SIGNIFICANT
  R² = 0.940 (94.0% variance explained)


STATISTICAL POWER
-----------------
With n=200 weeks:
- Can detect r=0.2 with >99% power
- Can detect r=0.3 with 100% power
- 95% CI width: ±0.017

Compare to n=4 weeks (preliminary):
- Could NOT detect even r=0.9 (power=31%)
- 95% CI width: ±2.0 (useless!)

IMPROVEMENT: 117.4x tighter confidence intervals!

KEY FINDINGS
------------
1. 9 states show significant correlation (p<0.05)
2. Mean correlation: 0.937 (vs -0.230 with n=4)
3. All confidence intervals are TIGHT (±0.14 typical)
4. High-consumption states show STRONG correlation

NEXT STEPS
----------
1. Cross-correlation analysis (test lags ±10 weeks)
2. Granger causality tests (GOLD STANDARD)
3. Decision: Enhance model if validated, document null result if not

FILES
-----
- Data: /Users/denielnankov/Documents/kalshi/Gas/state_analysis/data/eia_state_prices_weekly.csv
- Results: /Users/denielnankov/Documents/kalshi/Gas/results/eia_correlations_200weeks.csv
- Visualization: /Users/denielnankov/Documents/kalshi/Gas/results/eia_correlations_200weeks.png
