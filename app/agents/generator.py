"""Generator agent – produces a task answer using playbook bullets."""

from __future__ import annotations

import json

from app.schemas.bullet import Bullet
from app.schemas.task import TaskInput, TaskResult
from app.services.llm import BaseLLMService
from app.utils.logger import get_logger

logger = get_logger(__name__)

_PROMPT_TEMPLATE = """\
You are an expert assistant. Use the following playbook bullets as guidance.

## Playbook bullets
{bullets}

## Task
{description}

## Context
{context}

Respond with a JSON object with keys: answer, reasoning, confidence (0-1), bullets_used (list of bullet ids you relied on).
"""


class GeneratorAgent:
    def __init__(self, llm: BaseLLMService) -> None:
        self._llm = llm

    def run(self, task: TaskInput, bullets: list[Bullet]) -> TaskResult:
        bullet_text = "\n".join(
            f"- [{b.id}] ({b.domain}) {b.content}" for b in bullets
        ) or "(no bullets yet)"

        prompt = _PROMPT_TEMPLATE.format(
            bullets=bullet_text,
            description=task.description,
            context=json.dumps(task.context, ensure_ascii=False),
        )

        logger.debug("Generator prompt for task %s", task.id)
        raw = self._llm.complete(prompt)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"answer": raw, "reasoning": "", "confidence": 0.5, "bullets_used": []}

        return TaskResult(
            task_id=task.id,
            answer=str(data.get("answer", "")),
            reasoning=str(data.get("reasoning", "")),
            bullets_used=list(data.get("bullets_used", [])),
            confidence=float(data.get("confidence", 0.5)),
        )
