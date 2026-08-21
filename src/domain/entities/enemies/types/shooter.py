"""ShooterEnemy - ranged enemy type.

Corresponds to artilheiro, guardiao, sentinela archetypes.
Uses float or straight movement with various ranged attack patterns.
"""

from __future__ import annotations

import math
import random
from typing import Optional

import pygame

from src.domain.entities.enemies.base import Enemy

CIANO = (0, 220, 255)
BRANCO = (255, 255, 255)
DOURADO = (255, 215, 0)


class ShooterEnemy(Enemy):
    """Enemy with ranged attack capabilities.

    Migrated from artilheiro/guardiao/sentinela archetypes.
    Uses various attack patterns: rajada, feixe, tudo.
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
        self.timer_feixe: int = 0

    def on_update(self, dt: float = 1.0, **kwargs) -> list:
        events = super().on_update(dt, **kwargs)
        if self.timer_feixe > 0:
            self.timer_feixe -= 1
        return events

    def render(self, surface, **kwargs) -> None:
        if self.invisivel > 0 and (self.invisivel // 4) % 2 == 0:
            return
        x, y = int(self.x), int(self.y)
        cor = (255, 255, 255) if self.flash > 0 else self.cor
        # Pentagon shape for shooters
        pts = Enemy._pontos_poligono((x, y), self.raio, 5, self.angulo)
        pygame.draw.polygon(surface, cor, pts)
        pygame.draw.polygon(surface, BRANCO, pts, 3)
        # Inner glow for ranged attackers
        pygame.draw.circle(surface, cor, (x, y), int(self.raio * 0.4))
