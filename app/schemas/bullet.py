"""Bullet data model – the atomic unit of the ACE playbook."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from app.utils.ids import new_id


class Bullet(BaseModel):
    """A single actionable insight stored in the playbook."""

    id: str = Field(default_factory=new_id)
    content: str
    domain: str = "general"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    helpful_count: int = Field(default=0, ge=0)
    harmful_count: int = Field(default=0, ge=0)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    tags: list[str] = Field(default_factory=list)
    embedding: Optional[list[float]] = None

    @property
    def net_score(self) -> float:
        """Composite ranking score."""
        return self.confidence + 0.1 * self.helpful_count - 0.15 * self.harmful_count

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()


class DeltaUpdate(BaseModel):
    """Proposed change from the Curator to be merged into the playbook."""

    content: str
    domain: str = "general"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    helpful_delta: int = 0
    harmful_delta: int = 0
    tags: list[str] = Field(default_factory=list)
    source_task_id: Optional[str] = None
