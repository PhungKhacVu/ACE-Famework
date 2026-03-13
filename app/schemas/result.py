"""TaskResult dataclass."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class TaskResult:
    """
    The output produced by the ACE pipeline for a single task.

    Attributes
    ----------
    task_id : str
        Reference to the originating TaskInput.
    output : str
        Final generated answer / response.
    reasoning : str
        Internal chain-of-thought or scratchpad produced by the Generator.
    reflection : str
        The Reflector's analysis of whether the output was good.
    insights : list[str]
        Distilled learnings extracted by the Reflector.
    confidence : float
        Self-assessed confidence in [0, 1].
    correct : bool | None
        Whether the output matched ground truth (None if not evaluated).
    applied_bullet_ids : list[str]
        IDs of playbook bullets that were applied during generation.
    """

    task_id: str
    output: str = ""
    reasoning: str = ""
    reflection: str = ""
    insights: List[str] = field(default_factory=list)
    confidence: float = 0.5
    correct: bool | None = None
    applied_bullet_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "output": self.output,
            "reasoning": self.reasoning,
            "reflection": self.reflection,
            "insights": self.insights,
            "confidence": self.confidence,
            "correct": self.correct,
            "applied_bullet_ids": self.applied_bullet_ids,
        }
