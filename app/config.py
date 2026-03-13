"""Application configuration – pure stdlib, no external deps."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

_DEFAULT_DATA_DIR = Path(__file__).parent.parent / "data"


@dataclass
class Config:
    data_dir: Path = field(default_factory=lambda: _DEFAULT_DATA_DIR)
    playbooks_dir: Path = field(init=False)
    tasks_dir: Path = field(init=False)
    llm_backend: str = "mock"  # "mock" | future: "openai" | "ollama"
    max_steps: int = 10

    def __post_init__(self) -> None:
        self.playbooks_dir = self.data_dir / "playbooks"
        self.tasks_dir = self.data_dir / "tasks"
        self.playbooks_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> "Config":
        """Load config from environment variables (all optional)."""
        data_dir = Path(os.environ.get("ACE_DATA_DIR", str(_DEFAULT_DATA_DIR)))
        llm_backend = os.environ.get("ACE_LLM_BACKEND", "mock")
        max_steps = int(os.environ.get("ACE_MAX_STEPS", "10"))
        return cls(data_dir=data_dir, llm_backend=llm_backend, max_steps=max_steps)

    @classmethod
    def from_file(cls, path: Path) -> "Config":
        """Load config from a JSON file."""
        with open(path) as fh:
            data = json.load(fh)
        kwargs: dict = {}
        if "data_dir" in data:
            kwargs["data_dir"] = Path(data["data_dir"])
        if "llm_backend" in data:
            kwargs["llm_backend"] = data["llm_backend"]
        if "max_steps" in data:
            kwargs["max_steps"] = int(data["max_steps"])
        return cls(**kwargs)
