"""Configuration for the ACE framework (reads from env or uses defaults)."""
import os

# Directory where data files live (overridable via ACE_DATA_DIR env var)
DATA_DIR: str = os.environ.get(
    "ACE_DATA_DIR",
    os.path.join(os.path.dirname(__file__), "..", "data"),
)

PLAYBOOK_PATH: str = os.environ.get(
    "ACE_PLAYBOOK_PATH",
    os.path.join(DATA_DIR, "playbook.json"),
)

# LLM provider: "mock" (default, no API key needed) | "openai"
LLM_PROVIDER: str = os.environ.get("ACE_LLM_PROVIDER", "mock")

# OpenAI-compatible base URL (only used when LLM_PROVIDER != "mock")
LLM_BASE_URL: str = os.environ.get("ACE_LLM_BASE_URL", "http://localhost:11434/v1")
LLM_API_KEY: str = os.environ.get("ACE_LLM_API_KEY", "")
LLM_MODEL: str = os.environ.get("ACE_LLM_MODEL", "llama3")

# Similarity threshold for deduplication in merge engine
MERGE_SIMILARITY_THRESHOLD: float = float(
    os.environ.get("ACE_MERGE_THRESHOLD", "0.85")
)
