"""Tests for JSON-backed storage (playbook & task stores)."""

from __future__ import annotations

import pytest

from app.schemas import Playbook, Step, StepType, Task, TaskStatus
from app.storage.playbook_store import PlaybookStore
from app.storage.task_store import TaskStore


@pytest.fixture()
def tmp_pb_store(tmp_path):
    return PlaybookStore(tmp_path / "playbooks")


@pytest.fixture()
def tmp_task_store(tmp_path):
    return TaskStore(tmp_path / "tasks")


class TestPlaybookStore:
    def test_save_and_load(self, tmp_pb_store):
        pb = Playbook(name="my-pb", steps=[Step("s1", StepType.PROMPT, "do it")])
        tmp_pb_store.save(pb)
        loaded = tmp_pb_store.load(pb.id)
        assert loaded.name == "my-pb"
        assert len(loaded.steps) == 1

    def test_load_missing_raises(self, tmp_pb_store):
        with pytest.raises(FileNotFoundError):
            tmp_pb_store.load("nonexistent-id")

    def test_list_all(self, tmp_pb_store):
        pb1 = Playbook(name="pb1")
        pb2 = Playbook(name="pb2")
        tmp_pb_store.save(pb1)
        tmp_pb_store.save(pb2)
        names = {pb.name for pb in tmp_pb_store.list_all()}
        assert names == {"pb1", "pb2"}

    def test_delete(self, tmp_pb_store):
        pb = Playbook(name="delete-me")
        tmp_pb_store.save(pb)
        assert tmp_pb_store.delete(pb.id) is True
        assert tmp_pb_store.delete(pb.id) is False

    def test_find_by_name(self, tmp_pb_store):
        pb = Playbook(name="find-me")
        tmp_pb_store.save(pb)
        found = tmp_pb_store.find_by_name("find-me")
        assert found is not None
        assert found.id == pb.id

    def test_find_by_name_case_insensitive(self, tmp_pb_store):
        pb = Playbook(name="Hello-World")
        tmp_pb_store.save(pb)
        assert tmp_pb_store.find_by_name("hello-world") is not None

    def test_find_by_name_missing(self, tmp_pb_store):
        assert tmp_pb_store.find_by_name("ghost") is None


class TestTaskStore:
    def test_save_and_load(self, tmp_task_store):
        task = Task(goal="my goal")
        tmp_task_store.save(task)
        loaded = tmp_task_store.load(task.id)
        assert loaded.goal == "my goal"

    def test_load_missing_raises(self, tmp_task_store):
        with pytest.raises(FileNotFoundError):
            tmp_task_store.load("no-such-task")

    def test_list_all(self, tmp_task_store):
        t1 = Task(goal="first")
        t2 = Task(goal="second")
        tmp_task_store.save(t1)
        tmp_task_store.save(t2)
        tasks = list(tmp_task_store.list_all())
        assert len(tasks) == 2

    def test_delete(self, tmp_task_store):
        task = Task(goal="bye")
        tmp_task_store.save(task)
        assert tmp_task_store.delete(task.id) is True
        assert tmp_task_store.delete(task.id) is False

    def test_list_by_status(self, tmp_task_store):
        t_done = Task(goal="done task", status=TaskStatus.DONE)
        t_fail = Task(goal="fail task", status=TaskStatus.FAILED)
        tmp_task_store.save(t_done)
        tmp_task_store.save(t_fail)
        done_list = list(tmp_task_store.list_by_status(TaskStatus.DONE))
        assert len(done_list) == 1
        assert done_list[0].goal == "done task"
