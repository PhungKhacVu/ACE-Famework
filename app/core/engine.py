"""ACE Engine – orchestrates agents, stores, and services."""

from __future__ import annotations

from app.agents.playbook_agent import PlaybookAgent
from app.agents.simple_agent import SimpleAgent
from app.config import Config
from app.schemas import Playbook, Task, TaskStatus
from app.services.llm import get_llm_backend
from app.storage.playbook_store import PlaybookStore
from app.storage.task_store import TaskStore


class ACEEngine:
    """Main entry point for running ACE tasks and managing playbooks."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config.from_env()
        self.llm = get_llm_backend(self.config.llm_backend)
        self.playbook_store = PlaybookStore(self.config.playbooks_dir)
        self.task_store = TaskStore(self.config.tasks_dir)

    # ------------------------------------------------------------------
    # Task operations
    # ------------------------------------------------------------------

    def run_task(self, goal: str, playbook_id: str = "") -> Task:
        """Create and run a task, optionally driven by a playbook."""
        task = Task(goal=goal, playbook_id=playbook_id)

        if playbook_id:
            try:
                playbook = self.playbook_store.load(playbook_id)
                agent = PlaybookAgent(self.llm)
                task = agent.run_playbook(task, playbook)
            except FileNotFoundError:
                task.status = TaskStatus.FAILED
                task.result = f"Playbook '{playbook_id}' not found."
        else:
            agent_simple = SimpleAgent(self.llm)
            task = agent_simple.run(task)

        self.task_store.save(task)
        return task

    def get_task(self, task_id: str) -> Task:
        return self.task_store.load(task_id)

    def list_tasks(self) -> list[Task]:
        return list(self.task_store.list_all())

    # ------------------------------------------------------------------
    # Playbook operations
    # ------------------------------------------------------------------

    def save_playbook(self, playbook: Playbook) -> None:
        self.playbook_store.save(playbook)

    def get_playbook(self, playbook_id: str) -> Playbook:
        return self.playbook_store.load(playbook_id)

    def list_playbooks(self) -> list[Playbook]:
        return list(self.playbook_store.list_all())

    def delete_playbook(self, playbook_id: str) -> bool:
        return self.playbook_store.delete(playbook_id)
