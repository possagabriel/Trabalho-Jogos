"""Patrulhas distintas, persistência e mecânicas em coordenadas do mundo."""

import math
import random
from unittest.mock import Mock

import pygame
import pytest

from src.runtime.application.core import Jogo
from src.runtime.domain.world.open_world import OpenWorldRuntime


def test_sete_patrulhas_distintas_e_spawn_fora_das_arenas():
    pygame.font.init()
    mundo = OpenWorldRuntime(rng=random.Random(9))
    assert len(mundo.patrulhas) == 7
    assert len({p.boss.chave for p in mundo.patrulhas}) == 7
    assert len(mundo.enemies) >= 260
    for p in mundo.patrulhas:
        assert math.dist(p.centro, mundo.SPAWN) > 500
        assert math.dist(p.centro, mundo.BOSS_LAIR) > 1000
    assert len([d for d in mundo.destinos_navegacao() if d[0].startswith('patrulha')]) == 7


def test_derrota_persistida_nao_recria_recompensa_ao_retomar():
    jogo = Jogo(sons=Mock())
    jogo.modo_atual = 'mundo_aberto'
    mundo = OpenWorldRuntime(rng=random.Random(2))
    p = mundo.patrulhas[2]
    mundo.x, mundo.y = p.centro
    mundo._place_hostiles_in_world()
    mundo._activate_encounters(jogo)
    assert mundo.miniboss is p.boss
    p.boss.vida = 0
    mundo._sync_encounter_targets(0, jogo)
    mundo._finish_encounter_frame(jogo)
    assert p.derrotada
    assert mundo.progress_dirty
    estado = mundo.save_state()
    novo = OpenWorldRuntime(toca_boss=estado['toca_boss'],
                            patrulhas_derrotadas=estado['patrulhas_derrotadas'])
    assert novo.patrulhas[2].derrotada
    assert p.ident not in {d[0] for d in novo.destinos_navegacao()}
    assert len([d for d in novo.destinos_navegacao() if d[0].startswith('patrulha')]) == 6


@pytest.mark.parametrize('chave', ['censor', 'bastiao', 'espectro', 'matriz',
                                   'cartografo', 'eco', 'cronista'])
def test_encontro_continua_independente_da_camera(chave):
    jogo = Jogo(sons=Mock())
    jogo.modo_atual = 'mundo_aberto'
    mundo = OpenWorldRuntime()
    p = next(p for p in mundo.patrulhas if p.boss.chave == chave)
    mundo.x, mundo.y = p.centro
    mundo.camera_x, mundo.camera_y = mundo.x - 640, mundo.y - 360
    mundo._place_hostiles_in_world()
    mundo._activate_encounters(jogo)
    for _ in range(150):
        mundo._sync_encounter_targets(1 / 60, jogo)
        mundo._finish_encounter_frame(jogo)
    antes = mundo._miniboss_world
    zonas = [z.copy() for z in p.boss.zonas]
    mundo.camera_x += 700
    mundo.camera_y -= 210
    mundo._sync_encounter_targets(0, jogo)
    mundo._finish_encounter_frame(jogo)
    assert mundo._miniboss_world == pytest.approx(antes)
    assert p.boss.zonas == zonas
    if chave == 'matriz':
        assert len(mundo._lacaios_mundo) == 3


@pytest.mark.parametrize('dimensao', range(1, 7))
def test_arenas_sao_seguras_e_estaveis_na_retomada(dimensao):
    pygame.font.init()
    mundo = OpenWorldRuntime(dimension=dimensao, rng=random.Random(dimensao))
    novo = OpenWorldRuntime(dimension=dimensao, toca_boss=mundo.BOSS_LAIR)
    assert novo._centros_patrulhas == mundo._centros_patrulhas
    for p in mundo.patrulhas:
        assert all(math.dist(p.centro, h.position) >= h.influence + 400
                   for h in mundo.anomalies.black_holes)
        assert all(math.dist(p.centro, portal.position) >= 600
                   for portal in mundo.anomalies.wormholes)


def test_avisos_de_salto_e_quarentena_ficam_no_mundo_ao_mover_camera():
    jogo = Jogo(sons=Mock())
    jogo.modo_atual = 'mundo_aberto'
    for chave in ('espectro', 'cartografo'):
        mundo = OpenWorldRuntime()
        p = next(p for p in mundo.patrulhas if p.boss.chave == chave)
        mundo.x, mundo.y = p.centro
        mundo.camera_x, mundo.camera_y = mundo.x - 640, mundo.y - 360
        mundo._place_hostiles_in_world()
        mundo._activate_encounters(jogo)
        mundo._sync_encounter_targets(0.4, jogo)
        mundo._finish_encounter_frame(jogo)
        zonas = [z.copy() for z in p.boss.zonas]
        destino = p.boss.estrategia.destino
        mundo.camera_x += 777.25
        mundo.camera_y -= 210.125
        mundo._sync_encounter_targets(0, jogo)
        mundo._finish_encounter_frame(jogo)
        assert p.boss.zonas == zonas
        assert p.boss.estrategia.destino == destino
        if chave == 'espectro':
            mundo._sync_encounter_targets(0.9, jogo)
            mundo._finish_encounter_frame(jogo)
            assert mundo._miniboss_world == pytest.approx(destino)


def test_destino_nao_usa_coordenadas_projetadas_para_interface():
    jogo = Jogo(sons=Mock())
    jogo.modo_atual = 'mundo_aberto'
    mundo = OpenWorldRuntime()
    mundo.miniboss_active = True
    jogo.miniboss = mundo.miniboss
    inicio = mundo.destinos_navegacao()
    mundo.project_targets_for_ui(jogo)
    assert mundo.destinos_navegacao() == inicio


def test_todas_as_derrotas_recompensam_uma_vez_e_liberam_proxima_patrulha():
    jogo = Jogo(sons=Mock())
    jogo.modo_atual = 'mundo_aberto'
    mundo = OpenWorldRuntime()
    for p in mundo.patrulhas:
        mundo.x, mundo.y = p.centro
        mundo._place_hostiles_in_world()
        mundo._activate_encounters(jogo)
        assert mundo.miniboss is p.boss
        moedas = jogo.loja.moedas
        p.boss.vida = 0
        mundo._sync_encounter_targets(0, jogo)
        mundo._finish_encounter_frame(jogo)
        assert jogo.loja.moedas == moedas + p.boss.cfg['moedas']
        mundo._sync_encounter_targets(0, jogo)
        mundo._finish_encounter_frame(jogo)
        assert jogo.loja.moedas == moedas + p.boss.cfg['moedas']
    assert all(p.derrotada for p in mundo.patrulhas)
    assert len(mundo.save_state()['patrulhas_derrotadas']) == 7
    mundo._pending_dimension = 2
    mundo.advance_dimension()
    assert len(mundo._patrulhas_vivas()) == 7
    assert mundo._lacaios_mundo == []


@pytest.mark.parametrize('estilo', ['ORIGINAL', 'COMIC'])
def test_renderiza_patrulhas_e_avisos_sem_mutar_posicoes(estilo):
    from src.core.constants import ALTURA, LARGURA
    from src.infrastructure.graphics.comic_theme import usar_visual

    jogo = Jogo(sons=Mock())
    jogo.modo_atual = 'mundo_aberto'
    mundo = OpenWorldRuntime()
    tela = pygame.Surface((LARGURA, ALTURA))
    with usar_visual({'estilo_visual': estilo, 'reduzir_efeitos': True}):
        for p in mundo.patrulhas:
            mundo.x, mundo.y = p.centro
            mundo.camera_x, mundo.camera_y = mundo.x - 640, mundo.y - 360
            mundo._patrulha_atual = p
            mundo.miniboss = p.boss
            mundo.miniboss_active = True
            mundo._miniboss_world = p.posicao(mundo.elapsed)
            mundo._sync_encounter_targets(0.1, jogo)
            mundo._finish_encounter_frame(jogo)
            antes = mundo._miniboss_world
            zonas = [z.copy() for z in p.boss.zonas]
            destino = p.boss.estrategia.destino
            mundo._draw_hostiles(tela)
            mundo.render_map(tela)
            assert mundo._miniboss_world == antes
            assert p.boss.zonas == zonas
            assert p.boss.estrategia.destino == destino


def test_censor_inverte_movimento_so_durante_ataque():
    from collections import defaultdict

    from src.runtime.domain.entities.minibosses.states import Ataque, Recuperacao

    pygame.font.init()
    mundo = OpenWorldRuntime()
    mundo.miniboss_active = True
    mundo.x, mundo.y = mundo._patrulha_atual.centro
    teclas = defaultdict(bool, {pygame.K_RIGHT: True})
    mundo.miniboss.estado = Ataque(2)
    mundo.update(1 / 60, teclas, {})
    assert mundo.vx < 0
    mundo.miniboss.estado = Recuperacao(2)
    mundo.update(1 / 60, teclas, {})
    assert mundo.vx > 0


def test_eco_observa_disparos_reais_do_mundo_aberto():
    from collections import defaultdict
    from unittest.mock import patch

    from src.runtime.domain.entities.weapons import Projetil

    jogo = Jogo(sons=Mock())
    jogo.modo_atual = 'mundo_aberto'
    mundo = OpenWorldRuntime()
    p = next(p for p in mundo.patrulhas if p.boss.chave == 'eco')
    mundo.x, mundo.y = p.centro
    mundo._place_hostiles_in_world()
    mundo._activate_encounters(jogo)
    tiro = Projetil(640, 360, 3, -7, 1, (255, 255, 255), 4)
    with patch.object(jogo.jogador, 'atirar', return_value=[tiro]):
        mundo._update_combat(1 / 60, defaultdict(bool, {pygame.K_SPACE: True}), {}, jogo)
    assert [(t[0], t[1]) for t in p.boss.ultimo_disparo] == [(3, -7)]
