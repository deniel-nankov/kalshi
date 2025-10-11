import sys
from pathlib import Path

import pandas as pd
import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.append(str(SCRIPTS_DIR))

import validate_silver_layer as vs  # noqa: E402
import validate_gold_layer as vg  # noqa: E402


def _write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def test_validate_silver_layer_success(tmp_path, monkeypatch, capsys):
    silver_dir = tmp_path / "silver"
    silver_dir.mkdir()

    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    rbob_df = pd.DataFrame({"date": dates, "price_rbob": 1.9, "volume_rbob": 1000})
    _write_parquet(rbob_df, silver_dir / "rbob_daily.parquet")

    wti_df = pd.DataFrame({"date": dates, "price_wti": 70.0})
    _write_parquet(wti_df, silver_dir / "wti_daily.parquet")

    retail_df = pd.DataFrame({"date": dates, "retail_price": 2.5})
    _write_parquet(retail_df, silver_dir / "retail_prices_daily.parquet")

    weekly_dates = pd.to_datetime(["2024-01-03", "2024-01-10"])
    inventory_df = pd.DataFrame({"date": weekly_dates, "inventory_mbbl": [230.0, 231.0]})
    _write_parquet(inventory_df, silver_dir / "eia_inventory_weekly.parquet")

    utilization_df = pd.DataFrame({"date": weekly_dates, "utilization_pct": [85.0, 86.0]})
    _write_parquet(utilization_df, silver_dir / "eia_utilization_weekly.parquet")

    imports_df = pd.DataFrame({"date": weekly_dates, "net_imports_kbd": [500.0, 520.0]})
    _write_parquet(imports_df, silver_dir / "eia_imports_weekly.parquet")

    padd3_df = pd.DataFrame({"date": weekly_dates, "padd3_share": [35.0, 36.0]})
    _write_parquet(padd3_df, silver_dir / "padd3_share_weekly.parquet")

    monkeypatch.setattr(vs, "SILVER_DIR", silver_dir)

    assert vs.validate_silver_layer() is True
    captured = capsys.readouterr()
    assert "✓" in captured.out


def test_validate_silver_layer_missing_file(tmp_path, monkeypatch, capsys):
    silver_dir = tmp_path / "silver"
    silver_dir.mkdir()

    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    rbob_df = pd.DataFrame({"date": dates, "price_rbob": 1.9, "volume_rbob": 900})
    _write_parquet(rbob_df, silver_dir / "rbob_daily.parquet")

    monkeypatch.setattr(vs, "SILVER_DIR", silver_dir)

    assert vs.validate_silver_layer() is False
    captured = capsys.readouterr()
    assert "MISSING" in captured.out


def test_validate_gold_layer_success(tmp_path, monkeypatch, capsys):
    gold_dir = tmp_path / "gold"
    gold_dir.mkdir()

    columns = vg.CORE_COLUMNS
    base_dates = pd.date_range("2024-10-01", periods=2, freq="D")
    base_df = pd.DataFrame(
        {
            "date": base_dates,
            "retail_price": [2.5, 2.6],
            "price_rbob": [2.0, 2.02],
            "price_wti": [70.0, 71.0],
            "crack_spread": [0.5, 0.58],
            "retail_margin": [0.5, 0.58],
            "rbob_lag3": [1.95, 1.96],
            "rbob_lag7": [1.9, 1.91],
            "rbob_lag14": [1.85, 1.86],
            "delta_rbob_1w": [0.1, 0.1],
            "vol_rbob_10d": [0.01, 0.01],
            "winter_blend_effect": [-0.05, -0.06],
            "target": [2.5, 2.6],
        }
    )

    for name in ["master_daily.parquet", "master_october.parquet", "master_model_ready.parquet"]:
        _write_parquet(base_df, gold_dir / name)

    monkeypatch.setattr(vg, "GOLD_DIR", gold_dir)

    assert vg.validate_gold_layer() is True
    captured = capsys.readouterr()
    assert "Ready for modeling" in captured.out


def test_validate_gold_layer_missing_column(tmp_path, monkeypatch, capsys):
    gold_dir = tmp_path / "gold"
    gold_dir.mkdir()

    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-10-01"]),
            "retail_price": [2.5],
            "price_rbob": [2.0],
        }
    )
    _write_parquet(df, gold_dir / "master_daily.parquet")
    _write_parquet(df, gold_dir / "master_october.parquet")
    _write_parquet(df, gold_dir / "master_model_ready.parquet")

    monkeypatch.setattr(vg, "GOLD_DIR", gold_dir)

    assert vg.validate_gold_layer() is False
    captured = capsys.readouterr()
    assert "Missing expected columns" in captured.out
