"""Unit tests for the merge engine."""

from __future__ import annotations

import pytest

from app.schemas.bullet import Bullet, BulletType, DeltaUpdate
from app.storage.playbook_store import PlaybookStore
from app.core.merge_engine import MergeEngine


@pytest.fixture
def tmp_store(tmp_path):
    return PlaybookStore(path=tmp_path / "playbook.json")


@pytest.fixture
def engine(tmp_store):
    return MergeEngine(store=tmp_store, dedup_threshold=0.85)


def test_merge_adds_new_bullet(engine, tmp_store):
    bullet = Bullet(content="Use list comprehensions for concise iteration.", bullet_type=BulletType.HELPFUL)
    delta = DeltaUpdate(new_bullets=[bullet])
    summary = engine.merge(delta)
    assert summary["added"] == 1
    assert tmp_store.count() == 1


def test_merge_deduplicates_similar_bullet(tmp_store):
    # Use a lower threshold so near-identical bullets are caught
    engine_low = MergeEngine(store=tmp_store, dedup_threshold=0.70)
    b1 = Bullet(content="Use list comprehensions for concise iteration in Python code.")
    tmp_store.add(b1)

    # Shares 8/9 tokens → Jaccard ≈ 0.89 > 0.70 → should be skipped
    b2 = Bullet(content="Use list comprehensions for concise iteration in Python.")
    delta = DeltaUpdate(new_bullets=[b2])
    summary = engine_low.merge(delta)
    assert summary["skipped_duplicates"] == 1
    assert summary["added"] == 0


def test_merge_allows_dissimilar_bullet(engine, tmp_store):
    b1 = Bullet(content="Use list comprehensions for concise iteration.")
    tmp_store.add(b1)

    b2 = Bullet(content="Always document your public API endpoints.")
    delta = DeltaUpdate(new_bullets=[b2])
    summary = engine.merge(delta)
    assert summary["added"] == 1
    assert tmp_store.count() == 2


def test_merge_reinforce(engine, tmp_store):
    b = Bullet(content="Some bullet")
    tmp_store.add(b)
    delta = DeltaUpdate(reinforce_ids=[b.id])
    summary = engine.merge(delta)
    assert summary["reinforced"] == 1
    assert tmp_store.get(b.id).helpful_count == 1


def test_merge_penalise(engine, tmp_store):
    b = Bullet(content="Some bullet")
    tmp_store.add(b)
    delta = DeltaUpdate(penalise_ids=[b.id])
    summary = engine.merge(delta)
    assert summary["penalised"] == 1
    assert tmp_store.get(b.id).harmful_count == 1


def test_merge_missing_reinforce_id_is_safe(engine, tmp_store):
    delta = DeltaUpdate(reinforce_ids=["nonexistent-id"])
    summary = engine.merge(delta)
    assert summary["reinforced"] == 0
