"""Tests for JSONStore."""
from __future__ import annotations

import pytest

from app.storage.json_store import JSONStore


@pytest.fixture()
def store(tmp_path):
    return JSONStore("test_col", tmp_path)


def test_save_and_get(store):
    record = {"id": "r1", "value": 42}
    store.save(record)
    assert store.get("r1") == record


def test_list_returns_all(store):
    store.save({"id": "a"})
    store.save({"id": "b"})
    ids = {r["id"] for r in store.list()}
    assert ids == {"a", "b"}


def test_delete_existing(store):
    store.save({"id": "x"})
    assert store.delete("x") is True
    assert store.get("x") is None


def test_delete_nonexistent(store):
    assert store.delete("missing") is False


def test_save_requires_id(store):
    with pytest.raises(ValueError, match="id"):
        store.save({"no_id": True})


def test_persistence(tmp_path):
    s1 = JSONStore("col", tmp_path)
    s1.save({"id": "persisted", "data": "hello"})
    # New instance reads same file
    s2 = JSONStore("col", tmp_path)
    assert s2.get("persisted") == {"id": "persisted", "data": "hello"}


def test_save_many_inserts_all(store):
    records = [{"id": f"r{i}", "value": i} for i in range(5)]
    store.save_many(records)
    assert len(store.list()) == 5
    for r in records:
        assert store.get(r["id"]) == r


def test_save_many_single_disk_write(tmp_path, monkeypatch):
    """save_many should write the file exactly once regardless of record count."""
    store = JSONStore("col", tmp_path)
    write_count = 0

    original_save = store._save

    def counting_save():
        nonlocal write_count
        write_count += 1
        original_save()

    monkeypatch.setattr(store, "_save", counting_save)
    store.save_many([{"id": "a"}, {"id": "b"}, {"id": "c"}])
    assert write_count == 1


def test_save_many_empty_list_no_write(tmp_path, monkeypatch):
    """save_many with an empty list must not trigger a disk write."""
    store = JSONStore("col", tmp_path)
    write_count = 0

    original_save = store._save

    def counting_save():
        nonlocal write_count
        write_count += 1
        original_save()

    monkeypatch.setattr(store, "_save", counting_save)
    store.save_many([])
    assert write_count == 0


def test_save_many_requires_id(store):
    with pytest.raises(ValueError, match="id"):
        store.save_many([{"id": "ok"}, {"no_id": True}])
