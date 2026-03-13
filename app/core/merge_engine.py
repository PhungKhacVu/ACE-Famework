"""Merge engine – integrates DeltaUpdates into a PlaybookStore.

Key responsibilities:
- deduplicate new bullets against existing ones (Jaccard similarity)
- add genuinely new bullets
- apply reinforce/penalise counter updates
"""

from __future__ import annotations

from typing import List

from app.config import config
from app.schemas.bullet import Bullet, DeltaUpdate
from app.services.embeddings import jaccard_similarity
from app.storage.playbook_store import PlaybookStore
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MergeEngine:
    def __init__(
        self,
        store: PlaybookStore,
        dedup_threshold: float | None = None,
    ) -> None:
        self._store = store
        self._threshold = (
            dedup_threshold if dedup_threshold is not None else config.DEDUP_THRESHOLD
        )

    def merge(self, delta: DeltaUpdate) -> dict:
        """Apply a DeltaUpdate to the store and return a summary."""
        added = 0
        skipped = 0
        reinforced = 0
        penalised = 0

        existing = self._store.all()

        for new_b in delta.new_bullets:
            if self._is_duplicate(new_b, existing):
                logger.debug("Skipping duplicate bullet: %s", new_b.content[:60])
                skipped += 1
            else:
                self._store.add(new_b)
                existing.append(new_b)
                added += 1

        for bid in delta.reinforce_ids:
            b = self._store.get(bid)
            if b:
                b.reinforce()
                reinforced += 1

        for bid in delta.penalise_ids:
            b = self._store.get(bid)
            if b:
                b.penalise()
                penalised += 1

        summary = {
            "added": added,
            "skipped_duplicates": skipped,
            "reinforced": reinforced,
            "penalised": penalised,
        }
        logger.info("Merge result: %s", summary)
        return summary

    def _is_duplicate(self, candidate: Bullet, existing: List[Bullet]) -> bool:
        for b in existing:
            sim = jaccard_similarity(candidate.content, b.content)
            if sim >= self._threshold:
                return True
        return False
