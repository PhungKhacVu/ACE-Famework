"""Reflector agent – evaluates the generated answer and extracts insights."""

from __future__ import annotations

import json

from app.schemas.bullet import DeltaUpdate
from app.schemas.result import ReflectorOutput
from app.schemas.task import TaskInput, TaskResult
from app.services.llm import BaseLLMService
from app.utils.logger import get_logger

logger = get_logger(__name__)

_PROMPT_TEMPLATE = """\
You are a critical evaluator. Analyse the following task and the produced answer.

## Task
{description}

## Ground truth (if available)
{ground_truth}

## Agent answer
{answer}

## Reasoning
{reasoning}

Respond with a JSON object with keys:
- is_correct (bool)
- quality_score (float 0-1)
- insight (string: one-sentence lesson learnt)
- suggested_deltas (list of objects with keys: content, domain, confidence, helpful_delta, harmful_delta, tags)
"""


class ReflectorAgent:
    def __init__(self, llm: BaseLLMService) -> None:
        self._llm = llm

    def run(self, task: TaskInput, result: TaskResult) -> ReflectorOutput:
        prompt = _PROMPT_TEMPLATE.format(
            description=task.description,
            ground_truth=task.ground_truth or "N/A",
            answer=result.answer,
            reasoning=result.reasoning,
        )

        logger.debug("Reflector prompt for task %s", task.id)
        raw = self._llm.complete(prompt)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {
                "is_correct": False,
                "quality_score": 0.5,
                "insight": raw[:200],
                "suggested_deltas": [],
            }

        deltas = [DeltaUpdate(**d) for d in data.get("suggested_deltas", [])]
        return ReflectorOutput(
            task_id=task.id,
            is_correct=bool(data.get("is_correct", False)),
            quality_score=float(data.get("quality_score", 0.5)),
            insight=str(data.get("insight", "")),
            suggested_deltas=deltas,
        )
