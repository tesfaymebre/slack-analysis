"""Add project root to sys.path so Streamlit pages can import src."""

import sys
from pathlib import Path


def ensure_project_root():
    """Insert the repository root on sys.path if it is missing."""
    root = Path(__file__).resolve().parent.parent
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


ensure_project_root()
