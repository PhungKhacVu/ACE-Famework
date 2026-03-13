"""LLM service interface + mock backend – zero external deps."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from app.schemas import Message


class LLMBackend(ABC):
    """Abstract LLM backend interface."""

    @abstractmethod
    def chat(self, messages: List[Message]) -> str:
        """Send a list of messages and return the assistant reply."""


class MockLLMBackend(LLMBackend):
    """Deterministic mock backend for local testing without any API key."""

    _KEYWORD_REPLIES: dict[str, str] = {
        "hello": "Hello! I am ACE, your Autonomous Cognitive Engine. How can I help?",
        "help": "Available commands: run <playbook>, list playbooks, list tasks, status <id>.",
        "plan": "Step 1 – analyse goal. Step 2 – decompose into sub-tasks. Step 3 – execute.",
        "summarize": "Summary: the task was completed successfully with no errors.",
        "error": "An error occurred. Please check your input and try again.",
    }

    def chat(self, messages: List[Message]) -> str:
        """Return a canned reply based on keywords in the last user message."""
        last_user = next(
            (m.content for m in reversed(messages) if m.role == "user"), ""
        )
        lower = last_user.lower()
        for keyword, reply in self._KEYWORD_REPLIES.items():
            if keyword in lower:
                return reply
        return f'[mock] Received: "{last_user}". (No live LLM configured – running in mock mode.)'


def get_llm_backend(backend_name: str) -> LLMBackend:
    """Factory: return the appropriate LLM backend."""
    if backend_name == "mock":
        return MockLLMBackend()
    raise ValueError(
        f"Unknown LLM backend: '{backend_name}'. "
        "Currently supported: 'mock'. Set ACE_LLM_BACKEND=mock."
    )
