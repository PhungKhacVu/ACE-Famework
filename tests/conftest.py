"""Shared pytest fixtures."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from app.schemas.bullet import Bullet
from app.storage.playbook_store import PlaybookStore


@pytest.fixture
def tmp_playbook(tmp_path: Path) -> PlaybookStore:
    """Return a fresh PlaybookStore backed by a temp file."""
    return PlaybookStore(tmp_path / "playbook.json")


@pytest.fixture
def seeded_store(tmp_path: Path) -> PlaybookStore:
    """Return a PlaybookStore pre-seeded with three bullets."""
    store = PlaybookStore(tmp_path / "playbook.json")
    for i in range(3):
        store.add(
            Bullet(
                id=f"b{i:03d}",
                content=f"Test bullet {i}: always consider edge cases carefully.",
                domain="general",
                confidence=0.5 + i * 0.1,
                helpful_count=i,
            )
        )
    return store
