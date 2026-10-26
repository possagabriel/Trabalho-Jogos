"""Regressões da exploração, dos encontros e dos controles do mundo aberto."""

from __future__ import annotations

from types import SimpleNamespace

import pygame

from src.core.constants import ALTURA, LARGURA, EstadoJogo
from src.core.event_bus import GameEventType
from src.core.settings import Configuracoes
from src.runtime.controllers.render import ControladorRenderizacao
from src.runtime.domain.entities.player import Jogador
from src.runtime.domain.entities.weapons import Projetil
from src.runtime.domain.game_modes import OpenWorldModeStrategy
from src.runtime.domain.world.asteroid_field import AsteroidField
from src.runtime.domain.world.open_world import OpenWorldRuntime


class Teclas:
    """Estado mínimo de teclado para simular um quadro."""

    def __init__(self, *pressed: int) -> None:
        self.pressed = set(pressed)

    def __getitem__(self, key: int) -> bool:
        return key in self.pressed


def test_mapa_ampliado_distribui_asteroides_por_toda_a_area():
    world = OpenWorldRuntime()

    assert world.REGION_SIZE == (19200.0, 13200.0)
    assert world.BOSS_LAIR[0] > 16000
    quadrantes = {
        (int(rock.x >= world.width / 2), int(rock.y >= world.height / 2))
        for rock in world.asteroids.asteroids
    }
    assert quadrantes == {(0, 0), (0, 1), (1, 0), (1, 1)}
    assert len(world.asteroids.asteroids) >= 500


def test_asteroide_destruido_reaparece_apos_cooldown():
    field = AsteroidField(3200, 2800, seed=7, cooldown=24.0)
    rock = field.asteroids[0]

    assert field.damage(rock, rock.max_health, now=10.0)
    assert rock.respawn_at == 34.0
    field.update(33.9)
    assert rock.health == 0
    field.update(34.0)
    assert rock.health == rock.max_health
    assert rock.respawn_at is None


def test_tiro_destroi_obstaculo_e_save_preserva_recarga():
    world = OpenWorldRuntime()
    rock = world.asteroids.asteroids[0]
    world.camera_x = rock.x - LARGURA / 2
    world.camera_y = rock.y - ALTURA / 2
    shot = Projetil(LARGURA / 2, ALTURA / 2, 0, 0,
                    rock.max_health, (255, 220, 90), 5)
    game = SimpleNamespace(
        projeteis=[shot], sons=SimpleNamespace(tocar=lambda _sound: None))

    world._resolve_asteroid_hits(game)

    assert not rock.active()
    assert game.projeteis == []
    state = world.save_state()
    restored = OpenWorldRuntime(elapsed=world.elapsed,
                                cooldowns=state["asteroides"])
    assert not restored.asteroids.asteroids[rock.ident].active()


def test_ion_horizontal_atinge_asteroide_no_mundo_aberto():
    pygame.font.init()
    world = OpenWorldRuntime()
    rock = world.asteroids.asteroids[0]
    world.camera_x = rock.x - LARGURA / 2
    world.camera_y = rock.y - ALTURA / 2
    shot = Projetil(LARGURA / 2 - 160, ALTURA / 2, 1, 0,
                    rock.max_health, (200, 220, 255), 6, tipo="ion")
    shot.atualizar()
    game = SimpleNamespace(
        projeteis=[shot], sons=SimpleNamespace(tocar=lambda _sound: None))

    world._resolve_asteroid_hits(game)

    assert not rock.active()
    assert game.projeteis == [shot]


def test_nave_intangivel_atravessa_asteroide():
    pygame.font.init()
    world = OpenWorldRuntime()
    rock = world.asteroids.asteroids[0]
    player = Jogador()
    player.tempo_intangivel = 60
    world.x, world.y = rock.x, rock.y

    world._collide_ship_with_asteroids(SimpleNamespace(jogador=player))

    assert (world.x, world.y) == (rock.x, rock.y)


def test_turbo_move_mais_e_consumo_e_recarga_usam_medidor_existente():
    normal = OpenWorldRuntime()
    turbo = OpenWorldRuntime()
    game = SimpleNamespace(boost=1.0, energia=100.0)
    turbo._update_combat = lambda *_args: None

    normal.update(1 / 60, Teclas(pygame.K_RIGHT), {})
    turbo.update(1 / 60, Teclas(pygame.K_RIGHT, pygame.K_LSHIFT), {}, game)

    assert turbo.x - turbo.SPAWN[0] > normal.x - normal.SPAWN[0]
    assert game.boost < 1.0
    assert game.energia < 100.0
    turbo.update(1 / 60, Teclas(), {}, game)
    assert game.boost > 0.99


def test_invencibilidade_avanca_e_nave_permanece_visivel_no_mundo():
    world = OpenWorldRuntime()
    player = Jogador()
    player.invencivel = 120
    game = SimpleNamespace(jogador=player, menu_equipamento=False)
    surface = pygame.Surface((LARGURA, ALTURA))
    world._update_combat = lambda *_args: None

    world._draw_ship(surface, player)
    world.update(1 / 60, Teclas(), {}, game)

    assert player.invencivel == 119
    assert surface.get_at((LARGURA // 2, ALTURA // 2))[:3] != (0, 0, 0)


def test_m_abre_mapa_em_tela_cheia_e_esc_fecha_sem_pausar():
    strategy = OpenWorldModeStrategy()
    strategy.world = OpenWorldRuntime()
    game = SimpleNamespace(
        estado=EstadoJogo.JOGANDO, menu_equipamento=False,
        controles={"pausar": pygame.K_p},
    )

    assert strategy.handle_event(game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m))
    assert strategy.world.map_open
    assert strategy.handle_event(game, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert not strategy.world.map_open
    assert game.estado is EstadoJogo.JOGANDO


def test_mapa_em_tela_cheia_mostra_limites_e_nave():
    world = OpenWorldRuntime()
    surface = pygame.Surface((LARGURA, ALTURA))

    world.render_map(surface)

    assert surface.get_at((42, 68))[:3] != surface.get_at((0, 0))[:3]
    px = 42 + round(world.x / world.width * (LARGURA - 84))
    py = 68 + round(world.y / world.height * (ALTURA - 120))
    assert surface.get_at((px, py))[:3] != surface.get_at((0, 0))[:3]


def test_boss_do_mundo_orbita_em_duas_dimensoes_e_vitoria_abre_a_proxima():
    world = OpenWorldRuntime()
    world.boss_active = True
    start = world._boss_world

    world._update_world_boss(1.0)
    assert world._boss_world[0] != start[0]
    assert world._boss_world[1] != start[1]

    world.boss_defeated = True
    world._pending_dimension = 2
    assert world.advance_dimension()
    assert world.dimension == 2
    assert world.boss.nome == "LOSANGO"
    assert (world.x, world.y) == world.SPAWN


def test_vitoria_do_boss_aceita_configuracoes_reais_do_jogo():
    pygame.font.init()
    world = OpenWorldRuntime(visual_config=Configuracoes())
    world.boss_defeated = True
    world._pending_dimension = 2

    assert world.advance_dimension()
    assert world.dimension == 2
    assert world._cenario.parallax is not None


def test_eventos_de_boss_e_passagem_acionam_cutscenes_existentes(monkeypatch):
    events = []
    monkeypatch.setattr(
        "src.runtime.domain.world.open_world.publicar_evento",
        lambda kind, **data: events.append((kind, data)),
    )
    world = OpenWorldRuntime()
    world.x, world.y = world.BOSS_LAIR
    game = SimpleNamespace(
        sons=SimpleNamespace(tocar=lambda _sound: None), boss_intro=0,
        miniboss_controller=SimpleNamespace(reiniciar=lambda: None),
    )

    world._activate_encounters(game)
    assert events[0][0] is GameEventType.BOSS_SPAWNED
    assert events[0][1]["cenario_id"] == 1

    world.boss_defeated = True
    world._pending_dimension = 2
    world.advance_dimension(game)
    assert events[-1][0] is GameEventType.DIMENSION_CHANGED
    assert events[-1][1]["cenario_id"] == 2


def test_interface_do_mundo_preserva_menu_de_armas_desenhado_no_tab(monkeypatch):
    surface = pygame.Surface((LARGURA, ALTURA))
    ui = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)

    def render(_game, _surface):
        ui.set_at((25, 25), (80, 210, 250, 255))
        return True

    game = SimpleNamespace(
        tela=surface, tela_ui=ui,
        estrategia_modo=SimpleNamespace(handles_gameplay=True, render=render),
        estado=EstadoJogo.JOGANDO, _hud_nativo_pronto=False,
        _apresentar=lambda: None,
    )
    controller = object.__new__(ControladorRenderizacao)
    controller.jogo = game
    controller.sincronizar_cursor = lambda: None
    controller.aplicar_shake = lambda: None
    controller._desenhar_overlays_logicos = lambda: None
    controller._desenhar_mira_e_debug = lambda: None
    monkeypatch.setattr(pygame.display, "flip", lambda: None)

    controller._compor()

    assert ui.get_at((25, 25)).a == 255


def test_borda_do_vazio_ocupa_a_borda_da_tela():
    world = OpenWorldRuntime((60, 900))
    surface = pygame.Surface((LARGURA, ALTURA))
    world._draw_void_border(surface)

    assert surface.get_at((0, ALTURA // 2))[:3] != (0, 0, 0)
    assert surface.get_at((LARGURA // 2, ALTURA // 2))[:3] == (0, 0, 0)


def test_fundo_muda_com_a_area_do_mapa():
    world = OpenWorldRuntime()
    first = world.background.surface_for_sector(0, comic=False)
    second = world.background.surface_for_sector(1, comic=False)

    assert first.get_at((LARGURA // 2, ALTURA // 2)) != second.get_at(
        (LARGURA // 2, ALTURA // 2)
    )
    world.x, world.y = world.SECTORS[1][1]
    world.update(1 / 60, Teclas(), {})
    assert world.background.target_sector == 1


def test_fundo_conclui_transicao_antes_de_trocar_o_setor_alvo():
    world = OpenWorldRuntime()
    background = world.background
    background.update(*world.SECTORS[1][1], 0.1)
    background.update(*world.SECTORS[1][1], 0.2)
    assert background.target_sector == 1

    background.update(*world.SECTORS[2][1], 0.1)
    assert background.current_sector == 0
    assert background.target_sector == 1
    assert background.transition > 0.2

    background.update(*world.SECTORS[2][1], 0.8)
    background.update(*world.SECTORS[2][1], 0.0)
    assert background.current_sector == 1
    assert background.target_sector == 2
