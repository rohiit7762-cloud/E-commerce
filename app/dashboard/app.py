"""Streamlit dashboard entrypoint shim.

Ensures sys.path correctly resolves the top-level 'app' package when launched
via `streamlit run app/dashboard/app.py`.
"""

import sys
from pathlib import Path

# Ensure repository root is placed at index 0 of sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import and execute main dashboard
from app.dashboard.main import run_dashboard  # noqa: E402

if __name__ == "__main__":
    run_dashboard()
