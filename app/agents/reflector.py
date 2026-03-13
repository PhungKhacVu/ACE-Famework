"""Reflector agent: analyses reasoning and extracts actionable insights."""
from __future__ import annotations
from app.schemas import TaskInput, TaskResult
from app.services import get_llm_service


class ReflectorAgent:
    """Produces insights from a completed TaskResult."""

    def __init__(self, llm=None):
        self._llm = llm or get_llm_service()

    def run(self, result: TaskResult, task: TaskInput) -> TaskResult:
        insights = self._llm.reflect(result.reasoning, task.description)
        result.insights = insights
        result.confidence = min(result.confidence + 0.05 * len(insights), 1.0)
        return result
