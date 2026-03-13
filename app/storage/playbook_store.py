"""PlaybookStore: JSON-file-backed persistence for Bullet objects."""
from __future__ import annotations
import json
import os
from typing import List
from app.schemas import Bullet
from app import config


class PlaybookStore:
    """Load and save a list of Bullets to/from a local JSON file."""

    def __init__(self, path: str | None = None):
        self.path = path or config.PLAYBOOK_PATH
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)

    def load(self) -> List[Bullet]:
        """Return bullets from disk, or an empty list if the file is missing."""
        if not os.path.isfile(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Bullet.from_dict(d) for d in data]

    def save(self, bullets: List[Bullet]) -> None:
        """Persist *bullets* to disk (overwrites existing file)."""
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([b.to_dict() for b in bullets], f, indent=2)

    def add(self, bullet: Bullet) -> None:
        """Append a single bullet and persist immediately."""
        bullets = self.load()
        bullets.append(bullet)
        self.save(bullets)

    def clear(self) -> None:
        """Remove all bullets from the store."""
        self.save([])
