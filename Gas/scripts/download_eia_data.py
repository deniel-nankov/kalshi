"""
Compatibility wrapper that exposes legacy download helpers for tests.

Delegates to the ingestion modules under src.ingestion.
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ingestion.download_eia_data import (  # type: ignore[import]
    fetch_inventory,
    fetch_net_imports,
    fetch_utilization,
    main as _run_download,
)


def main() -> None:
    _run_download()


if __name__ == "__main__":
    main()
