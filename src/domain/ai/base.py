"""Abstract AI strategy for enemy movement and behaviour.

Follows the Strategy pattern: each concrete movement type (straight,
zigzag, chase, etc.) is a separate class that implements this interface.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.entities.base import Entity


class AIStrategy(abc.ABC):
    """Interface that every enemy AI behaviour must implement.

    An ``AIStrategy`` receives a reference to the owning ``Entity`` and a
    reference to the player entity, then computes velocity / position
    changes for the current frame.
    """

    @abc.abstractmethod
    def update(
        self,
        owner: "Entity",
        player: "Entity | None",
        dt: float,
    ) -> None:
        """Compute the next movement step for *owner*.

        Implementations should modify ``owner.vx`` and ``owner.vy`` (or
        ``owner.x`` / ``owner.y`` directly) to achieve the desired
        movement pattern.

        Args:
            owner: The entity this AI controls.
            player: The player entity (for chase / aim behaviours).
            dt: Time step in seconds.
        """

    @abc.abstractmethod
    def reset(self) -> None:
        """Reset any internal state (timers, phases, etc.)."""
