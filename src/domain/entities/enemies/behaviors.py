"""Enemy movement behavior classes (Strategy pattern).

Each behavior encapsulates a different movement algorithm that can be
swapped onto an Enemy at runtime.
"""

from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.entities.enemies.base import Enemy

LARGURA = 900


class MovementBehavior(ABC):
    """Abstract base for enemy movement behaviors."""

    @abstractmethod
    def update(self, enemy: "Enemy", jogador) -> None:
        """Modify enemy position based on this behavior."""


class StraightMovement(MovementBehavior):
    """Move straight down with gentle rotation."""

    def update(self, enemy: "Enemy", jogador) -> None:
        enemy.y += enemy.vel
        enemy.angulo += 0.04


class ZigzagMovement(MovementBehavior):
    """Sinusoidal horizontal movement while descending."""

    def __init__(self, amplitude: float = 70.0, frequency: float = 0.05) -> None:
        self.amplitude = amplitude
        self.frequency = frequency

    def update(self, enemy: "Enemy", jogador) -> None:
        enemy.y += enemy.vel
        enemy.fase += self.frequency
        enemy.x = enemy.base_x + math.sin(enemy.fase) * self.amplitude
        enemy.angulo += 0.04


class SpiralMovement(MovementBehavior):
    """Tight spiral descent."""

    def update(self, enemy: "Enemy", jogador) -> None:
        enemy.y += enemy.vel * 0.9
        enemy.fase += 0.045
        enemy.x = enemy.base_x + math.sin(enemy.fase) * 60
        enemy.angulo += 0.08


class ChaseMovement(MovementBehavior):
    """Actively pursuit the player."""

    def update(self, enemy: "Enemy", jogador) -> None:
        dx = jogador.x - enemy.x
        dy = jogador.y - enemy.y
        norma = math.hypot(dx, dy) or 1
        enemy.x += dx / norma * enemy.vel * 0.9
        enemy.y += dy / norma * enemy.vel * 0.9
        enemy.angulo += 0.06


class RotateMovement(MovementBehavior):
    """Rotate while descending with slight oscillation."""

    def update(self, enemy: "Enemy", jogador) -> None:
        enemy.y += enemy.vel
        enemy.angulo += 0.07
        enemy.fase += 0.03
        enemy.x = enemy.base_x + math.sin(enemy.fase) * 40


class WaveMovement(MovementBehavior):
    """Wide sinusoidal wave pattern."""

    def update(self, enemy: "Enemy", jogador) -> None:
        enemy.y += enemy.vel
        enemy.angulo += 0.05
        enemy.x = enemy.base_x + math.sin(enemy.fase) * 90
        enemy.fase += 0.04


class ErraticMovement(MovementBehavior):
    """Random velocity changes creating unpredictable movement."""

    def update(self, enemy: "Enemy", jogador) -> None:
        if random.random() < 0.02:
            enemy.vel_x = random.uniform(-1.6, 1.6)
        if random.random() < 0.02:
            enemy.vel_y = random.uniform(1.0, 2.6)
        enemy.x += enemy.vel_x
        enemy.y += enemy.vel_y
        enemy.x = max(20, min(LARGURA - 20, enemy.x))
        enemy.angulo += 0.12


class FloatMovement(MovementBehavior):
    """Slow descent with small horizontal bobbing."""

    def update(self, enemy: "Enemy", jogador) -> None:
        enemy.y += enemy.vel * 0.5
        enemy.fase += 0.05
        enemy.x = enemy.base_x + math.sin(enemy.fase) * 30
        enemy.angulo += 0.03


class ChargeMovement(MovementBehavior):
    """Accelerating dive toward the player."""

    def update(self, enemy: "Enemy", jogador) -> None:
        enemy.y += enemy.vel * (1 + enemy.fase * 0.06)
        enemy.x += (jogador.x - enemy.x) * 0.03
        enemy.fase += 0.01
        enemy.angulo += 0.1


class FairyMovement(MovementBehavior):
    """Erratic sinusoidal movement with periodic invisibility."""

    def update(self, enemy: "Enemy", jogador) -> None:
        enemy.y += enemy.vel
        enemy.fase += 0.03
        enemy.x = enemy.base_x + math.sin(enemy.fase * 1.3) * 80
        enemy.angulo += 0.05
        if enemy.invisivel <= 0 and random.random() < 0.006:
            enemy.invisivel = 40


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

BEHAVIORS: dict[str, MovementBehavior] = {
    "reta": StraightMovement(),
    "zigzag": ZigzagMovement(),
    "zigzag_lento": ZigzagMovement(amplitude=100.0, frequency=0.03),
    "espiral": SpiralMovement(),
    "persegue": ChaseMovement(),
    "gira": RotateMovement(),
    "ondulacao": WaveMovement(),
    "erratico": ErraticMovement(),
    "flutua": FloatMovement(),
    "investida": ChargeMovement(),
    "fada": FairyMovement(),
}


def get_behavior(name: str) -> MovementBehavior:
    """Look up a movement behavior by name."""
    return BEHAVIORS.get(name, StraightMovement())
