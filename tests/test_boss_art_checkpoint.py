"""Artes dos novos guardiões, avisos de ataque e checkpoint ao voltar ao lobby."""

from unittest.mock import Mock, patch

import pygame
import pytest

from src.core.constants import EstadoJogo
from src.runtime.application.core import Jogo
from src.runtime.domain.entities.bosses import Boss
from src.runtime.domain.entities.player import Jogador
from src.runtime.domain.world.scenarios import Cenario

pygame.font.init()


@pytest.mark.parametrize('nome', ['prisma', 'oraculo', 'obelisco'])
def test_imagem_do_boss_tem_alpha_e_quadro_em_cache(nome):
    from src.runtime.infrastructure.graphics.boss_art import quadro_boss

    arte = pygame.image.load(f'images/bosses/{nome}.png')
    assert arte.get_at((0, 0)).a == 0
    sprite = quadro_boss(nome.upper(), 128, 0)
    assert sprite is not None and max(sprite.get_size()) == 128
    assert sprite is quadro_boss(nome.upper(), 128, 0)
    assert sprite.get_at((0, 0)).a == 0


@pytest.mark.parametrize('cid', [7, 8, 9])
def test_aviso_do_boss_preserva_alvo_ate_o_disparo(cid):
    boss = Boss(cid * 5, Cenario(cid))
    boss.entrando = False
    boss.x, boss.y = 640, 150
    alvo = Jogador()
    boss.timer_ataque = 31
    boss.atualizar(alvo)
    assert boss.aviso_ataques
    alvo_salvo = boss.alvo_ataque
    alvo.x -= 300
    boss.timer_ataque = 1
    # O plano usa o mesmo alvo anunciado, mesmo se a nave sair da linha.
    with patch.object(boss, '_executar_ataque', wraps=boss._executar_ataque) as ataque:
        tiros = boss.atualizar(alvo)
    assert tiros
    assert (ataque.call_args.args[1].x, ataque.call_args.args[1].y) == alvo_salvo
    assert not boss.aviso_ataques
    antes = (boss.rect.copy(), boss.vida, boss.timer_ataque)
    boss.desenhar(pygame.Surface((1280, 720)), efeitos_reduzidos=True)
    assert (boss.rect, boss.vida, boss.timer_ataque) == antes


@pytest.mark.parametrize('nivel', [13, 33, 42])
def test_fase_alcancada_persiste_e_pode_retornar_ao_lobby(tmp_path, monkeypatch, nivel):
    monkeypatch.setenv('INCARNATE_DATA_DIR', str(tmp_path))
    jogo = Jogo(sons=Mock())
    perfil = jogo.profile_service.create('Piloto')
    jogo.ativar_perfil(perfil.id)
    jogo._novo_jogo('Piloto')
    jogo.progresso.campanha['fases_concluidas'] = list(range(1, (nivel - 1) // 5 + 1))
    jogo._iniciar_nivel(nivel)
    reiniciado = Jogo(sons=Mock())
    reiniciado.ativar_perfil(perfil.id)
    assert reiniciado.progresso.campanha['nivel_atual'] == nivel
    jogo.estado = EstadoJogo.PAUSA
    jogo.pausa_controller.confirmar_saida()
    assert jogo.estado is EstadoJogo.MENU
    assert jogo.menu.subestado == 'FASES'
    tela = jogo.menu.phase_screen
    assert tela.selected == (nivel - 1) // 5
    assert tela.confirm()
    assert jogo.jogador.nivel == nivel


def test_falha_de_save_mantem_partida_na_pausa(tmp_path, monkeypatch):
    monkeypatch.setenv('INCARNATE_DATA_DIR', str(tmp_path))
    jogo = Jogo(sons=Mock())
    perfil = jogo.profile_service.create('Piloto')
    jogo.ativar_perfil(perfil.id)
    jogo.estado = EstadoJogo.PAUSA
    with patch.object(jogo.profile_service.repository, 'save', return_value=False):
        jogo.pausa_controller.confirmar_saida()
    assert jogo.estado is EstadoJogo.PAUSA
