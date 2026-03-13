"""Tests for MergeEngine."""
import os
import tempfile
import unittest

from app.schemas.bullet import Bullet, DeltaUpdate
from app.storage.playbook_store import PlaybookStore
from app.core.merge_engine import MergeEngine


def _make_store() -> PlaybookStore:
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    os.unlink(tmp.name)
    store = PlaybookStore(tmp.name)
    store.load()
    return store


def _make_bullet(id_: str, content: str, domain: str = "general") -> Bullet:
    return Bullet(id=id_, content=content, domain=domain)


class TestMergeEngineAdd(unittest.TestCase):

    def setUp(self):
        self.store = _make_store()
        self.engine = MergeEngine(self.store, similarity_threshold=0.85, max_bullets=10)

    def tearDown(self):
        if os.path.exists(self.store.path):
            os.unlink(self.store.path)

    def test_add_new_bullet(self):
        b = _make_bullet("x1", "Always check boundary conditions thoroughly")
        delta = DeltaUpdate(new_bullets=[b])
        summary = self.engine.apply(delta)
        self.assertEqual(summary["added"], 1)
        self.assertEqual(len(self.store), 1)

    def test_add_multiple_bullets(self):
        bullets = [
            _make_bullet("y1", "Decompose problems into parts"),
            _make_bullet("y2", "Verify assumptions before acting"),
            _make_bullet("y3", "Write clear variable names always"),
        ]
        delta = DeltaUpdate(new_bullets=bullets)
        summary = self.engine.apply(delta)
        self.assertEqual(summary["added"], 3)
        self.assertEqual(len(self.store), 3)

    def test_empty_delta(self):
        delta = DeltaUpdate()
        summary = self.engine.apply(delta)
        self.assertEqual(summary["added"], 0)
        self.assertEqual(summary["duplicates"], 0)
        self.assertEqual(len(self.store), 0)


class TestMergeEngineDeduplication(unittest.TestCase):

    def setUp(self):
        self.store = _make_store()
        # Low threshold to make dedup easier to trigger in tests
        self.engine = MergeEngine(self.store, similarity_threshold=0.7, max_bullets=10)

    def tearDown(self):
        if os.path.exists(self.store.path):
            os.unlink(self.store.path)

    def test_near_duplicate_skipped(self):
        original = _make_bullet("d1", "Always handle edge cases in every function")
        self.store.add(original)

        # Very similar bullet
        duplicate = _make_bullet("d2", "Always handle edge cases in every function carefully")
        delta = DeltaUpdate(new_bullets=[duplicate])
        summary = self.engine.apply(delta)

        self.assertEqual(summary["duplicates"], 1)
        self.assertEqual(summary["added"], 0)

    def test_different_bullet_added(self):
        existing = _make_bullet("e1", "Handle edge cases in functions")
        self.store.add(existing)

        # Very different bullet
        different = _make_bullet("e2", "Use descriptive variable names for readability")
        delta = DeltaUpdate(new_bullets=[different])
        summary = self.engine.apply(delta)

        self.assertEqual(summary["added"], 1)

    def test_different_domain_not_deduped(self):
        b1 = _make_bullet("f1", "Handle edge cases", domain="coding")
        self.store.add(b1)

        # Same content but different domain — should NOT be considered a dup
        b2 = _make_bullet("f2", "Handle edge cases", domain="reasoning")
        delta = DeltaUpdate(new_bullets=[b2])
        summary = self.engine.apply(delta)
        self.assertEqual(summary["added"], 1)


class TestMergeEngineCounters(unittest.TestCase):

    def setUp(self):
        self.store = _make_store()
        self.engine = MergeEngine(self.store)
        b = _make_bullet("c1", "Verify assumptions before acting")
        self.store.add(b)

    def tearDown(self):
        if os.path.exists(self.store.path):
            os.unlink(self.store.path)

    def test_helpful_counter_updated(self):
        delta = DeltaUpdate(helpful_ids=["c1"])
        summary = self.engine.apply(delta)
        self.assertEqual(summary["helpful_updated"], 1)
        self.assertEqual(self.store.get("c1").helpful_count, 1)

    def test_harmful_counter_updated(self):
        delta = DeltaUpdate(harmful_ids=["c1"])
        summary = self.engine.apply(delta)
        self.assertEqual(summary["harmful_updated"], 1)
        self.assertEqual(self.store.get("c1").harmful_count, 1)

    def test_nonexistent_id_not_counted(self):
        delta = DeltaUpdate(helpful_ids=["does-not-exist"])
        summary = self.engine.apply(delta)
        self.assertEqual(summary["helpful_updated"], 0)


class TestMergeEnginePruning(unittest.TestCase):

    def setUp(self):
        self.store = _make_store()
        self.engine = MergeEngine(self.store, max_bullets=3)

    def tearDown(self):
        if os.path.exists(self.store.path):
            os.unlink(self.store.path)

    def test_pruning_enforces_cap(self):
        for i in range(5):
            b = _make_bullet(f"p{i}", f"Unique bullet number {i} with distinct text about topic {i}")
            self.store.add(b)

        delta = DeltaUpdate()
        self.engine.apply(delta)
        self.assertLessEqual(len(self.store), 3)


if __name__ == "__main__":
    unittest.main()
