"""Painéis sóbrios e reutilizáveis para os menus no estilo ORIGINAL."""

from functools import lru_cache

import pygame


@lru_cache(maxsize=64)
def painel_original(tamanho: tuple[int, int], fundo: tuple[int, int, int],
                     borda: tuple[int, int, int], *, selecionado: bool = False,
                     raio: int = 12, alpha: int = 240) -> pygame.Surface:
    """Prepara gradiente, relevo interno e indicador de foco dentro da área clicável."""
    largura, altura = tamanho
    tela = pygame.Surface(tamanho, pygame.SRCALPHA)
    topo = tuple(round(a + (b - a) * (0.18 if selecionado else 0.06))
                 for a, b in zip(fundo, borda))
    for y in range(altura):
        t = y / max(1, altura - 1)
        cor = tuple(round(a + (b - a) * t) for a, b in zip(topo, fundo))
        pygame.draw.line(tela, (*cor, alpha), (0, y), (largura - 1, y))
    mascara = pygame.Surface(tamanho, pygame.SRCALPHA)
    pygame.draw.rect(mascara, (255, 255, 255, 255), mascara.get_rect(), border_radius=raio)
    tela.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    pygame.draw.rect(tela, (*borda, 220 if selecionado else 110), tela.get_rect(),
                     2 if selecionado else 1, border_radius=raio)
    interno = tela.get_rect().inflate(-6, -6)
    pygame.draw.rect(tela, (*borda, 35), interno, 1, border_radius=max(1, raio - 2))
    if selecionado:
        margem = max(4, min(12, altura // 5))
        pygame.draw.rect(tela, (*borda, 255),
                         (2, margem, 3, max(1, altura - margem * 2)), border_radius=2)
    return tela
