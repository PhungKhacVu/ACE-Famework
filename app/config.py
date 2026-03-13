"""
ACE Framework Configuration.

Reads settings from environment variables or .env file if present.
All defaults allow the framework to run fully offline with no API keys.
"""
import os

# ---------------------------------------------------------------------------
# LLM provider
# ---------------------------------------------------------------------------
# Supported values: "mock" | "openai" | "ollama"
LLM_PROVIDER = os.environ.get("ACE_LLM_PROVIDER", "mock")

# Used when LLM_PROVIDER="openai" or any OpenAI-compatible endpoint
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")

# Used when LLM_PROVIDER="ollama"
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
DATA_DIR = os.environ.get("ACE_DATA_DIR", "data")
PLAYBOOK_FILE = os.path.join(DATA_DIR, "playbook.json")

# ---------------------------------------------------------------------------
# Merge / deduplication
# ---------------------------------------------------------------------------
# Cosine similarity threshold above which two bullets are considered duplicates
SIMILARITY_THRESHOLD = float(os.environ.get("ACE_SIMILARITY_THRESHOLD", "0.85"))

# Maximum bullets to keep in the playbook
MAX_BULLETS = int(os.environ.get("ACE_MAX_BULLETS", "200"))

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL = os.environ.get("ACE_LOG_LEVEL", "INFO")
