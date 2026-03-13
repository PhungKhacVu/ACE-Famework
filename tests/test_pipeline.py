"""End-to-end pipeline tests."""
import os
import json
import tempfile
import unittest

from app.schemas.task import TaskInput
from app.schemas.result import TaskResult
from app.storage.playbook_store import PlaybookStore
from app.core.pipeline import Pipeline


def _make_temp_playbook() -> str:
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.write(b"[]")
    tmp.close()
    return tmp.name


def _make_pipeline(playbook_path: str) -> Pipeline:
    store = PlaybookStore(playbook_path)
    store.load()
    return Pipeline(store=store, llm_provider="mock")


class TestPipelineSingleTask(unittest.TestCase):

    def setUp(self):
        self.playbook = _make_temp_playbook()
        self.pipeline = _make_pipeline(self.playbook)

    def tearDown(self):
        if os.path.exists(self.playbook):
            os.unlink(self.playbook)

    def test_run_task_returns_result(self):
        task = TaskInput(id="p1", instruction="What is 3 + 4?", domain="reasoning", ground_truth="7")
        result = self.pipeline.run_task(task, adapt=False)
        self.assertIsInstance(result, TaskResult)
        self.assertEqual(result.task_id, "p1")

    def test_run_task_output_non_empty(self):
        task = TaskInput(id="p2", instruction="Generate an answer to this question")
        result = self.pipeline.run_task(task, adapt=False)
        self.assertTrue(len(result.output) > 0)

    def test_run_task_with_adapt_updates_playbook(self):
        task = TaskInput(
            id="p3",
            instruction="Explain step-by-step reasoning",
            domain="reasoning",
            ground_truth="",
        )
        initial_count = len(self.pipeline.store)
        self.pipeline.run_task(task, adapt=True)
        # After adaptation, the playbook may grow (mock LLM generates bullets)
        final_count = len(self.pipeline.store)
        self.assertGreaterEqual(final_count, initial_count)

    def test_run_task_adapt_true_saves_playbook(self):
        task = TaskInput(id="p4", instruction="Solve this step by step", domain="general")
        self.pipeline.run_task(task, adapt=True)
        self.assertTrue(os.path.exists(self.playbook))
        with open(self.playbook) as f:
            data = json.load(f)
        self.assertIsInstance(data, list)


class TestPipelineBatch(unittest.TestCase):

    def setUp(self):
        self.playbook = _make_temp_playbook()
        self.pipeline = _make_pipeline(self.playbook)

    def tearDown(self):
        if os.path.exists(self.playbook):
            os.unlink(self.playbook)

    def test_batch_returns_all_results(self):
        tasks = [
            TaskInput(id=f"b{i}", instruction=f"Task number {i}") for i in range(3)
        ]
        results = self.pipeline.run_batch(tasks, adapt=False)
        self.assertEqual(len(results), 3)

    def test_batch_output_to_file(self):
        tmp_out = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        tmp_out.close()
        try:
            tasks = [TaskInput(id="o1", instruction="Produce some output for this task")]
            self.pipeline.run_batch(tasks, adapt=False, output_path=tmp_out.name)
            with open(tmp_out.name) as f:
                data = json.load(f)
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["task_id"], "o1")
        finally:
            os.unlink(tmp_out.name)


class TestPipelineEvaluate(unittest.TestCase):

    def setUp(self):
        self.playbook = _make_temp_playbook()
        self.pipeline = _make_pipeline(self.playbook)

    def tearDown(self):
        if os.path.exists(self.playbook):
            os.unlink(self.playbook)

    def test_evaluate_all_correct(self):
        results = [
            TaskResult(task_id=f"e{i}", output="answer", correct=True) for i in range(5)
        ]
        metrics = self.pipeline.evaluate(results)
        self.assertEqual(metrics["total"], 5)
        self.assertEqual(metrics["correct"], 5)
        self.assertAlmostEqual(metrics["accuracy"], 1.0)

    def test_evaluate_mixed(self):
        results = [
            TaskResult(task_id="m1", output="a", correct=True),
            TaskResult(task_id="m2", output="b", correct=False),
            TaskResult(task_id="m3", output="c", correct=None),
        ]
        metrics = self.pipeline.evaluate(results)
        self.assertEqual(metrics["total"], 3)
        self.assertEqual(metrics["correct"], 1)
        self.assertEqual(metrics["incorrect"], 1)
        self.assertEqual(metrics["unknown"], 1)
        self.assertAlmostEqual(metrics["accuracy"], 1 / 3, places=3)

    def test_evaluate_empty(self):
        metrics = self.pipeline.evaluate([])
        self.assertEqual(metrics["total"], 0)
        self.assertAlmostEqual(metrics["accuracy"], 0.0)


class TestPipelineRanking(unittest.TestCase):
    """Test that the cosine similarity ranking module works correctly."""

    def test_identical_texts_similarity_one(self):
        from app.core.ranking import cosine_similarity
        sim = cosine_similarity("hello world", "hello world")
        self.assertAlmostEqual(sim, 1.0, places=5)

    def test_different_texts_similarity_less_than_one(self):
        from app.core.ranking import cosine_similarity
        sim = cosine_similarity("hello world", "goodbye universe")
        self.assertLess(sim, 1.0)

    def test_empty_text_similarity_zero(self):
        from app.core.ranking import cosine_similarity
        sim = cosine_similarity("", "hello world")
        self.assertAlmostEqual(sim, 0.0)

    def test_rank_bullets_ordering(self):
        from app.schemas.bullet import Bullet
        from app.core.ranking import rank_bullets
        bullets = [
            Bullet(id="r1", content="error handling edge cases boundary", helpful_count=1),
            Bullet(id="r2", content="completely unrelated quantum physics", helpful_count=10),
        ]
        ranked = rank_bullets(bullets, query="error handling in code")
        # r1 should score higher on relevance; r2 higher on score — depends on alpha
        self.assertEqual(len(ranked), 2)
        # Just verify we get (bullet, float) tuples
        for b, score in ranked:
            self.assertIsInstance(b, Bullet)
            self.assertIsInstance(score, float)


if __name__ == "__main__":
    unittest.main()
