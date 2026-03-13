"""Mock LLM service — runs entirely offline, no API key required.

When ACE_LLM_PROVIDER=mock (default), all completions are generated
deterministically from a small template library so the full pipeline
works without any network access or paid account.
"""
from __future__ import annotations
import hashlib
from typing import List


class MockLLMService:
    """Deterministic mock that simulates Generator/Reflector/Curator responses."""

    # Small pool of template responses; index selected by hash of prompt
    _GENERATOR_TEMPLATES = [
        (
            "I will approach this step-by-step: first understand the goal, "
            "then break it into sub-tasks, then execute each sub-task carefully."
        ),
        (
            "To complete this task I need to: 1) clarify requirements, "
            "2) gather relevant context, 3) produce a structured output."
        ),
        (
            "My strategy: identify the core problem, apply domain knowledge, "
            "verify the result against known constraints."
        ),
    ]

    _REFLECTOR_TEMPLATES = [
        ["Applied systematic decomposition", "Verified constraints at each step"],
        ["Used domain-specific heuristics", "Cross-checked intermediate results"],
        ["Leveraged prior context from playbook", "Maintained consistency throughout"],
    ]

    _CURATOR_TEMPLATES = [
        [
            "Always decompose complex tasks before acting",
            "Verify each sub-result before proceeding",
        ],
        [
            "Use domain heuristics to guide decisions",
            "Cross-check results with known constraints",
        ],
        [
            "Leverage playbook context for faster resolution",
            "Maintain consistency across all steps",
        ],
    ]

    def _pick(self, prompt: str, pool: list):
        digest = int(hashlib.md5(prompt.encode()).hexdigest(), 16)
        return pool[digest % len(pool)]

    def generate(self, task_description: str, context: str = "") -> str:
        """Simulate Generator agent: produce reasoning + answer."""
        key = task_description + context
        return self._pick(key, self._GENERATOR_TEMPLATES)

    def reflect(self, reasoning: str, task_description: str) -> List[str]:
        """Simulate Reflector agent: extract insights from reasoning."""
        key = reasoning + task_description
        return list(self._pick(key, self._REFLECTOR_TEMPLATES))

    def curate(self, insights: List[str], domain: str) -> List[str]:
        """Simulate Curator agent: distil insights into bullet candidates."""
        key = "|".join(insights) + domain
        return list(self._pick(key, self._CURATOR_TEMPLATES))


def get_llm_service() -> MockLLMService:
    """Return the configured LLM service (currently always mock)."""
    from app.config import LLM_PROVIDER  # imported here to allow test overrides
    if LLM_PROVIDER == "mock":
        return MockLLMService()
    # Future: add OpenAI / Ollama providers here
    return MockLLMService()
