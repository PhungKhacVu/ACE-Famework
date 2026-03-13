"""End-to-end pipeline tests."""
import pytest
from app.schemas import TaskInput
from app.core.pipeline import ACEPipeline
from app.storage.playbook_store import PlaybookStore


@pytest.fixture
def store(tmp_path):
    return PlaybookStore(path=str(tmp_path / "playbook.json"))


@pytest.fixture
def pipeline(store):
    return ACEPipeline(store=store)


@pytest.fixture
def task():
    return TaskInput(
        id="pipe-test",
        description="How do I reverse a linked list in Python?",
        domain="algorithms",
    )


class TestACEPipeline:
    def test_run_returns_result(self, pipeline, task):
        from app.schemas import TaskResult
        result = pipeline.run(task)
        assert isinstance(result, TaskResult)

    def test_run_populates_playbook(self, pipeline, store, task):
        pipeline.run(task)
        bullets = store.load()
        assert len(bullets) > 0

    def test_run_twice_increments_counts(self, pipeline, store, task):
        pipeline.run(task)
        first_count = sum(b.helpful_count for b in store.load())
        pipeline.run(task)
        second_count = sum(b.helpful_count for b in store.load())
        assert second_count >= first_count

    def test_run_batch_multiple_tasks(self, pipeline, store):
        tasks = [
            TaskInput(description="Task A", domain="general"),
            TaskInput(description="Task B", domain="general"),
            TaskInput(description="Task C", domain="general"),
        ]
        results = pipeline.run_batch(tasks)
        assert len(results) == 3
        assert len(store.load()) > 0

    def test_empty_playbook_on_first_run(self, store, task):
        # Playbook starts empty — pipeline should still succeed
        assert store.load() == []
        pipe = ACEPipeline(store=store)
        result = pipe.run(task)
        assert result.task_id == task.id
