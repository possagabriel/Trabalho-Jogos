"""Estado e representação inicial do mundo aberto contínuo."""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Mapping
from typing import Any

import pygame

from src.core.constants import ALTURA, LARGURA
from src.core.event_bus import GameEventType, publicar_evento
from src.infrastructure.graphics.comic_theme import (
    CIANO,
    LARANJA,
    PAPEL,
    TINTA,
    opcoes_atuais,
)
from src.infrastructure.ui.layout import Layout
from src.runtime.domain.entities.bosses import Boss
from src.runtime.domain.entities.enemies import Inimigo
from src.runtime.domain.entities.minibosses.registry import criar_miniboss
from src.runtime.domain.entities.powerups import PowerUp
from src.runtime.domain.entities.weapons import Projetil
from src.runtime.domain.world.anomalies import CosmicAnomalies
from src.runtime.domain.world.asteroid_field import AsteroidField
from src.runtime.domain.world.region_background import SectorBackground
from src.runtime.domain.world.scenarios import CENARIOS, Cenario
from src.runtime.domain.world.scroll import EstadoAvanco
from src.runtime.infrastructure.graphics.fonts import fonte_texto
from src.runtime.infrastructure.graphics.meteor_shower import (
    desenhar_meteoro,
    gerar_chuva,
    janela_chuva,
)
from src.runtime.infrastructure.graphics.smooth import (
    desenhar_circulo,
    desenhar_painel,
    texto_suave,
)


class OpenWorldRuntime:
    """Movimento livre, câmera suave, fundo em parallax e borda do Vazio."""

    REGION_ID = "espaco_profundo"
    REGION_NAME = "ESPAÇO PROFUNDO"
    REGION_IDS = (
        "espaco_profundo", "nebulosa_em_chamas", "oceano_cosmico",
        "ruinas_cristalinas", "espaco_nulo", "nucleo_dourado",
    )
    REGION_SIZE = (19200.0, 13200.0)
    SPAWN = (2160.0, 6600.0)
    SPEED = 360.0
    MAX_GRAVITY_SPEED = 170.0
    BOSS_LAIR = (17100.0, 6600.0)
    MINIMAP_SIZE = (260, 180)
    SECTORS = (
        ("ESTRELA", (3300.0, 3300.0), (105, 72, 127)),
        ("PENTAGONO", (9600.0, 3300.0), (65, 115, 154)),
        ("ANEIS", (15900.0, 3300.0), (125, 91, 66)),
        ("CRISTAL", (3300.0, 9900.0), (72, 133, 150)),
        ("ABISMO", (9600.0, 9900.0), (90, 76, 140)),
        ("NÚCLEO", (15900.0, 9900.0), (131, 75, 112)),
    )

    def __init__(self, position: tuple[float, float] | None = None,
                 elapsed: float = 0.0,
                 visual_config: Mapping[str, Any] | None = None,
                 dimension: int = 1, bosses: int = 0,
                 cooldowns: Mapping[str, object] | None = None,
                 rng: random.Random | None = None) -> None:
        self.dimension = max(1, min(6, int(dimension)))
        self.REGION_ID = self.REGION_IDS[self.dimension - 1]
        self.REGION_NAME = CENARIOS[self.dimension - 1]["nome"]
        self.visual_config = visual_config or {}
        self.width, self.height = self.REGION_SIZE
        self._rng = rng if rng is not None else random.Random()
        self.anomalies = CosmicAnomalies(self.dimension)
        self.asteroids = AsteroidField(
            self.width, self.height, seed=4101 + self.dimension,
            protected=self._protected_zones(),
        )
        self.enemies = self._create_enemies()
        self.SPAWN = self._choose_spawn(position)
        self.x, self.y = position or self.SPAWN
        self.x = max(0.0, min(self.width, float(self.x)))
        self.y = max(0.0, min(self.height, float(self.y)))
        self.vx = 0.0
        self.vy = 0.0
        self.gravity_vx = 0.0
        self.gravity_vy = 0.0
        self.wormhole_cooldown = 0.0
        self.turbo_ativo = False
        self.camera_x = self.x - LARGURA / 2
        self.camera_y = self.y - ALTURA / 2
        self.elapsed = max(0.0, float(elapsed))
        self.map_open = False
        self.progress_dirty = False
        self.bosses_defeated = max(0, min(6, int(bosses)))
        self.regions_liberated = self.bosses_defeated
        self._pending_dimension: int | None = None
        self._stars = self._build_stars()
        self._rifts = self._build_rifts()
        self._chave_chuva: tuple[int, int, int] | None = None
        self._meteoros = ()
        if cooldowns:
            self.asteroids.restore(cooldowns, self.elapsed)
        self.background = SectorBackground(
            self.dimension, self.SECTORS, (self.x, self.y))
        self._cenario = Cenario(self.dimension)
        try:
            quality = visual_config["avanco_qualidade"] if visual_config else "MEDIA"
        except (KeyError, TypeError):
            quality = "MEDIA"
        self._cenario.configurar_avanco(
            quality, (0.0, 1.0), True, True, self.visual_config,
            4101 + self.dimension)
        self.miniboss = criar_miniboss(
            "censor", self.dimension, self._cenario,
            random.Random(4101 + self.dimension))
        self.miniboss.entrando = False
        self._miniboss_world = (6300.0, 3300.0)
        self.boss = Boss(self.dimension * 5, self._cenario)
        self.boss.x, self.boss.y = self.BOSS_LAIR
        self.boss.entrando = False
        self.boss.angulo = 0.0
        self._boss_world = self.BOSS_LAIR
        self._destino_id = "boss"
        self._boss_orbit = 0.0
        self._boss_attack_timer = 1.6
        self.miniboss_active = False
        self.miniboss_defeated = False
        self.boss_active = False
        self.boss_defeated = False
        self.projectiles: list[Projetil] = []
        self.powerups: list[PowerUp] = []
        self._aim_screen: tuple[int, int] | None = None
        self._minimap = pygame.Surface(self.MINIMAP_SIZE, pygame.SRCALPHA)
        self._font_edge = fonte_texto(28)
        self._font_region = fonte_texto(24)
        self._font_marker = fonte_texto(17)
        self._edge_label = self._font_edge.render(
            "VAZIO", True, (210, 170, 245))
        self._region_label = self._font_region.render(
            f"REGIÃO // {self.REGION_NAME}", True, (145, 180, 217))
        self._boss_label = self._font_marker.render(
            f"TOCA // {self.boss.nome}", True, (255, 202, 102))
        self._boss_comic_label = self._font_marker.render(
            f"TOCA // {self.boss.nome}", True, LARANJA)
        self._mini_label = self._font_marker.render(
            "CENSOR // PATRULHA", True, (255, 124, 201))
        self._mini_comic_label = self._font_marker.render(
            "CENSOR // PATRULHA", True, PAPEL)
        self._minimap_label = self._font_marker.render(
            "MINIMAPA", True, (205, 220, 245))
        self._minimap_comic_label = self._font_marker.render(
            "MINIMAPA", True, PAPEL)
        self._minimap_hint = self._font_marker.render(
            "M: MAPA", True, (170, 202, 225))
        self._minimap_comic_hint = self._font_marker.render(
            "M: MAPA", True, PAPEL)
        self._map_title = self._font_region.render(
            f"MAPA // {self.REGION_NAME} // DIMENSÃO {self.dimension}",
            True, (225, 236, 250))
        self._map_hint = self._font_marker.render(
            "ESQ / DIR: DESTINO    ENTER / M / ESC: VOLTAR", True, PAPEL)
        self._map_legend = tuple(
            self._font_marker.render(label, True, (225, 235, 246))
            for label in ("NAVE", "TOCA", "PATRULHA", "FENDA", "POÇO", "PORTAL")
        )
        self._sector_labels = tuple(
            (name, self._font_marker.render(name, True, color))
            for name, _center, color in self.SECTORS
        )

    def destinos_navegacao(self) -> tuple[tuple[str, str, tuple[float, float]], ...]:
        """Lista pontos existentes; encontros concluídos deixam de ser destinos."""
        destinos = []
        if not self.boss_defeated:
            destinos.append(("boss", f"TOCA // {self.boss.nome}", self.BOSS_LAIR))
        if not self.miniboss_defeated:
            destinos.append(("patrulha", "PATRULHA // CENSOR", self._miniboss_world))
        destinos.extend((f"setor_{i}", f"SETOR // {nome}", centro)
                        for i, (nome, centro, _cor) in enumerate(self.SECTORS))
        destinos.extend((f"portal_{i}", f"PORTAL {i + 1} > {portal.target + 1}",
                         portal.position)
                        for i, portal in enumerate(self.anomalies.wormholes))
        return tuple(destinos)

    def destino_atual(self) -> tuple[str, str, tuple[float, float]]:
        """Resolve o destino por identidade, mesmo após a conclusão de encontros."""
        destinos = self.destinos_navegacao()
        return next((item for item in destinos if item[0] == self._destino_id), destinos[0])

    def alternar_destino(self, passo: int) -> None:
        """Seleciona circularmente um ponto do mapa, sem mover a nave."""
        destinos = self.destinos_navegacao()
        indice = destinos.index(self.destino_atual())
        self._destino_id = destinos[(indice + passo) % len(destinos)][0]

    def texto_navegacao(self) -> str:
        """Informa destino e distância direta em unidades do mundo."""
        _ident, nome, posicao = self.destino_atual()
        distancia = math.dist((self.x, self.y), posicao)
        estado = "NO DESTINO" if distancia <= 120 else f"{round(distancia / 10) * 10} u"
        return f"{nome} | {estado}"

    def _draw_navigation(self, surface: pygame.Surface, mapa: bool = False) -> None:
        """Exibe orientação estática com fundo opaco e texto cacheado."""
        layout = Layout(*surface.get_size())
        texto = texto_suave(self._font_marker, self.texto_navegacao(), PAPEL)
        margem = layout.margem(8)
        largura = texto.get_width() + margem * 2
        x = layout.x(0.035) if mapa else layout.largura - largura - layout.margem()
        y = layout.y(0.07) if mapa else 20 + self.MINIMAP_SIZE[1] + margem
        painel = pygame.Rect(x, y, largura, texto.get_height() + margem)
        desenhar_painel(surface, PAPEL, painel, cor_fundo=TINTA,
                        alpha=255, glow_raio=0, raio_canto=0)
        surface.blit(texto, (x + margem, y + margem // 2))

    def _choose_spawn(self, position: tuple[float, float] | None = None
                      ) -> tuple[float, float]:
        """Escolhe uma área segura; posição salva tem prioridade na retomada."""
        if position is not None:
            return float(position[0]), float(position[1])
        for _ in range(64):
            center = self.SECTORS[self._rng.randrange(len(self.SECTORS))][1]
            candidate = (center[0] + self._rng.uniform(-1050, 1050),
                         center[1] + self._rng.uniform(-820, 820))
            if math.dist(candidate, self.BOSS_LAIR) < 900:
                continue
            if any(math.dist(candidate, hole.position) < hole.influence + 100
                   for hole in self.anomalies.black_holes):
                continue
            if any(math.dist(candidate, portal.position) < 300
                   for portal in self.anomalies.wormholes):
                continue
            if any(math.dist(candidate, (rock.x, rock.y)) <= rock.radius + 80
                   for rock in self.asteroids.nearby(*candidate, 120)):
                continue
            if any(math.dist(candidate, (x, y)) <= orbit + 300
                   for _enemy, x, y, orbit, _phase in self.enemies):
                continue
            return candidate
        return self.__class__.SPAWN

    def _protected_zones(self) -> tuple[tuple[float, float, float], ...]:
        """Reserva áreas fixas para manter IDs dos asteroides estáveis no save."""
        return (
            (*self.__class__.SPAWN, 440.0), (*self.BOSS_LAIR, 410.0),
            *((*hole.position, hole.influence) for hole in self.anomalies.black_holes),
            *((*portal.position, 320.0) for portal in self.anomalies.wormholes),
        )

    def _create_enemies(self) -> list[tuple[Inimigo, float, float, float, float]]:
        """Espalha patrulhas determinísticas por todas as áreas do mapa."""
        rng = random.Random(4102 + self.dimension)
        tipos = tuple(CENARIOS[self.dimension - 1]["inimigos"])
        patrulhas = []
        safe_positions = (
            (*self.__class__.SPAWN, 390.0), (*self.BOSS_LAIR, 420.0),
            *((*portal.position, 320.0) for portal in self.anomalies.wormholes),
            *((*hole.position, 300.0) for hole in self.anomalies.black_holes),
        )
        for row in range(12):
            for column in range(18):
                index = row * 18 + column
                base_x = (column + rng.uniform(0.22, 0.78)) * (
                    self.width / 18)
                base_y = (row + rng.uniform(0.22, 0.78)) * (
                    self.height / 12)
                if any(math.hypot(base_x - px, base_y - py) < safe
                       for px, py, safe in safe_positions):
                    continue
                orbit = rng.uniform(28, 76)
                phase = rng.uniform(0, math.tau)
                enemy = Inimigo(tipos[index % len(tipos)], 1,
                                x=base_x, y=base_y)
                enemy.angulo = phase
                patrulhas.append((enemy, base_x, base_y, orbit, phase))
        return patrulhas

    def _build_stars(self) -> tuple[tuple[tuple[float, float, int], ...], ...]:
        rng = random.Random(4101 + self.dimension)
        layers = []
        for count, low, high in ((320, 1, 1), (190, 1, 2), (75, 2, 3)):
            layers.append(tuple(
                (rng.uniform(-1200, self.width + 1200),
                 rng.uniform(-900, self.height + 900),
                 rng.randint(low, high))
                for _ in range(count)
            ))
        return tuple(layers)

    @staticmethod
    def _build_rifts() -> tuple[tuple[float, float, int], ...]:
        """Cria fendas fixas que marcam as passagens entre os setores."""
        return (
            (6450.0, 3300.0, 54), (12750.0, 3300.0, 68),
            (6450.0, 9900.0, 62), (12750.0, 9900.0, 50),
            (3300.0, 6600.0, 66), (9600.0, 6600.0, 58),
            (15900.0, 6600.0, 72),
        )

    def update(self, dt: float, keys: Any, controls: dict[str, int], game=None) -> None:
        """Move a nave, suaviza a câmera e rebate no limite do mundo."""
        if self.map_open:
            return
        dt = max(0.0, min(float(dt), 0.05))
        if game is not None and hasattr(game, "jogador"):
            self._tick_player(game.jogador)
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
        pressed = (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
                   or keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL])
        charge = getattr(game, "boost", 1.0)
        self.turbo_ativo = bool(pressed and charge > 0 and magnitude)
        if game is not None and hasattr(game, "boost"):
            if self.turbo_ativo:
                game.boost = max(0.0, game.boost - 0.008 * dt * 60)
            else:
                game.boost = min(1.0, game.boost + 0.006 * dt * 60)
            if hasattr(game, "energia"):
                game.energia = (max(0.0, game.energia - 1.6 * dt * 60)
                                if self.turbo_ativo else
                                min(100.0, game.energia + 0.7 * dt * 60))
        speed = self.SPEED * (2.1 if self.turbo_ativo else 1.0)
        self._update_gravity(dt)
        self.vx = dx * speed + self.gravity_vx
        self.vy = dy * speed + self.gravity_vy
        self._apply_void_force()
        self.x += self.vx * dt
        self.y += self.vy * dt
        self._bounce_from_void()
        self._try_wormhole(dt)
        self._collide_ship_with_asteroids(game)
        self.background.update(self.x, self.y, dt)
        smoothing = 1.0 - math.exp(-7.5 * dt)
        self.camera_x += (self.x - LARGURA / 2 - self.camera_x) * smoothing
        self.camera_y += (self.y - ALTURA / 2 - self.camera_y) * smoothing
        self.elapsed += dt
        self.asteroids.update(self.elapsed)
        if game is not None:
            self._update_combat(dt, keys, controls, game)

    def _update_gravity(self, dt: float) -> None:
        """Integra a atração com amortecimento e velocidade limitada."""
        ax, ay = self.anomalies.gravity(self.x, self.y)
        damping = math.exp(-0.55 * dt)
        self.gravity_vx = (self.gravity_vx + ax * dt) * damping
        self.gravity_vy = (self.gravity_vy + ay * dt) * damping
        magnitude = math.hypot(self.gravity_vx, self.gravity_vy)
        if magnitude > self.MAX_GRAVITY_SPEED:
            scale = self.MAX_GRAVITY_SPEED / magnitude
            self.gravity_vx *= scale
            self.gravity_vy *= scale

    def _try_wormhole(self, dt: float) -> None:
        """Teleporta uma vez e reposiciona a câmera sem travessia visual longa."""
        self.wormhole_cooldown = max(0.0, self.wormhole_cooldown - dt)
        destination = self.anomalies.destination(
            self.x, self.y, self.wormhole_cooldown)
        if destination is None:
            return
        self.x, self.y = destination
        self.vx = self.vy = 0.0
        self.gravity_vx = self.gravity_vy = 0.0
        self.camera_x = self.x - LARGURA / 2
        self.camera_y = self.y - ALTURA / 2
        self.background.transition_to(self.x, self.y)
        self.wormhole_cooldown = 1.5
        self.progress_dirty = True

    @staticmethod
    def _tick_player(player) -> None:
        """Avança timers do jogador sem mover a nave no canvas lógico."""
        if player.invencivel > 0:
            player.invencivel -= 1
        if player.tempo_intangivel > 0:
            player.tempo_intangivel -= 1
        if player.cooldown_esquiva > 0:
            player.cooldown_esquiva -= 1
        player.combo.atualizar()

    def _collide_ship_with_asteroids(self, game) -> None:
        """Impede passagem pelo casco dos asteroides e aplica dano existente."""
        if getattr(getattr(game, "jogador", None), "tempo_intangivel", 0) > 0:
            return
        radius = getattr(getattr(game, "jogador", None), "raio", 16)
        for rock in self.asteroids.nearby(self.x, self.y, radius):
            if not rock.active():
                continue
            dx, dy = self.x - rock.x, self.y - rock.y
            distance = math.hypot(dx, dy)
            penetration = rock.radius + radius - distance
            if penetration <= 0:
                continue
            norm = distance or 1.0
            self.x += (dx / norm if distance else 1.0) * penetration
            self.y += dy / norm * penetration
            if game is not None and hasattr(game, "combate_controller"):
                game.combate_controller.aplicar_dano_jogador()
            break

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
        self._update_world_encounters(dt, game)

    def _update_world_encounters(self, dt: float, game) -> None:
        """Mantém combate compartilhado com uma IA própria para o boss."""
        self._activate_encounters(game)
        if getattr(getattr(game, "cutscene_controller", None), "ativo", False):
            return
        self._sync_encounter_targets(dt, game)
        if game.boss is not None:
            game.projeteis.extend(self._update_world_boss(dt))
        for shot in self.projectiles:
            shot.x, shot.y = self._screen_position((shot.x, shot.y))
        game.projeteis.extend(self.projectiles)
        self.projectiles = []
        self._resolve_asteroid_hits(game)
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
            self._boss_world = self.BOSS_LAIR
            self.boss.entrando = False
            game.boss_intro = 130
            game.sons.tocar("boss")
            publicar_evento(
                GameEventType.BOSS_SPAWNED, sessao=game,
                boss=self.boss, cenario_id=self.dimension,
                nivel=self.boss.nivel,
            )

    def _update_world_boss(self, dt: float) -> list[Projetil]:
        """Orbita a toca em duas dimensões e mira a nave em salvas móveis."""
        boss = self.boss
        boss.t += 1
        boss.flash = max(0, boss.flash - 1)
        boss.pulso_fase = max(0, boss.pulso_fase - 1)
        phase = boss.fase_atual
        if phase != boss.fase_anterior:
            boss.fase_anterior = phase
            boss.pulso_fase = 75
        boss.enraivecido = phase == 3
        direction = -1 if self.dimension % 2 else 1
        self._boss_orbit += dt * direction * (0.72 + phase * 0.16)
        radius = 125 + 24 * phase + 9 * self.dimension
        target_x = self.BOSS_LAIR[0] + math.cos(self._boss_orbit) * radius
        target_y = self.BOSS_LAIR[1] + math.sin(self._boss_orbit * 1.3) * radius
        follow = min(1.0, dt * (2.6 + phase * 0.6))
        self._boss_world = (
            self._boss_world[0] + (target_x - self._boss_world[0]) * follow,
            self._boss_world[1] + (target_y - self._boss_world[1]) * follow,
        )
        boss.x, boss.y = self._screen_position(self._boss_world)
        boss.angulo += dt * (0.9 + phase * 0.35)
        self._boss_attack_timer -= dt
        if self._boss_attack_timer > 0:
            return []
        self._boss_attack_timer = max(0.52, 1.8 - phase * 0.28
                                      - self.dimension * 0.06)
        player_x, player_y = LARGURA / 2, ALTURA / 2
        direction = math.atan2(player_y - boss.y, player_x - boss.x)
        count = 1 + phase * 2
        speed = 3.2 + phase * 0.55
        shots = [
            Projetil(boss.x, boss.y,
                     math.cos(direction + (index - count // 2) * 0.18) * speed,
                     math.sin(direction + (index - count // 2) * 0.18) * speed,
                     1, boss.cor, 5, origem="inimigo")
            for index in range(count)
        ]
        if phase == 3 or self.dimension in (2, 4, 6):
            shots.extend(
                Projetil(boss.x, boss.y, math.cos(angle) * 2.8,
                         math.sin(angle) * 2.8, 1, boss.cor, 4,
                         origem="inimigo")
                for angle in (index * math.tau / 8 for index in range(8))
            )
        return shots

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
            if (abs(enemy.x - self.x) > LARGURA / 2 + 150
                    or abs(enemy.y - self.y) > ALTURA / 2 + 150):
                continue
            enemy.x, enemy.y = self._screen_position((enemy.x, enemy.y))
            game.inimigos.append(enemy)

        game.cenario = self._cenario
        game.boss = self.boss if self.boss_active and not self.boss_defeated else None
        if game.boss is not None:
            self.boss.x, self.boss.y = self._screen_position(self._boss_world)
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
        if self.boss_active and self.boss.vida <= 0 and not self.boss_defeated:
            self.boss_defeated = True
            self.boss_active = False
            self.bosses_defeated = min(6, self.bosses_defeated + 1)
            self.regions_liberated = self.bosses_defeated
            self._pending_dimension = (
                self.dimension + 1 if self.dimension < 6 else None)
            self.progress_dirty = True
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

    @staticmethod
    def _segment_distance(x: float, y: float, x1: float, y1: float,
                          x2: float, y2: float) -> float:
        """Distância de um obstáculo ao trajeto de um projétil no quadro."""
        dx, dy = x2 - x1, y2 - y1
        length_sq = dx * dx + dy * dy
        if length_sq == 0:
            return math.hypot(x - x1, y - y1)
        fraction = max(0.0, min(1.0,
                                ((x - x1) * dx + (y - y1) * dy) / length_sq))
        return math.hypot(x - (x1 + fraction * dx),
                          y - (y1 + fraction * dy))

    def _resolve_asteroid_hits(self, game) -> None:
        """Bloqueia tiros comuns e destrói asteroides no espaço do mundo."""
        remaining = []
        for shot in game.projeteis:
            if shot.origem != "jogador":
                remaining.append(shot)
                continue
            x1, y1 = shot.x + self.camera_x, shot.y + self.camera_y
            if shot.tipo == "ion":
                ponta_x, ponta_y = shot.ponta_ion()
                x2, y2 = ponta_x + self.camera_x, ponta_y + self.camera_y
            else:
                x2, y2 = x1 + shot.vel_x, y1 + shot.vel_y
            penetrating = shot.tipo in ("ion", "gauss", "nova", "bomba")
            blocked = False
            for rock in self.asteroids.nearby(
                    (x1 + x2) / 2, (y1 + y2) / 2,
                    math.hypot(x2 - x1, y2 - y1) / 2 + shot.raio):
                if not rock.active() or id(rock) in shot.alvos_atingidos:
                    continue
                if self._segment_distance(rock.x, rock.y, x1, y1, x2, y2) > (
                        rock.radius + shot.raio):
                    continue
                if self.asteroids.damage(rock, max(1, shot.dano), self.elapsed):
                    game.sons.tocar("explosao")
                    self.progress_dirty = True
                shot.alvos_atingidos.add(id(rock))
                if not penetrating:
                    blocked = True
                    break
            if not blocked:
                remaining.append(shot)
        game.projeteis = remaining

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
            "map_version": 2,
            "dimensao": self.dimension,
            "bosses": self.bosses_defeated,
            "regioes_libertas": self.regions_liberated,
            "proxima_dimensao": self._pending_dimension or 0,
            "boss_derrotado": self.boss_defeated,
            "asteroides": self.asteroids.cooldowns(),
        }

    def advance_dimension(self, game=None) -> bool:
        """Troca a região após a cena de derrota e emite a próxima abertura."""
        next_dimension = self._pending_dimension
        if next_dimension is None:
            return False
        self._pending_dimension = None
        self.dimension = next_dimension
        self.REGION_ID = self.REGION_IDS[next_dimension - 1]
        self.REGION_NAME = CENARIOS[next_dimension - 1]["nome"]
        self.anomalies = CosmicAnomalies(next_dimension)
        self.asteroids = AsteroidField(
            self.width, self.height, seed=4101 + next_dimension,
            protected=self._protected_zones(),
        )
        self.enemies = self._create_enemies()
        self.SPAWN = self._choose_spawn()
        self.x, self.y = self.SPAWN
        self.vx = self.vy = 0.0
        self.gravity_vx = self.gravity_vy = 0.0
        self.wormhole_cooldown = 0.0
        self.camera_x = self.x - LARGURA / 2
        self.camera_y = self.y - ALTURA / 2
        self._stars = self._build_stars()
        self._chave_chuva = None
        self._meteoros = ()
        self.background = SectorBackground(
            next_dimension, self.SECTORS, (self.x, self.y))
        self._cenario = Cenario(next_dimension)
        try:
            quality = self.visual_config["avanco_qualidade"]
        except (KeyError, TypeError):
            quality = "MEDIA"
        self._cenario.configurar_avanco(
            quality, (0.0, 1.0), True, True, self.visual_config,
            4101 + next_dimension)
        self.miniboss = criar_miniboss(
            "censor", next_dimension, self._cenario,
            random.Random(4101 + next_dimension))
        self.miniboss.entrando = False
        self._miniboss_world = (6300.0, 3300.0)
        self.miniboss_active = self.miniboss_defeated = False
        self.boss = Boss(next_dimension * 5, self._cenario)
        self.boss.entrando = False
        self.boss_active = self.boss_defeated = False
        self._boss_world = self.BOSS_LAIR
        self._destino_id = "boss"
        self._boss_orbit = 0.0
        self._boss_attack_timer = 1.6
        self.projectiles.clear()
        self.powerups.clear()
        self._region_label = self._font_region.render(
            f"REGIÃO // {self.REGION_NAME}", True, (145, 180, 217))
        self._boss_label = self._font_marker.render(
            f"TOCA // {self.boss.nome}", True, (255, 202, 102))
        self._boss_comic_label = self._font_marker.render(
            f"TOCA // {self.boss.nome}", True, LARANJA)
        self._map_title = self._font_region.render(
            f"MAPA // {self.REGION_NAME} // DIMENSÃO {self.dimension}",
            True, (225, 236, 250))
        self.progress_dirty = True
        if game is not None:
            game.cenario = self._cenario
            game.boss = None
            game.miniboss = None
            game.projeteis = []
            game.inimigos = []
            game.powerups = []
            game.miniboss_controller.reiniciar()
            publicar_evento(
                GameEventType.DIMENSION_CHANGED,
                sessao=game, cenario_id=next_dimension,
            )
        return True

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
        self.background.render(surface, opcoes_atuais().ativo)
        self._place_hostiles_in_world()
        parallax = (0.12, 0.32, 0.68)
        colors = (
            ((98, 82, 64), (171, 145, 104), PAPEL)
            if opcoes_atuais().ativo
            else ((55, 69, 112), (110, 138, 205), (200, 220, 255))
        )
        for stars, factor, color in zip(self._stars, parallax, colors):
            for x, y, radius in stars:
                sx = round(LARGURA / 2 + (x - self.x) * factor)
                sy = round(ALTURA / 2 + (y - self.y) * factor)
                if -3 <= sx < LARGURA + 3 and -3 <= sy < ALTURA + 3:
                    pygame.draw.circle(surface, color, (sx, sy), radius)
        self._draw_meteor_shower(surface)
        self._draw_sectors(surface)
        self.anomalies.render(surface, self.camera_x, self.camera_y,
                              opcoes_atuais().ativo)
        self._draw_asteroids(surface)
        self._draw_hostiles(surface)
        self._draw_void_border(surface)
        self._draw_speed_lines(surface)
        self._draw_boss_lair(surface)
        self._draw_objective_marker(surface)
        self._draw_powerups(surface)
        self._draw_projectiles(surface)
        self._draw_ship(surface, player)
        self._draw_region_label(surface)
        self._draw_minimap(surface)
        self._draw_navigation(surface)

    def _draw_asteroids(self, surface: pygame.Surface) -> None:
        """Desenha apenas rochas dos chunks que tocam a câmera."""
        comic = opcoes_atuais().ativo
        fill = (71, 59, 53) if comic else (58, 72, 91)
        edge = PAPEL if comic else (153, 191, 213)
        for rock in self.asteroids.visible(self.camera_x, self.camera_y,
                                           LARGURA, ALTURA):
            if not rock.active():
                continue
            sx, sy = self._screen_position((rock.x, rock.y))
            if not (-45 <= sx <= LARGURA + 45 and -45 <= sy <= ALTURA + 45):
                continue
            points = tuple((sx + dx, sy + dy) for dx, dy in rock.shape)
            pygame.draw.polygon(surface, fill, points)
            pygame.draw.polygon(surface, edge, points, 2)
            pygame.draw.circle(surface, edge, (sx - rock.radius // 4, sy),
                               max(2, rock.radius // 5), 1)

    def _draw_meteor_shower(self, surface: pygame.Surface) -> None:
        """Desenha grupos curtos no plano de fundo, sem colisão ou flashes."""
        janela = janela_chuva(self.elapsed)
        if janela is None:
            return
        ciclo, fase = janela
        try:
            qualidade = self.visual_config["qualidade_grafica"]
            efeitos = self.visual_config["intensidade_flash"]
        except (KeyError, TypeError):
            qualidade, efeitos = "ALTA", "NORMAL"
        reduzido = qualidade == "DESEMPENHO" or efeitos != "NORMAL"
        quantidade = 2 if reduzido else 4
        chave = (self.dimension, ciclo, quantidade)
        if chave != self._chave_chuva:
            self._meteoros = gerar_chuva(
                9101 + self.dimension * 1009 + ciclo, LARGURA, ALTURA,
                quantidade)
            self._chave_chuva = chave
        for meteoro in self._meteoros:
            desenhar_meteoro(surface, meteoro, fase - meteoro.atraso,
                             reduzido=reduzido)

    def _draw_void_border(self, surface: pygame.Surface) -> None:
        """Mantém o Vazio na borda visível da tela perto do limite externo."""
        near = (
            self.x < LARGURA / 2 + 110,
            self.x > self.width - LARGURA / 2 - 110,
            self.y < ALTURA / 2 + 110,
            self.y > self.height - ALTURA / 2 - 110,
        )
        if not any(near):
            return
        primary = LARANJA if opcoes_atuais().ativo else (170, 73, 183)
        secondary = PAPEL if opcoes_atuais().ativo else (72, 190, 218)
        if near[0]:
            pygame.draw.line(surface, primary, (0, 0), (0, ALTURA), 8)
            pygame.draw.line(surface, secondary, (14, 0), (14, ALTURA), 2)
        if near[1]:
            pygame.draw.line(surface, primary, (LARGURA - 1, 0),
                             (LARGURA - 1, ALTURA), 8)
            pygame.draw.line(surface, secondary, (LARGURA - 15, 0),
                             (LARGURA - 15, ALTURA), 2)
        if near[2]:
            pygame.draw.line(surface, primary, (0, 0), (LARGURA, 0), 8)
            pygame.draw.line(surface, secondary, (0, 14), (LARGURA, 14), 2)
        if near[3]:
            pygame.draw.line(surface, primary, (0, ALTURA - 1),
                             (LARGURA, ALTURA - 1), 8)
            pygame.draw.line(surface, secondary, (0, ALTURA - 15),
                             (LARGURA, ALTURA - 15), 2)
        surface.blit(self._edge_label, (24, ALTURA - 48))

    def render_map(self, surface: pygame.Surface) -> None:
        """Mostra todo o mundo no canvas lógico, ocupando a tela inteira."""
        comic = opcoes_atuais().ativo
        surface.fill((36, 33, 33) if comic else (5, 12, 29))
        area = pygame.Rect(42, 68, LARGURA - 84, ALTURA - 120)
        fill = (55, 51, 48) if comic else (13, 27, 49)
        edge = LARANJA if comic else (105, 203, 234)
        pygame.draw.rect(surface, fill, area)
        pygame.draw.rect(surface, edge, area, 3)
        surface.blit(self._map_title, (42, 20))
        surface.blit(self._map_hint,
                     (LARGURA - self._map_hint.get_width() - 42, ALTURA - 37))
        grid = (80, 73, 68) if comic else (31, 53, 76)
        for column in range(1, 6):
            x = area.left + round(area.width * column / 6)
            pygame.draw.line(surface, grid, (x, area.top), (x, area.bottom), 1)
        for row in range(1, 4):
            y = area.top + round(area.height * row / 4)
            pygame.draw.line(surface, grid, (area.left, y), (area.right, y), 1)

        def point(world_x: float, world_y: float) -> tuple[int, int]:
            return (area.left + round(world_x / self.width * area.width),
                    area.top + round(world_y / self.height * area.height))

        for (_name, center, color), (_label_name, label) in zip(
                self.SECTORS, self._sector_labels):
            x, y = point(*center)
            pygame.draw.circle(surface, PAPEL if comic else color,
                               (x, y), 16, 2)
            pygame.draw.circle(surface, edge, (x, y), 3)
            surface.blit(label, (x + 19, y - label.get_height() // 2))
        for world_x, world_y, _radius in self._rifts:
            x, y = point(world_x, world_y)
            pygame.draw.rect(surface, edge, (x - 4, y - 7, 8, 14), 2)
        for hole in self.anomalies.black_holes:
            x, y = point(*hole.position)
            pygame.draw.circle(surface, (230, 160, 104), (x, y), 7, 2)
            pygame.draw.circle(surface, (8, 11, 24), (x, y), 4)
        for portal in self.anomalies.wormholes:
            x, y = point(*portal.position)
            pygame.draw.ellipse(surface, (118, 216, 231),
                                (x - 5, y - 9, 10, 18), 2)
        rock_color = (153, 139, 120) if comic else (102, 138, 158)
        for rock in self.asteroids.asteroids:
            if rock.active():
                pygame.draw.circle(surface, rock_color, point(rock.x, rock.y), 1)
        if not self.boss_defeated:
            bx, by = point(*self.BOSS_LAIR)
            pygame.draw.polygon(surface, (255, 207, 115),
                                ((bx, by - 9), (bx + 9, by),
                                 (bx, by + 9), (bx - 9, by)), 2)
            surface.blit(self._boss_label,
                         (min(bx + 14, area.right - self._boss_label.get_width() - 5),
                          by - self._boss_label.get_height() // 2))
        if not self.miniboss_defeated:
            mx, my = point(*self._miniboss_world)
            pygame.draw.polygon(surface, (255, 156, 203),
                                ((mx, my - 7), (mx + 7, my),
                                 (mx, my + 7), (mx - 7, my)), 2)
        camera = pygame.Rect(
            *point(self.camera_x, self.camera_y),
            max(2, round(LARGURA / self.width * area.width)),
            max(2, round(ALTURA / self.height * area.height)),
        )
        pygame.draw.rect(surface, (230, 238, 245), camera.clip(area), 2)
        px, py = point(self.x, self.y)
        pygame.draw.polygon(surface, CIANO,
                            ((px, py - 11), (px - 8, py + 8),
                             (px + 8, py + 8)))
        pygame.draw.polygon(surface, PAPEL, ((px, py - 11),
                                             (px - 8, py + 8),
                                             (px + 8, py + 8)), 2)
        self._draw_map_legend(surface, area, comic)
        destino = point(*self.destino_atual()[2])
        desenhar_circulo(surface, TINTA, destino, 22, espessura=5)
        desenhar_circulo(surface, PAPEL, destino, 22, espessura=2)
        self._draw_navigation(surface, mapa=True)

    def _draw_map_legend(self, surface: pygame.Surface, area: pygame.Rect,
                         comic: bool) -> None:
        """Explica os símbolos sem depender apenas das cores do mapa."""
        player_x = area.left + round(self.x / self.width * area.width)
        player_y = area.top + round(self.y / self.height * area.height)
        box = pygame.Rect(
            area.left + 12 if player_x > area.centerx else area.right - 414,
            area.top + 12 if player_y > area.centery else area.bottom - 83,
            402, 70,
        )
        pygame.draw.rect(surface, (46, 42, 40) if comic else (8, 18, 35), box)
        pygame.draw.rect(surface, PAPEL if comic else (90, 153, 190), box, 1)
        for index, label in enumerate(self._map_legend):
            x = box.left + 17 + index % 3 * 132
            y = box.top + 19 + index // 3 * 31
            if index == 0:
                pygame.draw.polygon(surface, CIANO,
                                    ((x, y - 6), (x + 5, y + 5), (x - 5, y + 5)), 2)
            elif index == 1:
                pygame.draw.polygon(surface, (255, 207, 115),
                                    ((x, y - 6), (x + 6, y), (x, y + 6), (x - 6, y)), 2)
            elif index == 2:
                pygame.draw.circle(surface, (255, 156, 203), (x, y), 5, 2)
            elif index == 3:
                pygame.draw.rect(surface, (178, 145, 213), (x - 4, y - 6, 8, 12), 2)
            elif index == 4:
                pygame.draw.circle(surface, (230, 160, 104), (x, y), 5, 2)
            else:
                pygame.draw.ellipse(surface, (118, 216, 231),
                                    (x - 4, y - 7, 8, 14), 2)
            surface.blit(label, (x + 12, y - label.get_height() // 2))

    def _place_hostiles_in_world(self) -> None:
        for enemy, base_x, base_y, orbit, phase in self.enemies:
            enemy.x = base_x + math.sin(self.elapsed * 0.65 + phase) * orbit
            enemy.y = base_y + math.cos(self.elapsed * 0.48 + phase) * orbit * 0.55
        mini_x = 6300 + math.sin(self.elapsed * 0.42) * 95
        mini_y = 3300 + math.cos(self.elapsed * 0.58) * 48
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
        count = 15 if self.turbo_ativo else 9
        for index in range(count):
            t = self.elapsed * 0.9 + index / count
            x = int((index * 113 + t * 173) % LARGURA)
            y = int((index * 79 + t * 131) % ALTURA)
            length = 12 + int(speed / 32) + (13 if self.turbo_ativo else 0)
            start = (x, y)
            end = (x - int(math.cos(direction) * length),
                   y - int(math.sin(direction) * length))
            pygame.draw.line(surface, (46, 84, 125), start, end, 1)

    def _draw_sectors(self, surface: pygame.Surface) -> None:
        """Dá identidade visual aos seis setores e às fendas de passagem."""
        comic = opcoes_atuais().ativo
        for (_name, center, color), (_label_name, label) in zip(
                self.SECTORS, self._sector_labels):
            x, y = self._screen_position(center)
            radius = 410
            if not (-radius <= x <= LARGURA + radius
                    and -radius <= y <= ALTURA + radius):
                continue
            edge = LARANJA if comic else color
            pygame.draw.circle(surface, edge, (x, y), radius, 2)
            pygame.draw.circle(surface, edge, (x, y), 7, 1)
            surface.blit(label, (x - label.get_width() // 2,
                                 y - radius + 18))

        edge = LARANJA if comic else (94, 213, 238)
        for world_x, world_y, radius in self._rifts:
            x, y = self._screen_position((world_x, world_y))
            if not (-radius <= x <= LARGURA + radius
                    and -radius <= y <= ALTURA + radius):
                continue
            pygame.draw.ellipse(
                surface, edge,
                (x - radius, y - radius // 2, radius * 2, radius), 2,
            )
            pygame.draw.ellipse(
                surface, (207, 140, 255),
                (x - radius // 2, y - radius, radius, radius * 2), 1,
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
        game.inimigos = [
            enemy for enemy, *_ in self.enemies
            if enemy.vida > 0
            and abs(enemy.x - self.x) <= LARGURA / 2 + 150
            and abs(enemy.y - self.y) <= ALTURA / 2 + 150
        ]
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

    def _draw_objective_marker(self, surface: pygame.Surface) -> None:
        """Aponta para o destino escolhido quando ele está fora da câmera."""
        target_x, target_y = self._screen_position(self.destino_atual()[2])
        if 48 <= target_x <= LARGURA - 48 and 48 <= target_y <= ALTURA - 48:
            return
        center_x, center_y = LARGURA // 2, ALTURA // 2
        dx, dy = target_x - center_x, target_y - center_y
        angle = math.atan2(dy, dx)
        distance_x = (LARGURA // 2 - 76) / max(abs(math.cos(angle)), 0.001)
        distance_y = (ALTURA // 2 - 76) / max(abs(math.sin(angle)), 0.001)
        distance = min(distance_x, distance_y)
        x = round(center_x + math.cos(angle) * distance)
        y = round(center_y + math.sin(angle) * distance)
        tip = (round(x + math.cos(angle) * 15),
               round(y + math.sin(angle) * 15))
        back_angle = angle + math.pi
        left = (round(x + math.cos(back_angle + 0.55) * 12),
                round(y + math.sin(back_angle + 0.55) * 12))
        right = (round(x + math.cos(back_angle - 0.55) * 12),
                 round(y + math.sin(back_angle - 0.55) * 12))
        color = LARANJA if opcoes_atuais().ativo else (255, 202, 102)
        pygame.draw.polygon(surface, color, (tip, left, right))

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
                1.0, 0.35 + math.hypot(self.vx, self.vy) / self.SPEED * 0.65),
                piscar=False)
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

    @staticmethod
    def _local_map_point(position: tuple[float, float],
                         center: tuple[float, float],
                         area: pygame.Rect) -> tuple[int, int] | None:
        """Projeta um alvo próximo; alvos distantes ficam fora do minimapa."""
        x = area.centerx + round((position[0] - center[0]) * area.width / 3200)
        y = area.centery + round((position[1] - center[1]) * area.height / 1800)
        return (x, y) if area.collidepoint(x, y) else None

    def _draw_minimap(self, surface: pygame.Surface) -> None:
        self._place_hostiles_in_world()
        comic = opcoes_atuais().ativo
        panel = (39, 33, 29, 238) if comic else (4, 9, 24, 218)
        frame = LARANJA if comic else (78, 129, 173)
        grid = (91, 76, 61) if comic else (31, 48, 74)
        player_color = CIANO if comic else (110, 245, 255)
        self._minimap.fill(panel)
        pygame.draw.rect(self._minimap, frame,
                         (0, 0, *self.MINIMAP_SIZE), 2)
        label = self._minimap_comic_label if comic else self._minimap_label
        self._minimap.blit(label, (10, 5))
        hint = self._minimap_comic_hint if comic else self._minimap_hint
        self._minimap.blit(hint, (250 - hint.get_width(), 5))
        area = pygame.Rect(10, 30, 240, 138)
        pygame.draw.rect(self._minimap, (49, 42, 37) if comic else (15, 26, 49), area)
        pygame.draw.rect(self._minimap, frame, area, 1)
        for fraction in (0.25, 0.5, 0.75):
            x = area.left + round(area.width * fraction)
            y = area.top + round(area.height * fraction)
            pygame.draw.line(self._minimap, grid,
                             (x, area.top), (x, area.bottom), 1)
            pygame.draw.line(self._minimap, grid,
                             (area.left, y), (area.right, y), 1)

        def point(position: tuple[float, float]) -> tuple[int, int] | None:
            return self._local_map_point(position, (self.x, self.y), area)

        self._draw_minimap_terrain(point)
        view_start = point((self.camera_x, self.camera_y))
        if view_start is not None:
            view = pygame.Rect(
                view_start[0], view_start[1],
                max(2, round(LARGURA * area.width / 3200)),
                max(2, round(ALTURA * area.height / 1800)),
            )
            pygame.draw.rect(self._minimap, frame, view.clip(area), 1)
        self._draw_minimap_contacts(point, comic)
        destino = point(self.destino_atual()[2])
        if destino is not None:
            desenhar_circulo(self._minimap, PAPEL, destino, 8, espessura=2)
        px, py = area.center
        pygame.draw.polygon(self._minimap, player_color,
                            ((px, py - 6), (px + 5, py + 5), (px - 5, py + 5)))
        pygame.draw.polygon(self._minimap, (8, 20, 32),
                            ((px, py - 6), (px + 5, py + 5), (px - 5, py + 5)), 1)
        surface.blit(self._minimap, (LARGURA - self.MINIMAP_SIZE[0] - 16, 20))

    def _draw_minimap_terrain(
            self, point: Callable[[tuple[float, float]], tuple[int, int] | None]
    ) -> None:
        """Mostra obstáculos e passagens locais com silhuetas distintas."""
        for rock in self.asteroids.nearby(self.x, self.y, 1700):
            marker = point((rock.x, rock.y)) if rock.active() else None
            if marker is not None:
                pygame.draw.rect(self._minimap, (93, 112, 126),
                                 (marker[0] - 1, marker[1] - 1, 3, 3))
        for x, y, _radius in self._rifts:
            marker = point((x, y))
            if marker is not None:
                pygame.draw.rect(self._minimap, (178, 145, 213),
                                 (marker[0] - 3, marker[1] - 3, 6, 6), 1)
        for hole in self.anomalies.black_holes:
            marker = point(hole.position)
            if marker is not None:
                pygame.draw.circle(self._minimap, (230, 160, 104), marker, 4, 2)
        for portal in self.anomalies.wormholes:
            marker = point(portal.position)
            if marker is not None:
                x, y = marker
                pygame.draw.ellipse(self._minimap, (118, 216, 231),
                                    (x - 3, y - 5, 6, 10), 1)

    def _draw_minimap_contacts(
            self, point: Callable[[tuple[float, float]], tuple[int, int] | None],
            comic: bool) -> None:
        """Mostra ameaças próximas e preserva a forma de cada objetivo."""
        for enemy, *_ in self.enemies:
            if enemy.vida > 0:
                marker = point((enemy.x, enemy.y))
                if marker is not None:
                    pygame.draw.circle(self._minimap, PAPEL if comic else (219, 137, 126),
                                       marker, 2)
        mini = point(self._miniboss_world) if self.miniboss.vida > 0 else None
        if mini is not None:
            x, y = mini
            pygame.draw.polygon(self._minimap, (255, 156, 203),
                                ((x, y - 5), (x + 5, y), (x, y + 5), (x - 5, y)), 2)
        boss = point(self.BOSS_LAIR) if self.boss.vida > 0 else None
        if boss is not None:
            x, y = boss
            pygame.draw.polygon(self._minimap, (255, 210, 100),
                                ((x, y - 6), (x + 6, y + 4), (x - 6, y + 4)), 2)
