"""Concrete AI behaviour strategies for enemy movement.

Migrated from game/enemies.py movement patterns (``_movimento_*``) and
translated into Strategy objects that plug into the ``AIStrategy``
interface.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .base import AIStrategy

if TYPE_CHECKING:
    from src.domain.entities.base import Entity


class StraightAI(AIStrategy):
    """Move straight downward at a fixed speed.

    Corresponds to ``mov: "reta"`` in the original enemy data.
    """

    def __init__(self, speed: float = 2.5) -> None:
        self._speed = speed

    def update(self, owner: "Entity", player: "Entity | None",
               dt: float) -> None:
        owner.vy = self._speed
        owner.vx = 0.0
        owner.y += owner.vy * dt

    def reset(self) -> None:
        pass


class ZigZagAI(AIStrategy):
    """Horizontal oscillation while drifting downward.

    Corresponds to ``mov: "zigzag"`` / ``"zigzag_lento"``.
    """

    def __init__(self, speed: float = 2.2, amplitude: float = 40.0,
                 frequency: float = 2.0) -> None:
        self._speed = speed
        self._amplitude = amplitude
        self._frequency = frequency
        self._time: float = 0.0
        self._start_x: float = 0.0

    def update(self, owner: "Entity", player: "Entity | None",
               dt: float) -> None:
        if self._time == 0.0:
            self._start_x = owner.x
        self._time += dt
        owner.vy = self._speed
        owner.vx = math.sin(self._time * self._frequency) * self._amplitude
        owner.x = self._start_x + math.sin(
            self._time * self._frequency
        ) * self._amplitude
        owner.y += owner.vy * dt

    def reset(self) -> None:
        self._time = 0.0
        self._start_x = 0.0


class ChaseAI(AIStrategy):
    """Move toward the player with a capped speed.

    Corresponds to ``mov: "persegue"``.
    """

    def __init__(self, speed: float = 3.0, turn_rate: float = 0.05) -> None:
        self._speed = speed
        self._turn_rate = turn_rate

    def update(self, owner: "Entity", player: "Entity | None",
               dt: float) -> None:
        if player is None:
            owner.vy = self._speed
            owner.y += owner.vy * dt
            return
        dx = player.x - owner.x
        dy = player.y - owner.y
        dist = math.hypot(dx, dy)
        if dist < 1:
            return
        target_vx = dx / dist * self._speed
        target_vy = dy / dist * self._speed
        owner.vx += (target_vx - owner.vx) * self._turn_rate
        owner.vy += (target_vy - owner.vy) * self._turn_rate
        owner.x += owner.vx * dt
        owner.y += owner.vy * dt

    def reset(self) -> None:
        pass


class CircleAI(AIStrategy):
    """Orbit around a fixed point (or the player) while drifting.

    Corresponds to ``mov: "espiral"`` / ``"gira"``.
    """

    def __init__(self, radius: float = 60.0, angular_speed: float = 2.0,
                 drift: float = 1.5) -> None:
        self._radius = radius
        self._angular_speed = angular_speed
        self._drift = drift
        self._time: float = 0.0
        self._center_x: float = 0.0
        self._center_y: float = 0.0

    def update(self, owner: "Entity", player: "Entity | None",
               dt: float) -> None:
        if self._time == 0.0:
            self._center_x = owner.x
            self._center_y = owner.y
        self._time += dt
        angle = self._time * self._angular_speed
        owner.x = self._center_x + math.cos(angle) * self._radius
        self._center_y += self._drift * dt
        owner.y = self._center_y + math.sin(angle) * self._radius * 0.3

    def reset(self) -> None:
        self._time = 0.0
        self._center_x = 0.0
        self._center_y = 0.0
