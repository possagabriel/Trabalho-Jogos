"""Abstract Entity base class using Template Method pattern."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Optional


class Entity(ABC):
    """Base class for all game entities.

    Uses Template Method pattern: ``update`` and ``render`` define the
    skeleton algorithm, while subclasses provide concrete steps via
    ``before_update`` / ``after_update`` hooks and abstract methods.
    """

    def __init__(
        self,
        x: float,
        y: float,
        health: int,
        max_health: Optional[int] = None,
    ) -> None:
        self.x: float = x
        self.y: float = y
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.active: bool = True
        self.health: int = health
        self.max_health: int = max_health or health

    # ------------------------------------------------------------------
    # Template Method
    # ------------------------------------------------------------------

    def update(self, dt: float = 1.0, **kwargs) -> list:
        """Template method: runs hooks then delegates to concrete logic."""
        if not self.active:
            return []
        self.before_update(dt, **kwargs)
        events = self.on_update(dt, **kwargs)
        self.after_update(dt, **kwargs)
        return events

    def before_update(self, dt: float = 1.0, **kwargs) -> None:
        """Hook executed before the concrete update logic."""

    def after_update(self, dt: float = 1.0, **kwargs) -> None:
        """Hook executed after the concrete update logic."""

    @abstractmethod
    def on_update(self, dt: float = 1.0, **kwargs) -> list:
        """Concrete update logic implemented by subclasses.

        Returns a list of events (new projectiles, messages, etc.).
        """

    @abstractmethod
    def render(self, surface, **kwargs) -> None:
        """Draw the entity on the given pygame surface."""

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    @abstractmethod
    def get_rect(self):
        """Return a pygame.Rect bounding box for this entity."""

    def distance_to(self, other: "Entity") -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def collides_with(self, other: "Entity") -> bool:
        return self.get_rect().colliderect(other.get_rect())

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def take_damage(self, amount: int) -> bool:
        """Apply damage. Returns True if the entity died."""
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.active = False
            return True
        return False

    def heal(self, amount: int) -> None:
        self.health = min(self.health + amount, self.max_health)

    @property
    def alive(self) -> bool:
        return self.active and self.health > 0
