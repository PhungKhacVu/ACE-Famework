"""
LLM service abstraction layer.

Three providers are supported out of the box:
  - "mock"   – deterministic template responses, no API key required
  - "openai" – OpenAI-compatible REST API
  - "ollama" – local Ollama server (http://localhost:11434)

The active provider is determined by ACE_LLM_PROVIDER in the environment
(defaults to "mock" so the framework runs fully offline).
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Optional

from app.config import (
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LLMService:
    """Thin wrapper around an LLM backend."""

    def __init__(self, provider: Optional[str] = None) -> None:
        self.provider = (provider or LLM_PROVIDER).lower()
        logger.info("LLMService initialised with provider=%r", self.provider)

    def complete(self, prompt: str, max_tokens: int = 512) -> str:
        """
        Send *prompt* to the configured backend and return the completion.

        Parameters
        ----------
        prompt : str
            The full prompt text.
        max_tokens : int
            Approximate token budget for the response.

        Returns
        -------
        str
            The model's text response.
        """
        if self.provider == "mock":
            return self._mock_complete(prompt)
        if self.provider == "openai":
            return self._openai_complete(prompt, max_tokens)
        if self.provider == "ollama":
            return self._ollama_complete(prompt, max_tokens)
        raise ValueError(f"Unknown LLM provider: {self.provider!r}")

    # ------------------------------------------------------------------
    # Mock provider (no API, deterministic)
    # ------------------------------------------------------------------

    def _mock_complete(self, prompt: str) -> str:
        """
        Return a structured mock response based on keywords in the prompt.

        This is intentionally simple — it exists only to make tests and
        demos run without any external service.
        """
        prompt_lower = prompt.lower()

        # Check most specific patterns first to avoid false matches
        if "curator" in prompt_lower or "curate" in prompt_lower or "distil" in prompt_lower:
            return (
                "<bullets>\n"
                "- Always decompose complex tasks into smaller sub-problems.\n"
                "- Verify assumptions before proceeding to the solution.\n"
                "- Summarise the key insight at the end of each reasoning step.\n"
                "</bullets>\n"
                "<rationale>\n"
                "These bullets distil the core lessons from the current task.\n"
                "</rationale>"
            )

        if "reflect" in prompt_lower or "analyse" in prompt_lower or "evaluate" in prompt_lower:
            return (
                "<reflection>\n"
                "The output appears to be reasonable and addresses the task.\n"
                "Key strengths: structured approach, clear reasoning.\n"
                "Potential weaknesses: limited context available.\n"
                "</reflection>\n"
                "<insights>\n"
                "- Breaking the problem into steps improves clarity.\n"
                "- Referencing domain heuristics reduces errors.\n"
                "- Explicit reasoning traces aid verification.\n"
                "</insights>\n"
                "<confidence>0.72</confidence>"
            )

        # Fallback — generic generate response
        return (
            "<reasoning>\n"
            "I will apply the relevant playbook bullets to this task.\n"
            "Step 1: Understand the problem statement.\n"
            "Step 2: Apply domain heuristics from the playbook.\n"
            "Step 3: Formulate a clear, structured answer.\n"
            "</reasoning>\n"
            "<output>\n"
            "Based on the available information and applied heuristics, "
            "here is my best answer to the task. I have considered the "
            "relevant domain knowledge and applied systematic reasoning.\n"
            "</output>"
        )

    # ------------------------------------------------------------------
    # OpenAI-compatible provider
    # ------------------------------------------------------------------

    def _openai_complete(self, prompt: str, max_tokens: int) -> str:
        if not OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. "
                "Set ACE_LLM_PROVIDER=mock to run without an API key."
            )
        payload = {
            "model": OPENAI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{OPENAI_BASE_URL}/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
        except urllib.error.URLError as exc:
            logger.error("OpenAI request failed: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Ollama provider (local)
    # ------------------------------------------------------------------

    def _ollama_complete(self, prompt: str, max_tokens: int) -> str:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            return result.get("response", "")
        except urllib.error.URLError as exc:
            logger.error("Ollama request failed: %s", exc)
            raise
