"""Regressões de geração visual, posições de encontros e recompensas livres."""

import math
import random
from unittest.mock import Mock, patch

import pygame
import pytest

from src.runtime.application.core import Jogo
from src.runtime.domain.entities.powerups import PowerUp
from src.runtime.domain.world.open_world import OpenWorldRuntime
from src.runtime.domain.world.region_background import SectorBackground
from src.runtime.infrastructure.graphics import map_art

pygame.font.init()


def test_toca_varia_com_semente_e_preserva_save():
    mundos = [OpenWorldRuntime(rng=random.Random(i)) for i in range(5)]
    assert len({m.BOSS_LAIR for m in mundos}) == len(mundos)
    for mundo in mundos:
        assert math.dist(mundo.SPAWN, mundo.BOSS_LAIR) > 900
        estado = mundo.save_state()
        restaurado = OpenWorldRuntime(position=(mundo.x, mundo.y),
                                      toca_boss=estado['toca_boss'])
        assert restaurado.BOSS_LAIR == mundo.BOSS_LAIR
        assert mundo.destino_atual()[2] == mundo.BOSS_LAIR
        assert [r.ident for r in restaurado.asteroids.asteroids] == [
            r.ident for r in mundo.asteroids.asteroids]


@pytest.mark.parametrize('modo', ['linear', 'mundo_aberto'])
def test_recompensa_so_cai_no_linear(modo):
    jogo = Jogo(sons=Mock())
    jogo.modo_atual = modo
    vida = PowerUp('vida', jogo.jogador.x + 200, jogo.jogador.y)
    fora = PowerUp('moedas', jogo.jogador.x + 200, 2000)
    jogo.powerups = [vida, fora]
    inicio = (vida.x, vida.y)
    for _ in range(10):
        jogo.combate_controller.atualizar_powerups()
    if modo == 'mundo_aberto':
        assert (vida.x, vida.y) == inicio
        assert fora in jogo.powerups
    else:
        assert vida.y > inicio[1]
        assert fora not in jogo.powerups
    vida.x, vida.y = jogo.jogador.x, jogo.jogador.y
    jogo.jogador.vida -= 1
    anterior = jogo.jogador.vida
    jogo.combate_controller.atualizar_powerups()
    assert jogo.jogador.vida == anterior + 1
    assert vida not in jogo.powerups


def test_miniboss_patrulha_mundo_sem_se_prender_a_camera():
    jogo = Jogo(sons=Mock())
    jogo.modo_atual = 'mundo_aberto'
    mundo = OpenWorldRuntime()
    mundo.miniboss_active = True
    mundo.x, mundo.y = mundo._miniboss_world
    mundo.camera_x, mundo.camera_y = mundo.x - 640, mundo.y - 360
    inicial = mundo._miniboss_world
    with patch.object(jogo.miniboss_spawner, 'atualizar') as agendar:
        for _ in range(60):
            mundo._sync_encounter_targets(1 / 60, jogo)
            mundo._finish_encounter_frame(jogo)
        assert not agendar.called
    assert math.dist(inicial, mundo._miniboss_world) > 10
    antes = mundo._miniboss_world
    mundo.x += 700
    mundo.camera_x += 700
    mundo._sync_encounter_targets(0, jogo)
    mundo._finish_encounter_frame(jogo)
    assert mundo._miniboss_world == pytest.approx(antes)


def test_mapa_nao_gera_arte_grande_para_miniaturas():
    mundo = OpenWorldRuntime()
    map_art.miniatura_rocha.cache_clear()
    map_art.miniatura_anomalia.cache_clear()
    map_art.fundo_mapa.cache_clear()
    with (patch.object(map_art, 'criar_fundo_nebuloso',
                      side_effect=AssertionError('nebulosa'), create=True),
          patch.object(map_art, 'arte_asteroide',
                       side_effect=AssertionError('asteroide'), create=True),
          patch.object(map_art, 'camada_anomalia',
                       side_effect=AssertionError('anomalia'), create=True)):
        mundo.render_map(pygame.Surface((1280, 720)))


def test_render_de_fundo_nao_executa_geracao_pesada():
    fundo = SectorBackground(1, OpenWorldRuntime.SECTORS, OpenWorldRuntime.SPAWN)
    with patch.object(fundo, 'surface_for_sector', side_effect=AssertionError('sincrono')):
        fundo.render(pygame.Surface((1280, 720)), False)
        fundo.update(*OpenWorldRuntime.SECTORS[2][1], 0.1)
        fundo.render(pygame.Surface((1280, 720)), False)


def test_fundo_incremental_preserva_arte_e_limita_trabalho_por_quadro():
    from src.runtime.domain.world import region_background
    from src.runtime.infrastructure.graphics.nebula_background import (
        criar_fundo_nebuloso,
        etapas_fundo_nebuloso,
    )

    args = ((80, 60), (10, 16, 60), (4, 4, 26), (60, 40, 130), 42, False)
    etapas = list(etapas_fundo_nebuloso(*args))
    assert len(etapas) > 2
    assert pygame.image.tobytes(etapas[-1], 'RGB') == pygame.image.tobytes(
        criar_fundo_nebuloso(*args), 'RGB')
    fundo = SectorBackground(1, OpenWorldRuntime.SECTORS, OpenWorldRuntime.SPAWN)
    tarefas = Mock()
    fundo._tasks[(0, False)] = iter([None] * 20)
    original = fundo._tasks[(0, False)]
    def etapa():
        for item in original:
            tarefas()
            yield item
    fundo._tasks[(0, False)] = etapa()
    with patch.object(region_background, 'perf_counter', side_effect=[0, 0, 1]):
        fundo.update(*OpenWorldRuntime.SPAWN, 1 / 60)
    tarefas.assert_called_once()
