"""Mesma estrutura de menus, com acabamentos ORIGINAL e COMIC independentes."""

from copy import deepcopy
from unittest import mock

import pygame
import pytest

from src.infrastructure.graphics.comic_theme import LARANJA, PAPEL, SOMBRA, TINTA, usar_visual
from src.runtime.infrastructure.graphics.menu_panels import (
    ACENTO_ORIGINAL,
    TEXTO_ATIVO_ORIGINAL,
    TEXTO_ORIGINAL,
    cor_menu,
    painel_menu,
)


def novo_menu():
    from game.core import Jogo

    jogo = Jogo()
    jogo.config.salvar = mock.Mock(return_value=True)
    jogo.menu.entrada_t = jogo.menu.entrada_total
    jogo.menu.sub_anim = jogo.menu.sub_anim_total
    return jogo, jogo.menu


def test_paineis_compartilham_area_com_acabamento_e_cache_independentes():
    argumentos = ((320, 64), (0, 0, 0), ACENTO_ORIGINAL)
    with usar_visual({"estilo_visual": "ORIGINAL"}):
        original = painel_menu(*argumentos, selecionado=True, botao=True)
    with usar_visual({"estilo_visual": "COMIC"}):
        comic = painel_menu(*argumentos, selecionado=True, botao=True)
        assert comic is painel_menu(*argumentos, selecionado=True, botao=True)
        assert comic.get_at((160, 32))[:3] == LARANJA
    with usar_visual({"estilo_visual": "ORIGINAL"}):
        assert original is painel_menu(*argumentos, selecionado=True, botao=True)
        assert original.get_at((160, 32))[:3] == ACENTO_ORIGINAL
    assert comic is not original
    assert comic.get_size() == original.get_size() == (320, 64)
    assert comic.get_bounding_rect() == original.get_bounding_rect()


def test_comic_respeita_texturas_e_contraste_do_texto_essencial():
    with usar_visual({"estilo_visual": "COMIC", "comic_papel": False, "comic_halftone": False}):
        sem_textura = painel_menu((320, 100), SOMBRA, LARANJA)
        assert cor_menu(TEXTO_ORIGINAL) == PAPEL
        assert cor_menu(TEXTO_ATIVO_ORIGINAL) == TINTA
    with usar_visual({"estilo_visual": "COMIC", "comic_papel": True, "comic_halftone": True}):
        texturado = painel_menu((320, 100), SOMBRA, LARANJA)
    assert pygame.image.tobytes(sem_textura, "RGBA") != pygame.image.tobytes(texturado, "RGBA")

    def luminancia(cor):
        canais = [v / 255 for v in cor]
        linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in canais]
        return sum(a * b for a, b in zip(linear, (.2126, .7152, .0722)))

    for texto, fundo in ((PAPEL, SOMBRA), (TINTA, LARANJA)):
        maior, menor = sorted((luminancia(texto), luminancia(fundo)), reverse=True)
        assert (maior + .05) / (menor + .05) >= 4.5


def test_comic_mostra_contexto_e_configuracoes_com_a_mesma_estrutura():
    jogo, menu = novo_menu()
    jogo.config["estilo_visual"] = "COMIC"
    destino = pygame.Surface((menu.layout.largura, menu.layout.altura), pygame.SRCALPHA)
    with usar_visual(jogo.config), \
            mock.patch.object(menu.tela_principal, "desenhar_contexto_original") as contexto:
        menu.tela_principal.desenhar(destino)
        contexto.assert_called_once()
    menu._abrir_config()
    with mock.patch.object(menu.tela_configuracoes.original, "desenhar") as painel:
        menu.tela_configuracoes.desenhar(destino)
        painel.assert_called_once_with(destino)


def test_comic_e_original_compartilham_o_hangar_sem_trocar_o_estilo_do_jogo():
    jogo, menu = novo_menu()
    jogo.config["estilo_visual"] = "ORIGINAL"
    original = menu._rects_loja()
    jogo.config["estilo_visual"] = "COMIC"
    assert menu._rects_loja() == original
    menu.subestado = "LOJA"
    destino = pygame.Surface((menu.layout.largura, menu.layout.altura), pygame.SRCALPHA)
    antes = deepcopy(jogo.config._dados)
    with usar_visual(jogo.config), mock.patch(
            "src.runtime.presentation.screens.store_screen.miniatura_nave") as miniatura:
        miniatura.return_value = pygame.Surface((32, 32), pygame.SRCALPHA)
        menu.tela_loja.desenhar(destino)
        assert miniatura.call_count > 10
        assert all(chamada.args[2] is True for chamada in miniatura.call_args_list)
    assert jogo.config._dados == antes


@pytest.mark.parametrize("estilo", ["ORIGINAL", "COMIC"])
def test_menus_e_subtelas_preservam_preferencias_e_progresso(estilo):
    jogo, menu = novo_menu()
    jogo.config["estilo_visual"] = estilo
    menu.alpha_entrada = 255
    antes = deepcopy(jogo.config._dados)
    progresso = (jogo.loja.moedas, jogo.loja.skin_atual, jogo.loja.lista_desbloqueadas())
    with usar_visual(jogo.config):
        for estado in ("MENU", "JOGAR", "PERFIL", "LOJA", "CONFIG", "RECORDES"):
            menu.subestado = estado
            menu.desenhar(jogo.tela)
    assert jogo.config._dados == antes
    assert progresso == (jogo.loja.moedas, jogo.loja.skin_atual, jogo.loja.lista_desbloqueadas())
