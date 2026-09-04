"""Put the repository's source roots on sys.path for plain `pytest` runs.

Tests import from `cast/`, `environment/`, and the repository root, none of
which are installed packages. Without this, a bare `pytest` invocation fails
at collection; the suite previously required
`PYTHONPATH=cast:environment:.` to be set by hand.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

for _relative in ("cast", "environment", "."):
    _path = str((ROOT / _relative).resolve())
    if _path not in sys.path:
        sys.path.insert(0, _path)
