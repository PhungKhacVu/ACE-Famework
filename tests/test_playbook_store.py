"""Tests for PlaybookStore."""
import json
import os
import tempfile
import pytest
from app.schemas import Bullet
from app.storage.playbook_store import PlaybookStore


@pytest.fixture
def tmp_store(tmp_path):
    path = tmp_path / "test_playbook.json"
    return PlaybookStore(path=str(path))


class TestPlaybookStore:
    def test_load_empty_when_file_missing(self, tmp_store):
        assert tmp_store.load() == []

    def test_save_and_load_roundtrip(self, tmp_store):
        bullets = [
            Bullet(text="bullet one", helpful_count=3, confidence=0.9),
            Bullet(text="bullet two", helpful_count=1, confidence=0.6),
        ]
        tmp_store.save(bullets)
        loaded = tmp_store.load()
        assert len(loaded) == 2
        texts = {b.text for b in loaded}
        assert "bullet one" in texts
        assert "bullet two" in texts

    def test_add_appends_bullet(self, tmp_store):
        b1 = Bullet(text="first")
        b2 = Bullet(text="second")
        tmp_store.add(b1)
        tmp_store.add(b2)
        loaded = tmp_store.load()
        assert len(loaded) == 2

    def test_clear_empties_store(self, tmp_store):
        tmp_store.add(Bullet(text="to be deleted"))
        tmp_store.clear()
        assert tmp_store.load() == []

    def test_persisted_json_is_valid(self, tmp_store):
        tmp_store.add(Bullet(text="check json"))
        with open(tmp_store.path, "r") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert data[0]["text"] == "check json"

    def test_confidence_persisted(self, tmp_store):
        b = Bullet(text="conf test", confidence=0.88)
        tmp_store.save([b])
        loaded = tmp_store.load()
        assert abs(loaded[0].confidence - 0.88) < 1e-9
