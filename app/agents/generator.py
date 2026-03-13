"""Generator agent – produces an initial answer for a task.

It retrieves the top relevant bullets from the playbook and uses them
as additional context when prompting the LLM.
"""

from __future__ import annotations

from typing import List

from app.core.ranking import rank_bullets
from app.schemas.bullet import Bullet
from app.schemas.result import AgentOutput
from app.schemas.task import TaskInput
from app.services.llm import BaseLLMProvider, llm
from app.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "You are a Generator agent in the ACE (Adaptive Cognition Engineering) framework. "
    "Your job is to produce a clear, step-by-step answer for the given task. "
    "Use the playbook bullets provided as prior knowledge to improve your reasoning."
)


class GeneratorAgent:
    def __init__(
        self,
        provider: BaseLLMProvider | None = None,
        top_bullets: int = 5,
    ) -> None:
        self._provider = provider or llm()
        self._top_bullets = top_bullets

    def run(self, task: TaskInput, bullets: List[Bullet]) -> AgentOutput:
        top = rank_bullets(bullets, self._top_bullets)
        bullet_text = "\n".join(
            f"- [{b.bullet_type.value}] {b.content}" for b in top
        ) or "(no playbook bullets available yet)"

        user_prompt = (
            f"TASK: {task.description}\n\n"
            f"CONTEXT: {task.context or 'N/A'}\n\n"
            f"PLAYBOOK BULLETS:\n{bullet_text}\n\n"
            "Please provide a comprehensive answer."
        )

        logger.info("[Generator] Running for task: %s", task.id)
        answer = self._provider.complete(SYSTEM_PROMPT, user_prompt)
        return AgentOutput(agent="generator", content=answer)
