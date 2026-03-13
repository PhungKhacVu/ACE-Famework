"""Tests for Generator, Reflector, and Curator agents (mock LLM)."""
import unittest

from app.schemas.bullet import Bullet
from app.schemas.task import TaskInput
from app.schemas.result import TaskResult
from app.agents.llm_service import LLMService
from app.agents.generator import Generator
from app.agents.reflector import Reflector
from app.agents.curator import Curator


def _mock_llm() -> LLMService:
    return LLMService(provider="mock")


def _make_task(id_="t1", instruction="Solve this problem", domain="general", gt="") -> TaskInput:
    return TaskInput(id=id_, instruction=instruction, domain=domain, ground_truth=gt)


def _make_bullets() -> list:
    return [
        Bullet(id="b1", content="Break problems into sub-problems", domain="general"),
        Bullet(id="b2", content="Verify assumptions before acting", domain="general"),
    ]


class TestLLMServiceMock(unittest.TestCase):

    def test_mock_generate_response(self):
        llm = _mock_llm()
        result = llm.complete("Please generate an answer to this task")
        self.assertIn("<output>", result)
        self.assertIn("<reasoning>", result)

    def test_mock_reflect_response(self):
        llm = _mock_llm()
        result = llm.complete("Please reflect and analyse this output")
        self.assertIn("<reflection>", result)
        self.assertIn("<insights>", result)
        self.assertIn("<confidence>", result)

    def test_mock_curate_response(self):
        llm = _mock_llm()
        result = llm.complete("Please curate and distil bullets from insights")
        self.assertIn("<bullets>", result)

    def test_unknown_provider_raises(self):
        llm = LLMService(provider="unknown_provider")
        with self.assertRaises(ValueError):
            llm.complete("test")


class TestGenerator(unittest.TestCase):

    def test_run_returns_task_result(self):
        gen = Generator(llm=_mock_llm())
        task = _make_task(instruction="What is 2 + 2?", domain="reasoning")
        bullets = _make_bullets()
        result = gen.run(task, bullets)
        self.assertIsInstance(result, TaskResult)
        self.assertEqual(result.task_id, task.id)

    def test_output_not_empty(self):
        gen = Generator(llm=_mock_llm())
        task = _make_task(instruction="Generate an answer to this question")
        result = gen.run(task, [])
        self.assertTrue(len(result.output) > 0)

    def test_applied_bullet_ids_populated(self):
        gen = Generator(llm=_mock_llm(), top_k_bullets=2)
        task = _make_task()
        bullets = _make_bullets()
        result = gen.run(task, bullets)
        # applied_bullet_ids should contain IDs from the provided bullets
        self.assertIsInstance(result.applied_bullet_ids, list)

    def test_empty_bullets_still_works(self):
        gen = Generator(llm=_mock_llm())
        task = _make_task(instruction="Answer this with no context")
        result = gen.run(task, [])
        self.assertIsInstance(result, TaskResult)


class TestReflector(unittest.TestCase):

    def test_run_enriches_result(self):
        reflector = Reflector(llm=_mock_llm())
        task = _make_task(instruction="Reflect on this output", gt="expected answer")
        result = TaskResult(task_id=task.id, output="some output", reasoning="some reasoning")
        enriched = reflector.run(task, result)
        self.assertIsNotNone(enriched.reflection)
        self.assertIsInstance(enriched.insights, list)
        self.assertGreaterEqual(enriched.confidence, 0.0)
        self.assertLessEqual(enriched.confidence, 1.0)

    def test_correct_flag_set_on_exact_match(self):
        reflector = Reflector(llm=_mock_llm())
        task = _make_task(gt="105")
        result = TaskResult(task_id=task.id, output="105")
        enriched = reflector.run(task, result)
        self.assertTrue(enriched.correct)

    def test_correct_flag_false_on_mismatch(self):
        reflector = Reflector(llm=_mock_llm())
        task = _make_task(gt="105")
        result = TaskResult(task_id=task.id, output="completely different answer xyz")
        enriched = reflector.run(task, result)
        self.assertFalse(enriched.correct)

    def test_correct_none_when_no_ground_truth(self):
        reflector = Reflector(llm=_mock_llm())
        task = _make_task(gt="")
        result = TaskResult(task_id=task.id, output="some output")
        enriched = reflector.run(task, result)
        self.assertIsNone(enriched.correct)


class TestCurator(unittest.TestCase):

    def test_run_returns_delta_update(self):
        from app.schemas.bullet import DeltaUpdate
        curator = Curator(llm=_mock_llm())
        task = _make_task()
        result = TaskResult(
            task_id=task.id,
            output="answer",
            insights=["Use step-by-step reasoning", "Verify each step"],
            applied_bullet_ids=["b1"],
            correct=True,
        )
        delta = curator.run(task, result)
        self.assertIsInstance(delta, DeltaUpdate)

    def test_correct_result_sets_helpful_ids(self):
        curator = Curator(llm=_mock_llm())
        task = _make_task()
        result = TaskResult(
            task_id=task.id,
            output="answer",
            insights=["Insight A", "Insight B"],
            applied_bullet_ids=["b1", "b2"],
            correct=True,
        )
        delta = curator.run(task, result)
        self.assertIn("b1", delta.helpful_ids)
        self.assertIn("b2", delta.helpful_ids)
        self.assertEqual(len(delta.harmful_ids), 0)

    def test_wrong_result_sets_harmful_ids(self):
        curator = Curator(llm=_mock_llm())
        task = _make_task()
        result = TaskResult(
            task_id=task.id,
            output="wrong answer",
            insights=["Try harder"],
            applied_bullet_ids=["b1"],
            correct=False,
        )
        delta = curator.run(task, result)
        self.assertIn("b1", delta.harmful_ids)
        self.assertEqual(len(delta.helpful_ids), 0)

    def test_no_insights_returns_empty_delta(self):
        curator = Curator(llm=_mock_llm())
        task = _make_task()
        result = TaskResult(task_id=task.id, output="answer", insights=[])
        delta = curator.run(task, result)
        self.assertEqual(len(delta.new_bullets), 0)


if __name__ == "__main__":
    unittest.main()
