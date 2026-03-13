"""Tests for MergeEngine."""
import pytest
from app.schemas import Bullet
from app.core.merge_engine import MergeEngine, _jaccard


# ---------------------------------------------------------------------------
# Jaccard similarity
# ---------------------------------------------------------------------------

class TestJaccard:
    def test_identical(self):
        assert _jaccard("hello world", "hello world") == 1.0

    def test_disjoint(self):
        assert _jaccard("foo bar", "baz qux") == 0.0

    def test_partial(self):
        score = _jaccard("always decompose tasks", "decompose complex tasks")
        assert 0.0 < score < 1.0

    def test_empty_strings(self):
        assert _jaccard("", "") == 1.0


# ---------------------------------------------------------------------------
# MergeEngine
# ---------------------------------------------------------------------------

class TestMergeEngine:
    def _engine(self, threshold=0.5):
        return MergeEngine(threshold=threshold)

    def test_inserts_new_bullet(self):
        engine = self._engine()
        result = engine.merge([], ["Always decompose complex tasks"])
        assert len(result) == 1
        assert result[0].text == "Always decompose complex tasks"
        assert result[0].helpful_count == 1

    def test_dedup_similar_bullet(self):
        engine = self._engine(threshold=0.5)
        existing = [Bullet(text="Always decompose complex tasks", helpful_count=1)]
        # Very similar text — should increment existing bullet, not add new one
        result = engine.merge(existing, ["Always decompose tasks carefully"])
        # Should still be 1 bullet (deduplicated)
        assert len(result) == 1
        assert result[0].helpful_count == 2

    def test_adds_dissimilar_bullet(self):
        engine = self._engine(threshold=0.85)
        existing = [Bullet(text="Always decompose complex tasks", helpful_count=1)]
        # Completely different text — should add a new bullet
        result = engine.merge(existing, ["Use logging for debugging"])
        assert len(result) == 2

    def test_harmful_increments_harmful_count(self):
        engine = self._engine(threshold=0.5)
        existing = [Bullet(text="Always decompose complex tasks", helpful_count=2)]
        result = engine.merge(existing, ["Always decompose complex tasks"], harmful=True)
        assert result[0].harmful_count == 1
        assert result[0].helpful_count == 2

    def test_confidence_updated_after_merge(self):
        engine = self._engine(threshold=0.5)
        existing = [Bullet(text="Always decompose tasks", helpful_count=1, harmful_count=1, confidence=0.5)]
        result = engine.merge(existing, ["Always decompose tasks"])
        # helpful=2, harmful=1 → confidence = 2/3
        assert abs(result[0].confidence - 2 / 3) < 1e-9

    def test_merge_multiple_candidates(self):
        engine = self._engine()
        candidates = ["Step one: plan", "Step two: execute", "Step three: review"]
        result = engine.merge([], candidates)
        assert len(result) == 3

    def test_empty_candidates_no_change(self):
        engine = self._engine()
        existing = [Bullet(text="existing bullet")]
        result = engine.merge(existing, [])
        assert len(result) == 1
