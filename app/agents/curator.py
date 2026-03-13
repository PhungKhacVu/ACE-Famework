"""
Curator Agent — converts Reflector insights into playbook DeltaUpdates.

The Curator distils the insights from a TaskResult into concrete bullet
candidates and decides which existing bullets were helpful or harmful.
"""
from __future__ import annotations

import re
from typing import List, Optional

from app.schemas.bullet import Bullet, DeltaUpdate
from app.schemas.task import TaskInput
from app.schemas.result import TaskResult
from app.agents.llm_service import LLMService
from app.utils.ids import new_id
from app.utils.logger import get_logger

logger = get_logger(__name__)

_PROMPT_TEMPLATE = """\
You are a curator agent building a reusable playbook of heuristics.

## Task Domain
{domain}

## Insights from the current task
{insights}

## Applied bullet IDs (these were used during generation)
{applied_ids}

## Was the final answer correct?
{correct}

Produce new playbook bullets distilling lessons from these insights.
Respond in this exact format:
<bullets>
- [bullet 1: concise, general, actionable heuristic]
- [bullet 2]
- [bullet 3]
</bullets>
<rationale>
[why these bullets will help future tasks]
</rationale>
"""


def _parse_response(raw: str, domain: str) -> tuple[List[Bullet], str]:
    """Extract (new_bullets, rationale) from the LLM response."""
    bullets: List[Bullet] = []
    rationale = ""

    m = re.search(r"<bullets>(.*?)</bullets>", raw, re.DOTALL)
    if m:
        block = m.group(1).strip()
        for line in block.splitlines():
            content = line.strip().lstrip("-•*").strip()
            if len(content) > 10:  # ignore very short / empty lines
                bullets.append(
                    Bullet(
                        id=new_id(),
                        content=content,
                        domain=domain,
                        source="curator",
                    )
                )

    m = re.search(r"<rationale>(.*?)</rationale>", raw, re.DOTALL)
    if m:
        rationale = m.group(1).strip()

    return bullets, rationale


class Curator:
    """
    Produces a :class:`~app.schemas.bullet.DeltaUpdate` from a TaskResult.

    Parameters
    ----------
    llm : LLMService
        The LLM backend to use.
    """

    def __init__(self, llm: Optional[LLMService] = None) -> None:
        self.llm = llm or LLMService()

    def run(self, task: TaskInput, result: TaskResult) -> DeltaUpdate:
        """
        Produce a DeltaUpdate based on the insights in *result*.

        Parameters
        ----------
        task : TaskInput
        result : TaskResult
            Must have *insights* populated (run Reflector first).

        Returns
        -------
        DeltaUpdate
        """
        if not result.insights:
            logger.info("Curator: no insights for task=%s — returning empty delta", task.id)
            return DeltaUpdate()

        insights_text = "\n".join(f"- {i}" for i in result.insights)
        applied_ids_text = ", ".join(result.applied_bullet_ids) or "(none)"
        correct_text = (
            "yes" if result.correct is True else
            "no" if result.correct is False else
            "unknown"
        )

        prompt = _PROMPT_TEMPLATE.format(
            domain=task.domain,
            insights=insights_text,
            applied_ids=applied_ids_text,
            correct=correct_text,
        )

        logger.info("Curator running task=%s", task.id)
        raw = self.llm.complete(prompt)
        new_bullets, rationale = _parse_response(raw, task.domain)

        # Determine helpful/harmful bullet IDs based on correctness
        helpful_ids: List[str] = []
        harmful_ids: List[str] = []
        if result.correct is True:
            helpful_ids = result.applied_bullet_ids
        elif result.correct is False:
            harmful_ids = result.applied_bullet_ids

        return DeltaUpdate(
            new_bullets=new_bullets,
            helpful_ids=helpful_ids,
            harmful_ids=harmful_ids,
            rationale=rationale,
        )
