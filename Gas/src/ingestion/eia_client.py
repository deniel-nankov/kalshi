"""
Lightweight EIA API client with retries and structured error handling.

The client centralises authentication (API key), request execution, and the
common validation logic used by the Silver-layer download scripts. This makes
it easier to unit test downstream modules by swapping in a fake session.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import requests
from requests import Response, Session


class EIAClientError(RuntimeError):
    """Raised when the EIA API returns an unexpected response."""


@dataclass
class EIAClient:
    api_key: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    backoff_factor: float = 1.5
    session: Optional[Session] = None

    BASE_URL: str = "https://api.eia.gov/v2"

    def __post_init__(self) -> None:
        if self.api_key is None:
            self.api_key = os.getenv("EIA_API_KEY") or load_api_key_from_env_file()

        if not self.api_key:
            raise EIAClientError(
                "EIA API key not provided. Set EIA_API_KEY environment variable or "
                "pass api_key explicitly."
            )

        if self.session is None:
            self.session = requests.Session()

    def fetch(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> pd.DataFrame:
        """
        Execute a GET request against the EIA API and return the payload as a DataFrame.

        Args:
            endpoint: URL suffix after the base v2 path, e.g. "petroleum/stoc/wstk/data".
            params: Query parameters (the API key is injected automatically).
        """
        params = dict(params or {})
        params["api_key"] = self.api_key

        url = f"{self.BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
        attempt = 0

        while True:
            attempt += 1
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return self._to_dataframe(response)
            except (requests.RequestException, EIAClientError) as exc:
                if attempt >= self.max_retries:
                    raise EIAClientError(f"EIA request failed after {attempt} attempts: {exc}") from exc

                sleep_seconds = self.backoff_factor ** (attempt - 1)
                time.sleep(sleep_seconds)

    @staticmethod
    def _to_dataframe(response: Response) -> pd.DataFrame:
        try:
            payload = response.json()
        except ValueError as exc:
            raise EIAClientError("Failed to decode EIA response as JSON") from exc

        if "response" not in payload or "data" not in payload["response"]:
            raise EIAClientError(f"Unexpected EIA response format: {payload}")

        data = payload["response"]["data"]
        if not data:
            raise EIAClientError("EIA response contained no rows")

        return pd.DataFrame(data)

def load_api_key_from_env_file() -> Optional[str]:
    """
    Load EIA API key from a local .env file if present.
    This keeps secrets out of source while still enabling scripted usage.
    """
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return None

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("EIA_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def default_params(series_id: str, *, frequency: str, start: str, data_field: str = "value") -> Dict[str, str]:
    """
    Helper to construct common parameter payloads for series-based endpoints.
    EIA requires the series facet to be provided as facets[series][].
    """
    return {
        "data[0]": data_field,
        "facets[series][]": series_id,
        "frequency": frequency,
        "start": start,
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
    }
