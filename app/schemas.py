"""Data schemas (TypedDict) shared across the application."""
from __future__ import annotations

from typing import Any, List, TypedDict


class PlaybookStep(TypedDict):
    id: str
    description: str
    prompt: str


class Playbook(TypedDict):
    id: str
    name: str
    description: str
    steps: List[PlaybookStep]


class StepResult(TypedDict):
    step_id: str
    response: str
    ok: bool


class RunResult(TypedDict):
    playbook_id: str
    results: List[StepResult]
    metadata: Any
