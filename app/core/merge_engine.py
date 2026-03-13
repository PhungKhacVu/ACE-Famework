"""MergeEngine: merges new bullet candidates into the playbook.

Uses a simple character-level Jaccard similarity for deduplication so
the engine has zero external dependencies and works on any Python 3.9+
installation (including a-Shell on iPhone).
"""
from __future__ import annotations
import time
from typing import List
from app.schemas import Bullet
from app import config


def _jaccard(a: str, b: str) -> float:
    """Return Jaccard similarity between two strings at the word level."""
    sa = set(a.lower().split())
    sb = set(b.lower().split())
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


class MergeEngine:
    """Merge new bullet candidates into an existing playbook list.

    Strategy
    --------
    For each candidate text:
    - If a bullet with Jaccard similarity >= threshold already exists,
      increment its ``helpful_count`` (treats the new evidence as
      positive reinforcement) and update its confidence.
    - Otherwise insert a new Bullet.
    """

    def __init__(self, threshold: float | None = None):
        self.threshold = threshold if threshold is not None else config.MERGE_SIMILARITY_THRESHOLD

    def merge(
        self,
        existing: List[Bullet],
        candidates: List[str],
        harmful: bool = False,
    ) -> List[Bullet]:
        """Return an updated copy of *existing* with *candidates* merged in."""
        updated = list(existing)

        for text in candidates:
            matched = False
            for bullet in updated:
                if _jaccard(bullet.text, text) >= self.threshold:
                    if harmful:
                        bullet.harmful_count += 1
                    else:
                        bullet.helpful_count += 1
                    total = bullet.helpful_count + bullet.harmful_count
                    bullet.confidence = bullet.helpful_count / total if total else 0.5
                    bullet.updated_at = time.time()
                    matched = True
                    break

            if not matched:
                b = Bullet(
                    text=text,
                    helpful_count=0 if harmful else 1,
                    harmful_count=1 if harmful else 0,
                    confidence=0.3 if harmful else 0.7,
                )
                updated.append(b)

        return updated
