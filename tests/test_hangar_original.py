"""Geometria, estados e apresentação do hangar orbital ORIGINAL."""

import pygame
import pytest

from src.infrastructure.graphics.comic_theme import usar_visual
from src.infrastructure.ui.layout import Layout
from src.runtime.presentation.screens.store_screen import geometria_hangar_original


@pytest.mark.parametrize("tamanho", [(900, 700), (1280, 720), (1920, 1080)])
def test_grade_e_expositor_cabem_sem_sobreposicao(tamanho):
    layout = Layout(*tamanho)
    painel = pygame.Rect(layout.px(40), layout.px(108),
                          layout.largura - layout.px(80), layout.altura - layout.px(210))
    cards, expositor = geometria_hangar_original(layout, painel, 10)
    assert len(cards) == 10
    assert len({rect.x for rect in cards}) == 4
    assert painel.contains(expositor)
    for indice, rect in enumerate(cards):
        assert painel.contains(rect)
        assert not rect.colliderect(expositor)
        assert all(not rect.colliderect(outro) for outro in cards[indice + 1:])


def novo_hangar():
    from game.core import Jogo

    jogo = Jogo()
    jogo.config["estilo_visual"] = "ORIGINAL"
    jogo.menu.subestado = "LOJA"
    return jogo, jogo.menu.tela_loja


def test_expositor_reflete_compra_e_equipagem_sem_modificar_progresso():
    jogo, hangar = novo_hangar()
    loja = jogo.loja
    jogo.menu.loja_selecao = 1
    loja.moedas = 100
    antes = (loja.moedas, loja.skin_atual, loja.lista_desbloqueadas())
    estado, detalhe, acao = hangar.estado_selecao()
    assert estado == "BLOQUEADA" and "400" in detalhe and acao == "comprar"
    assert antes == (loja.moedas, loja.skin_atual, loja.lista_desbloqueadas())
    loja.moedas = 500
    assert hangar.estado_selecao()[1] == "PRONTO PARA COMPRAR"
    assert loja.comprar_skin(1)[0]
    assert hangar.estado_selecao() == ("LIBERADA", "PRONTO PARA EQUIPAR", "equipar")
    assert loja.equipar_skin(1)
    assert hangar.estado_selecao() == ("EM USO", "VISUAL EQUIPADO", "prévia")


def test_desenho_e_selecao_do_hangar_nao_gastam_moedas_nem_equipam():
    jogo, hangar = novo_hangar()
    menu = jogo.menu
    menu.sub_anim = menu.sub_anim_total
    antes = (jogo.loja.moedas, jogo.loja.skin_atual, jogo.loja.lista_desbloqueadas())
    tela = pygame.Surface((menu.layout.largura, menu.layout.altura), pygame.SRCALPHA)
    with usar_visual({"estilo_visual": "ORIGINAL"}):
        for indice in range(len(jogo.loja.skins)):
            hangar.tratar_clique(menu._rects_loja()[indice].center)
            assert menu.loja_selecao == indice
            hangar.desenhar(tela)
    assert antes == (jogo.loja.moedas, jogo.loja.skin_atual, jogo.loja.lista_desbloqueadas())


def test_botao_previa_abre_skin_bloqueada_e_escape_fecha_sem_equipar():
    jogo, hangar = novo_hangar()
    menu = jogo.menu
    menu.loja_selecao = 1
    antes = (jogo.loja.moedas, jogo.loja.skin_atual, jogo.loja.lista_desbloqueadas())
    hangar.tratar_clique(menu._botoes_loja()["prévia"].rect.center)
    assert menu.preview_skin is jogo.loja.skins[1]
    tela = pygame.Surface((menu.layout.largura, menu.layout.altura), pygame.SRCALPHA)
    with usar_visual({"estilo_visual": "ORIGINAL"}):
        hangar.desenhar(tela)
    hangar.tratar_tecla(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    assert menu.preview_skin is jogo.loja.skins[1]
    equipar = (menu.layout.x(.5) - menu.layout.px(90),
               menu.layout.altura - menu.layout.px(96))
    hangar.tratar_clique(equipar)
    assert menu.preview_skin is jogo.loja.skins[1]
    hangar.tratar_tecla(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert menu.preview_skin is None
    assert antes == (jogo.loja.moedas, jogo.loja.skin_atual, jogo.loja.lista_desbloqueadas())
