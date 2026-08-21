"""TankEnemy - heavy enemy type with high health.

Corresponds to forja, distorcao, cristalino archetypes.
Slow movement, high HP, area attacks.
"""

from __future__ import annotations

import math
import random
from typing import Optional

import pygame

from src.domain.entities.enemies.base import Enemy

ROXO = (140, 60, 200)
VERDE = (80, 220, 100)
BRANCO = (255, 255, 255)
LARANJA = (255, 160, 40)


class TankEnemy(Enemy):
    """Heavy enemy with high HP and area attacks.

    Migrated from forja/distorcao/cristalino archetypes.
    Slow but durable, often uses leque or baixo attacks.
    """

    def __init__(
        self,
        tipo: str,
        nivel: int,
        x: Optional[float] = None,
        y: float = -40.0,
        escala: float = 1.0,
    ) -> None:
        super().__init__(tipo, nivel, x=x, y=y, escala=escala)
        # Tanks get extra health
        self.health = int(self.health * 1.5)
        self.vida_max = self.health

    def on_update(self, dt: float = 1.0, **kwargs) -> list:
        events = super().on_update(dt, **kwargs)
        return events

    def render(self, surface, **kwargs) -> None:
        if self.invisivel > 0 and (self.invisivel // 4) % 2 == 0:
            return
        x, y = int(self.x), int(self.y)
        cor = (255, 255, 255) if self.flash > 0 else self.cor
        if self.tipo == "distorcao":
            # Pulsating circle for distortion
            pulso = 1 + 0.15 * math.sin(pygame.time.get_ticks() * 0.001)
            raio = int(self.raio * pulso)
            pygame.draw.circle(surface, cor, (x, y), raio)
            pygame.draw.circle(surface, BRANCO, (x, y), raio, 3)
            pygame.draw.circle(surface, (40, 10, 60), (x, y), raio // 2, 2)
        elif self.tipo == "cristalino":
            # Hexagon for crystal
            pts = Enemy._pontos_poligono((x, y), self.raio, 6, self.angulo)
            pygame.draw.polygon(surface, cor, pts)
            pygame.draw.polygon(surface, BRANCO, pts, 3)
            # Inner crystal pattern
            pts_inner = Enemy._pontos_poligono(
                (x, y), self.raio * 0.5, 6, -self.angulo
            )
            pygame.draw.polygon(surface, (200, 255, 220), pts_inner, 2)
        else:
            # Hexagon shape for forja
            pts = Enemy._pontos_poligono((x, y), self.raio, 6, self.angulo)
            pygame.draw.polygon(surface, cor, pts)
            pygame.draw.polygon(surface, BRANCO, pts, 3)
            pygame.draw.circle(surface, LARANJA, (x, y), int(self.raio * 0.4))
