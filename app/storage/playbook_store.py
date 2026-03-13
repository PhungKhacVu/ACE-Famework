"""JSON-backed playbook store – no external deps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from app.schemas import Playbook


class PlaybookStore:
    """Persist and retrieve playbooks as individual JSON files."""

    def __init__(self, directory: Path) -> None:
        self._dir = directory
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, playbook_id: str) -> Path:
        return self._dir / f"{playbook_id}.json"

    def save(self, playbook: Playbook) -> None:
        """Persist a playbook to disk (creates or overwrites)."""
        with open(self._path(playbook.id), "w", encoding="utf-8") as fh:
            json.dump(playbook.to_dict(), fh, indent=2, ensure_ascii=False)

    def load(self, playbook_id: str) -> Playbook:
        """Load a playbook by id; raises FileNotFoundError if missing."""
        path = self._path(playbook_id)
        if not path.exists():
            raise FileNotFoundError(f"Playbook not found: {playbook_id}")
        with open(path, encoding="utf-8") as fh:
            return Playbook.from_dict(json.load(fh))

    def delete(self, playbook_id: str) -> bool:
        """Delete a playbook; returns True if it existed."""
        path = self._path(playbook_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def list_all(self) -> Iterator[Playbook]:
        """Yield all stored playbooks."""
        for p in sorted(self._dir.glob("*.json")):
            with open(p, encoding="utf-8") as fh:
                yield Playbook.from_dict(json.load(fh))

    def find_by_name(self, name: str) -> Playbook | None:
        """Return the first playbook whose name matches (case-insensitive)."""
        name_lower = name.lower()
        for pb in self.list_all():
            if pb.name.lower() == name_lower:
                return pb
        return None
