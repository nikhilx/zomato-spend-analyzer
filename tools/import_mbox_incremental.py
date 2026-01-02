"""Thin wrapper CLI that calls the core importer in `zomato_analyzer.importer`.

Keep `tools/` scripts minimal — real logic lives in the package.
This wrapper ensures the project root is on `sys.path` so imports work when
running the script directly (e.g. `python tools/import_mbox_incremental.py`).
"""
from pathlib import Path
import sys

# Ensure project root (parent of `tools`) is on sys.path so `zomato_analyzer`
# can be imported when running this script directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from zomato_analyzer.importer import run_cli


if __name__ == '__main__':
    raise SystemExit(run_cli())
