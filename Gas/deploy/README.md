# Deployment Instructions

This directory contains scripts for deploying the regime-specific gasoline price forecasting system.

## Workflow
1. Build Gold layer: `python scripts/build_gold_layer.py`
2. Train and save regime models: `python deploy/train_and_save_models.py`
3. Predict: `python deploy/predict.py --input <input.csv>`

## Files
- `train_and_save_models.py`: Trains and saves regime-specific models.
- `predict.py`: Loads models and predicts for new data.

## Requirements
- Python 3.8+
- pandas, numpy, scikit-learn, joblib

## Example
```
python scripts/build_gold_layer.py
python deploy/train_and_save_models.py
python deploy/predict.py --input new_data.csv
```
