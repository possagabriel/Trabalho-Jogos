"""Navegação, geometria e ajustes da configuração orbital ORIGINAL."""

from copy import deepcopy
from unittest import mock

import pygame
import pytest

from src.infrastructure.graphics.comic_theme import usar_visual
from src.infrastructure.ui.layout import Layout
from src.runtime.presentation.screens.settings_view import (
    CATEGORIAS_CONFIG,
    categoria_config,
    geometria_config_original,
)


def nova_configuracao(estilo="ORIGINAL"):
    from game.core import Jogo

    jogo = Jogo()
    jogo.config.salvar = mock.Mock(return_value=True)
    jogo.config["estilo_visual"] = estilo
    jogo.menu._abrir_config()
    jogo.menu.sub_anim = jogo.menu.sub_anim_total
    return jogo, jogo.menu.tela_configuracoes


def tecla(tela, codigo, mod=0):
    tela.tratar_tecla(pygame.event.Event(pygame.KEYDOWN, key=codigo, mod=mod))


def test_categorias_contem_todas_as_opcoes_sem_duplicar():
    from src.runtime.presentation.menu import MenuPrincipal

    indices = [indice for _nome, grupo in CATEGORIAS_CONFIG for indice in grupo]
    assert sorted(indices) == list(range(len(MenuPrincipal._LINHAS_CONFIG)))
    for categoria, (_nome, grupo) in enumerate(CATEGORIAS_CONFIG):
        assert grupo
        assert all(categoria_config(indice) == categoria for indice in grupo)


@pytest.mark.parametrize("tamanho", [(900, 700), (1280, 720), (1920, 1080)])
def test_abas_lista_e_contexto_cabem_sem_sobreposicao(tamanho):
    layout = Layout(*tamanho)
    grade = geometria_config_original(layout)
    tela = pygame.Rect((0, 0), tamanho)
    assert tela.contains(grade.painel)
    assert grade.painel.contains(grade.lista)
    assert grade.painel.contains(grade.contexto)
    assert not grade.lista.colliderect(grade.contexto)
    assert len(grade.abas) == len(CATEGORIAS_CONFIG)
    for indice, aba in enumerate(grade.abas):
        assert grade.painel.contains(aba)
        assert not aba.colliderect(grade.lista)
        assert not aba.colliderect(grade.contexto)
        assert all(not aba.colliderect(outra) for outra in grade.abas[indice + 1:])


def test_tab_e_setas_percorrem_todas_as_opcoes_sem_alterar_config():
    jogo, tela = nova_configuracao()
    antes = deepcopy(jogo.config._dados)
    visitadas = set()
    with mock.patch.object(jogo.config, "salvar") as salvar:
        for _nome, grupo in CATEGORIAS_CONFIG:
            for _ in grupo:
                visitadas.add(jogo.menu.config_selecao)
                assert jogo.menu.config_selecao in tela.indices_visiveis_original()
                tecla(tela, pygame.K_DOWN)
            tecla(tela, pygame.K_TAB)
        assert jogo.menu.config_selecao == 0
        tecla(tela, pygame.K_TAB, pygame.KMOD_SHIFT)
        assert categoria_config(jogo.menu.config_selecao) == len(CATEGORIAS_CONFIG) - 1
        salvar.assert_not_called()
    assert visitadas == set(range(29))
    assert jogo.config._dados == antes


def test_clique_no_rotulo_ou_fora_do_painel_nao_altera_volume():
    jogo, tela = nova_configuracao()
    rect = tela.original.linhas()[0][1]
    antes = jogo.config["musica_volume"]
    tela.tratar_clique((rect.left + 10, rect.centery))
    tela.tratar_clique((0, rect.centery))
    assert jogo.config["musica_volume"] == antes


@pytest.mark.parametrize("estilo", ["ORIGINAL", "COMIC"])
def test_arrastar_slider_mostra_previa_e_aplica_ao_soltar(monkeypatch, estilo):
    jogo, tela = nova_configuracao(estilo)
    menu = jogo.menu
    monkeypatch.setattr(menu, "_pos_logica", lambda pos: pos)
    rect = tela.original.linhas()[0][1]
    x0, x1 = tela.original.trilha_slider()
    tela.tratar_clique((x0, rect.centery))
    assert jogo.config["musica_volume"] == 0
    with mock.patch.object(jogo.config, "salvar") as salvar:
        menu.tratar_eventos(pygame.event.Event(
            pygame.MOUSEMOTION, pos=(x1, rect.centery), buttons=(1, 0, 0)))
        assert jogo.config["musica_volume"] == 0
        assert tela.valor_opcao(0) == "100%"
        salvar.assert_not_called()
        menu.tratar_eventos(pygame.event.Event(
            pygame.MOUSEBUTTONUP, button=1, pos=(x1, rect.centery)))
        assert jogo.config["musica_volume"] == 1
        salvar.assert_called_once()


def test_abas_e_roda_do_mouse_navegam_sem_mudar_valores():
    jogo, tela = nova_configuracao()
    abas = tela.original.geometria().abas
    with mock.patch.object(jogo.config, "salvar") as salvar:
        tela.tratar_clique(abas[2].center)
        assert jogo.menu.config_selecao == 4
        jogo.menu.tratar_eventos(pygame.event.Event(pygame.MOUSEWHEEL, y=-1, x=0))
        assert jogo.menu.config_selecao == 5
        tecla(tela, pygame.K_RETURN)
        assert jogo.menu.config_submodo == "controles"
        tecla(tela, pygame.K_ESCAPE)
        assert jogo.menu.config_submodo is None
        salvar.assert_not_called()


@pytest.mark.parametrize("estilo", ["ORIGINAL", "COMIC"])
def test_resolucao_original_exige_confirmacao_e_permite_reverter(monkeypatch, estilo):
    jogo, tela = nova_configuracao(estilo)
    menu = jogo.menu
    monkeypatch.setattr(jogo, "_aplicar_modo_video", lambda: None)
    anterior = jogo.config["resolucao"]
    tecla(tela, pygame.K_TAB)
    tecla(tela, pygame.K_RETURN)
    assert menu.config_submodo == "resolucao"
    indice, rect = tela.original.linhas_submodo("resolucao")[0]
    destino = pygame.Surface((menu.layout.largura, menu.layout.altura), pygame.SRCALPHA)
    with mock.patch.object(jogo.config, "salvar") as salvar:
        tela.tratar_clique(rect.center)
        assert menu._resolucao_pendente["resolucao"] == anterior
        assert menu.resolucao_selecao == indice
        salvar.assert_not_called()
        with usar_visual(jogo.config):
            menu._desenhar_confirmacao_resolucao(destino, {})
        menu.tratar_eventos(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        assert jogo.config["resolucao"] == anterior
        assert menu._resolucao_pendente is None
        salvar.assert_not_called()
        tela.tratar_clique(rect.center)
        menu.tratar_eventos(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        assert menu._resolucao_pendente is None
        salvar.assert_called_once()


def test_remapeamento_original_abre_por_clique_e_escape_cancela():
    jogo, tela = nova_configuracao()
    menu = jogo.menu
    menu.config_submodo = "controles"
    rect = tela.original.linhas_submodo("controles")[0][1]
    tecla_anterior = jogo.config.controles["cima"]
    tela.tratar_clique(rect.center)
    assert menu.remapando == "cima"
    menu.tratar_eventos(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert menu.remapando is None
    assert menu.config_submodo == "controles"
    assert jogo.config.controles["cima"] == tecla_anterior
    tela.tratar_clique(menu._botoes_rodape(["VOLTAR"])[0].rect.center)
    assert menu.config_submodo is None


def test_atalho_de_salvar_e_seta_esquerda_nos_controles_ligado_desligado():
    jogo, tela = nova_configuracao()
    with mock.patch.object(jogo.config, "salvar") as salvar:
        tecla(tela, pygame.K_s, pygame.KMOD_CTRL)
        salvar.assert_called_once()
    with mock.patch.object(jogo.menu, "_toggle_tela_cheia") as alternar:
        jogo.menu.config_selecao = 3
        tecla(tela, pygame.K_LEFT)
        alternar.assert_called_once()


@pytest.mark.parametrize("tamanho", [(900, 700), (1920, 1080)])
@pytest.mark.parametrize("estilo", ["ORIGINAL", "COMIC"])
def test_desenho_de_todas_as_opcoes_e_subtelas_preserva_valores(tamanho, estilo):
    jogo, tela = nova_configuracao(estilo)
    menu = jogo.menu
    menu.layout = Layout(*tamanho)
    antes = deepcopy(jogo.config._dados)
    destino = pygame.Surface(tamanho, pygame.SRCALPHA)
    with usar_visual({"estilo_visual": estilo, "intensidade_flash": "REDUZIDO"}):
        for indice in range(29):
            menu.config_selecao = indice
            assert tela.valor_opcao(indice)
            tela.desenhar(destino)
            for _indice, rect in tela.original.linhas():
                assert tela.original.geometria().lista.contains(rect)
        for submodo in ("controles", "resolucao", "ajuste"):
            menu.config_submodo = submodo
            tela.desenhar(destino)
        menu.config_submodo, menu.remapando = "controles", "atirar"
        tela.desenhar(destino)
    assert jogo.config._dados == antes
