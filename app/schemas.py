"""Domain schemas using stdlib dataclasses."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class StepType(str, Enum):
    PROMPT = "prompt"
    TOOL = "tool"
    CONDITION = "condition"


@dataclass
class Step:
    """A single step inside a playbook."""

    name: str
    type: StepType
    instruction: str
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type.value,
            "instruction": self.instruction,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Step":
        return cls(
            name=data["name"],
            type=StepType(data.get("type", StepType.PROMPT.value)),
            instruction=data["instruction"],
            params=data.get("params", {}),
        )


@dataclass
class Playbook:
    """A reusable workflow composed of ordered steps."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    steps: list[Step] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: _now_iso())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Playbook":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            steps=[Step.from_dict(s) for s in data.get("steps", [])],
            created_at=data.get("created_at", _now_iso()),
        )


@dataclass
class Message:
    """A single message in an agent conversation."""

    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: str = field(default_factory=lambda: _now_iso())

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content, "timestamp": self.timestamp}

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp", _now_iso()),
        )


@dataclass
class Task:
    """A concrete execution of a playbook (or ad-hoc prompt)."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    playbook_id: str = ""
    goal: str = ""
    status: TaskStatus = TaskStatus.PENDING
    messages: list[Message] = field(default_factory=list)
    result: str = ""
    created_at: str = field(default_factory=lambda: _now_iso())
    updated_at: str = field(default_factory=lambda: _now_iso())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "playbook_id": self.playbook_id,
            "goal": self.goal,
            "status": self.status.value,
            "messages": [m.to_dict() for m in self.messages],
            "result": self.result,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            playbook_id=data.get("playbook_id", ""),
            goal=data.get("goal", ""),
            status=TaskStatus(data.get("status", TaskStatus.PENDING.value)),
            messages=[Message.from_dict(m) for m in data.get("messages", [])],
            result=data.get("result", ""),
            created_at=data.get("created_at", _now_iso()),
            updated_at=data.get("updated_at", _now_iso()),
        )
