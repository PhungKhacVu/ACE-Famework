"""Curator agent – distils reflections into DeltaUpdate objects."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from app.schemas.bullet import Bullet, BulletType, DeltaUpdate
from app.schemas.result import AgentOutput
from app.schemas.task import TaskInput
from app.services.llm import BaseLLMProvider, llm
from app.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "You are a Curator agent in the ACE framework. "
    "Your job is to convert insights from the Reflector into structured DeltaUpdate JSON. "
    "Return a JSON object with keys: "
    "  'new_bullets': list of objects with 'content', 'bullet_type' (helpful/harmful/neutral), "
    "    'confidence' (float 0–1), 'tags' (list of strings), "
    "  'reinforce_ids': list of existing bullet IDs to reinforce (strings), "
    "  'penalise_ids': list of existing bullet IDs to penalise (strings)."
)


class CuratorAgent:
    def __init__(self, provider: BaseLLMProvider | None = None) -> None:
        self._provider = provider or llm()

    def run(
        self,
        task: TaskInput,
        reflection: Dict[str, Any],
        existing_bullet_ids: List[str] | None = None,
    ) -> tuple[AgentOutput, DeltaUpdate]:
        insights_text = "\n".join(
            f"- {i}" for i in reflection.get("insights", [])
        ) or "(none)"

        user_prompt = (
            f"TASK: {task.description}\n\n"
            f"REFLECTION INSIGHTS:\n{insights_text}\n\n"
            f"EXISTING BULLET IDs (for reinforce/penalise): "
            f"{', '.join(existing_bullet_ids or []) or 'none'}\n\n"
            "Output valid JSON only."
        )

        logger.info("[Curator] Running for task: %s", task.id)
        raw = self._provider.complete(SYSTEM_PROMPT, user_prompt)

        delta = self._parse_delta(raw, task.id)
        output = AgentOutput(agent="curator", content=raw)
        return output, delta

    def _parse_delta(self, raw: str, task_id: str) -> DeltaUpdate:
        try:
            data = self._extract_json(raw)
        except (json.JSONDecodeError, ValueError):
            logger.warning("[Curator] Could not parse JSON; returning empty DeltaUpdate")
            return DeltaUpdate()

        new_bullets: List[Bullet] = []
        for item in data.get("new_bullets", []):
            try:
                bt = BulletType(item.get("bullet_type", "neutral"))
            except ValueError:
                bt = BulletType.NEUTRAL
            new_bullets.append(
                Bullet(
                    content=item.get("content", ""),
                    bullet_type=bt,
                    confidence=float(item.get("confidence", 0.5)),
                    tags=item.get("tags", []),
                    source_task_id=task_id,
                )
            )

        return DeltaUpdate(
            new_bullets=new_bullets,
            reinforce_ids=data.get("reinforce_ids", []),
            penalise_ids=data.get("penalise_ids", []),
        )

    @staticmethod
    def _extract_json(raw: str) -> Dict[str, Any]:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end <= start:
            raise ValueError("No JSON object found")
        return json.loads(raw[start:end])
