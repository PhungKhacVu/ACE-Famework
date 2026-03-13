"""Tests for PlaybookStore."""
import os
import json
import tempfile
import unittest

from app.schemas.bullet import Bullet
from app.storage.playbook_store import PlaybookStore


def _make_bullet(id_: str, content: str, domain: str = "general", helpful: int = 0, harmful: int = 0) -> Bullet:
    return Bullet(id=id_, content=content, domain=domain, helpful_count=helpful, harmful_count=harmful)


class TestPlaybookStoreBasic(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)  # remove so load() starts fresh
        self.store = PlaybookStore(self.tmp.name)
        self.store.load()

    def tearDown(self):
        if os.path.exists(self.tmp.name):
            os.unlink(self.tmp.name)

    def test_empty_on_missing_file(self):
        self.assertEqual(len(self.store), 0)

    def test_add_and_retrieve(self):
        b = _make_bullet("a1", "Always verify assumptions")
        self.store.add(b)
        self.assertEqual(len(self.store), 1)
        retrieved = self.store.get("a1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.content, "Always verify assumptions")

    def test_remove(self):
        b = _make_bullet("b1", "Handle edge cases")
        self.store.add(b)
        result = self.store.remove("b1")
        self.assertTrue(result)
        self.assertEqual(len(self.store), 0)
        self.assertIsNone(self.store.get("b1"))

    def test_remove_nonexistent(self):
        result = self.store.remove("does-not-exist")
        self.assertFalse(result)

    def test_save_and_load(self):
        b1 = _make_bullet("c1", "Decompose problems", helpful=2, harmful=0)
        b2 = _make_bullet("c2", "Check edge cases", helpful=1, harmful=1)
        self.store.add(b1)
        self.store.add(b2)
        self.store.save()

        store2 = PlaybookStore(self.tmp.name)
        store2.load()
        self.assertEqual(len(store2), 2)
        c1 = store2.get("c1")
        self.assertIsNotNone(c1)
        self.assertEqual(c1.helpful_count, 2)

    def test_by_domain(self):
        self.store.add(_make_bullet("d1", "Bullet A", domain="coding"))
        self.store.add(_make_bullet("d2", "Bullet B", domain="reasoning"))
        self.store.add(_make_bullet("d3", "Bullet C", domain="coding"))
        coding = self.store.by_domain("coding")
        self.assertEqual(len(coding), 2)

    def test_top_ranking(self):
        self.store.add(_make_bullet("e1", "Low score", helpful=0, harmful=3))
        self.store.add(_make_bullet("e2", "High score", helpful=5, harmful=0))
        self.store.add(_make_bullet("e3", "Medium score", helpful=2, harmful=1))
        top = self.store.top(2)
        self.assertEqual(top[0].id, "e2")
        self.assertEqual(top[1].id, "e3")

    def test_increment_helpful(self):
        b = _make_bullet("f1", "Some bullet")
        self.store.add(b)
        self.store.increment_helpful("f1")
        self.store.increment_helpful("f1")
        self.assertEqual(self.store.get("f1").helpful_count, 2)

    def test_increment_harmful(self):
        b = _make_bullet("g1", "Some bullet")
        self.store.add(b)
        self.store.increment_harmful("g1")
        self.assertEqual(self.store.get("g1").harmful_count, 1)


class TestPlaybookStoreSearch(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)
        self.store = PlaybookStore(self.tmp.name)
        self.store.load()
        self.store.add(_make_bullet("s1", "Handle error and exception carefully", domain="coding"))
        self.store.add(_make_bullet("s2", "Decompose complex problems step by step", domain="general"))
        self.store.add(_make_bullet("s3", "Verify edge cases in every function", domain="coding"))

    def tearDown(self):
        if os.path.exists(self.tmp.name):
            os.unlink(self.tmp.name)

    def test_search_keyword_match(self):
        results = self.store.search("error handling", top_k=5)
        ids = [b.id for b in results]
        self.assertIn("s1", ids)

    def test_search_domain_filter(self):
        results = self.store.search("edge cases", domain="coding", top_k=5)
        for b in results:
            self.assertEqual(b.domain, "coding")

    def test_search_no_match_returns_top(self):
        # No keywords match — should still return bullets
        results = self.store.search("xyzzy quantum entanglement", top_k=3)
        self.assertGreater(len(results), 0)


if __name__ == "__main__":
    unittest.main()
