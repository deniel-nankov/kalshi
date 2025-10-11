import sys
from pathlib import Path

import pandas as pd
import pytest
import requests

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.append(str(SCRIPTS_DIR))

from eia_client import (  # noqa: E402
    EIAClient,
    EIAClientError,
    default_params,
)


class FakeResponse:
    def __init__(self, status_code=200, payload=None, json_error=False):
        self.status_code = status_code
        self._payload = payload or {}
        self._json_error = json_error

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")

    def json(self):
        if self._json_error:
            raise ValueError("Invalid JSON")
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self._responses = responses
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params, timeout))
        resp = self._responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        return resp


def payload(rows):
    return {"response": {"data": rows}}


def test_default_params():
    params = default_params("SERIES", frequency="weekly", start="2020-10-01")
    assert params["facets[series][]"] == "SERIES"
    assert params["frequency"] == "weekly"
    assert params["start"] == "2020-10-01"
    assert params["data[0]"] == "value"


def test_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("EIA_API_KEY", raising=False)
    monkeypatch.setattr("eia_client.load_api_key_from_env_file", lambda: None)
    with pytest.raises(EIAClientError):
        EIAClient(api_key=None, session=FakeSession([]))


def test_client_fetch_success(monkeypatch):
    fake_data = payload([{"period": "2020-10-02", "value": "1"}])
    session = FakeSession([FakeResponse(payload=fake_data)])
    client = EIAClient(api_key="test", session=session, max_retries=1)
    df = client.fetch("petroleum/test/data", {"frequency": "weekly"})
    assert isinstance(df, pd.DataFrame)
    assert df.iloc[0]["period"] == "2020-10-02"
    assert session.calls[0][0].endswith("petroleum/test/data")


def test_client_handles_http_error():
    session = FakeSession([FakeResponse(status_code=500)])
    client = EIAClient(api_key="test", session=session, max_retries=1)
    with pytest.raises(EIAClientError):
        client.fetch("petroleum/test/data", {})


def test_client_handles_bad_json():
    session = FakeSession([FakeResponse(json_error=True)])
    client = EIAClient(api_key="test", session=session, max_retries=1)
    with pytest.raises(EIAClientError):
        client.fetch("petroleum/test/data", {})
