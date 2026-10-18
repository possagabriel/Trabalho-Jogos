"""Acabamento raster cacheado para os fundos que aparecem em cutscenes."""

from __future__ import annotations

from functools import lru_cache

import pygame

from src.infrastructure.graphics.comic_theme import CONTORNO, TINTA

TAMANHO_CONTORNO = (320, 180)
PASSO_RETICULA = 18
ALFA_TINTA_DIMENSAO = 30
ALFA_RETICULA = 14
LIMIAR_CONTORNO = 190


def _paleta_cartoon() -> list[tuple[int, int, int]]:
    """Cria uma paleta curta RGB para reduzir as faixas de cor do raster."""
    niveis = (0, 85, 170, 255)
    return [(r, g, b) for r in niveis for g in niveis for b in niveis]


@lru_cache(maxsize=8)
def filtrar_fundo_cutscene(
    origem: pygame.Surface,
    cor_dimensao: tuple[int, int, int],
) -> pygame.Surface:
    """Posteriza, tinge e acrescenta contorno e retícula uma vez por fundo.

    A superfície de origem nunca é alterada. O resultado é imutável e pode ser
    reutilizado em todos os quadros da cena.
    """
    largura, altura = origem.get_size()
    quantizada = pygame.Surface((largura, altura), depth=8)
    quantizada.set_palette(_paleta_cartoon())
    quantizada.blit(origem, (0, 0))
    resultado = pygame.Surface((largura, altura)).convert() if (
        pygame.display.get_surface() is not None
    ) else pygame.Surface((largura, altura))
    resultado.blit(quantizada, (0, 0))

    tinta = pygame.Surface((largura, altura), pygame.SRCALPHA)
    tinta.fill((*cor_dimensao, ALFA_TINTA_DIMENSAO))
    resultado.blit(tinta, (0, 0))

    reticula = pygame.Surface((largura, altura), pygame.SRCALPHA)
    for y in range(0, altura, PASSO_RETICULA):
        deslocamento = (y // PASSO_RETICULA % 2) * (PASSO_RETICULA // 2)
        for x in range(deslocamento, largura, PASSO_RETICULA):
            pygame.draw.circle(reticula, (*TINTA, ALFA_RETICULA),
                               (x, y), 1)
    resultado.blit(reticula, (0, 0))

    pequena = pygame.transform.scale(origem, TAMANHO_CONTORNO)
    bordas = pygame.transform.laplacian(pequena)
    escala_x = largura / TAMANHO_CONTORNO[0]
    escala_y = altura / TAMANHO_CONTORNO[1]
    espessura = max(1, CONTORNO // 3)
    for y in range(TAMANHO_CONTORNO[1]):
        for x in range(TAMANHO_CONTORNO[0]):
            cor = bordas.get_at((x, y))
            if max(cor.r, cor.g, cor.b) >= LIMIAR_CONTORNO:
                pygame.draw.circle(
                    resultado, TINTA,
                    (round((x + 0.5) * escala_x), round((y + 0.5) * escala_y)),
                    espessura,
                )
    return resultado
