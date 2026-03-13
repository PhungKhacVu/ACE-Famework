"""JSON-backed task store – no external deps."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from app.schemas import Task, TaskStatus


class TaskStore:
    """Persist and retrieve tasks as individual JSON files."""

    def __init__(self, directory: Path) -> None:
        self._dir = directory
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, task_id: str) -> Path:
        return self._dir / f"{task_id}.json"

    def save(self, task: Task) -> None:
        """Persist a task to disk (creates or overwrites)."""
        task.updated_at = datetime.now(timezone.utc).isoformat()
        with open(self._path(task.id), "w", encoding="utf-8") as fh:
            json.dump(task.to_dict(), fh, indent=2, ensure_ascii=False)

    def load(self, task_id: str) -> Task:
        """Load a task by id; raises FileNotFoundError if missing."""
        path = self._path(task_id)
        if not path.exists():
            raise FileNotFoundError(f"Task not found: {task_id}")
        with open(path, encoding="utf-8") as fh:
            return Task.from_dict(json.load(fh))

    def delete(self, task_id: str) -> bool:
        """Delete a task; returns True if it existed."""
        path = self._path(task_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def list_all(self) -> Iterator[Task]:
        """Yield all stored tasks (newest first by created_at)."""
        tasks = []
        for p in self._dir.glob("*.json"):
            with open(p, encoding="utf-8") as fh:
                tasks.append(Task.from_dict(json.load(fh)))
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        yield from tasks

    def list_by_status(self, status: TaskStatus) -> Iterator[Task]:
        """Yield tasks filtered by status."""
        for task in self.list_all():
            if task.status == status:
                yield task
