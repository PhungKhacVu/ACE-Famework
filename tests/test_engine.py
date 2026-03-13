"""Tests for the ACE Engine."""

from __future__ import annotations

import pytest

from app.config import Config
from app.core.engine import ACEEngine
from app.schemas import Playbook, Step, StepType, TaskStatus


@pytest.fixture()
def engine(tmp_path):
    config = Config(
        data_dir=tmp_path,
        llm_backend="mock",
        max_steps=5,
    )
    return ACEEngine(config)


class TestACEEngine:
    def test_run_simple_task(self, engine):
        task = engine.run_task(goal="hello world")
        assert task.status == TaskStatus.DONE
        assert task.id != ""
        assert task.result != ""

    def test_task_persisted(self, engine):
        task = engine.run_task(goal="persist me")
        loaded = engine.get_task(task.id)
        assert loaded.goal == "persist me"

    def test_list_tasks(self, engine):
        engine.run_task("task one")
        engine.run_task("task two")
        tasks = engine.list_tasks()
        assert len(tasks) == 2

    def test_run_task_with_missing_playbook(self, engine):
        task = engine.run_task(goal="run it", playbook_id="not-exist")
        assert task.status == TaskStatus.FAILED
        assert "not found" in task.result.lower()

    def test_run_task_with_playbook(self, engine):
        pb = Playbook(
            name="greet-pb",
            steps=[Step("greet", StepType.PROMPT, "say hello")],
        )
        engine.save_playbook(pb)
        task = engine.run_task(goal="use playbook", playbook_id=pb.id)
        assert task.status == TaskStatus.DONE
        assert task.playbook_id == pb.id

    def test_save_and_list_playbooks(self, engine):
        pb1 = Playbook(name="pb-alpha")
        pb2 = Playbook(name="pb-beta")
        engine.save_playbook(pb1)
        engine.save_playbook(pb2)
        names = {pb.name for pb in engine.list_playbooks()}
        assert names == {"pb-alpha", "pb-beta"}

    def test_delete_playbook(self, engine):
        pb = Playbook(name="temp")
        engine.save_playbook(pb)
        assert engine.delete_playbook(pb.id) is True
        assert engine.delete_playbook(pb.id) is False
