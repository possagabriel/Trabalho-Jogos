"""Quadros de orientação gerados a partir da arte de cada skin."""

from __future__ import annotations

import pygame

from src.core.constants import QUADROS_NAVE_DIRECIONAL


def gerar_quadros_direcionais(
    base: pygame.Surface,
    quantidade: int = QUADROS_NAVE_DIRECIONAL,
) -> tuple[pygame.Surface, ...]:
    """Pré-renderiza uma volta completa sem alterar a superfície de origem.

    Args:
        base: Arte voltada para cima, com centro no pivô da nave.
        quantidade: Número de orientações igualmente espaçadas.

    Returns:
        Sprites prontas para blit em cada direção.
    """
    if quantidade <= 0:
        raise ValueError("A quantidade de sprites direcionais deve ser positiva")
    passo = 360 / quantidade
    return tuple(
        pygame.transform.rotozoom(base, -indice * passo, 1.0)
        for indice in range(quantidade)
    )



class AtlasDirecional:
    """Prepara cada orientação somente quando ela é usada pela primeira vez."""

    def __init__(self, base: pygame.Surface,
                 quantidade: int = QUADROS_NAVE_DIRECIONAL) -> None:
        if quantidade <= 0:
            raise ValueError("A quantidade de sprites direcionais deve ser positiva")
        self.base = base
        self.quantidade = quantidade
        self._quadros: dict[int, pygame.Surface] = {}

    def __getitem__(self, indice: int) -> pygame.Surface:
        if not -self.quantidade <= indice < self.quantidade:
            raise IndexError(indice)
        indice %= self.quantidade
        if indice not in self._quadros:
            self._quadros[indice] = pygame.transform.rotozoom(
                self.base, -indice * 360 / self.quantidade, 1.0)
        return self._quadros[indice]

    def __len__(self) -> int:
        return self.quantidade
