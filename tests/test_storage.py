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
