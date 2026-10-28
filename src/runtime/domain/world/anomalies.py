"""Anomalias navegáveis do mundo aberto: gravidade e passagens pareadas."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from src.core.constants import ALTURA, LARGURA

COR_DISCO = (8, 11, 24)
COR_ACRECAO = (239, 150, 91)
COR_LENTE = (136, 190, 236)
COR_PORTAL = (111, 211, 236)
COR_PORTAL_INTERNO = (188, 139, 231)
COR_COMIC = (226, 197, 151)


@dataclass(frozen=True, slots=True)
class BlackHole:
    """Centro gravitacional com alcance limitado e núcleo visual."""

    x: float
    y: float
    radius: int = 90
    influence: float = 1100.0

    @property
    def position(self) -> tuple[float, float]:
        """Retorna a posição no mapa."""
        return self.x, self.y


@dataclass(frozen=True, slots=True)
class Wormhole:
    """Entrada de uma passagem ligada a outra posição."""

    x: float
    y: float
    target: int
    radius: float = 86.0

    @property
    def position(self) -> tuple[float, float]:
        """Retorna a posição no mapa."""
        return self.x, self.y


class CosmicAnomalies:
    """Mantém anomalias fixas por dimensão, sem gerar superfícies por quadro."""

    GRAVITY_STRENGTH = 36_000_000.0
    GRAVITY_SOFTENING = 180.0

    def __init__(self, dimension: int) -> None:
        shift = (dimension - 1) * 125.0
        self.black_holes = (
            BlackHole(9500.0 + shift, 6600.0 - shift / 2),
            BlackHole(12000.0 - shift / 2, 10300.0 - shift / 3),
        )
        self.wormholes = (
            Wormhole(4300.0 + shift, 2200.0, 1),
            Wormhole(14700.0 - shift, 10600.0, 0),
            Wormhole(4300.0, 10800.0 - shift, 3),
            Wormhole(14900.0, 2200.0 + shift, 2),
        )

    def gravity(self, x: float, y: float) -> tuple[float, float]:
        """Calcula aceleração suavizada em direção aos buracos negros próximos."""
        ax = ay = 0.0
        for hole in self.black_holes:
            dx, dy = hole.x - x, hole.y - y
            distance = math.hypot(dx, dy)
            if not 1.0 <= distance < hole.influence:
                continue
            acceleration = self.GRAVITY_STRENGTH / (distance * distance + self.GRAVITY_SOFTENING**2)
            ax += dx / distance * acceleration
            ay += dy / distance * acceleration
        return ax, ay

    def destination(self, x: float, y: float, cooldown: float) -> tuple[float, float] | None:
        """Encontra a saída, deixando a nave fora do raio do portal de destino."""
        if cooldown > 0:
            return None
        for portal in self.wormholes:
            if math.hypot(x - portal.x, y - portal.y) <= portal.radius:
                target = self.wormholes[portal.target]
                return target.x + target.radius + 100.0, target.y
        return None

    def render(
        self, surface: pygame.Surface, camera_x: float, camera_y: float, comic: bool
    ) -> None:
        """Desenha discos gravitacionais e portais visíveis na câmera."""
        accretion = COR_COMIC if comic else COR_ACRECAO
        lens = COR_COMIC if comic else COR_LENTE
        portal_color = COR_COMIC if comic else COR_PORTAL
        for hole in self.black_holes:
            x, y = round(hole.x - camera_x), round(hole.y - camera_y)
            if not (-150 <= x <= LARGURA + 150 and -150 <= y <= ALTURA + 150):
                continue
            pygame.draw.circle(surface, lens, (x, y), hole.radius + 35, 1)
            pygame.draw.ellipse(
                surface, accretion, (x - hole.radius - 28, y - 42, (hole.radius + 28) * 2, 84), 5
            )
            pygame.draw.circle(surface, accretion, (x, y), hole.radius + 8, 4)
            pygame.draw.circle(surface, COR_DISCO, (x, y), hole.radius)
            pygame.draw.circle(surface, lens, (x, y), hole.radius - 8, 2)
        for portal in self.wormholes:
            x, y = round(portal.x - camera_x), round(portal.y - camera_y)
            if not (-130 <= x <= LARGURA + 130 and -130 <= y <= ALTURA + 130):
                continue
            pygame.draw.ellipse(surface, portal_color, (x - 64, y - 103, 128, 206), 4)
            pygame.draw.ellipse(
                surface,
                COR_PORTAL_INTERNO if not comic else COR_COMIC,
                (x - 46, y - 82, 92, 164),
                2,
            )
            pygame.draw.circle(surface, portal_color, (x, y), 10, 2)
