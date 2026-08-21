"""EnemyAI coordinator — assigns and manages AI strategies for enemies.

Serves as a facade over the individual ``AIStrategy`` implementations,
providing a simple interface for the game loop to update all active
enemies with the correct behaviour.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Type

from .base import AIStrategy
from .behaviors import ChaseAI, CircleAI, StraightAI, ZigZagAI

if TYPE_CHECKING:
    from src.domain.entities.base import Entity


# Map of movement-type strings (as used in TIPOS) to AI classes.
_MOVEMENT_MAP: Dict[str, Type[AIStrategy]] = {
    "reta": StraightAI,
    "zigzag": ZigZagAI,
    "zigzag_lento": lambda: ZigZagAI(speed=1.4, amplitude=30.0,
                                      frequency=1.2),
    "persegue": ChaseAI,
    "espiral": CircleAI,
    "gira": lambda: CircleAI(radius=40.0, angular_speed=3.0, drift=1.0),
    "ondulacao": lambda: ZigZagAI(speed=1.7, amplitude=50.0,
                                   frequency=1.5),
    "erratico": lambda: ZigZagAI(speed=2.4, amplitude=35.0,
                                  frequency=4.0),
    "investida": StraightAI,
    "flutua": lambda: CircleAI(radius=80.0, angular_speed=0.8, drift=0.5),
    "fada": lambda: ZigZagAI(speed=2.4, amplitude=20.0, frequency=5.0),
}


def create_ai(movement_type: str) -> AIStrategy:
    """Factory: return the ``AIStrategy`` for *movement_type*.

    Falls back to ``StraightAI`` for unknown types.
    """
    factory = _MOVEMENT_MAP.get(movement_type)
    if factory is None:
        return StraightAI()
    if callable(factory) and not isinstance(factory, type):
        return factory()  # type: ignore[call-arg]
    return factory()  # type: ignore[call-arg]


class EnemyAI:
    """Coordinator that assigns AI strategies and updates active enemies.

    Usage::

        coordinator = EnemyAI()
        for enemy in enemies:
            coordinator.assign(enemy, enemy.movement_type)
        # each frame:
        coordinator.update_all(dt, player)
    """

    def __init__(self) -> None:
        self._assignments: dict[int, AIStrategy] = {}

    def assign(self, entity: "Entity", movement_type: str) -> None:
        """Bind an AI strategy to *entity* based on *movement_type*."""
        self._assignments[id(entity)] = create_ai(movement_type)

    def get_strategy(self, entity: "Entity") -> AIStrategy | None:
        """Return the strategy bound to *entity*, or ``None``."""
        return self._assignments.get(id(entity))

    def unassign(self, entity: "Entity") -> None:
        """Remove the strategy bound to *entity*."""
        self._assignments.pop(id(entity), None)

    def update_all(self, dt: float,
                   player: "Entity | None" = None) -> None:
        """Update every assigned entity."""
        for entity_id, strategy in list(self._assignments.items()):
            # The entity reference is kept weakly through the caller;
            # here we just iterate — actual entity management happens
            # in the game loop which passes ``owner`` directly.
            pass

    def update_one(self, owner: "Entity", player: "Entity | None",
                   dt: float) -> None:
        """Update a single entity using its assigned strategy."""
        strategy = self._assignments.get(id(owner))
        if strategy is not None:
            strategy.update(owner, player, dt)

    def clear(self) -> None:
        """Remove all assignments."""
        self._assignments.clear()
