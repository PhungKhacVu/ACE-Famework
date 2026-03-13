"""
PlaybookStore — local JSON-backed storage for ACE bullets.

Designed to run without any external dependencies so it works in
a-Shell / a-Shell mini on iPhone.
"""
from __future__ import annotations

import json
import os
from typing import List, Optional

from app.schemas.bullet import Bullet
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PlaybookStore:
    """
    Persists and retrieves :class:`~app.schemas.bullet.Bullet` objects
    from a local JSON file.

    Usage
    -----
    >>> store = PlaybookStore("data/playbook.json")
    >>> store.load()
    >>> store.add(bullet)
    >>> store.save()
    >>> bullets = store.search("error handling")
    """

    def __init__(self, path: str = "data/playbook.json") -> None:
        self.path = path
        self._bullets: List[Bullet] = []

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load bullets from disk.  Creates an empty store if file missing."""
        if not os.path.exists(self.path):
            logger.info("Playbook file not found — starting with empty store: %s", self.path)
            self._bullets = []
            return
        with open(self.path, encoding="utf-8") as fh:
            data = json.load(fh)
        self._bullets = [Bullet.from_dict(d) for d in data]
        logger.info("Loaded %d bullets from %s", len(self._bullets), self.path)

    def save(self) -> None:
        """Persist current bullets to disk, creating parent dirs as needed."""
        os.makedirs(os.path.dirname(self.path) if os.path.dirname(self.path) else ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump([b.to_dict() for b in self._bullets], fh, ensure_ascii=False, indent=2)
        logger.info("Saved %d bullets to %s", len(self._bullets), self.path)

    # ------------------------------------------------------------------
    # CRUD helpers
    # ------------------------------------------------------------------

    def add(self, bullet: Bullet) -> None:
        """Append a bullet (no dedup check here — use MergeEngine for that)."""
        self._bullets.append(bullet)

    def remove(self, bullet_id: str) -> bool:
        """Remove a bullet by ID.  Returns True if found and removed."""
        before = len(self._bullets)
        self._bullets = [b for b in self._bullets if b.id != bullet_id]
        return len(self._bullets) < before

    def get(self, bullet_id: str) -> Optional[Bullet]:
        """Return the bullet with the given ID, or None."""
        for b in self._bullets:
            if b.id == bullet_id:
                return b
        return None

    def all(self) -> List[Bullet]:
        """Return all bullets (a copy of the internal list)."""
        return list(self._bullets)

    def by_domain(self, domain: str) -> List[Bullet]:
        """Filter bullets by domain."""
        return [b for b in self._bullets if b.domain == domain]

    def top(self, n: int = 10, domain: Optional[str] = None) -> List[Bullet]:
        """Return the top-n bullets ranked by score descending."""
        pool = self.by_domain(domain) if domain else self._bullets
        return sorted(pool, key=lambda b: b.score, reverse=True)[:n]

    # ------------------------------------------------------------------
    # Search (keyword-based, no external libs needed)
    # ------------------------------------------------------------------

    def search(self, query: str, domain: Optional[str] = None, top_k: int = 5) -> List[Bullet]:
        """
        Simple keyword search over bullet content.

        Ranks bullets by the number of query tokens that appear in their
        content (case-insensitive).  Falls back to score-based ranking
        when there are no keyword hits.
        """
        tokens = query.lower().split()
        pool = self.by_domain(domain) if domain else self._bullets

        def _hits(bullet: Bullet) -> int:
            text = bullet.content.lower()
            return sum(1 for t in tokens if t in text)

        scored = [(b, _hits(b)) for b in pool]
        matched = [(b, h) for b, h in scored if h > 0]

        if matched:
            matched.sort(key=lambda x: (x[1], x[0].score), reverse=True)
            return [b for b, _ in matched[:top_k]]

        # Nothing matched — return top scoring bullets instead
        return self.top(top_k, domain=domain)

    # ------------------------------------------------------------------
    # Counter updates
    # ------------------------------------------------------------------

    def increment_helpful(self, bullet_id: str) -> bool:
        b = self.get(bullet_id)
        if b:
            b.helpful_count += 1
            return True
        return False

    def increment_harmful(self, bullet_id: str) -> bool:
        b = self.get(bullet_id)
        if b:
            b.harmful_count += 1
            return True
        return False

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._bullets)

    def __repr__(self) -> str:
        return f"PlaybookStore(path={self.path!r}, bullets={len(self._bullets)})"
