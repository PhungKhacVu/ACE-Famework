"""Unit tests for PlaybookStore."""

from __future__ import annotations

import pytest

from app.schemas.bullet import Bullet, BulletType
from app.storage.playbook_store import PlaybookStore


@pytest.fixture
def store(tmp_path):
    return PlaybookStore(path=tmp_path / "playbook.json")


def test_store_starts_empty(store):
    assert store.count() == 0


def test_add_and_retrieve(store):
    b = Bullet(content="Test bullet", bullet_type=BulletType.HELPFUL)
    store.add(b)
    assert store.count() == 1
    retrieved = store.get(b.id)
    assert retrieved is not None
    assert retrieved.content == "Test bullet"


def test_remove(store):
    b = Bullet(content="To be removed")
    store.add(b)
    assert store.remove(b.id) is True
    assert store.count() == 0
    assert store.remove(b.id) is False


def test_top_bullets_ordering(store):
    b_low = Bullet(content="Low score", bullet_type=BulletType.HELPFUL, helpful_count=1, harmful_count=9)
    b_high = Bullet(content="High score", bullet_type=BulletType.HELPFUL, helpful_count=9, harmful_count=1)
    store.add(b_low)
    store.add(b_high)
    top = store.top_bullets(2)
    assert top[0].content == "High score"


def test_by_type(store):
    h = Bullet(content="Helpful bullet", bullet_type=BulletType.HELPFUL)
    n = Bullet(content="Harmful bullet", bullet_type=BulletType.HARMFUL)
    store.add(h)
    store.add(n)
    assert len(store.by_type(BulletType.HELPFUL)) == 1
    assert len(store.by_type(BulletType.HARMFUL)) == 1
    assert len(store.by_type(BulletType.NEUTRAL)) == 0


def test_persistence(tmp_path):
    path = tmp_path / "playbook.json"
    store1 = PlaybookStore(path=path)
    b = Bullet(content="Persisted bullet")
    store1.add(b)
    store1.save()

    store2 = PlaybookStore(path=path)
    assert store2.count() == 1
    assert store2.get(b.id) is not None


def test_bullet_score(store):
    b = Bullet(content="Score test", helpful_count=3, harmful_count=1)
    assert b.score == pytest.approx(0.75)


def test_bullet_reinforce_penalise():
    b = Bullet(content="Counter test")
    b.reinforce()
    b.reinforce()
    b.penalise()
    assert b.helpful_count == 2
    assert b.harmful_count == 1
