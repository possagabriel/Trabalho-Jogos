"""BossFactory for creating boss instances.

Uses Factory Method pattern to instantiate the correct boss for each scenario.
"""

from __future__ import annotations

from src.domain.entities.bosses.types import Boss, BOSSES_POR_CENARIO


class BossFactory:
    """Factory for creating boss entities.

    Each scenario has a unique boss defined in BOSSES_POR_CENARIO.
    """

    @classmethod
    def create(cls, nivel: int, cenario_id: int) -> Boss:
        """Create a boss for the given level and scenario.

        Args:
            nivel: Current game level (bosses appear every 5 levels).
            cenario_id: Scenario ID (1-6) determining which boss to spawn.

        Returns:
            A fully configured Boss instance.
        """
        if cenario_id not in BOSSES_POR_CENARIO:
            raise ValueError(f"Unknown scenario ID: {cenario_id}")
        return Boss(nivel, cenario_id)

    @classmethod
    def get_boss_config(cls, cenario_id: int) -> dict:
        """Return the raw configuration dict for a boss."""
        if cenario_id not in BOSSES_POR_CENARIO:
            raise ValueError(f"Unknown scenario ID: {cenario_id}")
        return dict(BOSSES_POR_CENARIO[cenario_id])

    @classmethod
    def is_boss_level(cls, nivel: int) -> bool:
        """Check if the given level is a boss level (multiple of 5)."""
        return nivel % 5 == 0

    @classmethod
    def boss_for_level(cls, nivel: int) -> int | None:
        """Return the scenario ID for the boss at this level, or None."""
        if not cls.is_boss_level(nivel):
            return None
        return min((nivel - 1) // 5 + 1, 6)
