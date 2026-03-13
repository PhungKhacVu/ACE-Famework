"""Configuration management – reads from environment / .env file."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    LLM_PROVIDER: str = os.getenv("ACE_LLM_PROVIDER", "mock")
    PLAYBOOK_PATH: Path = Path(os.getenv("ACE_PLAYBOOK_PATH", "data/playbook.json"))
    SIM_THRESHOLD: float = float(os.getenv("ACE_SIM_THRESHOLD", "0.85"))
    LOG_LEVEL: str = os.getenv("ACE_LOG_LEVEL", "INFO")

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

    # Ollama
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")


config = Config()
