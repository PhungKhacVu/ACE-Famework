"""Programmatic entry point – convenience wrapper around ACEPipeline."""

from __future__ import annotations

from app.config import config
from app.core.pipeline import ACEPipeline
from app.services.llm import get_llm_service
from app.storage.playbook_store import PlaybookStore


def build_pipeline(playbook_path: str | None = None) -> ACEPipeline:
    """Construct a ready-to-use ACEPipeline with configured LLM and storage."""
    path = playbook_path or str(config.PLAYBOOK_PATH)
    store = PlaybookStore(path)
    llm = get_llm_service()
    return ACEPipeline(llm, store)
