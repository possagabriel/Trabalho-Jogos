"""In-memory repository for unit tests and ephemeral data.

No disk I/O — everything lives in a plain dict and is lost when the
process exits.
"""

from __future__ import annotations

from typing import Any, Optional

from .interface import Repository


class MemoryRepository(Repository[dict[str, Any]]):
    """Dict-backed repository.  Ideal for testing.

    Args:
        id_field: Key used as unique identifier (default ``"id"``).
    """

    def __init__(self, id_field: str = "id") -> None:
        self._id_field = id_field
        self._data: dict[str, dict[str, Any]] = {}

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

    def delete(self, entity_id: str) -> bool:
        if entity_id in self._data:
            del self._data[entity_id]
            return True
        return False

    def count(self) -> int:
        return len(self._data)

    def exists(self, entity_id: str) -> bool:
        return entity_id in self._data
