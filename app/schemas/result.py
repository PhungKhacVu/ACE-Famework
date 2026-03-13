"""Reflection and adaptation result schemas."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.bullet import DeltaUpdate
from app.schemas.task import TaskResult


class ReflectorOutput(BaseModel):
    """Insights produced by the Reflector agent."""

    task_id: str
    is_correct: bool
    quality_score: float
    insight: str
    suggested_deltas: list[DeltaUpdate]


class AdaptationResult(BaseModel):
    """Summary of one offline/online adaptation cycle."""

    tasks_processed: int = 0
    bullets_added: int = 0
    bullets_updated: int = 0
    bullets_merged: int = 0
    task_results: list[TaskResult] = []
