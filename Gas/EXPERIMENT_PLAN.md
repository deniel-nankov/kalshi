# Safe Experimentation Plan - Neural Networks & Optuna

**Date:** October 19, 2025  
**Goal:** Test new models WITHOUT breaking existing results  
**Time Budget:** 4-6 hours total

---

## 🔒 SAFETY GUARANTEES

### **What WON'T Change:**
- ✅ Your existing Ridge results (R²=0.931) - **SAFE**
- ✅ Your existing GB results - **SAFE**
- ✅ October 2025 predictions - **SAFE**
- ✅ Walk-forward validation results - **SAFE**
- ✅ All existing output files - **SAFE**

### **What WILL Change:**
- ✅ **NEW** Optuna-tuned models (saved separately)
- ✅ **NEW** Neural network results (in separate folder)
- ✅ **NEW** comparison plots (Ridge vs GB vs LSTM)

---

## 📊 EXPERIMENT 1: Optuna Hyperparameter Tuning

**Time:** 2-3 hours  
**Risk:** ⚡ LOW (won't break anything)  
**Expected:** R² +0.02-0.05 (small improvement)

### **What We'll Do:**

1. **Install Optuna** (30 seconds)
   ```bash
   pip install optuna
   ```

2. **Create new script:** `scripts/tune_with_optuna.py`
   - Tunes Ridge regression
   - Tunes Gradient Boosting
   - Saves to: `outputs/optuna/` (NEW folder!)

3. **Compare results:**
   - GridSearchCV (old) vs Optuna (new)
   - See if Optuna finds better hyperparameters

### **Output Files (NEW, won't overwrite!):**
- `outputs/optuna/optuna_best_params.json`
- `outputs/optuna/optuna_vs_grid_comparison.csv`
- `outputs/optuna/optimization_history.png`

### **Will Optuna Change Performance?**

**Realistic expectations:**

| Model | Current (GridSearchCV) | Expected (Optuna) | Change |
|-------|----------------------|-------------------|--------|
| Ridge | R²=0.931 | R²=0.935-0.950 | +0.004-0.019 |
| GB | R²=-1.113 | R²=-0.8 to +0.2 | +0.3-1.3 (still bad!) |

**Why small change?**
- Ridge is already near-optimal (hard to improve perfection!)
- GB overfits regardless of hyperparameters (data issue, not tuning issue)
- Optuna is "smarter" but can't work miracles

**Worth it?**
- ✅ YES - Only 2-3 hours
- ✅ Might squeeze out 1-2% more accuracy
- ✅ Good to mention in paper ("We used advanced Bayesian optimization")
- ✅ No risk (keeps existing results)

---

## 🧠 EXPERIMENT 2: Neural Network (LSTM) Test

**Time:** 3-4 hours  
**Risk:** ⚡ LOW (separate folder, won't touch existing files)  
**Expected:** Unknown! (R² could be -10 to +0.95)

### **What We'll Do:**

1. **Install TensorFlow** (2-3 minutes)
   ```bash
   pip install tensorflow
   ```

2. **Create new script:** `scripts/test_neural_network.py`
   - Builds simple LSTM model
   - Trains on same data as Ridge/GB
   - Tests on same walk-forward folds (2021-2024)
   - **Completely separate from existing scripts!**

3. **Compare 3 models:**
   - Ridge (existing results)
   - GB (existing results)
   - LSTM (NEW results)

### **Output Files (NEW folder!):**
- `outputs/neural_network_test/lstm_results.csv`
- `outputs/neural_network_test/model_comparison.png`
- `outputs/neural_network_test/ridge_vs_gb_vs_lstm.csv`
- `outputs/neural_network_test/lstm_training_history.png`

### **Architecture (Simple LSTM):**

```python
model = Sequential([
    LSTM(64, input_shape=(lookback, features)),
    Dropout(0.2),
    Dense(32, activation='relu'),
    Dense(1)  # Gas price prediction
])
```

**Why this architecture?**
- ✅ Simple (not too complex for 1,819 samples)
- ✅ Fast to train (30-60 minutes)
- ✅ Industry standard for time series

### **Will LSTM Beat Ridge?**

**Honest prediction:**

| Scenario | Probability | Expected R² | Reason |
|----------|------------|-------------|--------|
| **LSTM wins** | 30% | R²=0.85-0.95 | Captures temporal patterns Ridge misses |
| **Ridge wins** | 50% | R²=0.60-0.85 | LSTM overfits with limited data |
| **LSTM fails badly** | 20% | R²<0.50 | Not enough data (need 5,000+ samples) |

**Most likely outcome:**
- LSTM performs **slightly worse** than Ridge (R²=0.70-0.85)
- Ridge remains champion (R²=0.931)
- But LSTM might excel in specific periods (e.g., during hurricanes)

**Why might LSTM struggle?**
1. ❌ **Limited data:** 1,819 samples (LSTMs need 5,000+)
2. ❌ **Sparse sentiment:** Only 18.6% coverage
3. ❌ **Ridge already optimal:** Hard to beat 0.931!

**Why might LSTM win?**
1. ✅ **Temporal patterns:** Captures sequences Ridge can't
2. ✅ **Non-linear interactions:** Hurricane + inventory + sentiment
3. ✅ **Attention to recent data:** Weighs recent prices more

---

## 🗺️ STEP-BY-STEP EXECUTION PLAN

### **Phase 1: Optuna (2-3 hours)**

**Step 1:** Install Optuna (1 minute)
```bash
pip install optuna
```

**Step 2:** Create tuning script (30 minutes)
- Copy `tune_gradient_boosting.py` → `tune_with_optuna.py`
- Replace GridSearchCV with Optuna
- Add visualization of optimization history

**Step 3:** Run optimization (1-2 hours)
```bash
python scripts/tune_with_optuna.py
```

**Step 4:** Compare results (30 minutes)
- GridSearchCV best params vs Optuna best params
- R² comparison
- Create comparison plot

---

### **Phase 2: Neural Network (3-4 hours)**

**Step 1:** Install TensorFlow (2-3 minutes)
```bash
pip install tensorflow
```

**Step 2:** Create LSTM script (1 hour)
- Load Gold layer data
- Reshape for sequences (lookback=14 days)
- Build LSTM model
- Train with early stopping

**Step 3:** Run walk-forward validation (1-2 hours)
```bash
python scripts/test_neural_network.py
```

**Step 4:** Compare with Ridge/GB (30 minutes)
- Load existing Ridge/GB results
- Create 3-way comparison plot
- Generate comparison table

---

## 📊 COMPARISON OUTPUTS

### **Final Comparison Table:**

| Model | Method | 1-Day R² | 2-Day R² | 3-Day R² | Avg R² | Training Time |
|-------|--------|---------|---------|---------|--------|---------------|
| Ridge | GridSearchCV | 0.931 | 0.884 | 0.726 | 0.847 | 5 min |
| Ridge | Optuna | 0.935 | 0.890 | 0.735 | 0.853 | 2 hours |
| GB | GridSearchCV | -0.542 | -0.891 | -1.923 | -1.119 | 10 min |
| GB | Optuna | -0.123 | -0.456 | -0.987 | -0.522 | 3 hours |
| LSTM | Default | 0.756 | 0.689 | 0.523 | 0.656 | 1 hour |

*(Actual numbers TBD after running experiments)*

### **Visualization Plan:**

**Plot 1:** `optuna_vs_grid_ridge.png`
- X-axis: Optimization trials
- Y-axis: R² score
- Shows Optuna finding better hyperparameters

**Plot 2:** `three_model_comparison.png`
- Bar chart: Ridge vs GB vs LSTM
- Group by horizon (1-day, 2-day, 3-day)
- Color-coded by model

**Plot 3:** `lstm_training_history.png`
- Training loss vs validation loss
- Shows if LSTM is overfitting

---

## ⚠️ RISK MITIGATION

### **What if LSTM breaks something?**

**Protection:**
- ✅ All LSTM code in separate file (`test_neural_network.py`)
- ✅ All LSTM outputs in separate folder (`outputs/neural_network_test/`)
- ✅ No modification to existing scripts
- ✅ No modification to existing data files

**If LSTM fails:**
- ❌ Delete `outputs/neural_network_test/` folder
- ❌ Delete `scripts/test_neural_network.py`
- ✅ Everything else still works!

### **What if Optuna breaks something?**

**Protection:**
- ✅ All Optuna code in separate file (`tune_with_optuna.py`)
- ✅ All Optuna outputs in separate folder (`outputs/optuna/`)
- ✅ Original `tune_gradient_boosting.py` unchanged
- ✅ Original model results unchanged

**If Optuna fails:**
- ❌ Delete `outputs/optuna/` folder
- ❌ Delete `scripts/tune_with_optuna.py`
- ✅ Everything else still works!

---

## ✅ SAFETY CHECKLIST

Before starting experiments:

- [x] ✅ All existing work committed to Git (DONE - commit 972d16b)
- [x] ✅ All existing work pushed to GitHub (DONE)
- [ ] ✅ Create backup of `data/gold/` folder (optional but recommended)
- [ ] ✅ Create backup of `outputs/` folder (optional but recommended)

After each experiment:

- [ ] ✅ Verify existing Ridge results unchanged
- [ ] ✅ Verify existing GB results unchanged
- [ ] ✅ Verify October 2025 predictions unchanged
- [ ] ✅ Commit new experiment results separately

---

## 🎯 DECISION TREE

### **Should you run Optuna?**

```
Do you have 2-3 hours? 
  YES → Run Optuna (low risk, might help)
  NO → Skip it (Ridge already great)
```

### **Should you run LSTM?**

```
Do you have 3-4 hours?
  YES → Do you want to learn about neural networks?
    YES → Run LSTM (educational value)
    NO → Are you curious if it beats Ridge?
      YES → Run LSTM (satisfies curiosity)
      NO → Skip it (focus on paper)
  NO → Skip it (focus on paper)
```

---

## 📝 MY RECOMMENDATION

**Given your October 30th deadline (11 days away):**

### **PRIORITY 1: Write Your Paper (Oct 19-28)** ✅ CRITICAL
- You already have AMAZING results (R²=0.931)
- This is what gets you the grade!
- Time needed: 7-8 days

### **PRIORITY 2: Try Optuna (Oct 29, 2-3 hours)** 🟡 OPTIONAL
- Only if you finish paper early
- Low risk, might improve R² by 1-2%
- Good thing to mention in paper

### **PRIORITY 3: Try LSTM (After Oct 30)** 🟢 FUTURE
- Educational value, not grade value
- Save for future research project
- Could be a follow-up paper!

---

## 🚀 QUICK START COMMANDS

### **Option A: Try Optuna (Safe, 2-3 hours)**

```bash
# Install
pip install optuna

# Create script (I'll help you)
# Run optimization
python scripts/tune_with_optuna.py

# Compare results
python scripts/compare_optuna_vs_grid.py
```

### **Option B: Try LSTM (Safe, 3-4 hours)**

```bash
# Install
pip install tensorflow

# Create script (I'll help you)
# Run experiment
python scripts/test_neural_network.py

# Compare with Ridge/GB
python scripts/compare_all_models.py
```

### **Option C: Do Both (Safe, 5-6 hours)**

```bash
# Do Optuna first (easier)
# Then do LSTM (harder)
# Compare all 4 approaches:
#   1. Ridge (GridSearchCV) - Current champion
#   2. Ridge (Optuna) - New challenger
#   3. GB (Optuna) - Improved but still bad
#   4. LSTM - Wild card
```

---

## ✅ FINAL ANSWER TO YOUR QUESTIONS

### **Q1: Will Optuna change our performance?**

**A:** YES, but only slightly
- Ridge: +0.004-0.019 R² (from 0.931 → 0.935-0.950)
- GB: +0.3-1.3 R² (from -1.113 → -0.8 to +0.2, still bad!)
- **Worth trying:** Low risk, takes 2-3 hours, might help

### **Q2: Can we test neural networks without messing with other outputs?**

**A:** YES! Absolutely safe!
- ✅ New script: `test_neural_network.py`
- ✅ New folder: `outputs/neural_network_test/`
- ✅ No changes to existing Ridge/GB results
- ✅ No changes to October 2025 predictions
- ✅ Perfect for comparison (Ridge vs GB vs LSTM)

**If you want to try both, I can help you create the scripts right now!** 

Which would you like to start with?
1. **Optuna** (easier, 2-3 hours)
2. **LSTM** (harder, 3-4 hours)
3. **Both** (5-6 hours total)
4. **Neither** (focus on writing paper)

Let me know! 🚀
