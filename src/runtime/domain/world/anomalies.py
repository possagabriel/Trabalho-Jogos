"""Anomalias navegáveis do mundo aberto: gravidade e passagens pareadas."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from src.runtime.infrastructure.graphics.anomaly_visuals import desenhar_anomalia


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
        self, surface: pygame.Surface, camera_x: float, camera_y: float, comic: bool,
        *, tempo: float = 0.0, reduzido: bool = False,
    ) -> None:
        """Projeta anomalias visíveis; efeitos são independentes da física."""
        largura, altura = surface.get_size()
        pontos = [(hole.position, False, "BURACO NEGRO // ATRAÇÃO")
                  for hole in self.black_holes]
        pontos.extend((portal.position, True, f"PORTAL {indice + 1} > {portal.target + 1}")
                      for indice, portal in enumerate(self.wormholes))
        for posicao, portal, legenda in pontos:
            x, y = round(posicao[0] - camera_x), round(posicao[1] - camera_y)
            if not (-190 <= x <= largura + 190 and -180 <= y <= altura + 180):
                continue
            desenhar_anomalia(surface, (x, y), portal=portal, comic=comic,
                              reduzido=reduzido, tempo=tempo, legenda=legenda)
