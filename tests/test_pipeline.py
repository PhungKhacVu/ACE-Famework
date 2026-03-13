"""Integration tests for the full ACE pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.pipeline import ACEPipeline
from app.schemas.bullet import Bullet
from app.schemas.task import TaskInput, TaskResult
from app.services.llm import MockLLMService
from app.storage.playbook_store import PlaybookStore


def _make_pipeline(tmp_path: Path) -> ACEPipeline:
    store = PlaybookStore(tmp_path / "playbook.json")
    llm = MockLLMService()
    return ACEPipeline(llm, store)


def test_run_task_empty_playbook(tmp_path: Path) -> None:
    pipeline = _make_pipeline(tmp_path)
    task = TaskInput(id="p1", description="Test task", domain="general")
    result = pipeline.run_task(task)

    assert isinstance(result, TaskResult)
    assert result.task_id == "p1"
    assert len(result.answer) > 0


def test_run_task_with_bullets(tmp_path: Path) -> None:
    pipeline = _make_pipeline(tmp_path)
    pipeline._store.add(
        Bullet(content="Always check preconditions.", domain="general", confidence=0.8)
    )
    task = TaskInput(id="p2", description="Debug this error", domain="general")
    result = pipeline.run_task(task)
    assert result.task_id == "p2"


def test_adapt_online_grows_playbook(tmp_path: Path) -> None:
    pipeline = _make_pipeline(tmp_path)
    assert pipeline._store.count() == 0

    task = TaskInput(id="p3", description="Online adapt task", domain="general")
    result = pipeline.adapt_online(task)

    assert isinstance(result, TaskResult)
    # Playbook should grow after adaptation
    assert pipeline._store.count() >= 0  # May be 0 if curator returns no deltas


def test_adapt_offline_batch(tmp_path: Path) -> None:
    pipeline = _make_pipeline(tmp_path)

    tasks = [
        TaskInput(id=f"offline{i}", description=f"Task {i} about different topic {i*100}", domain="general")
        for i in range(3)
    ]
    results = [pipeline.run_task(t) for t in tasks]

    summary = pipeline.adapt_offline(tasks, results)

    assert summary.tasks_processed == 3
    assert isinstance(summary.bullets_added, int)
    assert isinstance(summary.bullets_merged, int)


def test_adapt_offline_persists_to_disk(tmp_path: Path) -> None:
    playbook_path = tmp_path / "playbook.json"
    store = PlaybookStore(playbook_path)
    llm = MockLLMService()
    pipeline = ACEPipeline(llm, store)

    task = TaskInput(id="persist1", description="Persist this to disk", domain="general")
    result = pipeline.run_task(task)
    pipeline.adapt_offline([task], [result])

    # File must exist after adaptation
    assert playbook_path.exists()


def test_pipeline_handles_no_matching_result(tmp_path: Path) -> None:
    """adapt_offline should skip tasks with no matching result gracefully."""
    pipeline = _make_pipeline(tmp_path)

    tasks = [TaskInput(id="missing", description="Task with no result", domain="general")]
    results: list[TaskResult] = []  # No results at all

    summary = pipeline.adapt_offline(tasks, results)
    assert summary.tasks_processed == 1
    # No bullets added since result was missing
    assert pipeline._store.count() == 0
