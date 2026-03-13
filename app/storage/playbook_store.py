"""Playbook store – persists Bullet objects in a local JSON file."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from app.config import config
from app.schemas.bullet import Bullet, BulletType
from app.storage.files import read_json, write_json
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PlaybookStore:
    """Thread-safe-ish in-process store backed by a JSON file."""

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path or config.PLAYBOOK_PATH)
        self._bullets: Dict[str, Bullet] = {}
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self._path.exists():
            try:
                raw = read_json(self._path)
                for item in raw.get("bullets", []):
                    b = Bullet.model_validate(item)
                    self._bullets[b.id] = b
                logger.info("Loaded %d bullets from %s", len(self._bullets), self._path)
            except Exception as exc:
                logger.warning("Could not load playbook (%s); starting fresh.", exc)
        else:
            logger.info("No existing playbook at %s; starting fresh.", self._path)

    def save(self) -> None:
        data = {"bullets": [b.model_dump() for b in self._bullets.values()]}
        write_json(self._path, data)
        logger.info("Saved %d bullets to %s", len(self._bullets), self._path)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add(self, bullet: Bullet) -> None:
        self._bullets[bullet.id] = bullet

    def get(self, bullet_id: str) -> Optional[Bullet]:
        return self._bullets.get(bullet_id)

    def all(self) -> List[Bullet]:
        return list(self._bullets.values())

    def count(self) -> int:
        return len(self._bullets)

    def remove(self, bullet_id: str) -> bool:
        if bullet_id in self._bullets:
            del self._bullets[bullet_id]
            return True
        return False

    def top_bullets(self, n: int = 10) -> List[Bullet]:
        """Return the top-n bullets by score."""
        return sorted(self._bullets.values(), key=lambda b: b.score, reverse=True)[:n]

    def by_type(self, bullet_type: BulletType) -> List[Bullet]:
        return [b for b in self._bullets.values() if b.bullet_type == bullet_type]
