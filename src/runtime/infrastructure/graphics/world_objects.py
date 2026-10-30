"""Arte procedural cacheada das rochas do mundo aberto."""

from functools import lru_cache

import pygame

from src.infrastructure.graphics.comic_theme import PAPEL, TINTA
from src.runtime.infrastructure.graphics.smooth import desenhar_circulo, desenhar_poligono

ROCHA_ORIGINAL = ((61, 77, 100), (107, 135, 158), (29, 40, 60), (168, 199, 210))
ROCHA_COMIC = ((113, 89, 69), (169, 139, 102), (62, 48, 43), PAPEL)


@lru_cache(maxsize=192)
def arte_asteroide(forma: tuple[tuple[int, int], ...], raio: int,
                   comic: bool) -> pygame.Surface:
    """Prepara facetas e crateras sem alterar geometria, vida ou colisões."""
    margem = raio + 12
    tela = pygame.Surface((margem * 2, margem * 2), pygame.SRCALPHA)
    corpo, luz, sombra, borda = ROCHA_COMIC if comic else ROCHA_ORIGINAL
    pontos = tuple((margem + x, margem + y) for x, y in forma)
    desenhar_poligono(tela, corpo, pontos)
    for indice, (p1, p2) in enumerate(zip(pontos, pontos[1:] + pontos[:1])):
        desenhar_poligono(tela, luz if indice < 3 else sombra,
                          ((margem - raio // 5, margem - raio // 4), p1, p2))
    desenhar_poligono(tela, TINTA if comic else borda, pontos, espessura=2)
    for dx, dy, tamanho in ((-0.28, -0.1, 0.22), (0.3, 0.25, 0.14)):
        centro = (margem + round(raio * dx), margem + round(raio * dy))
        r = max(2, round(raio * tamanho))
        desenhar_circulo(tela, sombra, centro, r)
        desenhar_circulo(tela, luz, (centro[0], centro[1] + 1), r, espessura=1)
    return tela
