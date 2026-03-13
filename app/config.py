"""App-level configuration resolved from environment variables and defaults."""
from __future__ import annotations

import os
from pathlib import Path

# Repository root (one level above this file's directory)
ROOT_DIR: Path = Path(__file__).parent.parent

# Where JSON data lives (can be overridden with ACE_DATA_DIR env var)
DATA_DIR: Path = Path(os.environ.get("ACE_DATA_DIR", str(ROOT_DIR / "data")))

# Sub-directories
PLAYBOOKS_DIR: Path = DATA_DIR / "playbooks"
STORE_DIR: Path = DATA_DIR / "store"

# Ensure writable directories exist at import time
PLAYBOOKS_DIR.mkdir(parents=True, exist_ok=True)
STORE_DIR.mkdir(parents=True, exist_ok=True)
