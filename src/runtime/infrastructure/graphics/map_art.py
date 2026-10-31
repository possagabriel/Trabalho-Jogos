"""Miniaturas do mapa derivadas da arte real, sem mover as entidades do jogo."""

from __future__ import annotations

from copy import copy
from functools import lru_cache
from typing import TYPE_CHECKING

import pygame

from src.infrastructure.graphics.comic_theme import usar_visual
from src.runtime.infrastructure.graphics.anomaly_visuals import camada_anomalia
from src.runtime.infrastructure.graphics.nebula_background import criar_fundo_nebuloso
from src.runtime.infrastructure.graphics.smooth import desenhar_circulo
from src.runtime.infrastructure.graphics.world_objects import arte_asteroide

if TYPE_CHECKING:
    from src.runtime.domain.entities.bosses import Boss
    from src.runtime.domain.entities.player import Skin


def _reduzir(arte: pygame.Surface, tamanho: int) -> pygame.Surface:
    area = arte.get_bounding_rect()
    if not area.w or not area.h:
        return pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
    fator = tamanho / max(area.size)
    return pygame.transform.smoothscale(
        arte.subsurface(area), (max(1, round(area.w * fator)), max(1, round(area.h * fator))))


@lru_cache(maxsize=48)
def miniatura_anomalia(portal: bool, comic: bool, tamanho: int) -> pygame.Surface:
    """Usa o mesmo disco de acreção ou túnel visto na exploração."""
    return _reduzir(camada_anomalia(portal, comic, True), tamanho)


@lru_cache(maxsize=8)
def miniatura_fenda(comic: bool, tamanho: int) -> pygame.Surface:
    """Mantém os dois anéis cruzados que identificam as fendas no mundo."""
    tela = pygame.Surface((80, 80), pygame.SRCALPHA)
    for tamanho_anel in ((68, 36), (36, 68)):
        rect = pygame.Rect((0, 0), tamanho_anel)
        rect.center = (40, 40)
        pygame.draw.ellipse(tela, (220, 225, 245) if comic else (160, 178, 226), rect, 3)
    desenhar_circulo(tela, (235, 240, 250), (40, 40), 5)
    return _reduzir(tela, tamanho)


@lru_cache(maxsize=1024)
def miniatura_rocha(forma: tuple[tuple[int, int], ...], raio: int,
                    comic: bool, tamanho: int) -> pygame.Surface:
    """Conserva a silhueta e as crateras de cada asteroide."""
    return _reduzir(arte_asteroide(forma, raio, comic), tamanho)


@lru_cache(maxsize=32)
def miniatura_entidade(entidade: Boss, comic: bool, tamanho: int) -> pygame.Surface:
    """Fotografa uma cópia do boss ou da patrulha, sem efeitos de dano."""
    modelo = copy(entidade)
    lado = round(modelo.raio * 4 + 64)
    base = pygame.Surface((lado, lado), pygame.SRCALPHA)
    modelo.x = modelo.y = lado // 2
    modelo.flash = modelo.pulso_fase = 0
    modelo.enraivecido = modelo.entrando = modelo.teleportando = False
    with usar_visual({"estilo_visual": "COMIC" if comic else "ORIGINAL"}):
        modelo.desenhar(base)
    return _reduzir(base, tamanho)


@lru_cache(maxsize=32)
def _base_nave(skin: Skin, comic: bool) -> pygame.Surface:
    base = pygame.Surface((160, 160), pygame.SRCALPHA)
    with usar_visual({"estilo_visual": "COMIC" if comic else "ORIGINAL"}):
        skin._desenhar_corpo(base, 80, 80, 0, 0)
    return base


@lru_cache(maxsize=512)
def miniatura_nave(skin: Skin, angulo: int, comic: bool, tamanho: int) -> pygame.Surface:
    """Reutiliza o casco equipado, com a orientação da mira ou do movimento."""
    return _reduzir(pygame.transform.rotate(_base_nave(skin, comic), -angulo), tamanho)


@lru_cache(maxsize=12)
def fundo_mapa(tamanho: tuple[int, int], dimensao: int, comic: bool) -> pygame.Surface:
    """Oferece contexto espacial discreto, preparado uma vez por dimensão."""
    arte = criar_fundo_nebuloso(tamanho, (6, 10, 18), (2, 5, 10),
                               (35, 57, 76), 7100 + dimensao, comic)
    return arte
