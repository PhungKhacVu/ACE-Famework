"""JSON-backed key/value store.

Each collection is stored as a single ``<name>.json`` file under *store_dir*.
Records are plain dicts; the ``id`` field is used as the primary key.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class JSONStore:
    """Lightweight JSON file store for a single collection."""

    def __init__(self, collection: str, store_dir: Path) -> None:
        self._path = store_dir / f"{collection}.json"
        # Ensure the directory exists once at construction time instead of on
        # every _save() call, which avoids a redundant syscall per write.
        store_dir.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Any] = {}
        self._load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self._path.exists():
            with self._path.open("r", encoding="utf-8") as fh:
                self._data = json.load(fh)

    def _save(self) -> None:
        with self._path.open("w", encoding="utf-8") as fh:
            json.dump(self._data, fh, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Return the record with *record_id*, or ``None`` if not found."""
        return self._data.get(record_id)

    def list(self) -> List[Dict[str, Any]]:
        """Return all records as a list."""
        return list(self._data.values())

    def save(self, record: Dict[str, Any]) -> None:
        """Insert or update *record*.  The dict **must** contain an ``id`` key."""
        if "id" not in record:
            raise ValueError("Record must have an 'id' field.")
        self._data[record["id"]] = record
        self._save()

    def delete(self, record_id: str) -> bool:
        """Delete record by *record_id*.  Returns ``True`` if it existed."""
        if record_id in self._data:
            del self._data[record_id]
            self._save()
            return True
        return False

    def save_many(self, records: List[Dict[str, Any]]) -> None:
        """Insert or update multiple records with a single disk write.

        This is far more efficient than calling :meth:`save` in a loop when
        inserting many records at once (e.g. during seed loading), because it
        batches all in-memory updates and flushes the JSON file only once.

        Every record in *records* **must** contain an ``id`` key.
        """
        for record in records:
            if "id" not in record:
                raise ValueError("Every record must have an 'id' field.")
            self._data[record["id"]] = record
        if records:
            self._save()
