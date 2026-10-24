"""Estado e representação inicial do mundo aberto contínuo."""

from __future__ import annotations

import math
import random
from collections.abc import Mapping
from typing import Any

import pygame

from src.core.constants import ALTURA, LARGURA
from src.infrastructure.graphics.comic_theme import (
    CIANO,
    LARANJA,
    PAPEL,
    opcoes_atuais,
)
from src.runtime.domain.entities.bosses import Boss
from src.runtime.domain.entities.enemies import Inimigo
from src.runtime.domain.entities.minibosses.registry import criar_miniboss
from src.runtime.domain.entities.powerups import PowerUp
from src.runtime.domain.entities.weapons import Projetil
from src.runtime.domain.world.scenarios import Cenario
from src.runtime.domain.world.scroll import EstadoAvanco
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
                 elapsed: float = 0.0,
                 visual_config: Mapping[str, Any] | None = None) -> None:
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
        try:
            quality = visual_config["avanco_qualidade"] if visual_config else "MEDIA"
        except (KeyError, TypeError):
            quality = "MEDIA"
        self._cenario.configurar_avanco(
            quality, (0.0, 1.0), True, True, visual_config or {}, 4101)
        self.enemies = self._create_enemies()
        self.miniboss = criar_miniboss(
            "censor", 1, self._cenario, random.Random(4101))
        self.miniboss.entrando = False
        self._miniboss_world = (1090.0, 873.0)
        self.boss = Boss(5, self._cenario)
        self.boss.x, self.boss.y = self.BOSS_LAIR
        self.boss.entrando = False
        self.boss.angulo = 0.0
        self.miniboss_active = False
        self.miniboss_defeated = False
        self.boss_active = False
        self.boss_defeated = False
        self.projectiles: list[Projetil] = []
        self.powerups: list[PowerUp] = []
        self._aim_screen: tuple[int, int] | None = None
        self._minimap = pygame.Surface((204, 144), pygame.SRCALPHA)
        self._font_edge = fonte_texto(28)
        self._font_region = fonte_texto(24)
        self._font_marker = fonte_texto(17)
        self._edge_label = self._font_edge.render(
            "VAZIO", True, (210, 170, 245))
        self._region_label = self._font_region.render(
            f"REGIÃO // {self.REGION_NAME}", True, (145, 180, 217))
        self._boss_label = self._font_marker.render(
            "TOCA // HEXAGONO", True, (255, 202, 102))
        self._boss_comic_label = self._font_marker.render(
            "TOCA // HEXAGONO", True, LARANJA)
        self._mini_label = self._font_marker.render(
            "CENSOR // PATRULHA", True, (255, 124, 201))
        self._mini_comic_label = self._font_marker.render(
            "CENSOR // PATRULHA", True, PAPEL)
        self._minimap_label = self._font_marker.render(
            "MAPA // REGIÃO", True, (205, 220, 245))
        self._minimap_comic_label = self._font_marker.render(
            "MAPA // REGIÃO", True, PAPEL)

    @staticmethod
    def _create_enemies() -> list[tuple[Inimigo, float, float, float, float]]:
        """Cria patrulhas fixas usando as mesmas entidades visuais do modo linear."""
        rng = random.Random(4102)
        tipos = ("scout", "soldado", "estelar", "bomba", "abissal",
                 "cristalino", "guardiao", "flamifero")
        patrulhas = []
        for index in range(24):
            setor = index % 6
            base_x = 300 + setor * 440 + rng.uniform(-110, 110)
            base_y = 280 + (index // 6) * 390 + rng.uniform(-100, 100)
            orbit = rng.uniform(28, 76)
            phase = rng.uniform(0, math.tau)
            enemy = Inimigo(tipos[index % len(tipos)], 1,
                            x=base_x, y=base_y)
            enemy.angulo = phase
            patrulhas.append((enemy, base_x, base_y, orbit, phase))
        return patrulhas

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

    def update(self, dt: float, keys: Any, controls: dict[str, int], game=None) -> None:
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
        old_x, old_y = self.x, self.y
        self.vx = dx * self.SPEED
        self.vy = dy * self.SPEED
        self._apply_void_force()
        self.x += self.vx * dt
        self.y += self.vy * dt
        self._bounce_from_void()
        self._update_parallax(dt, self.x - old_x, self.y - old_y)
        smoothing = 1.0 - math.exp(-7.5 * dt)
        self.camera_x += (self.x - LARGURA / 2 - self.camera_x) * smoothing
        self.camera_y += (self.y - ALTURA / 2 - self.camera_y) * smoothing
        self.elapsed += dt
        if game is not None:
            self._update_combat(dt, keys, controls, game)

    def _update_parallax(self, dt: float, dx: float, dy: float) -> None:
        if self._cenario.parallax is None:
            return
        distance = math.hypot(dx, dy)
        self._cenario.parallax.direcao = (-dx, -dy) if distance else (0.0, 1.0)
        speed = distance / dt if dt > 0 else 0.0
        self._cenario.parallax.atualizar(
            speed, speed, dt, EstadoAvanco.AVANCANDO, 0.0, 1.0,
            min(1.0, self.elapsed / 600), "JOGANDO")

    def _update_combat(self, dt: float, keys: Any, controls: dict[str, int],
                       game) -> None:
        if game.menu_equipamento:
            return
        player = game.jogador
        player.x, player.y = LARGURA // 2, ALTURA // 2
        player.cooldown_tiro = max(0, player.cooldown_tiro - 1)
        self._aim_screen = game.posicao_mira()
        player.atualizar_mira(self._aim_screen)
        fire_key = controls.get("atirar", 0)
        mouse_fire = self._aim_screen is not None and pygame.mouse.get_pressed()[0]
        if (keys[pygame.K_SPACE] or keys[pygame.K_z]
                or (fire_key and keys[fire_key]) or mouse_fire):
            aim = self._aim_screen or (LARGURA // 2, ALTURA // 4)
            shots = player.atirar(
                alvo=aim,
                dispersao_duplo_graus=game.config["dispersao_duplo_graus"],
                dispersao_espiral_graus=game.config["dispersao_espiral_graus"],
            )
            for shot in shots:
                shot.x += self.camera_x
                shot.y += self.camera_y
            self.projectiles.extend(shots)
            if shots:
                game.mira.ativar_pulso()
                game.sons.tocar("tiro")

        self._place_hostiles_in_world()
        self._update_linear_encounters(dt, game)

    def _update_linear_encounters(self, dt: float, game) -> None:
        """Usa os mesmos encontros e controladores, projetados na câmera livre."""
        self._activate_encounters(game)
        self._sync_encounter_targets(dt, game)
        if game.boss is not None:
            game.projeteis.extend(self.boss.atualizar(game.jogador))
        for shot in self.projectiles:
            shot.x, shot.y = self._screen_position((shot.x, shot.y))
        game.projeteis.extend(self.projectiles)
        self.projectiles = []
        game.combate_controller.atualizar_projeteis()
        game.combate_controller.atualizar_powerups()
        self._finish_encounter_frame(game)

    def _activate_encounters(self, game) -> None:
        """Arma encounters ao chegar perto de seus pontos no mapa."""
        if (not self.miniboss_defeated and not self.miniboss_active
                and math.hypot(self.x - self.miniboss.x,
                               self.y - self.miniboss.y) < 205):
            self.miniboss_active = True
            game.sons.tocar("boss")
        if (not self.boss_defeated and not self.boss_active
                and math.hypot(self.x - self.BOSS_LAIR[0],
                               self.y - self.BOSS_LAIR[1]) < 320):
            self.boss_active = True
            self.boss.x, self.boss.y = LARGURA // 2, -self.boss.raio - 20
            self.boss.entrando = True
            game.boss_intro = 130
            game.sons.tocar("boss")

    def _sync_encounter_targets(self, dt: float, game) -> None:
        """Projeta alvos e atualiza a IA dos encontros lineares."""
        self._place_hostiles_in_world()
        game.projeteis = []
        game.inimigos = []
        game.powerups = self.powerups
        for powerup in game.powerups:
            powerup.x, powerup.y = self._screen_position((powerup.x, powerup.y))
        for enemy, *_ in self.enemies:
            if enemy.vida <= 0:
                continue
            enemy.x, enemy.y = self._screen_position((enemy.x, enemy.y))
            game.inimigos.append(enemy)

        game.cenario = self._cenario
        game.boss = self.boss if self.boss_active and not self.boss_defeated else None
        game.miniboss = (
            self.miniboss if self.miniboss_active and not self.miniboss_defeated
            else None
        )
        if game.miniboss is not None:
            self.miniboss.x, self.miniboss.y = self._screen_position(
                (self.miniboss.x, self.miniboss.y))
            game.miniboss_controller.atualizar(dt)
            if game.miniboss is None or self.miniboss.vida <= 0:
                self.miniboss_defeated = True

    def _finish_encounter_frame(self, game) -> None:
        """Converte projéteis e alvos de volta para coordenadas do mundo."""
        player = game.jogador
        if self.boss_active and self.boss.vida <= 0:
            self.boss_defeated = True
        if (self.miniboss.vida <= 0
                or (game.miniboss is None and self.miniboss_active)):
            self.miniboss_defeated = True
        if game.miniboss is not None:
            game.miniboss_controller.colidir_jogador()
        for enemy in game.inimigos:
            if enemy.rect.colliderect(player.rect):
                game.combate_controller.aplicar_dano_jogador()
                break
        if game.boss is not None and game.boss.rect.colliderect(player.rect):
            game.combate_controller.aplicar_dano_jogador()

        for shot in game.projeteis:
            shot.x += self.camera_x
            shot.y += self.camera_y
        self.projectiles = game.projeteis
        for powerup in game.powerups:
            powerup.x += self.camera_x
            powerup.y += self.camera_y
        self.powerups = game.powerups
        self.enemies = [entry for entry in self.enemies if entry[0].vida > 0]
        if self.miniboss_active:
            self.miniboss.x += self.camera_x
            self.miniboss.y += self.camera_y
            self._miniboss_world = (self.miniboss.x, self.miniboss.y)
        self._place_hostiles_in_world()
        if not player.vivo:
            game._fim_de_jogo()

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

    def activate_special(self, game) -> bool:
        """Encaminha o especial ao controlador linear e converte o tiro ao mapa."""
        game.projeteis = []
        if not game.combate_controller.ativar_especial():
            return False
        for shot in game.projeteis:
            shot.x += self.camera_x
            shot.y += self.camera_y
        self.projectiles.extend(game.projeteis)
        game.projeteis = self.projectiles
        return True

    def render(self, surface: pygame.Surface, player=None) -> None:
        """Desenha fundo cacheável por semente, parallax, limites e nave."""
        self._cenario.desenhar(surface)
        self._place_hostiles_in_world()
        parallax = (0.12, 0.32, 0.68)
        colors = (
            ((98, 82, 64), (171, 145, 104), PAPEL)
            if opcoes_atuais().ativo
            else ((55, 69, 112), (110, 138, 205), (200, 220, 255))
        )
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
        self._draw_powerups(surface)
        self._draw_projectiles(surface)
        self._draw_ship(surface, player)
        self._draw_region_label(surface)
        self._draw_minimap(surface)

    def _place_hostiles_in_world(self) -> None:
        for enemy, base_x, base_y, orbit, phase in self.enemies:
            enemy.x = base_x + math.sin(self.elapsed * 0.65 + phase) * orbit
            enemy.y = base_y + math.cos(self.elapsed * 0.48 + phase) * orbit * 0.55
        mini_x = 1090 + math.sin(self.elapsed * 0.42) * 95
        mini_y = 825 + math.cos(self.elapsed * 0.58) * 48
        if not self.miniboss_active:
            self.miniboss.x, self.miniboss.y = mini_x, mini_y
            self._miniboss_world = (mini_x, mini_y)
        else:
            self.miniboss.x, self.miniboss.y = self._miniboss_world
        if not self.boss_active:
            self.boss.x, self.boss.y = self.BOSS_LAIR

    def _draw_projectiles(self, surface: pygame.Surface) -> None:
        for shot in self.projectiles:
            world_x, world_y = shot.x, shot.y
            screen_x, screen_y = self._screen_position((world_x, world_y))
            shot.x, shot.y = screen_x, screen_y
            if -50 <= screen_x <= LARGURA + 50 and -50 <= screen_y <= ALTURA + 50:
                shot.desenhar(surface)
            shot.x, shot.y = world_x, world_y

    def _draw_powerups(self, surface: pygame.Surface) -> None:
        for powerup in self.powerups:
            world_x, world_y = powerup.x, powerup.y
            powerup.x, powerup.y = self._screen_position((world_x, world_y))
            if (-40 <= powerup.x <= LARGURA + 40
                    and -40 <= powerup.y <= ALTURA + 40):
                powerup.desenhar(surface)
            powerup.x, powerup.y = world_x, world_y

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
        comic = opcoes_atuais().ativo
        for enemy, base_x, base_y, orbit, phase in self.enemies:
            world_x, world_y = enemy.x, enemy.y
            enemy.x, enemy.y = self._screen_position((enemy.x, enemy.y))
            if (enemy.vida > 0 and -60 <= enemy.x <= LARGURA + 60
                    and -60 <= enemy.y <= ALTURA + 60):
                enemy.desenhar(surface)
            enemy.x, enemy.y = world_x, world_y

        world_mini = self._miniboss_world
        self.miniboss.x, self.miniboss.y = self._screen_position(
            world_mini)
        if (not self.miniboss_defeated
                and -100 <= self.miniboss.x <= LARGURA + 100
                and -100 <= self.miniboss.y <= ALTURA + 100):
            self.miniboss.desenhar(surface)
            label = self._mini_comic_label if comic else self._mini_label
            surface.blit(label, (self.miniboss.x - 70, self.miniboss.y - 60))
        self.miniboss.x, self.miniboss.y = world_mini

    def project_targets_for_ui(self, game) -> None:
        """Mantém mira hover e indicadores alinhados aos alvos na tela."""
        game.inimigos = [enemy for enemy, *_ in self.enemies if enemy.vida > 0]
        for enemy in game.inimigos:
            enemy.x, enemy.y = self._screen_position((enemy.x, enemy.y))
        if game.miniboss is not None:
            game.miniboss.x, game.miniboss.y = self._screen_position(
                self._miniboss_world)

    def _draw_boss_lair(self, surface: pygame.Surface) -> None:
        x, y = self._screen_position(self.BOSS_LAIR)
        radius = 92
        comic = opcoes_atuais().ativo
        glow = (144, 76, 48) if comic else (115, 52, 155)
        core = (38, 30, 27) if comic else (36, 13, 67)
        edge = LARANJA if comic else (230, 160, 255)
        pygame.draw.circle(surface, glow, (x, y), radius + 30, 2)
        pygame.draw.circle(surface, core, (x, y), radius)
        pygame.draw.circle(surface, edge, (x, y), radius, 3)
        for index in range(3):
            angle = self.elapsed * 0.22 + index * math.tau / 3
            point = (round(x + math.cos(angle) * (radius + 14)),
                     round(y + math.sin(angle) * (radius + 14)))
            pygame.draw.circle(surface, edge, point, 5)
        if self.boss_active:
            if not self.boss_defeated:
                self.boss.desenhar(surface)
        elif not self.boss_defeated:
            self.boss.x, self.boss.y = x, y
            self.boss.angulo = self.elapsed * 0.18
            if (-150 <= x <= LARGURA + 150 and -150 <= y <= ALTURA + 150):
                self.boss.desenhar(surface)
        label = self._boss_comic_label if comic else self._boss_label
        surface.blit(label, (x - label.get_width() // 2, y + radius + 22))

    def _draw_ship(self, surface: pygame.Surface, player=None) -> None:
        center = (LARGURA // 2, ALTURA // 2)
        if player is not None:
            player.x, player.y = center
            player.tilt += (self.vx / self.SPEED * 5 - player.tilt) * 0.15
            if self._aim_screen is not None:
                player.atualizar_mira(self._aim_screen)
            elif self.vx or self.vy:
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

    def _draw_minimap(self, surface: pygame.Surface) -> None:
        self._place_hostiles_in_world()
        comic = opcoes_atuais().ativo
        panel = (39, 33, 29, 238) if comic else (4, 9, 24, 218)
        frame = LARANJA if comic else (78, 129, 173)
        grid = (91, 76, 61) if comic else (31, 48, 74)
        player_color = CIANO if comic else (110, 245, 255)
        self._minimap.fill(panel)
        pygame.draw.rect(self._minimap, frame, (0, 0, 204, 144), 2)
        label = self._minimap_comic_label if comic else self._minimap_label
        self._minimap.blit(label, (10, 5))
        area = pygame.Rect(10, 29, 184, 103)
        pygame.draw.rect(self._minimap, (49, 42, 37) if comic else (15, 26, 49), area)
        pygame.draw.rect(self._minimap, frame, area, 1)
        for fraction in (1 / 3, 2 / 3):
            x = area.left + round(area.width * fraction)
            y = area.top + round(area.height * fraction)
            pygame.draw.line(self._minimap, grid,
                             (x, area.top), (x, area.bottom), 1)
            pygame.draw.line(self._minimap, grid,
                             (area.left, y), (area.right, y), 1)

        def point(position: tuple[float, float]) -> tuple[int, int]:
            return (area.left + round(position[0] / self.width * area.width),
                    area.top + round(position[1] / self.height * area.height))

        view = pygame.Rect(
            area.left + round(self.camera_x / self.width * area.width),
            area.top + round(self.camera_y / self.height * area.height),
            max(2, round(LARGURA / self.width * area.width)),
            max(2, round(ALTURA / self.height * area.height)),
        )
        pygame.draw.rect(self._minimap, frame, view.clip(area), 1)
        for enemy, *_ in self.enemies:
            if enemy.vida > 0:
                pygame.draw.circle(self._minimap, enemy.cor,
                                   point((enemy.x, enemy.y)), 2)
        if self.miniboss.vida > 0:
            pygame.draw.circle(self._minimap, (255, 104, 190),
                               point((self.miniboss.x, self.miniboss.y)), 4)
        if self.boss.vida > 0:
            pygame.draw.circle(self._minimap, (255, 210, 100),
                               point(self.BOSS_LAIR), 5)
        pygame.draw.circle(self._minimap, player_color,
                           point((self.x, self.y)), 4)
        surface.blit(self._minimap, (LARGURA - 220, 20))
