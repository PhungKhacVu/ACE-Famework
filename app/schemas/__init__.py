"""Schemas: shared dataclasses for the ACE framework."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import uuid
import time


@dataclass
class Bullet:
    """A single playbook bullet (a learned action guideline)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    helpful_count: int = 0
    harmful_count: int = 0
    confidence: float = 0.5
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "helpful_count": self.helpful_count,
            "harmful_count": self.harmful_count,
            "confidence": self.confidence,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(d: dict) -> "Bullet":
        return Bullet(
            id=d.get("id", str(uuid.uuid4())),
            text=d.get("text", ""),
            helpful_count=d.get("helpful_count", 0),
            harmful_count=d.get("harmful_count", 0),
            confidence=d.get("confidence", 0.5),
            tags=d.get("tags", []),
            created_at=d.get("created_at", time.time()),
            updated_at=d.get("updated_at", time.time()),
        )


@dataclass
class TaskInput:
    """A task submitted to the ACE pipeline."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    domain: str = "general"
    context: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "domain": self.domain,
            "context": self.context,
        }

    @staticmethod
    def from_dict(d: dict) -> "TaskInput":
        return TaskInput(
            id=d.get("id", str(uuid.uuid4())),
            description=d.get("description", ""),
            domain=d.get("domain", "general"),
            context=d.get("context", ""),
        )


@dataclass
class TaskResult:
    """Output produced by the ACE pipeline for a task."""
    task_id: str = ""
    reasoning: str = ""
    answer: str = ""
    confidence: float = 0.5
    insights: List[str] = field(default_factory=list)
    delta_bullets: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "reasoning": self.reasoning,
            "answer": self.answer,
            "confidence": self.confidence,
            "insights": self.insights,
            "delta_bullets": self.delta_bullets,
        }
