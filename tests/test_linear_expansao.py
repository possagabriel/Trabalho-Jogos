"""Novas fases, guardiões e retomada do LINEAR sem alterar capítulos anteriores."""

from unittest.mock import Mock

import pygame
import pytest

from game.phase_select import PhaseStatus, get_phase_status
from src.infrastructure.graphics.comic_theme import usar_visual
from src.runtime.application.core import Jogo
from src.runtime.domain.entities.bosses import BOSSES_POR_CENARIO, Boss
from src.runtime.domain.entities.player import Jogador
from src.runtime.domain.world.scenarios import CENARIOS, Cenario, cenario_do_nivel

pygame.font.init()


@pytest.mark.parametrize('cenario,nivel', [(7, 31), (8, 36), (9, 41)])
def test_novas_fases_tem_boss_proprio_e_ataque_distinto(cenario, nivel):
    assert len(CENARIOS) == 9
    assert cenario_do_nivel(nivel) == cenario
    mundo = Cenario(cenario)
    boss = Boss(nivel + 4, mundo)
    assert boss.nome not in {BOSSES_POR_CENARIO[i]['nome'] for i in range(1, 7)}
    assert boss.ataques[0] not in {a for i in range(1, 7)
                                 for a in BOSSES_POR_CENARIO[i]['ataques']}
    tiros = boss._executar_ataque(boss.ataques[0], Jogador(), 500, 160)
    assert len(tiros) >= 3
    assert all(0 < (t.vel_x ** 2 + t.vel_y ** 2) ** 0.5 <= 5 for t in tiros)
    assert mundo.fundo_imagem is None


def test_lobby_libera_e_retoma_as_tres_fases_novas(tmp_path, monkeypatch):
    monkeypatch.setenv('INCARNATE_DATA_DIR', str(tmp_path))
    jogo = Jogo(sons=Mock())
    perfil = jogo.profile_service.create('Piloto')
    jogo.ativar_perfil(perfil.id)
    tela = jogo.menu.phase_screen
    assert len(tela.phases) == 9
    assert [p.id for p in tela.phases[:5]] == [
        'lealdade', 'funcao', 'identidade', 'silencio', 'descarte']
    for indice, nivel in [(6, 31), (7, 36), (8, 41)]:
        jogo.progresso.registrar_fase_concluida(nivel - 1)
        tela.refresh()
        fase = tela.phases[indice]
        assert get_phase_status(fase.id, jogo.progresso.jogador,
                                tela.phases) == PhaseStatus.AVAILABLE
        tela.selected = indice
        assert tela.confirm()
        assert jogo.jogador.nivel == nivel
        assert jogo.cenario.id == indice + 1
        jogo.progresso.registrar_checkpoint(nivel + 1)
        assert jogo.progresso.campanha['fase_atual'] == fase.id
        assert tela.confirm()
        assert jogo.jogador.nivel == nivel + 1
    for indice in range(len(tela.phases)):
        rect = tela.card_rect(indice)
        assert rect.bottom < tela._rect(30, 552, 220, 32).top
    jogo.progresso.salvar_arquivo()
    reiniciado = Jogo(sons=Mock())
    reiniciado.ativar_perfil(perfil.id)
    assert reiniciado.progresso.campanha['nivel_atual'] == 42


@pytest.mark.parametrize('estilo', ['ORIGINAL', 'COMIC'])
def test_novos_guardioes_e_fundos_tem_arte_propria(estilo):
    pygame.display.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))
    artes, fundos = [], []
    with usar_visual({'estilo_visual': estilo, 'intensidade_flash': 'REDUZIDO'}):
        for cid in (7, 8, 9):
            cenario = Cenario(cid)
            cenario.configurar_avanco('MEDIA', (0, 1), True, True, {}, cid)
            cenario.parallax.desenhar(pygame.Surface((1280, 720)))
            boss = Boss(cid * 5, cenario)
            boss.entrando = False
            boss.x, boss.y = 640, 200
            tela = pygame.Surface((1280, 720), pygame.SRCALPHA)
            boss.desenhar(tela)
            assert tela.get_bounding_rect().width >= boss.raio
            artes.append(pygame.image.tobytes(tela, 'RGBA'))
            fundos.append(pygame.image.tobytes(cenario.fundo_estatico, 'RGB'))
    assert len(set(artes)) == 3
    assert len(set(fundos)) == 3
