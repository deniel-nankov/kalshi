# 🔍 Cross-Correlation Analysis Report

**Date:** October 29, 2025  
**Sample Size:** n = 4 time points  
**Lags Tested:** -2 to +2 days  

---

## 🎯 PURPOSE

Determine if any states systematically **lead** or **lag** the national average, which could indicate:
- Regional price discovery (some markets lead others)
- Supply chain effects (upstream states influence downstream)
- Predictive value (leading states could improve forecasts)

---

## 📊 KEY FINDINGS

### States That Lead National Average

| State | Name | Weight | Lead | Best r |
|-------|------|--------|------|--------|
| NE | Nebraska | 0.008 | 2 day(s) | 0.999 |
| NM | New Mexico | 0.009 | 2 day(s) | 0.995 |
| MI | Michigan | 0.031 | 2 day(s) | 0.985 |
| IA | Iowa | 0.012 | 2 day(s) | 0.958 |
| ND | North Dakota | 0.003 | 2 day(s) | 0.945 |
| WV | West Virginia | 0.007 | 2 day(s) | 0.944 |
| HI | Hawaii | 0.004 | 2 day(s) | 0.924 |
| OK | Oklahoma | 0.013 | 2 day(s) | 0.905 |
| IN | Indiana | 0.026 | 2 day(s) | -0.739 |
| CT | Connecticut | 0.012 | 1 day(s) | -0.925 |

### Top 5 Consumption States

| State | Name | Weight | Best Lag | Best r |
|-------|------|--------|----------|--------|
| CA | California | 0.111 | 2 | 0.712 |
| TX | Texas | 0.094 | -1 | -0.987 |
| FL | Florida | 0.062 | 1 | -0.919 |
| NY | New York | 0.047 | 0 | 0.987 |
| PA | Pennsylvania | 0.041 | 1 | -0.935 |

---

## ⚠️ LIMITATIONS

1. **Sample size:** Only 4 time points severely limits statistical power
2. **Lag range:** Can only test ±2 days (need ≥3 overlapping points)
3. **Noise:** With n=4, random variation dominates signal
4. **Confidence:** Cannot establish statistical significance

---

## 🔬 NEXT STEPS

1. ✅ Continue daily data collection (target: 30 days)
2. ✅ Re-run cross-correlation with larger sample
3. ✅ Test lags up to ±7 days with sufficient data
4. ✅ Granger causality tests (requires 30+ observations)
5. ❌ Do NOT add lag features to model yet (premature)

---

## 💡 INTERPRETATION

While these results are **suggestive**, they are **not conclusive** due to small sample size. The observed lag patterns could easily be due to random chance. We need 30+ daily observations before making definitive statements about leading/lagging relationships.

