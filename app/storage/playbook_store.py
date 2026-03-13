"""Local JSON-backed playbook store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from app.schemas.bullet import Bullet
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PlaybookStore:
    """Persist and retrieve Bullet objects using a local JSON file."""

    def __init__(self, path: Path | str = "data/playbook.json") -> None:
        self.path = Path(path)
        self._bullets: dict[str, Bullet] = {}
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                self._bullets = {b["id"]: Bullet(**b) for b in raw}
                logger.info("Loaded %d bullets from %s", len(self._bullets), self.path)
            except Exception as exc:
                logger.warning("Could not load playbook (%s); starting fresh.", exc)
                self._bullets = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [b.model_dump(exclude={"embedding"}) for b in self._bullets.values()]
        self.path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        logger.info("Saved %d bullets to %s", len(data), self.path)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add(self, bullet: Bullet) -> None:
        self._bullets[bullet.id] = bullet

    def get(self, bullet_id: str) -> Optional[Bullet]:
        return self._bullets.get(bullet_id)

    def update(self, bullet: Bullet) -> None:
        bullet.touch()
        self._bullets[bullet.id] = bullet

    def remove(self, bullet_id: str) -> bool:
        if bullet_id in self._bullets:
            del self._bullets[bullet_id]
            return True
        return False

    def all(self) -> list[Bullet]:
        return list(self._bullets.values())

    def by_domain(self, domain: str) -> list[Bullet]:
        return [b for b in self._bullets.values() if b.domain == domain]

    def top(self, n: int = 10, domain: Optional[str] = None) -> list[Bullet]:
        bullets = self.by_domain(domain) if domain else self.all()
        return sorted(bullets, key=lambda b: b.net_score, reverse=True)[:n]

    def count(self) -> int:
        return len(self._bullets)
