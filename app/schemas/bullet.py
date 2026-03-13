"""Bullet and DeltaUpdate data models – core ACE data structures."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from app.utils.ids import new_id


class BulletType(str, Enum):
    HELPFUL = "helpful"
    HARMFUL = "harmful"
    NEUTRAL = "neutral"


class Bullet(BaseModel):
    """A single adaptive knowledge bullet stored in a playbook."""

    id: str = Field(default_factory=new_id)
    content: str
    bullet_type: BulletType = BulletType.NEUTRAL
    helpful_count: int = 0
    harmful_count: int = 0
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    tags: List[str] = Field(default_factory=list)
    source_task_id: Optional[str] = None

    @property
    def score(self) -> float:
        """Simple helpfulness score: helpful – harmful, normalised."""
        total = self.helpful_count + self.harmful_count
        if total == 0:
            return self.confidence
        return self.helpful_count / total

    def reinforce(self) -> None:
        self.helpful_count += 1

    def penalise(self) -> None:
        self.harmful_count += 1


class DeltaUpdate(BaseModel):
    """A proposed change to the playbook produced by the Curator agent."""

    new_bullets: List[Bullet] = Field(default_factory=list)
    reinforce_ids: List[str] = Field(default_factory=list)
    penalise_ids: List[str] = Field(default_factory=list)
