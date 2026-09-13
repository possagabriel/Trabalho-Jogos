"""Índice espacial simples para colisões do gameplay 2D."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Generic, Protocol, TypeVar

import pygame


class ComRetangulo(Protocol):
    """Entidade que expõe um retângulo de colisão."""

    @property
    def rect(self) -> pygame.Rect:
        """Retângulo ocupado pela entidade."""


T = TypeVar("T", bound=ComRetangulo)


class GradeEspacial(Generic[T]):
    """Agrupa entidades em células para reduzir testes de colisão."""

    def __init__(self, tamanho_celula: int = 96) -> None:
        self.tamanho_celula = max(16, tamanho_celula)
        self._celulas: dict[tuple[int, int], list[T]] = defaultdict(list)

    def _intervalo(self, rect: pygame.Rect) -> tuple[range, range]:
        tamanho = self.tamanho_celula
        direita = max(rect.left, rect.right - 1) // tamanho
        base = max(rect.top, rect.bottom - 1) // tamanho
        xs = range(rect.left // tamanho, direita + 1)
        ys = range(rect.top // tamanho, base + 1)
        return xs, ys

    def reconstruir(self, entidades: Iterable[T]) -> None:
        """Reconstrói o índice para o estado atual do mundo."""
        self._celulas.clear()
        for entidade in entidades:
            xs, ys = self._intervalo(entidade.rect)
            for x in xs:
                for y in ys:
                    self._celulas[(x, y)].append(entidade)

    def consultar(self, area: pygame.Rect) -> list[T]:
        """Retorna candidatos que ocupam as células tocadas por ``area``."""
        encontrados: list[T] = []
        vistos: set[int] = set()
        xs, ys = self._intervalo(area)
        for x in xs:
            for y in ys:
                for entidade in self._celulas.get((x, y), ()):
                    identidade = id(entidade)
                    if identidade not in vistos:
                        vistos.add(identidade)
                        encontrados.append(entidade)
        return encontrados
