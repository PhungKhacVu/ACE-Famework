"""Global configuration loaded from environment variables or defaults."""

from __future__ import annotations

import os


class Config:
    # LLM provider: "mock" | "openai" | "ollama"
    LLM_PROVIDER: str = os.getenv("ACE_LLM_PROVIDER", "mock")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")

    # Storage
    PLAYBOOK_PATH: str = os.getenv("ACE_PLAYBOOK_PATH", "data/playbook.json")

    # Similarity threshold for bullet deduplication (0–1)
    DEDUP_THRESHOLD: float = float(os.getenv("ACE_DEDUP_THRESHOLD", "0.85"))


config = Config()
