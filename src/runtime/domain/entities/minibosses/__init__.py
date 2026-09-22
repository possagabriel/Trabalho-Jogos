"""API pública e carregamento explícito dos protocolos registrados."""

from src.runtime.domain.entities.minibosses import types as _types  # noqa: F401
from src.runtime.domain.entities.minibosses.base import Miniboss
from src.runtime.domain.entities.minibosses.registry import REGISTRO, criar_miniboss, registrar

__all__ = ["Miniboss", "REGISTRO", "criar_miniboss", "registrar"]
