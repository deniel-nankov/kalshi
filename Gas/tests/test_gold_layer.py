import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.append(str(SCRIPTS_DIR))

import build_gold_layer as bgl  # noqa: E402


def _write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def test_build_gold_layer_model_ready(tmp_path, monkeypatch):
    silver_dir = tmp_path / "silver"
    gold_dir = tmp_path / "gold"
    silver_dir.mkdir()
    gold_dir.mkdir()

    retail_dates = pd.date_range("2020-10-03", "2020-10-25", freq="D")
    retail_df = pd.DataFrame(
        {
            "date": retail_dates,
            "retail_price": 2.00 + 0.01 * np.arange(len(retail_dates)),
        }
    )
    _write_parquet(retail_df, silver_dir / "retail_prices_daily.parquet")

    full_dates = pd.date_range("2020-10-01", "2020-10-25", freq="D")
    rbob_dates = full_dates[::2]  # every other day to test forward-fill
    rbob_df = pd.DataFrame(
        {
            "date": rbob_dates,
            "price_rbob": 1.80 + 0.01 * np.arange(len(rbob_dates)),
            "volume_rbob": 900 + np.arange(len(rbob_dates)),
        }
    )
    _write_parquet(rbob_df, silver_dir / "rbob_daily.parquet")

    wti_df = pd.DataFrame(
        {
            "date": rbob_dates,
            "price_wti": 65.0 + 0.5 * np.arange(len(rbob_dates)),
        }
    )
    _write_parquet(wti_df, silver_dir / "wti_daily.parquet")

    weekly_dates = pd.to_datetime(["2020-10-05", "2020-10-12", "2020-10-19"])
    inventory_df = pd.DataFrame({"date": weekly_dates, "inventory_mbbl": [230.0, 231.0, 229.5]})
    _write_parquet(inventory_df, silver_dir / "eia_inventory_weekly.parquet")

    utilization_df = pd.DataFrame({"date": weekly_dates, "utilization_pct": [85.0, 87.5, 86.0]})
    _write_parquet(utilization_df, silver_dir / "eia_utilization_weekly.parquet")

    imports_df = pd.DataFrame({"date": weekly_dates, "net_imports_kbd": [500.0, 520.0, 510.0]})
    _write_parquet(imports_df, silver_dir / "eia_imports_weekly.parquet")

    padd3_df = pd.DataFrame({"date": weekly_dates, "padd3_share": [35.0, 36.0, 34.5]})
    _write_parquet(padd3_df, silver_dir / "padd3_share_weekly.parquet")

    monkeypatch.setattr(bgl, "SILVER_DIR", silver_dir)
    monkeypatch.setattr(bgl, "GOLD_DIR", gold_dir)

    gold_df = bgl.build_gold_dataset()

    assert gold_df["date"].min() == pd.Timestamp("2020-10-03")

    rbob_on_fourth = gold_df.loc[gold_df["date"] == pd.Timestamp("2020-10-04"), "price_rbob"].iloc[0]
    rbob_on_third = gold_df.loc[gold_df["date"] == pd.Timestamp("2020-10-03"), "price_rbob"].iloc[0]
    assert rbob_on_fourth == pytest.approx(rbob_on_third)

    wti_on_fourth = gold_df.loc[gold_df["date"] == pd.Timestamp("2020-10-04"), "price_wti"].iloc[0]
    wti_on_third = gold_df.loc[gold_df["date"] == pd.Timestamp("2020-10-03"), "price_wti"].iloc[0]
    assert wti_on_fourth == pytest.approx(wti_on_third)

    post_inventory = gold_df[gold_df["date"] >= pd.Timestamp("2020-10-05")]
    assert post_inventory["inventory_mbbl"].isna().sum() == 0
    assert post_inventory["utilization_pct"].isna().sum() == 0

    bgl.save_outputs(gold_df)

    model_ready = pd.read_parquet(gold_dir / "master_model_ready.parquet")
    assert model_ready.isna().sum().sum() == 0
    assert model_ready["date"].min() >= pd.Timestamp("2020-10-15")
    assert model_ready["date"].max() == pd.Timestamp("2020-10-25")


def test_build_gold_layer_missing_required(tmp_path, monkeypatch):
    silver_dir = tmp_path / "silver"
    gold_dir = tmp_path / "gold"
    silver_dir.mkdir()
    gold_dir.mkdir()

    rbob_df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-10-01"]),
            "price_rbob": [1.9],
            "volume_rbob": [1000],
        }
    )
    _write_parquet(rbob_df, silver_dir / "rbob_daily.parquet")

    monkeypatch.setattr(bgl, "SILVER_DIR", silver_dir)
    monkeypatch.setattr(bgl, "GOLD_DIR", gold_dir)

    with pytest.raises(FileNotFoundError):
        bgl.build_gold_dataset()
