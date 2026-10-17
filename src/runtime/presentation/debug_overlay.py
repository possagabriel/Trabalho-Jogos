"""Overlay F3 de métricas e hitboxes, separado da lógica de combate."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.core.constants import QUANTUM_CYAN, VERDE, VERMELHO, VOID_BLACK
from src.runtime.infrastructure.graphics.fonts import fonte_texto

if TYPE_CHECKING:
    from src.runtime.application.core import Jogo


class OverlayDebug:
    """Mostra métricas por glifos cacheados e contornos de colisão."""

    def __init__(self) -> None:
        self._fonte = fonte_texto(18)
        self._glifos: dict[str, pygame.Surface] = {}
        self._fundo = pygame.Surface((260, 104), pygame.SRCALPHA)
        self._fundo.fill((*VOID_BLACK, 215))

    def desenhar(self, tela: pygame.Surface, jogo: Jogo, mira: tuple[int, int] | None) -> None:
        """Desenha FPS, camadas, mira e hitboxes sem criar surfaces por frame."""
        tela.blit(self._fundo, (12, 12))
        linhas = (
            f"FPS: {jogo.fps_atual:.0f}",
            "CAMADAS: 0",
            f"MIRA: {mira[0]}, {mira[1]}" if mira else "MIRA: --",
            f"ENTIDADES: {len(jogo.inimigos) + int(bool(jogo.boss)) + int(bool(jogo.miniboss))}",
        )
        for indice, linha in enumerate(linhas):
            x, y = 22, 20 + indice * 23
            for caractere in linha:
                if caractere not in self._glifos:
                    self._glifos[caractere] = self._fonte.render(caractere, True, QUANTUM_CYAN)
                glifo = self._glifos[caractere]
                tela.blit(glifo, (x, y))
                x += glifo.get_width()
        pygame.draw.rect(tela, VERDE, jogo.jogador.rect, 1)
        for inimigo in jogo.inimigos:
            pygame.draw.rect(tela, VERMELHO, inimigo.rect, 1)
        for entidade in (jogo.boss, jogo.miniboss):
            if entidade is not None:
                pygame.draw.rect(tela, VERMELHO, entidade.rect, 1)
        for proj in jogo.projeteis:
            pygame.draw.rect(tela, QUANTUM_CYAN, proj.rect, 1)
