import sys
from pathlib import Path

import pandas as pd
import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.append(str(SCRIPTS_DIR))

from download_eia_data import (  # noqa: E402
    fetch_inventory,
    fetch_net_imports,
    fetch_utilization,
)
from download_padd3_data import fetch_padd3_share  # noqa: E402
from download_retail_prices import fetch_retail_prices  # noqa: E402
from eia_client import EIAClientError  # noqa: E402


class StubClient:
    def __init__(self, responses_v2=None):
        self.responses_v2 = responses_v2 or {}
        self.calls = []

    def fetch(self, endpoint, params):
        if "facets[series][]" in params:
            key = (endpoint, params.get("facets[series][]"))
        elif "facets[product][]" in params and "facets[duoarea][]" in params:
            key = (
                endpoint,
                params.get("facets[product][]"),
                params.get("facets[duoarea][]"),
            )
        else:
            key = (endpoint, None)
        self.calls.append(("v2", key))
        df = self.responses_v2[key]
        return df.copy()



def make_series(period_value_pairs):
    return pd.DataFrame([{"period": period, "value": value} for period, value in period_value_pairs])


def test_fetch_inventory_success():
    responses = {
        ("petroleum/stoc/wstk/data", "WGTSTUS1"): make_series(
            [("2020-10-02", "200000"), ("2020-10-09", "215000")]
        )
    }
    client = StubClient(responses_v2=responses)
    df = fetch_inventory(client)
    assert list(df.columns) == ["date", "inventory_mbbl"]
    assert df["inventory_mbbl"].iloc[0] == pytest.approx(200.0)


def test_fetch_inventory_out_of_range():
    responses = {
        ("petroleum/stoc/wstk/data", "WGTSTUS1"): make_series(
            [("2020-10-02", "50")]
        )
    }
    client = StubClient(responses_v2=responses)
    with pytest.raises(EIAClientError):
        fetch_inventory(client)


def test_fetch_utilization_success():
    responses = {
        ("petroleum/pnp/wiup/data", "WPULEUS3"): make_series(
            [("2020-10-02", "85.2"), ("2020-10-09", "87.1")]
        )
    }
    client = StubClient(responses_v2=responses)
    df = fetch_utilization(client)
    assert list(df.columns) == ["date", "utilization_pct"]
    assert df["utilization_pct"].iloc[-1] == pytest.approx(87.1)


def test_fetch_net_imports_success():
    responses = {
        ("petroleum/move/wkly/data", "WGTIMUS2"): make_series(
            [("2020-10-02", "1000"), ("2020-10-09", "950")]
        ),
        ("petroleum/move/wkly/data", "W_EPM0F_EEX_NUS-Z00_MBBLD"): make_series(
            [("2020-10-02", "200"), ("2020-10-09", "250")]
        ),
    }
    client = StubClient(responses_v2=responses)
    df = fetch_net_imports(client)
    assert list(df.columns) == ["date", "net_imports_kbd"]
    assert df["net_imports_kbd"].iloc[0] == pytest.approx(800)


def test_fetch_padd3_share_success():
    responses = {
        ("petroleum/stoc/wstk/data", "WGTSTP31"): make_series(
            [("2020-10-02", "82000"), ("2020-10-09", "83000")]
        ),
        ("petroleum/stoc/wstk/data", "WGTSTUS1"): make_series(
            [("2020-10-02", "230000"), ("2020-10-09", "231000")]
        ),
    }
    client = StubClient(responses_v2=responses)
    df = fetch_padd3_share(client)
    assert list(df.columns) == ["date", "padd3_share"]
    assert df["padd3_share"].iloc[0] == pytest.approx(35.65, rel=1e-2)


def test_fetch_padd3_share_out_of_range():
    responses = {
        ("petroleum/stoc/wstk/data", "WGTSTP31"): make_series(
            [("2020-10-02", "1000")]
        ),
        ("petroleum/stoc/wstk/data", "WGTSTUS1"): make_series(
            [("2020-10-02", "230000")]
        ),
    }
    client = StubClient(responses_v2=responses)
    with pytest.raises(EIAClientError):
        fetch_padd3_share(client)


def test_fetch_retail_prices_success():
    responses_v2 = {
        ("petroleum/pri/gnd/data", "EPMR", "NUS"): make_series(
            [("2020-10-05", "2.20"), ("2020-10-12", "2.25")]
        )
    }
    client = StubClient(responses_v2=responses_v2)
    df = fetch_retail_prices(client)
    assert list(df.columns) == ["date", "retail_price"]
    assert df.loc[df["date"] == pd.Timestamp("2020-10-12"), "retail_price"].item() == pytest.approx(2.25)
    assert len(df) >= 8  # Daily expansion


def test_fetch_retail_prices_out_of_range():
    responses_v2 = {
        ("petroleum/pri/gnd/data", "EPMR", "NUS"): make_series(
            [("2020-10-05", "0.5")]
        )
    }
    client = StubClient(responses_v2=responses_v2)
    with pytest.raises(EIAClientError):
        fetch_retail_prices(client)


def test_fetch_retail_prices_empty():
    responses_v2 = {
        ("petroleum/pri/gnd/data", "EPMR", "NUS"): pd.DataFrame(columns=["period", "value"])
    }
    client = StubClient(responses_v2=responses_v2)
    with pytest.raises(EIAClientError):
        fetch_retail_prices(client)
