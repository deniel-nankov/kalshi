"""
Hyperparameter Tuning with Optuna (Bayesian Optimization)

This script uses Optuna to find optimal hyperparameters for Ridge and Gradient Boosting.
Optuna is smarter than GridSearchCV - it learns from previous trials to search more efficiently.

Results are saved separately from existing GridSearchCV results - completely safe!
"""

import pandas as pd
import numpy as np
import optuna
from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import json
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Output directory
OUTPUT_DIR = Path('outputs/optuna')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("="*80)
print("🎯 OPTUNA HYPERPARAMETER TUNING")
print("="*80)
print("Comparing GridSearchCV (old) vs Optuna (new)")
print(f"Results will be saved to: {OUTPUT_DIR}")
print("="*80)

# Load data
print("\n📊 Loading Gold layer data...")
df = pd.read_parquet('data/gold/master_model_ready.parquet')
print(f"Loaded {len(df):,} rows × {len(df.columns)} columns")

# Prepare features - exclude non-numeric columns
exclude_cols = ['date', 'target', 'target_date', 'hurricane_name', 'refinery_impact_level']
feature_cols = [col for col in df.columns if col not in exclude_cols]
X = df[feature_cols].fillna(0)
y = df['target']

print(f"\n✅ Features: {len(feature_cols)}")
print(f"✅ Samples: {len(X):,}")
print(f"✅ Excluded categorical columns: hurricane_name, refinery_impact_level")

# Time series cross-validation
tscv = TimeSeriesSplit(n_splits=5)

print("\n" + "="*80)
print("1️⃣  RIDGE REGRESSION OPTIMIZATION")
print("="*80)

def ridge_objective(trial):
    """Objective function for Ridge regression"""
    # Suggest hyperparameters
    alpha = trial.suggest_float('alpha', 0.001, 100.0, log=True)
    
    # Create model
    model = Ridge(alpha=alpha, random_state=42)
    
    # Cross-validation score
    scores = cross_val_score(model, X, y, cv=tscv, scoring='r2', n_jobs=-1)
    
    return scores.mean()

# Create study
print("\n🔍 Optimizing Ridge hyperparameters...")
print("This will try 50 different combinations (smarter than GridSearchCV!)")

ridge_study = optuna.create_study(
    direction='maximize',
    study_name='ridge_optimization',
    sampler=optuna.samplers.TPESampler(seed=42)
)

# Run optimization
ridge_study.optimize(ridge_objective, n_trials=50, show_progress_bar=True)

# Best parameters
ridge_best = ridge_study.best_params
ridge_best_score = ridge_study.best_value

print(f"\n✅ Best Ridge alpha: {ridge_best['alpha']:.6f}")
print(f"✅ Best Ridge R²: {ridge_best_score:.4f}")

# Compare with GridSearchCV defaults
print("\n📊 Comparison with GridSearchCV:")
print(f"   GridSearchCV used: alpha=1.0")
print(f"   Optuna found: alpha={ridge_best['alpha']:.6f}")
print(f"   Improvement: {(ridge_best_score - 0.931)*100:.2f} percentage points")

print("\n" + "="*80)
print("2️⃣  GRADIENT BOOSTING OPTIMIZATION")
print("="*80)

def gb_objective(trial):
    """Objective function for Gradient Boosting"""
    # Suggest hyperparameters (wider range than GridSearchCV!)
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 50, 500),
        'learning_rate': trial.suggest_float('learning_rate', 0.001, 0.3, log=True),
        'max_depth': trial.suggest_int('max_depth', 2, 10),
        'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
        'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', None]),
        'random_state': 42
    }
    
    # Create model
    model = GradientBoostingRegressor(**params)
    
    # Cross-validation score
    scores = cross_val_score(model, X, y, cv=tscv, scoring='r2', n_jobs=-1)
    
    return scores.mean()

# Create study
print("\n🔍 Optimizing Gradient Boosting hyperparameters...")
print("This will try 100 different combinations (way more than GridSearchCV!)")

gb_study = optuna.create_study(
    direction='maximize',
    study_name='gb_optimization',
    sampler=optuna.samplers.TPESampler(seed=42)
)

# Run optimization (more trials for complex model)
gb_study.optimize(gb_objective, n_trials=100, show_progress_bar=True)

# Best parameters
gb_best = gb_study.best_params
gb_best_score = gb_study.best_value

print(f"\n✅ Best GB parameters:")
for key, value in gb_best.items():
    print(f"   {key}: {value}")
print(f"\n✅ Best GB R²: {gb_best_score:.4f}")

# Compare with GridSearchCV
print("\n📊 Comparison with GridSearchCV:")
print(f"   GridSearchCV R²: -1.113 (failed!)")
print(f"   Optuna R²: {gb_best_score:.4f}")
print(f"   Improvement: {(gb_best_score - (-1.113))*100:.2f} percentage points!")

print("\n" + "="*80)
print("3️⃣  SAVING RESULTS")
print("="*80)

# Save best parameters
best_params = {
    'ridge': {
        'alpha': float(ridge_best['alpha']),
        'best_r2': float(ridge_best_score)
    },
    'gradient_boosting': {
        **{k: (float(v) if isinstance(v, (int, float)) else v) for k, v in gb_best.items()},
        'best_r2': float(gb_best_score)
    }
}

with open(OUTPUT_DIR / 'optuna_best_params.json', 'w') as f:
    json.dump(best_params, f, indent=2)

print(f"✅ Saved best parameters to: {OUTPUT_DIR / 'optuna_best_params.json'}")

# Create comparison table
comparison = pd.DataFrame({
    'Model': ['Ridge', 'Ridge', 'GB', 'GB'],
    'Method': ['GridSearchCV', 'Optuna', 'GridSearchCV', 'Optuna'],
    'R² Score': [0.931, ridge_best_score, -1.113, gb_best_score],
    'Alpha/Learning Rate': [1.0, ridge_best['alpha'], 0.1, gb_best['learning_rate']]
})

comparison.to_csv(OUTPUT_DIR / 'optuna_vs_grid_comparison.csv', index=False)
print(f"✅ Saved comparison to: {OUTPUT_DIR / 'optuna_vs_grid_comparison.csv'}")

print("\n" + "="*80)
print("4️⃣  CREATING VISUALIZATIONS")
print("="*80)

# Plot 1: Optimization history (Ridge)
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Ridge optimization history
ax = axes[0]
ridge_trials = ridge_study.trials_dataframe()
ax.plot(ridge_trials['number'], ridge_trials['value'], 'o-', alpha=0.6)
ax.axhline(y=ridge_best_score, color='r', linestyle='--', label=f'Best: {ridge_best_score:.4f}')
ax.axhline(y=0.931, color='g', linestyle='--', label='GridSearchCV: 0.931')
ax.set_xlabel('Trial Number')
ax.set_ylabel('R² Score')
ax.set_title('Ridge Optimization History')
ax.legend()
ax.grid(True, alpha=0.3)

# GB optimization history
ax = axes[1]
gb_trials = gb_study.trials_dataframe()
ax.plot(gb_trials['number'], gb_trials['value'], 'o-', alpha=0.6, color='orange')
ax.axhline(y=gb_best_score, color='r', linestyle='--', label=f'Best: {gb_best_score:.4f}')
ax.axhline(y=-1.113, color='g', linestyle='--', label='GridSearchCV: -1.113')
ax.set_xlabel('Trial Number')
ax.set_ylabel('R² Score')
ax.set_title('Gradient Boosting Optimization History')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'optimization_history.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved optimization history to: {OUTPUT_DIR / 'optimization_history.png'}")

# Plot 2: Method comparison
fig, ax = plt.subplots(figsize=(10, 6))

methods = ['Ridge\n(GridSearchCV)', 'Ridge\n(Optuna)', 'GB\n(GridSearchCV)', 'GB\n(Optuna)']
scores = [0.931, ridge_best_score, -1.113, gb_best_score]
colors = ['#2ecc71', '#27ae60', '#e74c3c', '#e67e22']

bars = ax.bar(methods, scores, color=colors, alpha=0.7, edgecolor='black')

# Add value labels on bars
for bar, score in zip(bars, scores):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{score:.3f}',
            ha='center', va='bottom' if score > 0 else 'top',
            fontsize=12, fontweight='bold')

ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax.set_ylabel('R² Score', fontsize=12)
ax.set_title('GridSearchCV vs Optuna: Model Performance', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')
ax.set_ylim(-2, 1.0)

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'method_comparison.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved method comparison to: {OUTPUT_DIR / 'method_comparison.png'}")

# Plot 3: Parameter importance (Ridge)
fig, ax = plt.subplots(figsize=(8, 5))
ridge_importance = optuna.importance.get_param_importances(ridge_study)
params = list(ridge_importance.keys())
importances = list(ridge_importance.values())

ax.barh(params, importances, color='#3498db', alpha=0.7)
ax.set_xlabel('Importance')
ax.set_title('Ridge: Parameter Importance')
ax.grid(True, alpha=0.3, axis='x')

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'ridge_param_importance.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved Ridge parameter importance to: {OUTPUT_DIR / 'ridge_param_importance.png'}")

# Plot 4: Parameter importance (GB)
fig, ax = plt.subplots(figsize=(10, 6))
gb_importance = optuna.importance.get_param_importances(gb_study)
params = list(gb_importance.keys())
importances = list(gb_importance.values())

ax.barh(params, importances, color='#e67e22', alpha=0.7)
ax.set_xlabel('Importance')
ax.set_title('Gradient Boosting: Parameter Importance')
ax.grid(True, alpha=0.3, axis='x')

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'gb_param_importance.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved GB parameter importance to: {OUTPUT_DIR / 'gb_param_importance.png'}")

print("\n" + "="*80)
print("5️⃣  TRAIN FINAL MODELS WITH BEST PARAMETERS")
print("="*80)

# Train Ridge with best params
print("\n🔧 Training Ridge with Optuna parameters...")
ridge_optuna = Ridge(alpha=ridge_best['alpha'], random_state=42)
ridge_optuna.fit(X, y)

# Train GB with best params
print("🔧 Training GB with Optuna parameters...")
gb_optuna = GradientBoostingRegressor(**gb_best)
gb_optuna.fit(X, y)

# Evaluate on full dataset (for comparison)
ridge_pred = ridge_optuna.predict(X)
gb_pred = gb_optuna.predict(X)

ridge_r2 = r2_score(y, ridge_pred)
ridge_mae = mean_absolute_error(y, ridge_pred)

gb_r2 = r2_score(y, gb_pred)
gb_mae = mean_absolute_error(y, gb_pred)

print(f"\n✅ Ridge (Optuna) - Training R²: {ridge_r2:.4f}, MAE: ${ridge_mae:.4f}")
print(f"✅ GB (Optuna) - Training R²: {gb_r2:.4f}, MAE: ${gb_mae:.4f}")

# Save final metrics
final_metrics = {
    'ridge_optuna': {
        'training_r2': float(ridge_r2),
        'training_mae': float(ridge_mae),
        'cv_r2': float(ridge_best_score)
    },
    'gb_optuna': {
        'training_r2': float(gb_r2),
        'training_mae': float(gb_mae),
        'cv_r2': float(gb_best_score)
    }
}

with open(OUTPUT_DIR / 'optuna_final_metrics.json', 'w') as f:
    json.dump(final_metrics, f, indent=2)

print(f"\n✅ Saved final metrics to: {OUTPUT_DIR / 'optuna_final_metrics.json'}")

print("\n" + "="*80)
print("✅ OPTUNA OPTIMIZATION COMPLETE!")
print("="*80)

print("\n📊 SUMMARY:")
print(f"\n🏆 Ridge Regression:")
print(f"   GridSearchCV: R²=0.931, alpha=1.0")
print(f"   Optuna:       R²={ridge_best_score:.4f}, alpha={ridge_best['alpha']:.6f}")
print(f"   Change:       {((ridge_best_score/0.931 - 1)*100):+.2f}%")

print(f"\n🏆 Gradient Boosting:")
print(f"   GridSearchCV: R²=-1.113 (failed!)")
print(f"   Optuna:       R²={gb_best_score:.4f}")
print(f"   Improvement:  {(gb_best_score - (-1.113)):.3f} R² points!")

print(f"\n📁 All results saved to: {OUTPUT_DIR}")
print(f"   ✅ Best parameters: optuna_best_params.json")
print(f"   ✅ Comparison table: optuna_vs_grid_comparison.csv")
print(f"   ✅ Visualizations: 4 PNG files")

print("\n" + "="*80)
print("🎯 NEXT STEPS:")
print("="*80)
print("1. Review the optimization_history.png to see how Optuna searched")
print("2. Check method_comparison.png to see the improvements")
print("3. Decide: Use Optuna parameters for your final model?")
print("4. Ready for Option 2: Neural Networks! 🧠")
print("="*80)
