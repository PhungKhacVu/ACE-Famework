"""Generator agent: produces reasoning and an answer for a given task."""
from __future__ import annotations
from app.schemas import TaskInput, TaskResult
from app.services import get_llm_service


class GeneratorAgent:
    """Reads playbook bullets for context and generates a response."""

    def __init__(self, llm=None):
        self._llm = llm or get_llm_service()

    def run(self, task: TaskInput, playbook_context: str = "") -> TaskResult:
        reasoning = self._llm.generate(task.description, playbook_context)
        # The answer is a concise summary of the reasoning
        answer = reasoning.split(".")[0].strip() + "."
        return TaskResult(
            task_id=task.id,
            reasoning=reasoning,
            answer=answer,
            confidence=0.7,
        )
