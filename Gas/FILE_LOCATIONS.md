# Quick Reference: File Locations After Reorganization

## 📁 Data Ingestion Scripts
**Location:** `src/ingestion/`

### Bronze Layer Downloads:
```bash
python src/ingestion/download_rbob_data_bronze.py
python src/ingestion/download_retail_prices_bronze.py
python src/ingestion/download_eia_data_bronze.py
```

### Legacy Downloads (deprecated):
```bash
python src/ingestion/download_rbob_data.py
python src/ingestion/download_retail_prices.py
python src/ingestion/download_eia_data.py
python src/ingestion/download_padd3_data.py
```

### API Client:
```python
from src.ingestion.eia_client import EIAClient
```

---

## 📁 Processing Scripts
**Location:** `scripts/`

### Silver Layer (Cleaning):
```bash
python scripts/clean_rbob_to_silver.py
python scripts/clean_retail_to_silver.py
python scripts/clean_eia_to_silver.py
```

### Gold Layer (Features):
```bash
python scripts/build_gold_layer.py
```

---

## 📁 Model Scripts
**Location:** `scripts/`

### Training:
```bash
python scripts/train_models.py
python scripts/train_quantile_models.py
```

### Validation:
```bash
python scripts/walk_forward_validation.py
python scripts/validate_silver_layer.py
python scripts/validate_gold_layer.py
```

---

## 📁 Pipeline Orchestration
**Location:** `scripts/`

### Full Pipeline:
```bash
python scripts/run_medallion_pipeline.py  # Uses src/ingestion/ automatically
```

This script now automatically finds download scripts in `src/ingestion/`.

---

## 📁 Visualization
**Location:** `scripts/`

```bash
python scripts/visualize_*.py
```

---

## 🔄 Migration Path

**Old Command:**
```bash
python scripts/download_rbob_data_bronze.py
```

**New Command:**
```bash
python src/ingestion/download_rbob_data_bronze.py
```

**Pipeline (no change):**
```bash
python scripts/run_medallion_pipeline.py  # Automatically updated
```

---

## ✅ Verification

All files successfully moved:
- ✅ 8 download scripts in `src/ingestion/`
- ✅ `eia_client.py` in `src/ingestion/`
- ✅ `__init__.py` created for module
- ✅ Pipeline updated to find new locations
- ✅ No files left in old location

**Status:** 🟢 COMPLETE
