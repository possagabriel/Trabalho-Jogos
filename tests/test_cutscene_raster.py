"""Regressões do acabamento raster cacheado das cutscenes."""

import pygame

from src.runtime.presentation.cutscene_raster import filtrar_fundo_cutscene


def test_filtro_preserva_origem_dimensoes_e_cache() -> None:
    origem = pygame.Surface((96, 54))
    origem.fill((34, 66, 120))
    pygame.draw.circle(origem, (230, 200, 80), (44, 27), 14)
    original = origem.copy()

    primeiro = filtrar_fundo_cutscene(origem, (120, 160, 255))
    segundo = filtrar_fundo_cutscene(origem, (120, 160, 255))

    assert primeiro.get_size() == origem.get_size()
    assert segundo is primeiro
    assert pygame.image.tobytes(origem, "RGB") == pygame.image.tobytes(original, "RGB")
    assert pygame.image.tobytes(primeiro, "RGB") != pygame.image.tobytes(origem, "RGB")


def test_filtro_aplica_tingimento_por_dimensao() -> None:
    origem = pygame.Surface((96, 54))
    origem.fill((75, 80, 90))

    azul = filtrar_fundo_cutscene(origem, (120, 160, 255))
    cobre = filtrar_fundo_cutscene(origem, (255, 120, 70))

    assert pygame.image.tobytes(azul, "RGB") != pygame.image.tobytes(cobre, "RGB")
