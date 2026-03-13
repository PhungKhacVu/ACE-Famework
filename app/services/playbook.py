"""Playbook CRUD service backed by :class:`~app.storage.json_store.JSONStore`."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from app.schemas import Playbook
from app.storage.json_store import JSONStore


class PlaybookService:
    """Create, read, update, and delete playbooks stored as JSON files.

    Parameters
    ----------
    store_dir:
        Directory where the ``playbooks.json`` collection file is written.
    playbooks_dir:
        Directory where individual playbook JSON seed files are read from
        (e.g. ``data/playbooks/``).  Seed files are loaded on first use.
    """

    def __init__(self, store_dir: Path, playbooks_dir: Path) -> None:
        self._store = JSONStore("playbooks", store_dir)
        self._playbooks_dir = playbooks_dir
        self._seeded = False

    # ------------------------------------------------------------------
    # Seed helpers
    # ------------------------------------------------------------------

    def _seed_from_dir(self) -> None:
        """Load any ``*.json`` files from *playbooks_dir* into the store."""
        if self._seeded:
            return
        self._seeded = True
        new_records = []
        for path in sorted(self._playbooks_dir.glob("*.json")):
            try:
                with path.open("r", encoding="utf-8") as fh:
                    pb: Playbook = json.load(fh)
                if "id" in pb and self._store.get(pb["id"]) is None:
                    new_records.append(pb)
            except (json.JSONDecodeError, KeyError):
                pass  # skip malformed seed files
        # Use save_many so all seed records are flushed in a single disk write
        # instead of triggering a full JSON serialisation per record.
        if new_records:
            self._store.save_many(new_records)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list(self) -> List[Playbook]:
        """Return all stored playbooks (seeds loaded on first call)."""
        self._seed_from_dir()
        return self._store.list()  # type: ignore[return-value]

    def get(self, playbook_id: str) -> Optional[Playbook]:
        """Return a single playbook by *playbook_id*, or ``None``."""
        self._seed_from_dir()
        return self._store.get(playbook_id)  # type: ignore[return-value]

    def save(self, playbook: Playbook) -> None:
        """Persist (insert or update) a playbook."""
        self._store.save(playbook)  # type: ignore[arg-type]

    def delete(self, playbook_id: str) -> bool:
        """Delete a playbook.  Returns ``True`` if it existed."""
        return self._store.delete(playbook_id)
