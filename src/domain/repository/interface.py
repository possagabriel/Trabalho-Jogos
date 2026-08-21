"""Repository interface — abstract base for data persistence.

Follows the Repository pattern: the domain layer depends on this
interface, and concrete implementations (JSON, in-memory) live in the
infrastructure or repository package.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """Abstract generic repository.

    Subclasses implement storage-specific logic while the domain layer
    codes against this interface.

    Type params:
        T: The entity / value object managed by this repository.
    """

    @abstractmethod
    def get(self, entity_id: str) -> Optional[T]:
        """Return the entity identified by *entity_id*, or ``None``."""

    @abstractmethod
    def get_all(self) -> list[T]:
        """Return all stored entities."""

    @abstractmethod
    def save(self, entity: T, entity_id: Optional[str] = None) -> None:
        """Persist *entity* (insert or update).

        If *entity_id* is ``None`` the implementation must derive or
        generate one (e.g. ``entity.id``).
        """

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Remove entity by *entity_id*. Returns ``True`` if removed."""

    @abstractmethod
    def count(self) -> int:
        """Return the number of stored entities."""

    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """Return ``True`` if *entity_id* is present."""
