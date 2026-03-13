"""
Generator Agent — produces a reasoned answer for a task.

Retrieves relevant playbook bullets, constructs a prompt, calls the LLM,
and parses the structured response.
"""
from __future__ import annotations

import re
from typing import List, Optional

from app.schemas.bullet import Bullet
from app.schemas.task import TaskInput
from app.schemas.result import TaskResult
from app.agents.llm_service import LLMService
from app.core.ranking import rank_bullets
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Prompt template — kept simple for token efficiency
_PROMPT_TEMPLATE = """\
You are an adaptive AI agent.

## Your Playbook (apply these heuristics)
{bullets_section}

## Task
{instruction}

{context_section}

Respond in this exact format:
<reasoning>
[your step-by-step reasoning]
</reasoning>
<output>
[your final answer]
</output>
"""


def _format_bullets(bullets: List[Bullet]) -> str:
    if not bullets:
        return "(No relevant playbook bullets available yet.)"
    return "\n".join(f"- {b.content}" for b in bullets)


def _format_context(context: dict) -> str:
    if not context:
        return ""
    lines = ["## Additional Context"]
    for k, v in context.items():
        lines.append(f"- {k}: {v}")
    return "\n".join(lines)


def _parse_response(raw: str) -> tuple[str, str]:
    """Extract (reasoning, output) from the structured LLM response."""
    reasoning = ""
    output = ""

    m = re.search(r"<reasoning>(.*?)</reasoning>", raw, re.DOTALL)
    if m:
        reasoning = m.group(1).strip()

    m = re.search(r"<output>(.*?)</output>", raw, re.DOTALL)
    if m:
        output = m.group(1).strip()

    if not output:
        # Fallback: use the entire response as output
        output = raw.strip()

    return reasoning, output


class Generator:
    """
    Generates a task response by conditioning on playbook bullets.

    Parameters
    ----------
    llm : LLMService
        The LLM backend to use for generation.
    top_k_bullets : int
        How many playbook bullets to include in the prompt.
    """

    def __init__(self, llm: Optional[LLMService] = None, top_k_bullets: int = 5) -> None:
        self.llm = llm or LLMService()
        self.top_k_bullets = top_k_bullets

    def run(self, task: TaskInput, bullets: List[Bullet]) -> TaskResult:
        """
        Generate a response for *task* using *bullets* as context.

        Parameters
        ----------
        task : TaskInput
        bullets : list of Bullet
            Pre-retrieved relevant bullets (may be empty).

        Returns
        -------
        TaskResult
            Populated with reasoning, output, and applied bullet IDs.
        """
        # Rank and select top-k bullets
        ranked = rank_bullets(bullets, query=task.instruction)
        selected = [b for b, _ in ranked[: self.top_k_bullets]]

        prompt = _PROMPT_TEMPLATE.format(
            bullets_section=_format_bullets(selected),
            instruction=task.instruction,
            context_section=_format_context(task.context),
        )

        logger.info("Generator running task=%s (bullets=%d)", task.id, len(selected))
        raw = self.llm.complete(prompt)
        reasoning, output = _parse_response(raw)

        return TaskResult(
            task_id=task.id,
            output=output,
            reasoning=reasoning,
            applied_bullet_ids=[b.id for b in selected],
        )
