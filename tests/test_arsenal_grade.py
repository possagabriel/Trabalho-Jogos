"""Navegação espacial do arsenal e geometria compartilhada das cartas."""

from unittest.mock import Mock

import pygame
import pytest

from src.infrastructure.graphics.comic_theme import usar_visual
from src.infrastructure.ui.layout import Layout
from src.runtime.application.core import Jogo
from src.runtime.presentation.equipment_overlay import (
    desenhar_menu_equipamento,
    geometria_equipamento,
    mover_selecao_equipamento,
)


@pytest.mark.parametrize('inicio,direcao,fim', [
    ((0, 0), (0, 1), (0, 3)),
    ((0, 4), (0, 1), (0, 7)),
    ((0, 7), (0, 1), (1, 1)),
    ((1, 1), (0, -1), (0, 7)),
    ((0, 8), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (0, 1)),
    ((0, 1), (-1, 0), (0, 0)),
])
def test_setas_seguem_fileiras_e_colunas(inicio, direcao, fim):
    assert mover_selecao_equipamento(*inicio, (9, 2), direcao) == fim


def test_listas_vazias_nao_bloqueiam_navegacao():
    assert mover_selecao_equipamento(0, 0, (0, 0), (0, 1)) == (0, 0)
    assert mover_selecao_equipamento(0, 0, (0, 2), (1, 0)) == (1, 1)


@pytest.mark.parametrize('tamanho', [(900, 700), (1920, 1080)])
@pytest.mark.parametrize('estilo', ['ORIGINAL', 'COMIC'])
def test_catalogo_cabe_e_preview_nao_sobrepoe_cartas(tamanho, estilo):
    jogo = Jogo(sons=Mock())
    jogo.layout = Layout(*tamanho)
    jogo.tela = pygame.Surface(tamanho)
    jogo._sombra_equipamento = pygame.Surface(tamanho)
    jogo.jogador.armas_desbloqueadas = list(range(9))
    jogo.especiais_desbloqueados = ['bomba', 'intangivel', 'cura', 'imortal']
    g = geometria_equipamento(jogo.layout, (9, 4))
    cartas = g.armas + g.especiais
    assert len(cartas) == 13
    for i, rect in enumerate(cartas):
        assert g.painel.contains(rect)
        assert not rect.colliderect(g.detalhe)
        assert not rect.colliderect(g.rodape)
        assert not any(rect.colliderect(outro) for outro in cartas[i + 1:])
    with usar_visual({'estilo_visual': estilo}):
        desenhar_menu_equipamento(jogo)


def test_teclas_descem_antes_de_trocar_secao_e_equipam():
    jogo = Jogo(sons=Mock())
    jogo.jogador.armas_desbloqueadas = list(range(9))
    jogo.menu_equipamento = True
    jogo.linha_equipamento, jogo.indice_equipamento = 0, 1
    jogo._tratar_menu_equipamento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN))
    assert (jogo.linha_equipamento, jogo.indice_equipamento) == (0, 4)
    jogo._tratar_menu_equipamento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    assert jogo.jogador.arma_atual == 4
    jogo._tratar_menu_equipamento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert not jogo.menu_equipamento
