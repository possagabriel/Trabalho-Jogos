"""Navegação de confirmações e geometria compartilhada da pausa ORIGINAL."""

from types import SimpleNamespace
from unittest.mock import Mock

import pygame
import pytest

from src.infrastructure.graphics.comic_theme import usar_visual
from src.infrastructure.graphics.theme import tema_atual
from src.infrastructure.ui.layout import Layout
from src.runtime.controllers.pause import ControladorPausa
from src.runtime.presentation.menu import Dialogo


@pytest.fixture(autouse=True)
def video():
    pygame.font.init()
    pygame.display.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))


def test_confirmacao_permitem_escolher_cancelar_pelo_teclado():
    confirmar, cancelar = Mock(), Mock()
    dialogo = Dialogo("Sair", "Deseja encerrar?", confirmar, cancelar)
    dialogo.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    dialogo.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    cancelar.assert_called_once()
    confirmar.assert_not_called()


def test_mouse_muda_foco_e_enter_executa_uma_unica_vez():
    confirmar, cancelar = Mock(), Mock()
    dialogo = Dialogo("Sair", "Deseja encerrar?", confirmar, cancelar)
    _, botao = dialogo._retangulos()
    dialogo.tratar_evento(pygame.event.Event(pygame.MOUSEMOTION, pos=botao.center))
    dialogo.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    dialogo.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    cancelar.assert_called_once()
    confirmar.assert_not_called()


def test_dialogo_original_desenha_sem_botoes_cartoon():
    layout = Layout(900, 700)
    dialogo = Dialogo("Sair da missão", "A sessão será salva ao voltar ao menu.",
                     Mock(), Mock(), layout)
    dialogo._desenhar_botao_cartoon = Mock()
    tela = pygame.Surface((900, 700), pygame.SRCALPHA)
    with usar_visual({"estilo_visual": "ORIGINAL"}):
        dialogo.desenhar(tela, layout.fonte_titulo(32), layout.fonte_texto(22),
                         tema=tema_atual("NEON"))
    dialogo._desenhar_botao_cartoon.assert_not_called()
    confirmar, cancelar = dialogo._retangulos()
    assert dialogo._rect.contains(confirmar) and dialogo._rect.contains(cancelar)
    assert not confirmar.colliderect(cancelar)


def test_pausa_original_compartilha_area_dos_botoes_com_controlador():
    from src.runtime.presentation.screens.pause_screen import geometria_pausa

    layout = Layout()
    painel, botoes = geometria_pausa(layout)
    jogo = SimpleNamespace(config={"estilo_visual": "ORIGINAL"}, layout=layout)
    controlador = ControladorPausa(jogo)
    for indice, botao in enumerate(botoes):
        assert painel.contains(botao)
        assert controlador.colidir_opcao(botao.center) == indice


@pytest.mark.parametrize("configuracoes", [False, True])
def test_pausa_original_renderiza_sessao_e_configuracoes(configuracoes):
    from src.runtime.presentation.screens.pause_screen import desenhar_pausa_original

    layout = Layout(900, 700)
    jogo = SimpleNamespace(
        layout=layout, tela=pygame.Surface((900, 700), pygame.SRCALPHA),
        _pausa_selecao=2, _pausa_config_selecao=1,
        jogador=SimpleNamespace(nivel=7, pontuacao=1234, skin=SimpleNamespace(nome="Fênix")),
        config={"musica_volume": 0, "efeitos_volume": 0, "tema": "NEON", "tela_cheia": False})
    desenhar_pausa_original(jogo, tema_atual("NEON"), configuracoes=configuracoes)
    assert jogo.tela.get_bounding_rect().width > 300


def test_configuracao_original_usa_mesma_linha_para_clique():
    from src.runtime.presentation.screens.pause_screen import geometria_config_pausa

    layout = Layout(900, 700)
    jogo = SimpleNamespace(layout=layout, config={"estilo_visual": "ORIGINAL"})
    controlador = ControladorPausa(jogo)
    controlador.ajustar_config = Mock()
    for indice, linha in enumerate(geometria_config_pausa(layout)[1]):
        controlador.clique_config(linha.center)
        controlador.ajustar_config.assert_called_with(indice, 1)
