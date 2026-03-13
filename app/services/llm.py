"""LLM service abstraction with mock, OpenAI, and Ollama backends."""

from __future__ import annotations

import hashlib
import json
import textwrap
from typing import Any

from app.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class BaseLLMService:
    def complete(self, prompt: str, **kwargs: Any) -> str:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Mock – deterministic, no network required
# ---------------------------------------------------------------------------


class MockLLMService(BaseLLMService):
    """Deterministic mock that returns structured JSON based on prompt hash."""

    def complete(self, prompt: str, **kwargs: Any) -> str:
        # Use a hash of the prompt to make responses repeatable
        digest = hashlib.md5(prompt.encode()).hexdigest()[:8]

        lower = prompt.lower()

        # Match curator prompt first (most specific keywords)
        if "knowledge curator" in lower or "generalizable" in lower:
            return json.dumps(
                {
                    "deltas": [
                        {
                            "content": f"Distilled insight [{digest}]: apply structured reasoning.",
                            "domain": "general",
                            "confidence": 0.7,
                            "helpful_delta": 1,
                            "harmful_delta": 0,
                            "tags": ["distilled", "mock"],
                        }
                    ]
                }
            )

        # Match reflector prompt
        if "critical evaluator" in lower or "quality_score" in lower:
            return json.dumps(
                {
                    "is_correct": True,
                    "quality_score": 0.7,
                    "insight": f"Mock insight: the approach [{digest}] was reasonable.",
                    "suggested_deltas": [
                        {
                            "content": f"When solving tasks like [{digest}], use a systematic approach.",
                            "domain": "general",
                            "confidence": 0.65,
                            "helpful_delta": 1,
                            "harmful_delta": 0,
                            "tags": ["mock"],
                        }
                    ],
                }
            )

        # Match generator prompt (contains "playbook bullets")
        if "playbook bullets" in lower or "generate" in lower or "answer" in lower:
            return json.dumps(
                {
                    "answer": f"Mock answer for task [{digest}]",
                    "reasoning": "This is a deterministic mock response based on the prompt hash.",
                    "confidence": 0.6,
                    "bullets_used": [],
                }
            )

        # Default fallback
        return json.dumps({"response": f"Mock response [{digest}]"})


# ---------------------------------------------------------------------------
# OpenAI backend
# ---------------------------------------------------------------------------


class OpenAILLMService(BaseLLMService):
    def __init__(self) -> None:
        try:
            import openai  # type: ignore

            self._client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        except ImportError as exc:
            raise RuntimeError(
                "openai package not installed. Run: pip install openai"
            ) from exc

    def complete(self, prompt: str, **kwargs: Any) -> str:
        response = self._client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Ollama backend
# ---------------------------------------------------------------------------


class OllamaLLMService(BaseLLMService):
    def __init__(self) -> None:
        try:
            import requests  # type: ignore

            self._requests = requests
        except ImportError as exc:
            raise RuntimeError(
                "requests package not installed. Run: pip install requests"
            ) from exc

    def complete(self, prompt: str, **kwargs: Any) -> str:
        url = f"{config.OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": config.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        }
        resp = self._requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json().get("response", "")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_llm_service() -> BaseLLMService:
    provider = config.LLM_PROVIDER
    logger.info("Using LLM provider: %s", provider)
    if provider == "openai":
        return OpenAILLMService()
    if provider == "ollama":
        return OllamaLLMService()
    return MockLLMService()
