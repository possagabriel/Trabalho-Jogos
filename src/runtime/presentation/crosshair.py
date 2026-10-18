"""Mira cartoon cacheada, desenhada na superfície lógica do gameplay."""

from __future__ import annotations

import pygame

from src.core.constants import (
    ESPESSURA_CONTORNO_MIRA,
    ESPESSURA_COR_MIRA,
    PULSO_MIRA_QUADROS,
    RAIO_MIRA,
    RAIO_PULSO_MIRA,
    SHIFT_WHITE,
    VERMELHO,
    VOID_BLACK,
)


class Mira:
    """Reutiliza sprites de retícula por cor, hover e pulso."""

    def __init__(self) -> None:
        self.pulso = 0
        self._sprites: dict[tuple[tuple[int, int, int], bool], pygame.Surface] = {}

    def ativar_pulso(self) -> None:
        """Realça brevemente a mira após um disparo real."""
        self.pulso = PULSO_MIRA_QUADROS

    def desenhar(
        self, tela: pygame.Surface, posicao: tuple[int, int],
        cor_dimensao: tuple[int, int, int], sobre_inimigo: bool,
    ) -> None:
        """Desenha a mira em coordenadas lógicas, sem alocar por quadro."""
        cor = VERMELHO if sobre_inimigo else cor_dimensao
        pulsando = self.pulso > 0
        chave = (cor, pulsando)
        if chave not in self._sprites:
            self._sprites[chave] = self._criar_sprite(cor, pulsando)
        sprite = self._sprites[chave]
        tela.blit(sprite, sprite.get_rect(center=posicao))
        if self.pulso:
            self.pulso -= 1

    @staticmethod
    def _criar_sprite(cor: tuple[int, int, int], pulsando: bool) -> pygame.Surface:
        raio = RAIO_PULSO_MIRA if pulsando else RAIO_MIRA
        margem = raio + 13
        sprite = pygame.Surface((margem * 2 + 1, margem * 2 + 1), pygame.SRCALPHA)
        centro = (margem, margem)
        pygame.draw.circle(sprite, VOID_BLACK, centro, raio + 2, ESPESSURA_CONTORNO_MIRA)
        pygame.draw.circle(sprite, cor, centro, raio, ESPESSURA_COR_MIRA)
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            inicio = (margem + dx * (raio + 5), margem + dy * (raio + 5))
            fim = (margem + dx * (raio + 11), margem + dy * (raio + 11))
            pygame.draw.line(sprite, VOID_BLACK, inicio, fim, ESPESSURA_CONTORNO_MIRA)
            pygame.draw.line(sprite, cor, inicio, fim, ESPESSURA_COR_MIRA)
        pygame.draw.circle(sprite, VOID_BLACK, centro, 4)
        pygame.draw.circle(sprite, SHIFT_WHITE, centro, 2)
        return sprite
