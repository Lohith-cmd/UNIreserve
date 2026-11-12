"""
backend/tests/conftest.py
=========================
Pytest configuration: adds the backend/ directory to sys.path so that
  `from app.xxx import ...`  resolves correctly when tests are run from
  the repo root (python -m pytest backend/tests/).
"""
import sys
from pathlib import Path

# Insert backend/ at the front of the module search path.
# When running from project root: UNIreserve/backend/ must be on sys.path.
_backend_dir = Path(__file__).resolve().parent.parent  # → .../UNIreserve/backend
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

