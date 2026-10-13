"""Convenience root entrypoint for launching the Streamlit dashboard."""

import sys
from pathlib import Path

# Ensure repository root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.dashboard.main import run_dashboard  # noqa: E402

if __name__ == "__main__":
    run_dashboard()
