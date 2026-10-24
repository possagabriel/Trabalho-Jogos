"""Estado e representação inicial do mundo aberto contínuo."""

from __future__ import annotations

import math
import random
from typing import Any

import pygame

from src.core.constants import ALTURA, LARGURA
from src.runtime.domain.entities.bosses import Boss
from src.runtime.domain.entities.enemies import Inimigo
from src.runtime.domain.entities.minibosses.registry import criar_miniboss
from src.runtime.domain.world.scenarios import Cenario
from src.runtime.infrastructure.graphics.fonts import fonte_texto


class OpenWorldRuntime:
    """Movimento livre, câmera suave, fundo em parallax e borda do Vazio."""

    REGION_ID = "espaco_profundo"
    REGION_NAME = "ESPAÇO PROFUNDO"
    REGION_SIZE = (2800.0, 1800.0)
    SPAWN = (520.0, 900.0)
    SPEED = 360.0
    BOSS_LAIR = (2260.0, 900.0)

    def __init__(self, position: tuple[float, float] | None = None,
                 elapsed: float = 0.0) -> None:
        self.width, self.height = self.REGION_SIZE
        self.x, self.y = position or self.SPAWN
        self.x = max(0.0, min(self.width, float(self.x)))
        self.y = max(0.0, min(self.height, float(self.y)))
        self.vx = 0.0
        self.vy = 0.0
        self.camera_x = self.x - LARGURA / 2
        self.camera_y = self.y - ALTURA / 2
        self.elapsed = max(0.0, float(elapsed))
        self._stars = self._build_stars()
        self._landmarks = self._build_landmarks()
        self._cenario = Cenario(1)
        self.enemies = self._create_enemies()
        self.miniboss = criar_miniboss(
            "censor", 1, self._cenario, random.Random(4101))
        self.boss = Boss(5, self._cenario)
        self.boss.x, self.boss.y = self.BOSS_LAIR
        self.boss.entrando = False
        self.boss.angulo = 0.0
        self._font_edge = fonte_texto(28)
        self._font_region = fonte_texto(24)
        self._font_marker = fonte_texto(17)
        self._edge_label = self._font_edge.render(
            "VAZIO", True, (210, 170, 245))
        self._region_label = self._font_region.render(
            f"REGIÃO // {self.REGION_NAME}", True, (145, 180, 217))
        self._boss_label = self._font_marker.render(
            "TOCA // HEXAGONO", True, (255, 202, 102))
        self._mini_label = self._font_marker.render(
            "CENSOR // PATRULHA", True, (255, 124, 201))

    @staticmethod
    def _create_enemies() -> list[tuple[Inimigo, float, float, float, float]]:
        """Cria patrulhas fixas usando as mesmas entidades visuais do modo linear."""
        return [
            (Inimigo("scout", 1, x=790, y=780), 790, 780, 52, 0.0),
            (Inimigo("soldado", 1, x=980, y=1040), 980, 1040, 44, 1.7),
            (Inimigo("estelar", 1, x=360, y=650), 360, 650, 62, 3.1),
            (Inimigo("bomba", 1, x=1180, y=720), 1180, 720, 35, 4.4),
            (Inimigo("abissal", 1, x=1340, y=980), 1340, 980, 54, 5.2),
        ]

    @staticmethod
    def _build_stars() -> tuple[tuple[tuple[float, float, int], ...], ...]:
        rng = random.Random(4101)
        layers = []
        for count, low, high in ((95, 1, 1), (58, 1, 2), (24, 2, 3)):
            layers.append(tuple(
                (rng.uniform(-1200, 4000), rng.uniform(-900, 2700),
                 rng.randint(low, high))
                for _ in range(count)
            ))
        return tuple(layers)

    def _build_landmarks(self) -> tuple[tuple[float, float, int, tuple[int, int, int]], ...]:
        rng = random.Random(4101 ^ 0x5A)
        palette = ((73, 74, 140), (56, 115, 150), (110, 66, 126))
        return tuple(
            (rng.uniform(350, self.width - 350),
             rng.uniform(280, self.height - 280),
             rng.randint(22, 46), palette[index % len(palette)])
            for index in range(3)
        )

    def update(self, dt: float, keys: Any, controls: dict[str, int]) -> None:
        """Move a nave, suaviza a câmera e rebate no limite do mundo."""
        dt = max(0.0, min(float(dt), 0.05))
        left = keys[controls.get("esquerda", pygame.K_LEFT)] or keys[pygame.K_a]
        right = keys[controls.get("direita", pygame.K_RIGHT)] or keys[pygame.K_d]
        up = keys[controls.get("cima", pygame.K_UP)] or keys[pygame.K_w]
        down = keys[controls.get("baixo", pygame.K_DOWN)] or keys[pygame.K_s]
        dx = float(bool(right)) - float(bool(left))
        dy = float(bool(down)) - float(bool(up))
        magnitude = math.hypot(dx, dy)
        if magnitude:
            dx /= magnitude
            dy /= magnitude
        self.vx = dx * self.SPEED
        self.vy = dy * self.SPEED
        self._apply_void_force()
        self.x += self.vx * dt
        self.y += self.vy * dt
        self._bounce_from_void()
        smoothing = 1.0 - math.exp(-7.5 * dt)
        self.camera_x += (self.x - LARGURA / 2 - self.camera_x) * smoothing
        self.camera_y += (self.y - ALTURA / 2 - self.camera_y) * smoothing
        self.elapsed += dt

    def _bounce_from_void(self) -> None:
        margin = 58.0
        if self.x < margin:
            self.x = margin
            self.vx = abs(self.vx) * 0.18
        elif self.x > self.width - margin:
            self.x = self.width - margin
            self.vx = -abs(self.vx) * 0.18
        if self.y < margin:
            self.y = margin
            self.vy = abs(self.vy) * 0.18
        elif self.y > self.height - margin:
            self.y = self.height - margin
            self.vy = -abs(self.vy) * 0.18

    def _apply_void_force(self) -> None:
        margin = 58.0
        reach = 110.0
        force = 560.0
        if self.x < margin + reach:
            self.vx += force * (1 - max(0.0, self.x - margin) / reach)
        elif self.x > self.width - margin - reach:
            self.vx -= force * (1 - max(0.0, self.width - margin - self.x) / reach)
        if self.y < margin + reach:
            self.vy += force * (1 - max(0.0, self.y - margin) / reach)
        elif self.y > self.height - margin - reach:
            self.vy -= force * (
                1 - max(0.0, self.height - margin - self.y) / reach)

    def save_state(self) -> dict[str, object]:
        """Devolve o ponto de continuação serializável do mundo."""
        return {
            "regiao": self.REGION_ID,
            "posicao": [round(self.x, 2), round(self.y, 2)],
            "checkpoint": "inicio",
            "tempo": round(self.elapsed),
        }

    def render(self, surface: pygame.Surface, player=None) -> None:
        """Desenha fundo cacheável por semente, parallax, limites e nave."""
        surface.fill((5, 8, 26))
        parallax = (0.12, 0.32, 0.68)
        colors = ((55, 69, 112), (110, 138, 205), (200, 220, 255))
        for stars, factor, color in zip(self._stars, parallax, colors):
            for x, y, radius in stars:
                sx = int(x - self.camera_x * factor)
                sy = int(y - self.camera_y * factor)
                if -3 <= sx < LARGURA + 3 and -3 <= sy < ALTURA + 3:
                    pygame.draw.circle(surface, color, (sx, sy), radius)
        self._draw_landmarks(surface)
        self._draw_hostiles(surface)

        world_rect = pygame.Rect(
            round(-self.camera_x), round(-self.camera_y),
            round(self.width), round(self.height),
        )
        if world_rect.colliderect(surface.get_rect()):
            pygame.draw.rect(surface, (108, 37, 116), world_rect, 8)
            inner = world_rect.inflate(-24, -24)
            pygame.draw.rect(surface, (40, 172, 199), inner, 2)
            if world_rect.top <= 48 <= world_rect.bottom:
                label_x = max(8, min(LARGURA - self._edge_label.get_width() - 8,
                                     world_rect.left + 18))
                label_y = max(58, min(ALTURA - self._edge_label.get_height() - 8,
                                      world_rect.top + 48))
                surface.blit(self._edge_label, (label_x, label_y))

        self._draw_speed_lines(surface)
        self._draw_boss_lair(surface)
        self._draw_ship(surface, player)
        self._draw_region_label(surface)

    def _draw_speed_lines(self, surface: pygame.Surface) -> None:
        speed = math.hypot(self.vx, self.vy)
        if speed < 20:
            return
        direction = math.atan2(self.vy, self.vx)
        for index in range(9):
            t = self.elapsed * 0.9 + index / 9
            x = int((index * 113 + t * 173) % LARGURA)
            y = int((index * 79 + t * 131) % ALTURA)
            length = 12 + int(speed / 32)
            start = (x, y)
            end = (x - int(math.cos(direction) * length),
                   y - int(math.sin(direction) * length))
            pygame.draw.line(surface, (46, 84, 125), start, end, 1)

    def _draw_landmarks(self, surface: pygame.Surface) -> None:
        factor = 0.2
        for x, y, radius, color in self._landmarks:
            center = (round(LARGURA / 2 + (x - self.x) * factor),
                      round(ALTURA / 2 + (y - self.y) * factor))
            if not (-radius <= center[0] <= LARGURA + radius
                    and -radius <= center[1] <= ALTURA + radius):
                continue
            pygame.draw.circle(surface, color, center, radius + 8, 2)
            pygame.draw.circle(surface, color, center, radius)
            pygame.draw.ellipse(
                surface, (138, 151, 201),
                (center[0] - radius * 2, center[1] - radius // 3,
                 radius * 4, max(4, radius // 2)), 2,
            )

    def _screen_position(self, position: tuple[float, float]) -> tuple[int, int]:
        return (round(position[0] - self.camera_x),
                round(position[1] - self.camera_y))

    def _draw_hostiles(self, surface: pygame.Surface) -> None:
        for enemy, base_x, base_y, orbit, phase in self.enemies:
            enemy.x = base_x + math.sin(self.elapsed * 0.65 + phase) * orbit
            enemy.y = base_y + math.cos(self.elapsed * 0.48 + phase) * orbit * 0.55
            enemy.x, enemy.y = self._screen_position((enemy.x, enemy.y))
            if -60 <= enemy.x <= LARGURA + 60 and -60 <= enemy.y <= ALTURA + 60:
                enemy.desenhar(surface)

        mini_x = 1090 + math.sin(self.elapsed * 0.42) * 95
        mini_y = 825 + math.cos(self.elapsed * 0.58) * 48
        self.miniboss.x, self.miniboss.y = self._screen_position((mini_x, mini_y))
        if (-100 <= self.miniboss.x <= LARGURA + 100
                and -100 <= self.miniboss.y <= ALTURA + 100):
            self.miniboss.desenhar(surface)
            surface.blit(self._mini_label, (self.miniboss.x - 70,
                                            self.miniboss.y - 60))

    def _draw_boss_lair(self, surface: pygame.Surface) -> None:
        x, y = self._screen_position(self.BOSS_LAIR)
        radius = 92
        pygame.draw.circle(surface, (115, 52, 155), (x, y), radius + 30, 2)
        pygame.draw.circle(surface, (36, 13, 67), (x, y), radius)
        pygame.draw.circle(surface, (230, 160, 255), (x, y), radius, 3)
        for index in range(3):
            angle = self.elapsed * 0.22 + index * math.tau / 3
            point = (round(x + math.cos(angle) * (radius + 14)),
                     round(y + math.sin(angle) * (radius + 14)))
            pygame.draw.circle(surface, (192, 122, 255), point, 5)
        self.boss.x, self.boss.y = x, y
        self.boss.angulo = self.elapsed * 0.18
        if (-150 <= x <= LARGURA + 150 and -150 <= y <= ALTURA + 150):
            self.boss.desenhar(surface)
        surface.blit(self._boss_label, (x - self._boss_label.get_width() // 2,
                                       y + radius + 22))

    def _draw_ship(self, surface: pygame.Surface, player=None) -> None:
        center = (LARGURA // 2, ALTURA // 2)
        if player is not None:
            player.x, player.y = center
            if self.vx or self.vy:
                player.angulo_mira = math.degrees(
                    math.atan2(self.vx, -self.vy)) % 360
            else:
                player.angulo_mira = None
            player.desenhar(surface, intensidade_propulsor=min(
                1.0, 0.35 + math.hypot(self.vx, self.vy) / self.SPEED * 0.65))
            return
        angle = math.atan2(self.vy, self.vx) if self.vx or self.vy else 0.0
        cosine, sine = math.cos(angle), math.sin(angle)
        local = ((19, 0), (-13, -12), (-6, 0), (-13, 12))
        points = [(round(center[0] + x * cosine - y * sine),
                   round(center[1] + x * sine + y * cosine))
                  for x, y in local]
        pygame.draw.polygon(surface, (31, 207, 220), points)
        pygame.draw.polygon(surface, (225, 251, 255), points, 2)

    def _draw_region_label(self, surface: pygame.Surface) -> None:
        surface.blit(self._region_label, (24, 20))
