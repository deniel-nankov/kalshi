"""
Compatibility shim exposing the EIA client from the ingestion package.
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ingestion.eia_client import (  # type: ignore[import]
    EIAClient,
    EIAClientError,
    default_params,
)

__all__ = ["EIAClient", "EIAClientError", "default_params"]
