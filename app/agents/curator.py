"""Curator agent: distils insights into candidate playbook bullets."""
from __future__ import annotations
from app.schemas import TaskInput, TaskResult
from app.services import get_llm_service


class CuratorAgent:
    """Converts reflector insights into delta bullet candidates."""

    def __init__(self, llm=None):
        self._llm = llm or get_llm_service()

    def run(self, result: TaskResult, task: TaskInput) -> TaskResult:
        delta = self._llm.curate(result.insights, task.domain)
        result.delta_bullets = delta
        return result
