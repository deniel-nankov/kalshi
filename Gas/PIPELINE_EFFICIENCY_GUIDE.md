# Pipeline Efficiency Guide

## 🚀 The Problem

**Current:** `run_medallion_pipeline.py` **ALWAYS rebuilds everything**

```bash
python scripts/run_medallion_pipeline.py
```

This runs:
1. ✅ Download Bronze (30+ seconds - API calls)
2. ✅ Clean to Silver (5 seconds)
3. ✅ Build Gold (10 seconds)

**Total: ~45 seconds every time, even if nothing changed!**

---

## ⚡ The Solution: Smart Updates

**New:** `update_pipeline.py` **only rebuilds what's stale**

```bash
python scripts/update_pipeline.py  # Smart mode (default)
```

This checks modification times and only rebuilds stale layers.

### Example Scenarios:

#### Scenario 1: All data is fresh (< 24 hours old)
```bash
$ python scripts/update_pipeline.py

Status check:
  📦 Bronze: ✅ FRESH
  🪙 Silver: ✅ FRESH
  ⭐ Gold:   ✅ FRESH

✅ All layers are up-to-date! Nothing to do.
```
**Time: < 1 second** 🎉

#### Scenario 2: Bronze is stale (new day)
```bash
$ python scripts/update_pipeline.py

Status check:
  📦 Bronze: 🔴 STALE (28 hours old)
  🪙 Silver: 🔴 STALE (depends on Bronze)
  ⭐ Gold:   🔴 STALE (depends on Silver)

📥 UPDATING BRONZE LAYER...
🧹 UPDATING SILVER LAYER...
⭐ UPDATING GOLD LAYER...

✅ SMART UPDATE COMPLETE!
```
**Time: ~45 seconds** (same as full rebuild, but only when needed)

#### Scenario 3: Just changed feature engineering
```bash
$ python scripts/update_pipeline.py --gold-only

⭐ GOLD LAYER REBUILD

Rebuilding Gold layer from existing Silver data...
✅ GOLD REBUILD COMPLETE!
```
**Time: ~10 seconds** 🚀 (skips Bronze/Silver downloads)

---

## 📋 Command Reference

### Smart Update (Recommended)
```bash
# Check what's stale and update only what's needed
python scripts/update_pipeline.py

# Custom max age (default is 24 hours)
python scripts/update_pipeline.py --max-age 6  # 6 hours
```

### Gold Only (Feature Engineering Changes)
```bash
# You changed build_gold_layer.py? Just rebuild Gold:
python scripts/update_pipeline.py --gold-only
```
**Use when:**
- Changed feature engineering logic
- Added/removed features
- Fixed bugs in Gold layer
- Want to test feature changes quickly

### Silver + Bronze (Data Updates)
```bash
# Update data but skip Gold
python scripts/update_pipeline.py --silver
```
**Use when:**
- Want fresh data
- Don't need to retrain models yet
- Testing Silver layer cleaning

### Full Rebuild (Nuclear Option)
```bash
# Rebuild everything from scratch
python scripts/update_pipeline.py --full
```
**Use when:**
- First time setup
- Something is corrupted
- Want to ensure clean state
- Same as old `run_medallion_pipeline.py`

---

## ⏱️ Time Savings

### Typical Development Workflow

**Before (always full rebuild):**
```bash
# Change feature in build_gold_layer.py
python scripts/run_medallion_pipeline.py  # 45 seconds
# Make another change
python scripts/run_medallion_pipeline.py  # 45 seconds
# Fix a bug
python scripts/run_medallion_pipeline.py  # 45 seconds

Total: 135 seconds for 3 iterations
```

**After (smart updates):**
```bash
# Change feature in build_gold_layer.py
python scripts/update_pipeline.py --gold-only  # 10 seconds
# Make another change
python scripts/update_pipeline.py --gold-only  # 10 seconds
# Fix a bug
python scripts/update_pipeline.py --gold-only  # 10 seconds

Total: 30 seconds for 3 iterations
```

**Savings: 105 seconds (70% faster!)** 🚀

---

## 🧠 How Smart Mode Works

```python
# Smart mode checks:
1. Does layer exist?
2. Is layer older than max_age (default 24 hours)?
3. Is source layer newer than target layer?

If ANY is true → REBUILD
If ALL are false → SKIP ✅
```

### Example Decision Tree:

```
Bronze exists & < 24 hours old?
  └─ YES → ✅ Skip Bronze download
      │
      Silver exists & newer than Bronze?
        └─ YES → ✅ Skip Silver cleaning
            │
            Gold exists & newer than Silver?
              └─ YES → ✅ Skip Gold build
                  │
                  ✅ Nothing to do!
```

---

## 🎯 When to Use Each Mode

### Daily Data Updates
```bash
# Morning: Get fresh data
python scripts/update_pipeline.py  # Smart update

# If data is fresh, takes < 1 second
# If data is stale, rebuilds automatically
```

### Feature Engineering Iteration
```bash
# Edit build_gold_layer.py
python scripts/update_pipeline.py --gold-only  # 10 seconds

# Test
python scripts/train_models.py

# Iterate...
```

### First Time / Clean Slate
```bash
# Initial setup
python scripts/update_pipeline.py --full  # 45 seconds
```

### Debugging Silver Layer
```bash
# Edit clean_*_to_silver.py
python scripts/update_pipeline.py --silver  # 35 seconds

# Validate
python scripts/validate_silver_layer.py
```

---

## 🔄 Migration from Old Pipeline

### Old Way:
```bash
python scripts/run_medallion_pipeline.py  # Always 45 seconds
```

### New Way (Equivalent):
```bash
python scripts/update_pipeline.py --full  # Same behavior
```

### New Way (Better):
```bash
python scripts/update_pipeline.py  # Only rebuilds what's stale
```

**Recommendation:** 
- Keep `run_medallion_pipeline.py` for documentation/compatibility
- Use `update_pipeline.py` for daily development

---

## 📊 Performance Comparison

| Operation | Old Pipeline | New Pipeline | Savings |
|-----------|--------------|--------------|---------|
| **Fresh data (nothing changed)** | 45s | <1s | 98% |
| **Gold layer change** | 45s | 10s | 78% |
| **Silver layer change** | 45s | 35s | 22% |
| **Full rebuild** | 45s | 45s | 0% |

---

## 🛠️ Advanced Usage

### Custom Max Age
```bash
# Update if older than 6 hours
python scripts/update_pipeline.py --max-age 6

# Update if older than 1 hour
python scripts/update_pipeline.py --max-age 1

# Always rebuild (force)
python scripts/update_pipeline.py --max-age 0
```

### Cron Job (Daily Updates)
```bash
# Add to crontab for daily 8am updates
0 8 * * * cd /path/to/Gas && python scripts/update_pipeline.py

# Only updates if data is stale, otherwise exits immediately
```

---

## ✅ Quick Start

**Replace this habit:**
```bash
python scripts/run_medallion_pipeline.py
```

**With this:**
```bash
python scripts/update_pipeline.py
```

**Or for feature work:**
```bash
# After editing build_gold_layer.py
python scripts/update_pipeline.py --gold-only
```

---

## 📝 Summary

✅ **Smart mode** checks timestamps and only rebuilds what's stale  
✅ **Gold-only mode** rebuilds just Gold layer (10 seconds vs 45)  
✅ **Silver mode** updates data without feature engineering  
✅ **Full mode** same as old pipeline (compatibility)  

**Result:** 70-98% faster development iteration! 🚀
