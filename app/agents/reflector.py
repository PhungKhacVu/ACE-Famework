"""Reflector agent – analyses the generator output and extracts insights."""

from __future__ import annotations

import json
from typing import Any, Dict

from app.schemas.result import AgentOutput
from app.schemas.task import TaskInput
from app.services.llm import BaseLLMProvider, llm
from app.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "You are a Reflector agent in the ACE framework. "
    "Analyse the task and the generated answer. "
    "Return a JSON object with keys: "
    "  'insights' (list of strings), "
    "  'confidence' (float 0–1), "
    "  'quality' (one of: excellent/good/fair/poor)."
)


class ReflectorAgent:
    def __init__(self, provider: BaseLLMProvider | None = None) -> None:
        self._provider = provider or llm()

    def run(self, task: TaskInput, generator_output: str) -> AgentOutput:
        user_prompt = (
            f"TASK: {task.description}\n\n"
            f"GENERATED ANSWER:\n{generator_output}\n\n"
            "Provide your reflection as valid JSON."
        )

        logger.info("[Reflector] Running for task: %s", task.id)
        raw = self._provider.complete(SYSTEM_PROMPT, user_prompt)

        # Attempt to parse JSON; fall back to a default structure
        reflection: Dict[str, Any] = self._parse(raw)
        return AgentOutput(
            agent="reflector",
            content=raw,
            metadata=reflection,
        )

    def _parse(self, raw: str) -> Dict[str, Any]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract JSON from within the response
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(raw[start:end])
                except json.JSONDecodeError:
                    pass
        return {"insights": [], "confidence": 0.5, "quality": "fair"}
