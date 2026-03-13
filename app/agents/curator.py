"""Curator agent – distils reflector insights into clean DeltaUpdates."""

from __future__ import annotations

import json

from app.schemas.bullet import DeltaUpdate
from app.schemas.result import ReflectorOutput
from app.services.llm import BaseLLMService
from app.utils.logger import get_logger

logger = get_logger(__name__)

_PROMPT_TEMPLATE = """\
You are a knowledge curator. Given the following reflection insight, produce clean, generalizable bullet points for a playbook.

## Insight
{insight}

## Suggested deltas (raw)
{raw_deltas}

Respond with a JSON object with a single key "deltas" containing a list of objects with keys:
content, domain, confidence, helpful_delta, harmful_delta, tags.

Ensure each bullet is:
- Concise (max 200 characters)
- Actionable and domain-agnostic where possible
- Not a duplicate of information already covered
"""


class CuratorAgent:
    def __init__(self, llm: BaseLLMService) -> None:
        self._llm = llm

    def run(self, reflection: ReflectorOutput) -> list[DeltaUpdate]:
        if not reflection.insight and not reflection.suggested_deltas:
            return []

        raw_deltas = json.dumps(
            [d.model_dump() for d in reflection.suggested_deltas], ensure_ascii=False
        )

        prompt = _PROMPT_TEMPLATE.format(
            insight=reflection.insight,
            raw_deltas=raw_deltas,
        )

        logger.debug("Curator processing reflection for task %s", reflection.task_id)
        raw = self._llm.complete(prompt)

        try:
            data = json.loads(raw)
            deltas_raw = data.get("deltas", [])
        except json.JSONDecodeError:
            # Fall back to using reflection's own suggested deltas
            logger.warning("Curator failed to parse LLM output; using raw suggested deltas.")
            return reflection.suggested_deltas

        result: list[DeltaUpdate] = []
        for item in deltas_raw:
            try:
                result.append(DeltaUpdate(**item))
            except Exception as exc:
                logger.warning("Skipping malformed delta: %s", exc)

        return result or reflection.suggested_deltas
