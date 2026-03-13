"""Bullet dataclass — the atomic unit of the ACE playbook."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class Bullet:
    """
    A single playbook bullet representing a learned heuristic or rule.

    Attributes
    ----------
    id : str
        Unique identifier (UUID4 hex).
    content : str
        Human-readable heuristic text.
    domain : str
        Task domain this bullet applies to (e.g. "coding", "reasoning").
    helpful_count : int
        How many times applying this bullet led to success.
    harmful_count : int
        How many times applying this bullet led to failure.
    tags : list[str]
        Free-form tags for search / filtering.
    source : str
        Where this bullet came from ("curator", "manual", etc.).
    """

    id: str
    content: str
    domain: str = "general"
    helpful_count: int = 0
    harmful_count: int = 0
    tags: List[str] = field(default_factory=list)
    source: str = "curator"

    # ------------------------------------------------------------------
    # Derived metrics
    # ------------------------------------------------------------------

    @property
    def score(self) -> float:
        """Net score: helpful - harmful (higher is better)."""
        return float(self.helpful_count - self.harmful_count)

    @property
    def confidence(self) -> float:
        """
        Bayesian-style confidence in [0, 1].

        Returns 0.5 (neutral) when there is no evidence yet.
        """
        total = self.helpful_count + self.harmful_count
        if total == 0:
            return 0.5
        return self.helpful_count / total

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Bullet":
        return cls(
            id=data["id"],
            content=data["content"],
            domain=data.get("domain", "general"),
            helpful_count=data.get("helpful_count", 0),
            harmful_count=data.get("harmful_count", 0),
            tags=data.get("tags", []),
            source=data.get("source", "curator"),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class DeltaUpdate:
    """
    A proposed change to the playbook produced by the Curator.

    A delta can add new bullets or mark existing ones as helpful / harmful.
    """

    new_bullets: List[Bullet] = field(default_factory=list)
    helpful_ids: List[str] = field(default_factory=list)
    harmful_ids: List[str] = field(default_factory=list)
    rationale: str = ""

    def to_dict(self) -> dict:
        return {
            "new_bullets": [b.to_dict() for b in self.new_bullets],
            "helpful_ids": self.helpful_ids,
            "harmful_ids": self.harmful_ids,
            "rationale": self.rationale,
        }
