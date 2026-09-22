"""Factory/Registry extensível sem seleção de tipos por condicionais."""

from __future__ import annotations

import random
from collections.abc import Callable
from typing import TYPE_CHECKING

from src.runtime.domain.entities.minibosses.base import Miniboss
from src.runtime.domain.entities.minibosses.config import CATALOGO

if TYPE_CHECKING:
    from src.runtime.domain.world.scenarios import Cenario

REGISTRO: dict[str, type[Miniboss]] = {}


def registrar(chave: str) -> Callable[[type[Miniboss]], type[Miniboss]]:
    """Registra uma classe cujo balanceamento está no catálogo."""
    def decorar(classe: type[Miniboss]) -> type[Miniboss]:
        if chave in REGISTRO or chave not in CATALOGO:
            raise ValueError(f"Registro duplicado ou sem configuração: {chave}")
        classe.chave = chave
        REGISTRO[chave] = classe
        return classe
    return decorar


def criar_miniboss(chave: str, nivel: int, cenario: Cenario,
                  rng: random.Random | None = None) -> Miniboss:
    """Instancia a classe registrada com RNG próprio e configuração independente."""
    return REGISTRO[chave](nivel, cenario, CATALOGO[chave], rng or random.Random())
