"""Merge engine – integrates DeltaUpdates into the PlaybookStore with deduplication."""

from __future__ import annotations

from app.config import config
from app.schemas.bullet import Bullet, DeltaUpdate
from app.services.embeddings import cosine_similarity, embed
from app.storage.playbook_store import PlaybookStore
from app.utils.ids import new_id
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MergeEngine:
    """Merge incoming DeltaUpdates into the playbook, deduplicating by semantic similarity."""

    def __init__(
        self,
        store: PlaybookStore,
        similarity_threshold: float | None = None,
    ) -> None:
        self._store = store
        self._threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else config.SIM_THRESHOLD
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def merge(self, deltas: list[DeltaUpdate]) -> dict[str, int]:
        """Merge a list of DeltaUpdates and return counts."""
        added = updated = merged = 0

        for delta in deltas:
            result = self._merge_one(delta)
            if result == "added":
                added += 1
            elif result == "updated":
                updated += 1
            elif result == "merged":
                merged += 1

        return {"added": added, "updated": updated, "merged": merged}

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _merge_one(self, delta: DeltaUpdate) -> str:
        """Return 'added', 'updated', or 'merged'."""
        delta_emb = embed(delta.content)
        candidates = self._store.by_domain(delta.domain) or self._store.all()

        best: Bullet | None = None
        best_sim = 0.0

        for bullet in candidates:
            emb = bullet.embedding or embed(bullet.content)
            bullet.embedding = emb
            sim = cosine_similarity(delta_emb, emb)
            if sim > best_sim:
                best_sim = sim
                best = bullet

        if best is not None and best_sim >= self._threshold:
            # Update existing bullet
            logger.debug(
                "Merging delta into bullet %s (sim=%.3f)", best.id, best_sim
            )
            best.helpful_count += max(0, delta.helpful_delta)
            best.harmful_count += max(0, delta.harmful_delta)
            # Blend confidence with exponential moving average
            best.confidence = 0.7 * best.confidence + 0.3 * delta.confidence
            best.confidence = max(0.0, min(1.0, best.confidence))
            best.embedding = embed(best.content)
            self._store.update(best)
            return "merged"

        # Create new bullet
        logger.debug("Adding new bullet from delta: %s", delta.content[:60])
        bullet = Bullet(
            id=new_id(),
            content=delta.content,
            domain=delta.domain,
            confidence=delta.confidence,
            helpful_count=max(0, delta.helpful_delta),
            harmful_count=max(0, delta.harmful_delta),
            tags=delta.tags,
            embedding=delta_emb,
        )
        self._store.add(bullet)
        return "added"
