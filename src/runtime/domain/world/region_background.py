"""Fundos próprios por setor do mundo, com troca suave por posição."""

from __future__ import annotations

import math
import random

import pygame

from src.core.constants import ALTURA, LARGURA
from src.runtime.domain.world.scenarios import CENARIOS


def _misturar(a: tuple[int, int, int], b: tuple[int, int, int],
             proportion: float) -> tuple[int, int, int]:
    return tuple(round(a[index] * (1 - proportion) + b[index] * proportion)
                 for index in range(3))


class SectorBackground:
    """Cacheia seis composições e acompanha o setor próximo da nave."""

    def __init__(self, dimension: int,
                 sectors: tuple[tuple[str, tuple[float, float],
                                      tuple[int, int, int]], ...],
                 position: tuple[float, float]) -> None:
        self.dimension = dimension
        self.sectors = sectors
        self.current_sector = self._nearest(*position)
        self.target_sector = self.current_sector
        self.transition = 1.0
        self._surfaces: dict[tuple[int, bool], pygame.Surface] = {}
        self._blend = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)

    def _nearest(self, x: float, y: float) -> int:
        return min(range(len(self.sectors)), key=lambda index:
                   math.hypot(x - self.sectors[index][1][0],
                              y - self.sectors[index][1][1]))

    def update(self, x: float, y: float, dt: float) -> None:
        """Escolhe a área da nave e avança uma transição sem pop."""
        if self.current_sector != self.target_sector:
            self.transition = min(1.0, self.transition + max(0.0, dt) / 0.8)
            if self.transition >= 1.0:
                self.current_sector = self.target_sector
            return
        nearest = self._nearest(x, y)
        if nearest != self.current_sector:
            self.target_sector = nearest
            self.transition = 0.0

    def surface_for_sector(self, sector: int, comic: bool) -> pygame.Surface:
        """Obtém a composição cacheada de um setor e estilo de apresentação."""
        key = (sector, comic)
        if key in self._surfaces:
            return self._surfaces[key]
        rng = random.Random(self.dimension * 1009 + sector * 97 + int(comic))
        scene = CENARIOS[self.dimension - 1]
        accent = self.sectors[sector][2]
        top = _misturar(scene["topo"], accent, 0.22)
        bottom = _misturar(scene["base"], accent, 0.18)
        if comic:
            top = _misturar((37, 37, 43), accent, 0.22)
            bottom = _misturar((52, 46, 43), accent, 0.16)
        result = pygame.Surface((LARGURA, ALTURA))
        for y in range(ALTURA):
            color = _misturar(top, bottom, y / max(1, ALTURA - 1))
            pygame.draw.line(result, color, (0, y), (LARGURA, y))

        veil = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        for index in range(9):
            cx = rng.randrange(-120, LARGURA + 120)
            cy = rng.randrange(-100, ALTURA + 100)
            rx = rng.randrange(90, 260)
            ry = rng.randrange(50, 170)
            color = _misturar(accent, (110, 130, 170), index / 18)
            pygame.draw.ellipse(
                veil, (*color, 9 if comic else 15),
                (cx - rx, cy - ry, rx * 2, ry * 2),
            )
        result.blit(veil, (0, 0))
        if comic:
            ink = _misturar(top, (7, 10, 18), 0.4)
            for y in range(8, ALTURA, 24):
                for x in range(8 + (y // 24 % 2) * 12, LARGURA, 24):
                    pygame.draw.circle(result, ink, (x, y), 1)
        else:
            line = _misturar(accent, (16, 20, 37), 0.65)
            for index in range(3):
                x = rng.randrange(0, LARGURA)
                y = rng.randrange(0, ALTURA)
                radius = 70 + index * 42
                pygame.draw.circle(result, line, (x, y), radius, 1)
        self._surfaces[key] = result
        return result

    def render(self, surface: pygame.Surface, comic: bool) -> None:
        """Desenha o setor atual e mistura gradualmente o próximo."""
        surface.blit(self.surface_for_sector(self.current_sector, comic), (0, 0))
        if self.current_sector != self.target_sector:
            self._blend.blit(self.surface_for_sector(self.target_sector, comic), (0, 0))
            self._blend.set_alpha(round(255 * self.transition))
            surface.blit(self._blend, (0, 0))
