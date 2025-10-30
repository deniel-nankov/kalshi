# EIA API Issue Resolution

**Date:** October 28, 2025  
**Status:** ✅ RESOLVED

## Problem

The EIA API was returning 400/403/500 errors when attempting to fetch the latest gasoline price data. The old API parameters were not working:
- ❌ Product code: `EPM0_EPD2D_PTE_NUS_DPG` (invalid)
- ❌ Frequency: `daily` (not supported)
- ❌ Endpoint structure outdated

## Root Cause

The EIA API v2 structure changed:
1. **Product codes simplified:** Old compound codes no longer work
2. **Frequency changed:** Only supports `weekly`, `monthly`, `annual` (NOT `daily`)
3. **Facet structure different:** Need to use `facets[product][]` and `facets[duoarea][]` parameters

## Solution

### Correct API Parameters

```python
url = "https://api.eia.gov/v2/petroleum/pri/gnd/data/"

params = {
    'api_key': '<your_key>',
    'frequency': 'weekly',           # NOT 'daily'
    'data[0]': 'value',
    'facets[product][]': 'EPMR',     # Regular Gasoline (simple code)
    'facets[duoarea][]': 'NUS',      # U.S. National
    'sort[0][column]': 'period',
    'sort[0][direction]': 'desc',
    'length': 50
}
```

### Valid Product Codes (Gas/Gasoline)

Available from endpoint: `https://api.eia.gov/v2/petroleum/pri/gnd/facet/product`

- `EPMR` - **Regular Gasoline** ⭐ (Main one we need)
- `EPM0` - Total Gasoline
- `EPMM` - Midgrade Gasoline
- `EPMP` - Premium Gasoline
- `EPM0R` - Reformulated Motor Gasoline
- `EPM0U` - Conventional Gasoline (No Oxy)
- `EPMRR` - Reformulated Regular Gasoline
- `EPMRU` - Conventional Regular Gasoline
- `EPMPR` - Reformulated Premium Gasoline
- `EPMPU` - Conventional Premium Gasoline
- `EPMMR` - Reformulated Midgrade
- `EPMMU` - Conventional Midgrade

### Valid Area Codes

Available from endpoint: `https://api.eia.gov/v2/petroleum/pri/gnd/facet/duoarea`

- `NUS` - **U.S. National Average** ⭐ (Main one we need)
- `R10` - PADD 1 (East Coast)
- `R20` - PADD 2 (Midwest)
- `R30` - PADD 3 (Gulf Coast)
- `R40` - PADD 4 (Rocky Mountain)
- `R50` - PADD 5 (West Coast)
- Plus individual states and cities

## Latest Data Retrieved

**Successfully fetched on:** October 28, 2025

### U.S. National Average - Regular Gasoline (EPMR)

| Date | Price ($/gal) |
|------|---------------|
| 2025-10-27 | $3.035 |
| 2025-10-20 | $3.063 |
| 2025-10-13 | $3.094 |
| 2025-10-06 | $3.100 |

**Latest available:** October 27, 2025 - **$3.035/gal**

### Current Status

- ✅ **Gold Layer:** 1,819 rows through October 18, 2025
- ✅ **EIA Latest:** October 27, 2025 ($3.035/gal)
- ℹ️ **Gap:** 9 days (Oct 18 → Oct 27)
- ℹ️ **Data Frequency:** Weekly (published Mondays)

## Key Findings

1. **EIA API Key is VALID** - Authentication works correctly
2. **Data is WEEKLY, not DAILY** - EIA publishes retail gas prices weekly (Mondays)
3. **Latest data is Oct 27, 2025** - Published yesterday (Monday, Oct 27)
4. **No new daily data exists** - EIA doesn't provide daily retail prices anymore
5. **Weekly data is sufficient** - Our model trained on historical data can predict for any date

## Implications for Predictions

### ✅ What We CAN Do

1. **Use the model to predict for Oct 28, 29, 30** - Model trained on historical patterns
2. **Validate predictions when weekly data published** - Compare with actual weekly prices
3. **Track performance over time** - Build validation dataset for submission

### ⚠️ What We CANNOT Do

1. **Get daily actual prices for validation** - EIA only publishes weekly
2. **Update gold layer with daily data** - Would need all 108 features per day
3. **Real-time validation** - Must wait for Monday weekly releases

## Rate Limiting

After extensive testing (20+ API calls in short period), the API started returning:
- HTTP 403 (Forbidden) - Temporary rate limit
- Suggest: **Wait 5-10 minutes between calls**
- Saved data to `/tmp/eia_us_weekly.json` for offline use

## Recommendations

### For Kalshi Submission (Due Oct 30)

1. **Use existing model** to predict Oct 28, 29, 30
2. **Submit predictions** based on current gold layer (through Oct 18)
3. **Validate when possible** using weekly EIA data (next Monday: Nov 3)
4. **Document methodology** in submission memo

### Script Updates Needed

1. ✅ Update `fetch_eia_with_retry()` to use correct parameters
2. ✅ Change frequency from `daily` to `weekly`
3. ✅ Update product code from `EPM0_EPD2D_PTE_NUS_DPG` to `EPMR`
4. ✅ Add area filter `duoarea: NUS`
5. ⚠️ Add rate limiting (5-10 min between calls)
6. ⚠️ Cache results to avoid repeated API calls

## Testing Commands

### Test 1: Validate API Key
```bash
curl "https://api.eia.gov/v2/?api_key=YOUR_KEY"
```

### Test 2: Check Route Info
```bash
curl "https://api.eia.gov/v2/petroleum/pri/gnd?api_key=YOUR_KEY"
```

### Test 3: List Product Codes
```bash
curl "https://api.eia.gov/v2/petroleum/pri/gnd/facet/product?api_key=YOUR_KEY"
```

### Test 4: Fetch Latest Data
```bash
curl "https://api.eia.gov/v2/petroleum/pri/gnd/data/?api_key=YOUR_KEY&frequency=weekly&facets[product][]=EPMR&facets[duoarea][]=NUS&length=5"
```

## Comparison: Our Prediction vs. Latest Actual

| Date | Our Prediction | Actual (EIA) | Error |
|------|----------------|--------------|-------|
| Oct 19, 2025 | $3.065 (Fused) | (Weekly Oct 20: $3.063) | -$0.002 |

**Note:** Oct 19 falls in week ending Oct 20. Our prediction of $3.065 is extremely close to the weekly average of $3.063!

## Next Steps

1. **Wait 5-10 minutes** for API rate limit to reset
2. **Make predictions** for Oct 28, 29, 30 using existing model
3. **Update tracking file** with new predictions
4. **Finalize submission** by Oct 30 deadline
5. **Validate predictions** when next weekly data published (Nov 3)

## Success Metrics

- ✅ API key validated
- ✅ Correct endpoint found: `/petroleum/pri/gnd/data/`
- ✅ Correct parameters: `EPMR`, `NUS`, `weekly`
- ✅ Latest data retrieved: Oct 27, 2025 ($3.035/gal)
- ✅ Data format understood: JSON with period, value, area-name
- ✅ Saved offline copy for development: `/tmp/eia_us_weekly.json`

---

**Problem Resolved:** October 28, 2025, 10:45 AM  
**Time to Resolution:** ~2 hours  
**API Calls Made:** ~25 (hit rate limit)  
**Data Retrieved:** 50 weeks of U.S. regular gasoline prices
