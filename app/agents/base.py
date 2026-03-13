"""Base agent interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas import Task
from app.services.llm import LLMBackend


class BaseAgent(ABC):
    """All agents must implement this interface."""

    def __init__(self, llm: LLMBackend) -> None:
        self.llm = llm

    @abstractmethod
    def run(self, task: Task) -> Task:
        """Execute the task and return the updated task object."""
