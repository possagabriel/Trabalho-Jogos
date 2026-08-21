"""CollisionSystem - handles spatial collision checks.

Extracted from game/core.py collision detection logic.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.domain.entities.base import Entity
    from src.domain.entities.bosses.types import Boss
    from src.domain.entities.enemies.base import Enemy
    from src.domain.entities.enemies.factory import SpecialEnemy
    from src.domain.entities.player import Player
    from src.domain.entities.projectiles.factory import Projetil


class CollisionResult:
    """Result of a single collision check."""

    def __init__(
        self,
        entity_a: "Entity",
        entity_b: "Entity",
        collision_type: str,
    ) -> None:
        self.entity_a = entity_a
        self.entity_b = entity_b
        self.collision_type: str = collision_type


class CollisionSystem:
    """Handles all spatial collision detection in the game.

    Extracted from game/core.py collision checks. Uses spatial queries
    rather than event-based collisions for finer control.
    """

    def __init__(self) -> None:
        self.screen_width: int = 900
        self.screen_height: int = 700

    def check_projectile_vs_enemies(
        self,
        projeteis: list["Projetil"],
        inimigos: list["Enemy"],
    ) -> list[CollisionResult]:
        """Check player projectiles against all enemies."""
        results: list[CollisionResult] = []
        for proj in projeteis:
            if proj.origem != "jogador":
                continue
            for inimigo in inimigos:
                if proj.rect.colliderect(inimigo.rect):
                    results.append(CollisionResult(proj, inimigo, "projectile_enemy"))
        return results

    def check_projectile_vs_boss(
        self,
        projeteis: list["Projetil"],
        boss: Optional["Boss"],
    ) -> list[CollisionResult]:
        """Check player projectiles against the boss."""
        if boss is None:
            return []
        results: list[CollisionResult] = []
        for proj in projeteis:
            if proj.origem != "jogador":
                continue
            if proj.rect.colliderect(boss.rect):
                results.append(CollisionResult(proj, boss, "projectile_boss"))
        return results

    def check_enemy_projectile_vs_player(
        self,
        projeteis: list["Projetil"],
        jogador: "Player",
    ) -> list[CollisionResult]:
        """Check enemy projectiles against the player."""
        results: list[CollisionResult] = []
        for proj in projeteis:
            if proj.origem != "inimigo":
                continue
            if proj.rect.colliderect(jogador.rect):
                results.append(CollisionResult(proj, jogador, "enemy_projectile_player"))
        return results

    def check_enemy_vs_player(
        self,
        inimigos: list["Enemy"],
        jogador: "Player",
    ) -> list[CollisionResult]:
        """Check physical enemy-player collisions."""
        results: list[CollisionResult] = []
        for inimigo in inimigos:
            if inimigo.rect.colliderect(jogador.rect):
                results.append(CollisionResult(inimigo, jogador, "enemy_player"))
        return results

    def check_boss_vs_player(
        self,
        boss: Optional["Boss"],
        jogador: "Player",
    ) -> list[CollisionResult]:
        """Check boss-player collision."""
        if boss is None:
            return []
        if boss.rect.colliderect(jogador.rect):
            return [CollisionResult(boss, jogador, "boss_player")]
        return []

    def check_powerup_vs_player(
        self,
        powerups: list,
        jogador: "Player",
    ) -> list[CollisionResult]:
        """Check powerup collection."""
        results: list[CollisionResult] = []
        for pu in powerups:
            if pu.rect.colliderect(jogador.rect):
                results.append(CollisionResult(pu, jogador, "powerup_player"))
        return results

    def is_in_range(
        self,
        entity_a: "Entity",
        entity_b: "Entity",
        range_dist: float,
    ) -> bool:
        """Check if two entities are within a given distance."""
        return entity_a.distance_to(entity_b) <= range_dist

    def gravity_field(
        self,
        source_x: float,
        source_y: float,
        target_x: float,
        target_y: float,
        max_dist: float = 150.0,
        force: float = 0.35,
    ) -> tuple[float, float]:
        """Calculate gravitational pull from a source point.

        Used by distortion and conductor enemies to attract player projectiles.
        Returns (dx, dy) force components.
        """
        dx = source_x - target_x
        dy = source_y - target_y
        dist = math.hypot(dx, dy)
        if dist < max_dist and dist > 1:
            return dx / dist * force, dy / dist * force
        return 0.0, 0.0

    def is_off_screen(self, entity: "Entity", margin: int = 60) -> bool:
        """Check if an entity has left the screen."""
        return entity.y > self.screen_height + margin

    def aabb_overlap(self, rect_a, rect_b) -> bool:
        """Simple AABB overlap check."""
        return rect_a.colliderect(rect_b)
