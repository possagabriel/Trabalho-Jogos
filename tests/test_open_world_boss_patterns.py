"""Padrões anunciados, movimento e segurança dos ataques do mundo aberto."""

import math

import pygame
import pytest

from src.runtime.domain.world.boss_patterns import angulos_ataque, posicao_patrulha
from src.runtime.domain.world.open_world import OpenWorldRuntime


@pytest.mark.parametrize("dimensao", range(1, 7))
def test_rota_ampla_independe_do_jogador(dimensao):
    centro = OpenWorldRuntime.BOSS_LAIR
    pontos = [posicao_patrulha(centro, t, dimensao, 1) for t in (0, 5, 10)]
    assert math.dist(pontos[0], pontos[1]) > 300
    assert all(0 < x < 19200 and 0 < y < 13200 for x, y in pontos)


def test_bosses_tem_padroes_distintos_e_fases_diferentes():
    assert len({angulos_ataque(d, 1, 0) for d in range(1, 7)}) == 6
    assert all(angulos_ataque(d, 1, 0) != angulos_ataque(d, 3, 0) for d in range(1, 7))


def test_boss_anuncia_mira_travada_antes_de_disparar():
    pygame.font.init()
    world = OpenWorldRuntime()
    world.boss_active = True
    world._boss_attack_timer = 0.7
    assert world._update_world_boss(0.1) == []
    assert world._boss_attack_angle is not None
    mira = world._boss_attack_angle
    origem = world._boss_world
    world.x += 900
    assert world._update_world_boss(0.2) == []
    assert world._boss_attack_angle == mira
    assert world._boss_world == origem
    tiros = world._update_world_boss(0.46)
    esperados = angulos_ataque(world.dimension, world.boss.fase_atual, mira)
    assert len(tiros) == len(esperados)
    for tiro, angulo in zip(tiros, esperados):
        assert math.atan2(tiro.vel_y, tiro.vel_x) == pytest.approx(
            math.atan2(math.sin(angulo), math.cos(angulo)))
    assert world._boss_attack_angle is None


def test_quadro_longo_e_mudanca_de_fase_preservam_aviso():
    pygame.font.init()
    world = OpenWorldRuntime()
    assert world._update_world_boss(5.0) == []
    assert world._boss_attack_timer == pytest.approx(0.65)
    world.boss.vida = 1
    assert world._update_world_boss(0.05) == []
    assert world._boss_attack_angle is None
    assert world._boss_attack_timer >= 0.65


@pytest.mark.parametrize("estilo", ["COMIC", "ORIGINAL"])
def test_aviso_permanece_visivel_com_efeitos_reduzidos_sem_alterar_estado(estilo):
    from src.infrastructure.graphics.comic_theme import usar_visual

    pygame.font.init()
    pygame.display.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))
    world = OpenWorldRuntime(visual_config={"intensidade_flash": "REDUZIDO"})
    world.boss_active = True
    world._boss_attack_angle = 0.0
    world._boss_attack_timer = 0.4
    world.camera_x = world._boss_world[0] - 640
    world.camera_y = world._boss_world[1] - 360
    antes = (world._boss_world, world.boss.vida, world._boss_attack_timer)
    tela = pygame.Surface((1280, 720), pygame.SRCALPHA)
    with usar_visual({"estilo_visual": estilo}):
        world._draw_boss_warning(tela)
    assert tela.get_bounding_rect().width > 300
    assert (world._boss_world, world.boss.vida, world._boss_attack_timer) == antes
