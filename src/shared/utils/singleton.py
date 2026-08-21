"""Singleton - Metaclass para garantir instancia unica."""

from __future__ import annotations

from typing import Any


class SingletonMeta(type):
    """Metaclass que implementa o padrao Singleton.

    Garante que apenas uma instancia da classe seja criada.
    """

    _instances: dict[type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
