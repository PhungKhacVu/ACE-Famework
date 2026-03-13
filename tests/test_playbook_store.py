"""Tests for PlaybookStore persistence and CRUD."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.schemas.bullet import Bullet
from app.storage.playbook_store import PlaybookStore


def test_empty_store(tmp_playbook: PlaybookStore) -> None:
    assert tmp_playbook.count() == 0
    assert tmp_playbook.all() == []


def test_add_and_get(tmp_playbook: PlaybookStore) -> None:
    bullet = Bullet(content="Test bullet", domain="general")
    tmp_playbook.add(bullet)
    assert tmp_playbook.count() == 1
    fetched = tmp_playbook.get(bullet.id)
    assert fetched is not None
    assert fetched.content == "Test bullet"


def test_save_and_reload(tmp_path: Path) -> None:
    path = tmp_path / "playbook.json"
    store = PlaybookStore(path)
    store.add(Bullet(id="abc123", content="Persist me", domain="test"))
    store.save()

    assert path.exists()
    # Reload from disk
    store2 = PlaybookStore(path)
    assert store2.count() == 1
    b = store2.get("abc123")
    assert b is not None
    assert b.content == "Persist me"


def test_update_bullet(tmp_playbook: PlaybookStore) -> None:
    bullet = Bullet(content="Original", domain="general", confidence=0.4)
    tmp_playbook.add(bullet)
    bullet.confidence = 0.9
    tmp_playbook.update(bullet)
    updated = tmp_playbook.get(bullet.id)
    assert updated is not None
    assert updated.confidence == pytest.approx(0.9)


def test_remove_bullet(tmp_playbook: PlaybookStore) -> None:
    bullet = Bullet(content="Remove me", domain="general")
    tmp_playbook.add(bullet)
    assert tmp_playbook.count() == 1
    removed = tmp_playbook.remove(bullet.id)
    assert removed is True
    assert tmp_playbook.count() == 0


def test_by_domain(seeded_store: PlaybookStore) -> None:
    result = seeded_store.by_domain("general")
    assert len(result) == 3

    result_missing = seeded_store.by_domain("nonexistent")
    assert result_missing == []


def test_top_returns_sorted(seeded_store: PlaybookStore) -> None:
    top = seeded_store.top(n=2)
    assert len(top) == 2
    # Should be sorted by net_score descending
    assert top[0].net_score >= top[1].net_score


def test_save_excludes_embedding(tmp_path: Path) -> None:
    """Embeddings should not be written to the JSON file."""
    path = tmp_path / "playbook.json"
    store = PlaybookStore(path)
    bullet = Bullet(content="Embedded", domain="general", embedding=[0.1, 0.2, 0.3])
    store.add(bullet)
    store.save()

    raw = json.loads(path.read_text())
    assert "embedding" not in raw[0]
