"""JSON-backed repository implementation.

Persists entities as a JSON array on disk.  Suitable for save files,
records, settings, and any semi-structured data that the game needs to
survive across sessions.
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from .interface import Repository


class JsonRepository(Repository[dict[str, Any]]):
    """JSON file repository — stores a list of dicts keyed by an ``id`` field.

    Args:
        file_path: Absolute path to the JSON file.
        id_field: Name of the key used as unique identifier (default ``"id"``).
    """

    def __init__(self, file_path: str, id_field: str = "id") -> None:
        self._file_path = file_path
        self._id_field = id_field
        self._data: dict[str, dict[str, Any]] = {}
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Read the JSON file and index by *id_field*."""
        if not os.path.exists(self._file_path):
            self._data = {}
            return
        try:
            with open(self._file_path, "r", encoding="utf-8") as fh:
                items: list[dict[str, Any]] = json.load(fh)
            self._data = {
                str(item[self._id_field]): item for item in items
            }
        except (json.JSONDecodeError, KeyError, OSError):
            self._data = {}

    def _persist(self) -> None:
        """Write the in-memory index back to disk."""
        os.makedirs(os.path.dirname(self._file_path) or ".", exist_ok=True)
        try:
            with open(self._file_path, "w", encoding="utf-8") as fh:
                json.dump(list(self._data.values()), fh,
                          ensure_ascii=False, indent=2)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Repository interface
    # ------------------------------------------------------------------

    def get(self, entity_id: str) -> Optional[dict[str, Any]]:
        return self._data.get(entity_id)

    def get_all(self) -> list[dict[str, Any]]:
        return list(self._data.values())

    def save(self, entity: dict[str, Any],
             entity_id: Optional[str] = None) -> None:
        eid = str(entity_id or entity.get(self._id_field, ""))
        if not eid:
            raise ValueError("Entity must have an id to be saved.")
        self._data[eid] = entity
        self._persist()

    def delete(self, entity_id: str) -> bool:
        if entity_id in self._data:
            del self._data[entity_id]
            self._persist()
            return True
        return False

    def count(self) -> int:
        return len(self._data)

    def exists(self, entity_id: str) -> bool:
        return entity_id in self._data
