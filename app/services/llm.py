"""LLM service abstraction with mock, OpenAI, and Ollama providers.

Default provider is ``mock`` so the framework runs fully offline
without any API keys.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from app.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BaseLLMProvider(ABC):
    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Return a completion string given system and user messages."""


# ---------------------------------------------------------------------------
# Mock provider – deterministic, no API key required
# ---------------------------------------------------------------------------

class MockLLMProvider(BaseLLMProvider):
    """Returns canned but structurally valid responses for every prompt type."""

    def complete(self, system: str, user: str) -> str:
        system_lower = system.lower()
        if "generator" in system_lower:
            return (
                "Based on the available context I will approach this step-by-step. "
                "First, I identify the key requirements. "
                "Second, I apply known best practices. "
                "Third, I synthesise a clear answer."
            )
        if "curator" in system_lower:
            return json.dumps({
                "new_bullets": [
                    {
                        "content": "Decompose complex tasks before attempting solutions.",
                        "bullet_type": "helpful",
                        "confidence": 0.8,
                        "tags": ["strategy", "decomposition"],
                    }
                ],
                "reinforce_ids": [],
                "penalise_ids": [],
            })
        if "reflector" in system_lower:
            return json.dumps({
                "insights": [
                    "Breaking the task into sub-steps improved clarity.",
                    "Referencing existing playbook bullets accelerated reasoning.",
                ],
                "confidence": 0.78,
                "quality": "good",
            })
        return "Acknowledged."


# ---------------------------------------------------------------------------
# OpenAI-compatible provider
# ---------------------------------------------------------------------------

class OpenAIProvider(BaseLLMProvider):
    def __init__(self) -> None:
        try:
            import openai  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "openai package is required for OpenAI provider. "
                "Install it with: pip install openai"
            ) from exc
        self._client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self._model = config.OPENAI_MODEL

    def complete(self, system: str, user: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Ollama provider (local models)
# ---------------------------------------------------------------------------

class OllamaProvider(BaseLLMProvider):
    def __init__(self) -> None:
        try:
            import requests  # type: ignore
            self._requests = requests
        except ImportError as exc:
            raise ImportError(
                "requests package is required for Ollama provider. "
                "Install it with: pip install requests"
            ) from exc
        self._base_url = config.OLLAMA_BASE_URL
        self._model = config.OLLAMA_MODEL

    def complete(self, system: str, user: str) -> str:
        payload: Dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
        }
        resp = self._requests.post(
            f"{self._base_url}/api/chat", json=payload, timeout=120
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_PROVIDERS: Dict[str, type] = {
    "mock": MockLLMProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
}


def get_llm_provider(provider: str | None = None) -> BaseLLMProvider:
    name = (provider or config.LLM_PROVIDER).lower()
    cls = _PROVIDERS.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown LLM provider '{name}'. Choose from: {list(_PROVIDERS)}"
        )
    logger.info("Using LLM provider: %s", name)
    return cls()


# Module-level singleton (lazy, replaced in tests easily)
_llm: BaseLLMProvider | None = None


def llm() -> BaseLLMProvider:
    global _llm
    if _llm is None:
        _llm = get_llm_provider()
    return _llm


def reset_llm(provider: BaseLLMProvider | None = None) -> None:
    """Replace the singleton – useful in tests."""
    global _llm
    _llm = provider
