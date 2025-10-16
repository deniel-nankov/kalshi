"""
Compatibility wrapper for legacy PADD3 share download.
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ingestion.download_padd3_data import (  # type: ignore[import]
    fetch_padd3_share,
    main as _run_download,
)


def main() -> None:
    _run_download()


if __name__ == "__main__":
    main()
