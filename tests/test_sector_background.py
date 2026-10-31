"""Identidade, textura e contraste dos fundos do mundo aberto."""

import random

import pygame

from src.core.constants import ALTURA, LARGURA
from src.runtime.domain.world.open_world import OpenWorldRuntime
from src.runtime.domain.world.region_background import SectorBackground


def fundo(dimensao=1):
    return SectorBackground(dimensao, OpenWorldRuntime.SECTORS, OpenWorldRuntime.SPAWN)


def test_nebulosa_tem_variacao_horizontal_em_vez_de_gradiente_plano():
    arte = fundo().surface_for_sector(0, False)
    amostras = {tuple(arte.get_at((x, 90))[:3]) for x in range(16, LARGURA - 16, 16)}
    assert len(amostras) > 30


def test_fundos_reproduziveis_preservam_rng_e_cache():
    estado = random.getstate()
    primeiro, segundo = fundo(), fundo()
    original = primeiro.surface_for_sector(2, False)
    assert random.getstate() == estado
    assert original is primeiro.surface_for_sector(2, False)
    assert pygame.image.tobytes(original, "RGB") == pygame.image.tobytes(
        segundo.surface_for_sector(2, False), "RGB")
    assert pygame.image.tobytes(original, "RGB") != pygame.image.tobytes(
        primeiro.surface_for_sector(2, True), "RGB")
    antes = pygame.image.tobytes(original, "RGB")
    primeiro.update(*OpenWorldRuntime.SECTORS[2][1], 2.0)
    primeiro.render(pygame.Surface((LARGURA, ALTURA)), False)
    assert pygame.image.tobytes(original, "RGB") == antes


def test_centro_das_seis_dimensoes_tem_luz_controlada_para_combate():
    for dimensao in range(1, 7):
        arte = fundo(dimensao).surface_for_sector(0, False)
        lumas = [sum(c * peso for c, peso in zip(
            arte.get_at((x, y))[:3], (0.2126, 0.7152, 0.0722)))
            for x in range(LARGURA // 2 - 100, LARGURA // 2 + 100, 20)
            for y in range(ALTURA // 2 - 80, ALTURA // 2 + 80, 20)]
        assert sum(lumas) / len(lumas) < 65
