#!/usr/bin/env python3
"""
Test RBOB Futures → Retail Price Conversion

RBOB = Reformulated Blendstock for Oxygenate Blending (wholesale gasoline)
Retail = What consumers pay at the pump

Retail typically = RBOB + Distribution + Marketing + Taxes
Average markup: ~$0.60-0.80/gallon
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from pathlib import Path

print("=" * 80)
print("🔍 TESTING RBOB → RETAIL CONVERSION")
print("=" * 80)

# ============================================================================
# 1. Get RBOB daily data for Oct 18-27
# ============================================================================
print("\n1️⃣ Fetching RBOB futures data (Oct 18-27)...")

rbob = yf.download('RB=F', start='2025-10-18', end='2025-10-29', progress=False)
rbob = rbob[['Close']].copy()
rbob.columns = ['rbob_wholesale']
rbob.index = pd.to_datetime(rbob.index)

print(f"   Got {len(rbob)} trading days of RBOB data")
print(f"\n   RBOB Wholesale Prices:")
for idx, row in rbob.iterrows():
    print(f"      {idx.strftime('%Y-%m-%d')}: ${row['rbob_wholesale']:.3f}/gal")

# ============================================================================
# 2. EIA weekly retail actuals (ground truth)
# ============================================================================
print("\n2️⃣ Loading EIA weekly retail actuals...")

eia_weekly = {
    '2025-10-13': 3.061,
    '2025-10-20': 3.019,
    '2025-10-27': 3.035,
}

eia_df = pd.DataFrame([
    {'date': pd.Timestamp(date), 'eia_retail': price}
    for date, price in eia_weekly.items()
])
eia_df = eia_df.set_index('date')

print(f"   Got {len(eia_df)} EIA weekly prices:")
for idx, row in eia_df.iterrows():
    print(f"      {idx.strftime('%Y-%m-%d')}: ${row['eia_retail']:.3f}/gal")

# ============================================================================
# 3. Find optimal RBOB → Retail conversion
# ============================================================================
print("\n3️⃣ Finding optimal conversion formula...")

# Merge RBOB and EIA on dates where both exist
merged = rbob.join(eia_df, how='inner')

if len(merged) > 0:
    print(f"\n   Overlapping dates: {len(merged)}")
    
    # Calculate markup needed
    merged['markup'] = merged['eia_retail'] - merged['rbob_wholesale']
    merged['multiplier'] = merged['eia_retail'] / merged['rbob_wholesale']
    
    print(f"\n   Analysis:")
    for idx, row in merged.iterrows():
        print(f"      {idx.strftime('%Y-%m-%d')}:")
        print(f"         RBOB: ${row['rbob_wholesale']:.3f}")
        print(f"         Retail: ${row['eia_retail']:.3f}")
        print(f"         Markup: ${row['markup']:.3f}")
        print(f"         Multiplier: {row['multiplier']:.3f}x")
    
    # Calculate average conversion
    avg_markup = merged['markup'].mean()
    avg_multiplier = merged['multiplier'].mean()
    
    print(f"\n   📊 Average Conversion Factors:")
    print(f"      Markup: ${avg_markup:.3f}/gal")
    print(f"      Multiplier: {avg_multiplier:.3f}x")
    
    print(f"\n   💡 Conversion Formulas:")
    print(f"      Method 1 (Additive): Retail = RBOB + ${avg_markup:.3f}")
    print(f"      Method 2 (Multiplicative): Retail = RBOB × {avg_multiplier:.3f}")
else:
    print(f"\n   ⚠️ No overlapping dates between RBOB and EIA")
    print(f"   Using industry average: Retail = RBOB + $0.70")
    avg_markup = 0.70
    avg_multiplier = 1.30

# ============================================================================
# 4. Create daily retail estimates for Oct 18-27
# ============================================================================
print(f"\n{'=' * 80}")
print("4️⃣ Creating daily retail price estimates...")
print("=" * 80)

# Method 1: Additive markup
rbob['retail_est_additive'] = rbob['rbob_wholesale'] + avg_markup

# Method 2: Multiplicative
rbob['retail_est_mult'] = rbob['rbob_wholesale'] * avg_multiplier

print(f"\n   Daily Estimates (Oct 18-27):")
print(f"\n   {'Date':<12} {'RBOB':<8} {'Est(+)':<8} {'Est(×)':<8} {'EIA Actual':<12}")
print(f"   {'-'*60}")

for idx, row in rbob.iterrows():
    date_str = idx.strftime('%Y-%m-%d')
    rbob_val = row['rbob_wholesale']
    est_add = row['retail_est_additive']
    est_mult = row['retail_est_mult']
    
    # Check if EIA actual exists
    eia_actual = eia_weekly.get(date_str, None)
    eia_str = f"${eia_actual:.3f}" if eia_actual else "—"
    
    print(f"   {date_str:<12} ${rbob_val:.3f}   ${est_add:.3f}   ${est_mult:.3f}   {eia_str:<12}")
    
    # Calculate error if EIA actual exists
    if eia_actual:
        error_add = est_add - eia_actual
        error_mult = est_mult - eia_actual
        print(f"   {'':>12} {'':>8} {error_add:+.3f}    {error_mult:+.3f}")

# ============================================================================
# 5. Validate against EIA actuals
# ============================================================================
print(f"\n{'=' * 80}")
print("5️⃣ Validation against EIA actuals...")
print("=" * 80)

# Join with EIA
validation = rbob.join(eia_df, how='inner')

if len(validation) > 0:
    validation['error_additive'] = validation['retail_est_additive'] - validation['eia_retail']
    validation['error_mult'] = validation['retail_est_mult'] - validation['eia_retail']
    validation['abs_error_add'] = validation['error_additive'].abs()
    validation['abs_error_mult'] = validation['error_mult'].abs()
    
    print(f"\n   Validation on {len(validation)} EIA actual dates:")
    print(f"\n   Method 1 (Additive: RBOB + ${avg_markup:.3f}):")
    print(f"      Mean Absolute Error: ${validation['abs_error_add'].mean():.4f}")
    print(f"      Max Error: ${validation['abs_error_add'].max():.4f}")
    
    print(f"\n   Method 2 (Multiplicative: RBOB × {avg_multiplier:.3f}):")
    print(f"      Mean Absolute Error: ${validation['abs_error_mult'].mean():.4f}")
    print(f"      Max Error: ${validation['abs_error_mult'].max():.4f}")
    
    # Choose better method
    if validation['abs_error_add'].mean() < validation['abs_error_mult'].mean():
        best_method = "Additive"
        best_formula = f"RBOB + ${avg_markup:.3f}"
        rbob['retail_estimate'] = rbob['retail_est_additive']
    else:
        best_method = "Multiplicative"
        best_formula = f"RBOB × {avg_multiplier:.3f}"
        rbob['retail_estimate'] = rbob['retail_est_mult']
    
    print(f"\n   ✅ Best Method: {best_method}")
    print(f"   ✅ Formula: Retail = {best_formula}")

# ============================================================================
# 6. Fill gaps with RBOB estimates
# ============================================================================
print(f"\n{'=' * 80}")
print("6️⃣ Creating complete daily series (Oct 18-27)...")
print("=" * 80)

# Create date range
date_range = pd.date_range(start='2025-10-18', end='2025-10-27', freq='D')

# Combine RBOB estimates + EIA actuals
daily_series = pd.DataFrame(index=date_range)
daily_series.index.name = 'date'

# Add RBOB estimates (trading days only)
daily_series = daily_series.join(rbob[['retail_estimate']], how='left')

# Add EIA actuals
daily_series = daily_series.join(eia_df, how='left')

# For non-trading days (weekends), forward fill RBOB
daily_series['retail_estimate'] = daily_series['retail_estimate'].fillna(method='ffill')

# Create final daily price: EIA if available, else RBOB estimate
daily_series['daily_price'] = daily_series['eia_retail'].fillna(daily_series['retail_estimate'])
daily_series['source'] = daily_series['eia_retail'].notna().map({True: 'EIA', False: 'RBOB'})

print(f"\n   Complete Daily Series:")
print(f"\n   {'Date':<12} {'Price':<10} {'Source':<10}")
print(f"   {'-'*35}")

for idx, row in daily_series.iterrows():
    print(f"   {idx.strftime('%Y-%m-%d'):<12} ${row['daily_price']:.3f}     {row['source']:<10}")

# Save to CSV
output_path = Path('/Users/denielnankov/Documents/kalshi/Gas/outputs/daily_prices_rbob_eia.csv')
output_path.parent.mkdir(parents=True, exist_ok=True)
daily_series.to_csv(output_path)

print(f"\n   💾 Saved to: {output_path}")

# ============================================================================
# 7. Summary
# ============================================================================
print(f"\n{'=' * 80}")
print("📊 SUMMARY")
print("=" * 80)

print(f"""
RBOB → Retail Conversion Results:

Conversion Formula: Retail = {best_formula}

Daily Price Coverage (Oct 18-27):
   • Trading days with RBOB: {len(rbob)} days
   • EIA actual validations: {len(eia_df)} days (weekly)
   • Weekend gaps: Filled with forward-fill
   • Total daily series: 10 days

Accuracy on EIA Actuals:
   • Mean Error: ${validation['abs_error_add'].mean():.4f} (additive)
   • Max Error: ${validation['abs_error_add'].max():.4f}
   • Within $0.05: {(validation['abs_error_add'] < 0.05).sum()}/{len(validation)}

Recommendation:
   ✅ Use RBOB-derived estimates for daily training/tracking
   ✅ Validate weekly against EIA actuals
   ✅ Document methodology in submission
   ✅ Acknowledge: "Daily estimates from RBOB futures + markup"

This approach gives you:
   ✓ Daily data for all 10 days (Oct 18-27)
   ✓ No web scraping required
   ✓ Based on actual market prices (RBOB futures)
   ✓ Validated against EIA weekly
   ✓ Transparent, replicable methodology
""")

print("=" * 80)
