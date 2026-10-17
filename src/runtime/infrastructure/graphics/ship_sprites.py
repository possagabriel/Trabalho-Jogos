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
