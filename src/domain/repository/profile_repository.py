"""Porta de persistência dos perfis, independente do armazenamento."""

from __future__ import annotations

from typing import Any, Protocol

from src.domain.profiles import Profile


class ProfileRepository(Protocol):
    """Contrato utilizado pelo serviço de perfis."""

    def load(self, profile_id: str) -> Profile: ...

    def save(self, profile: Profile) -> bool: ...

    def read_index(self) -> dict[str, Any]: ...

    def write_index(self, index: dict[str, Any]) -> bool: ...

    def delete(self, profile_id: str) -> None: ...
