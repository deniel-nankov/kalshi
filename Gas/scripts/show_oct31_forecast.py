#!/usr/bin/env python3
"""
Display the October 31 forecast in a nice format
"""

import json
from pathlib import Path

# Read the prediction
prediction_file = Path(__file__).parent.parent / 'outputs' / 'final_validation' / 'oct31_prediction.json'

with open(prediction_file, 'r') as f:
    pred = json.load(f)

# Display
print("=" * 70)
print(" " * 15 + "OCTOBER 31, 2025 GAS PRICE FORECAST")
print("=" * 70)
print()
print(f"  Prediction Date: {pred['prediction_date']}")
print(f"  Target Date:     {pred['target_date']}")
print()
print(f"  {'FORECAST:':<20} ${pred['prediction']:.3f} per gallon")
print()
print(f"  95% Confidence Interval:")
print(f"    Lower Bound:   ${pred['lower_95ci']:.3f}")
print(f"    Upper Bound:   ${pred['upper_95ci']:.3f}")
print(f"    Width:         ${pred['upper_95ci'] - pred['lower_95ci']:.3f} ({((pred['upper_95ci'] - pred['lower_95ci'])/pred['prediction']*100):.2f}%)")
print()
print(f"  Model Performance:")
print(f"    Training R²:         {pred['training_r2']:.6f}")
print(f"    Training Samples:    {pred['training_samples']:,}")
print(f"    Features:            {pred['features']}")
print(f"    Recent MAE:          ${pred['recent_mae']:.4f}")
print(f"    Recent Std Dev:      ${pred['recent_std']:.4f}")
print()
print(f"  Model: {pred['model']}")
print()
print("=" * 70)
print()
print(f"📊 Summary: ${pred['prediction']:.3f} (95% CI: ${pred['lower_95ci']:.3f} - ${pred['upper_95ci']:.3f})")
print()
print("=" * 70)
