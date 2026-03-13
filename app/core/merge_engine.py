"""
MergeEngine — merges Curator DeltaUpdates into the PlaybookStore.

Key responsibilities:
- Add new bullets proposed by the Curator
- Deduplicate against existing bullets using cosine similarity
- Update helpful/harmful counters
- Enforce max-bullet cap (prune lowest-scoring bullets when over limit)
"""
from __future__ import annotations

from typing import List

from app.schemas.bullet import Bullet, DeltaUpdate
from app.storage.playbook_store import PlaybookStore
from app.core.ranking import cosine_similarity
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MergeEngine:
    """
    Applies a :class:`~app.schemas.bullet.DeltaUpdate` to a
    :class:`~app.storage.playbook_store.PlaybookStore`.

    Parameters
    ----------
    store : PlaybookStore
        The live playbook store to mutate.
    similarity_threshold : float
        Cosine similarity cutoff above which an incoming bullet is
        considered a duplicate of an existing one (default 0.85).
    max_bullets : int
        Hard cap on the number of bullets in the store.
    """

    def __init__(
        self,
        store: PlaybookStore,
        similarity_threshold: float = 0.85,
        max_bullets: int = 200,
    ) -> None:
        self.store = store
        self.similarity_threshold = similarity_threshold
        self.max_bullets = max_bullets

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def apply(self, delta: DeltaUpdate) -> dict:
        """
        Apply *delta* to the store and return a summary dict.

        Returns
        -------
        dict with keys:
            added (int)         – new bullets inserted
            duplicates (int)    – bullets skipped because too similar
            helpful_updated (int)
            harmful_updated (int)
            pruned (int)        – bullets removed to respect max_bullets
        """
        added = 0
        duplicates = 0

        # 1. Insert new bullets
        for new_b in delta.new_bullets:
            dup = self._find_duplicate(new_b)
            if dup:
                logger.debug(
                    "Duplicate found for bullet %r — skipping (similar to %s)", new_b.id, dup.id
                )
                duplicates += 1
                # Merge counters into the existing bullet instead
                dup.helpful_count += new_b.helpful_count
                dup.harmful_count += new_b.harmful_count
            else:
                self.store.add(new_b)
                added += 1
                logger.debug("Added bullet %s: %r", new_b.id, new_b.content[:60])

        # 2. Update counters for referenced existing bullets
        helpful_updated = sum(
            1 for bid in delta.helpful_ids if self.store.increment_helpful(bid)
        )
        harmful_updated = sum(
            1 for bid in delta.harmful_ids if self.store.increment_harmful(bid)
        )

        # 3. Prune if over cap
        pruned = self._prune()

        summary = {
            "added": added,
            "duplicates": duplicates,
            "helpful_updated": helpful_updated,
            "harmful_updated": harmful_updated,
            "pruned": pruned,
        }
        logger.info("Merge summary: %s", summary)
        return summary

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_duplicate(self, incoming: Bullet) -> Bullet | None:
        """
        Return the first existing bullet whose cosine similarity with
        *incoming* exceeds the threshold, or None if no duplicate found.
        """
        for existing in self.store.all():
            if existing.domain != incoming.domain:
                continue
            sim = cosine_similarity(incoming.content, existing.content)
            if sim >= self.similarity_threshold:
                return existing
        return None

    def _prune(self) -> int:
        """
        Remove the lowest-scoring bullets when the store is over the cap.

        Returns the number of bullets pruned.
        """
        all_bullets = self.store.all()
        if len(all_bullets) <= self.max_bullets:
            return 0

        sorted_bullets = sorted(all_bullets, key=lambda b: b.score, reverse=True)
        to_remove = sorted_bullets[self.max_bullets :]
        for b in to_remove:
            self.store.remove(b.id)
        logger.info("Pruned %d low-scoring bullets", len(to_remove))
        return len(to_remove)
