"""Asteroides destrutíveis, distribuídos por chunks e com reaparecimento."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Mapping


@dataclass(slots=True)
class Asteroide:
    """Obstáculo persistente de uma posição do mundo."""

    ident: int
    x: float
    y: float
    radius: int
    max_health: int
    health: int
    shape: tuple[tuple[int, int], ...]
    respawn_at: float | None = None

    def active(self) -> bool:
        """Informa se o asteroide participa de desenho e colisão."""
        return self.respawn_at is None


class AsteroidField:
    """Mantém obstáculos em todo o mapa e consulta apenas chunks próximos."""

    CHUNK_SIZE = 800

    def __init__(
        self,
        width: float,
        height: float,
        seed: int,
        protected: tuple[tuple[float, float, float], ...] = (),
        cooldown: float = 30.0,
    ) -> None:
        self.width = float(width)
        self.height = float(height)
        self.cooldown = float(cooldown)
        self.asteroids: list[Asteroide] = []
        self._chunks: dict[tuple[int, int], list[Asteroide]] = {}
        self._destroyed: dict[int, float] = {}
        rng = random.Random(seed)
        columns = math.ceil(self.width / self.CHUNK_SIZE)
        rows = math.ceil(self.height / self.CHUNK_SIZE)
        for row in range(rows):
            for column in range(columns):
                for _ in range(2):
                    x = min(self.width - 48, (column + rng.uniform(0.18, 0.82))
                            * self.CHUNK_SIZE)
                    y = min(self.height - 48, (row + rng.uniform(0.18, 0.82))
                            * self.CHUNK_SIZE)
                    if any(math.hypot(x - px, y - py) < safe_radius
                           for px, py, safe_radius in protected):
                        continue
                    radius = rng.randint(19, 38)
                    health = 2 + radius // 16
                    shape = tuple(
                        (round(math.cos(angle) * radius * rng.uniform(0.78, 1.13)),
                         round(math.sin(angle) * radius * rng.uniform(0.78, 1.13)))
                        for angle in (index * math.tau / 7 for index in range(7))
                    )
                    rock = Asteroide(len(self.asteroids), x, y, radius,
                                     health, health, shape)
                    self.asteroids.append(rock)
                    self._chunks.setdefault((column, row), []).append(rock)

    def nearby(self, x: float, y: float, radius: float) -> list[Asteroide]:
        """Consulta obstáculos nos chunks tocados por um círculo."""
        margin = radius + 40
        left = max(0, int((x - margin) // self.CHUNK_SIZE))
        right = min(math.ceil(self.width / self.CHUNK_SIZE) - 1,
                    int((x + margin) // self.CHUNK_SIZE))
        top = max(0, int((y - margin) // self.CHUNK_SIZE))
        bottom = min(math.ceil(self.height / self.CHUNK_SIZE) - 1,
                     int((y + margin) // self.CHUNK_SIZE))
        return [rock for row in range(top, bottom + 1)
                for column in range(left, right + 1)
                for rock in self._chunks.get((column, row), ())]

    def visible(self, camera_x: float, camera_y: float,
                width: int, height: int) -> list[Asteroide]:
        """Seleciona apenas os obstáculos dos chunks próximos à câmera."""
        return self.nearby(camera_x + width / 2, camera_y + height / 2,
                           math.hypot(width, height) / 2)

    def damage(self, rock: Asteroide, amount: int, now: float) -> bool:
        """Aplica dano e agenda reaparecimento quando a vida chega a zero."""
        if not rock.active() or amount <= 0:
            return False
        rock.health = max(0, rock.health - amount)
        if rock.health:
            return False
        rock.respawn_at = now + self.cooldown
        self._destroyed[rock.ident] = rock.respawn_at
        return True

    def update(self, now: float) -> None:
        """Reativa os obstáculos cujo tempo de reaparecimento terminou."""
        for ident, when in tuple(self._destroyed.items()):
            if now >= when:
                rock = self.asteroids[ident]
                rock.health = rock.max_health
                rock.respawn_at = None
                del self._destroyed[ident]

    def cooldowns(self) -> dict[str, float]:
        """Serializa apenas obstáculos temporariamente destruídos."""
        return {str(ident): round(when, 2)
                for ident, when in self._destroyed.items()}

    def restore(self, saved: Mapping[str, object], now: float) -> None:
        """Restaura tempos de reaparecimento de um save do modo aberto."""
        for key, value in saved.items():
            try:
                ident = int(key)
                when = float(value)
            except (TypeError, ValueError):
                continue
            if not 0 <= ident < len(self.asteroids) or not now < when < now + 3600:
                continue
            rock = self.asteroids[ident]
            rock.health = 0
            rock.respawn_at = when
            self._destroyed[ident] = when
