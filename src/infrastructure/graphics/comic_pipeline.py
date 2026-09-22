"""Preparação de sprites: quantização, hachuras e silhuetas em cache."""

from functools import lru_cache

import pygame

from src.infrastructure.graphics.comic_theme import (
    CIANO,
    CONTORNO,
    FATOR_LUZ,
    FATOR_SOMBRA,
    NIVEIS,
    PASSO_HACHURA,
    TINTA,
)


def superficie_alpha(tamanho: tuple[int, int]) -> pygame.Surface:
    """Cria superfície com alpha no formato do display, inclusive no modo dummy."""
    surf = pygame.Surface(tamanho, pygame.SRCALPHA)
    return surf.convert_alpha() if pygame.display.get_surface() is not None else surf


def gerar_paleta(cor: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    """Gera as três faixas de sombra, base e luz de um material."""
    return (tuple(int(c * FATOR_SOMBRA) for c in cor[:3]), tuple(cor[:3]),
            tuple(min(255, int(c + (255 - c) * FATOR_LUZ)) for c in cor[:3]))


@lru_cache(maxsize=128)
def posterizar(origem: pygame.Surface, hachuras: bool = False,
               material: tuple | None = None) -> pygame.Surface:
    """Quantiza no carregamento, preservando transparência e a superfície original."""
    resultado = superficie_alpha(origem.get_size())
    paleta = gerar_paleta(material) if material is not None else None
    for y in range(origem.get_height()):
        for x in range(origem.get_width()):
            r, g, b, a = origem.get_at((x, y))
            rgb = tuple(NIVEIS[min(3, c * 4 // 256)] for c in (r, g, b))
            if paleta is not None:
                rgb = paleta[min(2, max(r, g, b) * 3 // 256)]
            if hachuras and max(r, g, b) < 160 and (x + y) % PASSO_HACHURA == 0:
                rgb = TINTA
            resultado.set_at((x, y), (*rgb, a))
    return resultado


@lru_cache(maxsize=128)
def _silhueta(origem: pygame.Surface, cor: tuple) -> pygame.Surface:
    mascara = pygame.mask.from_surface(origem)
    return mascara.to_surface(setcolor=(*cor[:3], 255), unsetcolor=(0, 0, 0, 0))


@lru_cache(maxsize=256)
def contornar(origem: pygame.Surface, espessura: int = CONTORNO,
              cor: tuple[int, ...] = TINTA, variacao: int = 0) -> pygame.Surface:
    """Prepara o contorno uma vez por asset, com padding fora da área de colisão.

    Args:
        origem: Sprite imutável; a identidade da superfície é a chave do cache.
        espessura: Margem da tinta em pixels.
        cor: Cor opaca da silhueta.
        variacao: Segunda impressão da borda para line boil sem mover o sprite.
    """
    pad = max(0, espessura)
    w, h = origem.get_size()
    resultado = superficie_alpha((w + 2 * pad, h + 2 * pad))
    silhueta = _silhueta(origem, cor)
    for dx, dy in ((-pad, 0), (pad, 0), (0, -pad), (0, pad),
                   (-pad + 1, -pad), (pad, pad - 1), (-pad, pad - 1), (pad - 1, -pad)):
        resultado.blit(silhueta, (pad + dx + (variacao if dx < 0 else 0), pad + dy))
    resultado.blit(origem, (pad, pad))
    return resultado


@lru_cache(maxsize=64)
def preparar_rotacoes(origem: pygame.Surface, hachuras: bool,
                      variacao: int = 0) -> tuple[pygame.Surface, ...]:
    """Prepara a nave e todos os 21 ângulos de banking antes de animá-la."""
    base = contornar(posterizar(origem, hachuras, CIANO), variacao=variacao)
    return tuple(pygame.transform.rotate(base, -i / 2).convert_alpha()
                 for i in range(-10, 11))
