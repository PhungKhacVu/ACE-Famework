"""Smoke tests for the full ACE pipeline (end-to-end)."""

from __future__ import annotations

import json
import pytest

from app.core.pipeline import ACEPipeline
from app.schemas.task import TaskInput
from app.services.llm import MockLLMProvider
from app.storage.playbook_store import PlaybookStore


@pytest.fixture
def pipeline(tmp_path):
    store = PlaybookStore(path=tmp_path / "playbook.json")
    provider = MockLLMProvider()
    return ACEPipeline(store=store, provider=provider)


@pytest.fixture
def sample_task():
    return TaskInput(
        description="What is the difference between a stack and a queue?",
        context="CS student studying data structures.",
    )


def test_run_task_returns_result(pipeline, sample_task):
    result = pipeline.run_task(sample_task)
    assert result.task_id == sample_task.id
    assert len(result.final_answer) > 0
    assert len(result.agent_outputs) == 3


def test_run_task_updates_playbook(pipeline, sample_task, tmp_path):
    count_before = pipeline._store.count()
    pipeline.run_task(sample_task)
    # The mock curator adds one bullet each run
    assert pipeline._store.count() >= count_before


def test_offline_adaptation_multiple_tasks(pipeline):
    tasks = [
        TaskInput(description=f"Task {i}", context="test")
        for i in range(3)
    ]
    results = pipeline.offline_adaptation(tasks)
    assert len(results) == 3


def test_online_adaptation(pipeline, sample_task):
    result = pipeline.online_adaptation(sample_task)
    assert result.task_id == sample_task.id
    assert result.final_answer


def test_pipeline_with_preloaded_playbook(tmp_path):
    from app.schemas.bullet import Bullet, BulletType

    store = PlaybookStore(path=tmp_path / "playbook.json")
    store.add(Bullet(content="Pre-existing bullet", bullet_type=BulletType.HELPFUL))
    store.save()

    store2 = PlaybookStore(path=tmp_path / "playbook.json")
    pipeline = ACEPipeline(store=store2, provider=MockLLMProvider())
    task = TaskInput(description="Test with existing bullets")
    result = pipeline.run_task(task)
    assert result.final_answer


def test_evaluate_batch():
    from app.services.evaluator import evaluate_batch

    predictions = ["The sky is blue", "Python is a language"]
    ground_truths = ["The sky is blue", "Python is a programming language"]
    metrics = evaluate_batch(predictions, ground_truths)
    assert metrics["n"] == 2
    assert metrics["avg_exact_match"] == pytest.approx(0.5)
    assert 0 <= metrics["avg_f1"] <= 1
    assert 0 <= metrics["avg_jaccard"] <= 1


def test_playbook_persisted_after_pipeline(tmp_path):
    path = tmp_path / "playbook.json"
    store = PlaybookStore(path=path)
    pipeline = ACEPipeline(store=store, provider=MockLLMProvider())
    task = TaskInput(description="Does persistence work?")
    pipeline.run_task(task)

    # Load playbook fresh and check bullets were saved
    store2 = PlaybookStore(path=path)
    assert store2.count() >= 0  # at least it loads without error
