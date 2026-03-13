"""TaskInput dataclass."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TaskInput:
    """
    Represents a single task fed into the ACE pipeline.

    Attributes
    ----------
    id : str
        Unique task identifier.
    instruction : str
        The natural-language task description / prompt.
    domain : str
        Task domain for playbook bullet retrieval.
    context : dict
        Optional extra context (e.g. code snippet, image path).
    ground_truth : str
        Expected output, used for offline evaluation.
    """

    id: str
    instruction: str
    domain: str = "general"
    context: Dict[str, Any] = field(default_factory=dict)
    ground_truth: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "instruction": self.instruction,
            "domain": self.domain,
            "context": self.context,
            "ground_truth": self.ground_truth,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TaskInput":
        return cls(
            id=data["id"],
            instruction=data["instruction"],
            domain=data.get("domain", "general"),
            context=data.get("context", {}),
            ground_truth=data.get("ground_truth", ""),
        )

    @classmethod
    def load_jsonl(cls, path: str) -> List["TaskInput"]:
        """Load tasks from a JSON-lines file."""
        tasks: List[TaskInput] = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    tasks.append(cls.from_dict(json.loads(line)))
        return tasks

    @classmethod
    def load_json(cls, path: str) -> List["TaskInput"]:
        """Load tasks from a JSON array file."""
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return [cls.from_dict(d) for d in data]
        return [cls.from_dict(data)]
