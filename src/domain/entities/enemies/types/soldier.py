"""SoldierEnemy - basic melee enemy type.

Corresponds to the 'soldado' / 'scout' archetypes from the original game.
Uses zigzag or straight movement, no ranged attack.
"""

from __future__ import annotations

import math
import random
from typing import Optional

import pygame

from src.domain.entities.enemies.base import Enemy

AMARELO = (255, 220, 60)
VERDE = (80, 220, 100)


class SoldierEnemy(Enemy):
    """Basic soldier enemy with simple movement and no ranged attack.

    Migrated from the scout/soldado archetype in game/enemies.py.
    """

    def __init__(
        self,
        nivel: int,
        x: Optional[float] = None,
        y: float = -40.0,
        escala: float = 1.0,
        variante: str = "soldado",
    ) -> None:
        super().__init__(variante, nivel, x=x, y=y, escala=escala)
        self.variante = variante

    def on_update(self, dt: float = 1.0, **kwargs) -> list:
        events = super().on_update(dt, **kwargs)
        # Soldiers don't shoot; just move and try to collide
        return events

    def render(self, surface, **kwargs) -> None:
        if self.invisivel > 0 and (self.invisivel // 4) % 2 == 0:
            return
        x, y = int(self.x), int(self.y)
        cor = (255, 255, 255) if self.flash > 0 else self.cor
        if self.variante == "scout":
            # Triangle shape for scouts
            pts = [
                (x, y - self.raio),
                (x - self.raio, y + self.raio),
                (x + self.raio, y + self.raio),
            ]
            pygame.draw.polygon(surface, cor, pts)
            pygame.draw.polygon(surface, (255, 255, 255), pts, 3)
        else:
            # Square shape for soldiers
            s = self.raio
            pts = [
                (x - s, y - s), (x + s, y - s),
                (x + s, y + s), (x - s, y + s),
            ]
            pygame.draw.polygon(surface, cor, pts)
            pygame.draw.polygon(surface, (255, 255, 255), pts, 3)
