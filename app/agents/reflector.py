"""
Reflector Agent — analyses a task result and extracts insights.

The Reflector compares the Generator's output to the ground truth (if
available), scores confidence, and distils learning insights.
"""
from __future__ import annotations

import re
from typing import List, Optional

from app.schemas.task import TaskInput
from app.schemas.result import TaskResult
from app.agents.llm_service import LLMService
from app.utils.logger import get_logger

logger = get_logger(__name__)

_PROMPT_TEMPLATE = """\
You are a reflection agent analysing an AI task result.

## Task
{instruction}

## Agent Output
{output}

## Reasoning Trace
{reasoning}

{ground_truth_section}

Analyse the output and respond in this exact format:
<reflection>
[brief qualitative assessment: strengths, weaknesses, correctness]
</reflection>
<insights>
- [insight 1]
- [insight 2]
- [insight 3]
</insights>
<confidence>{confidence_hint}</confidence>
"""


def _ground_truth_section(gt: str) -> str:
    if not gt:
        return ""
    return f"## Ground Truth\n{gt}"


def _parse_response(raw: str) -> tuple[str, List[str], float]:
    """Extract (reflection, insights, confidence) from the LLM response."""
    reflection = ""
    insights: List[str] = []
    confidence = 0.5

    m = re.search(r"<reflection>(.*?)</reflection>", raw, re.DOTALL)
    if m:
        reflection = m.group(1).strip()

    m = re.search(r"<insights>(.*?)</insights>", raw, re.DOTALL)
    if m:
        block = m.group(1).strip()
        for line in block.splitlines():
            line = line.strip().lstrip("-•*").strip()
            if line:
                insights.append(line)

    m = re.search(r"<confidence>([\d.]+)</confidence>", raw)
    if m:
        try:
            confidence = float(m.group(1))
            confidence = max(0.0, min(1.0, confidence))
        except ValueError:
            pass

    return reflection, insights, confidence


def _simple_correct(output: str, ground_truth: str) -> Optional[bool]:
    """
    Heuristic correctness check when no LLM evaluation is available.

    Returns True/False/None (None = indeterminate).
    """
    if not ground_truth:
        return None
    # Exact match (case-insensitive, stripped)
    if output.strip().lower() == ground_truth.strip().lower():
        return True
    # Ground-truth contained in output
    if ground_truth.strip().lower() in output.lower():
        return True
    return False


class Reflector:
    """
    Reflects on a :class:`~app.schemas.result.TaskResult` and enriches it
    with qualitative analysis and extracted insights.

    Parameters
    ----------
    llm : LLMService
        The LLM backend to use.
    """

    def __init__(self, llm: Optional[LLMService] = None) -> None:
        self.llm = llm or LLMService()

    def run(self, task: TaskInput, result: TaskResult) -> TaskResult:
        """
        Run reflection on *result* and return an enriched copy.

        Modifies and returns the same *result* object for convenience.
        """
        prompt = _PROMPT_TEMPLATE.format(
            instruction=task.instruction,
            output=result.output,
            reasoning=result.reasoning or "(not provided)",
            ground_truth_section=_ground_truth_section(task.ground_truth),
            confidence_hint="0.5",
        )

        logger.info("Reflector running task=%s", task.id)
        raw = self.llm.complete(prompt)
        reflection, insights, confidence = _parse_response(raw)

        result.reflection = reflection
        result.insights = insights
        result.confidence = confidence
        result.correct = _simple_correct(result.output, task.ground_truth)

        return result
