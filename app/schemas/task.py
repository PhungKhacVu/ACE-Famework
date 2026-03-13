"""Task input/output schemas."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from app.utils.ids import new_id


class TaskInput(BaseModel):
    """A task presented to the ACE pipeline."""

    id: str = Field(default_factory=new_id)
    description: str
    domain: str = "general"
    context: dict[str, Any] = Field(default_factory=dict)
    ground_truth: Optional[str] = None


class TaskResult(BaseModel):
    """The output produced by the Generator agent for a task."""

    task_id: str
    answer: str
    reasoning: str = ""
    bullets_used: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
