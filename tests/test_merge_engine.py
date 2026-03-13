"""Tests for the MergeEngine: deduplication and counter updates."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.merge_engine import MergeEngine
from app.schemas.bullet import Bullet, DeltaUpdate
from app.storage.playbook_store import PlaybookStore


def _make_store(tmp_path: Path, bullets: list[Bullet] | None = None) -> PlaybookStore:
    store = PlaybookStore(tmp_path / "playbook.json")
    for b in bullets or []:
        store.add(b)
    return store


def test_merge_adds_new_bullet(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    engine = MergeEngine(store, similarity_threshold=0.85)
    delta = DeltaUpdate(
        content="A completely new and unique bullet about database indexing strategies.",
        domain="general",
        confidence=0.7,
        helpful_delta=1,
    )
    counts = engine.merge([delta])
    assert counts["added"] == 1
    assert store.count() == 1


def test_merge_deduplicates_similar_content(tmp_path: Path) -> None:
    existing = Bullet(
        content="Always break down complex problems into smaller, manageable sub-tasks.",
        domain="general",
        confidence=0.6,
        helpful_count=2,
    )
    store = _make_store(tmp_path, [existing])
    engine = MergeEngine(store, similarity_threshold=0.5)

    # Very similar content – should merge, not add
    delta = DeltaUpdate(
        content="Always break down complex problems into smaller manageable sub-tasks.",
        domain="general",
        confidence=0.75,
        helpful_delta=1,
    )
    counts = engine.merge([delta])
    # Should merge into existing bullet, not create a new one
    assert store.count() == 1
    assert counts["merged"] == 1


def test_merge_updates_helpful_count(tmp_path: Path) -> None:
    existing = Bullet(
        id="bullet1",
        content="Use meaningful variable names to improve readability.",
        domain="software",
        helpful_count=3,
        harmful_count=0,
        confidence=0.7,
    )
    store = _make_store(tmp_path, [existing])
    engine = MergeEngine(store, similarity_threshold=0.5)

    delta = DeltaUpdate(
        content="Use meaningful variable names to improve readability.",
        domain="software",
        confidence=0.8,
        helpful_delta=2,
        harmful_delta=0,
    )
    engine.merge([delta])
    updated = store.get("bullet1")
    assert updated is not None
    assert updated.helpful_count == 5  # 3 + 2


def test_merge_updates_harmful_count(tmp_path: Path) -> None:
    existing = Bullet(
        id="harm1",
        content="Skip writing tests to save time.",
        domain="software",
        helpful_count=0,
        harmful_count=1,
        confidence=0.3,
    )
    store = _make_store(tmp_path, [existing])
    engine = MergeEngine(store, similarity_threshold=0.5)

    delta = DeltaUpdate(
        content="Skip writing tests to save time.",
        domain="software",
        confidence=0.2,
        helpful_delta=0,
        harmful_delta=1,
    )
    engine.merge([delta])
    updated = store.get("harm1")
    assert updated is not None
    assert updated.harmful_count == 2


def test_merge_multiple_distinct_deltas(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    engine = MergeEngine(store, similarity_threshold=0.9)

    # Use truly distinct content from different domains/topics
    distinct_contents = [
        "Database indexing improves query speed significantly.",
        "Photosynthesis converts sunlight into chemical energy stored in glucose.",
        "Test-driven development reduces defects in shipped software.",
        "Compound interest grows wealth exponentially over long time horizons.",
        "Aerobic exercise strengthens cardiovascular health and lung capacity.",
    ]
    deltas = [
        DeltaUpdate(content=c, domain="general", confidence=0.5)
        for c in distinct_contents
    ]
    counts = engine.merge(deltas)
    assert counts["added"] == 5
    assert store.count() == 5


def test_merge_blends_confidence(tmp_path: Path) -> None:
    existing = Bullet(
        id="conf1",
        content="Always validate user input before processing.",
        domain="software",
        confidence=0.8,
    )
    store = _make_store(tmp_path, [existing])
    engine = MergeEngine(store, similarity_threshold=0.5)

    delta = DeltaUpdate(
        content="Always validate user input before processing.",
        domain="software",
        confidence=0.4,
    )
    engine.merge([delta])
    updated = store.get("conf1")
    assert updated is not None
    # Blended: 0.7 * 0.8 + 0.3 * 0.4 = 0.56 + 0.12 = 0.68
    assert abs(updated.confidence - 0.68) < 0.01
