"""Testes do kit de UI e da tela-piloto de Recordes."""

from __future__ import annotations

import pygame
import pytest

from src.infrastructure.graphics.comic_theme import PAPEL, usar_visual
from src.infrastructure.graphics.theme import TEMAS_CORES
from src.infrastructure.ui.layout import Layout
from src.runtime.presentation.components import (
    BarraRolagem,
    Botao,
    CabecalhoTela,
    EstadoVazio,
    ItemLista,
    Lista,
    Painel,
    RodapeAcoes,
    tokens_para,
)
from src.runtime.presentation.components.primitives import (
    desenhar_caixa,
    fonte,
    medir_texto,
    truncar_texto,
)


@pytest.fixture(scope="module", autouse=True)
def _video_headless():
    pygame.display.init()
    pygame.font.init()
    pygame.display.set_mode((1, 1))
    yield


def _surface() -> pygame.Surface:
    return pygame.Surface((900, 700), pygame.SRCALPHA)


def test_tokens_resolvem_estilo_e_tema():
    original = tokens_para("ORIGINAL", "MAGMA")
    comic = tokens_para("COMIC")
    assert original.estilo == "ORIGINAL"
    assert comic.estilo == "COMIC"
    assert original.superficie.borda == TEMAS_CORES["MAGMA"]["secundaria"]
    assert comic.superficie.fundo == PAPEL
    assert original.superficie.glow > comic.superficie.glow


def test_painel_original_cacheado_tem_profundidade_e_cantos_transparentes():
    from src.runtime.infrastructure.graphics.menu_panels import painel_original

    fundo, borda = (6, 12, 28), (70, 190, 220)
    normal = painel_original((300, 80), fundo, borda)
    foco = painel_original((300, 80), fundo, borda, selecionado=True)
    assert normal is painel_original((300, 80), fundo, borda)
    assert normal.get_at((0, 0)).a == 0
    assert normal.get_at((150, 12)) != normal.get_at((150, 65))
    assert pygame.image.tobytes(normal, "RGBA") != pygame.image.tobytes(foco, "RGBA")
    antes = pygame.image.tobytes(normal, "RGBA")
    _surface().blit(normal, (20, 20))
    assert pygame.image.tobytes(normal, "RGBA") == antes


@pytest.mark.parametrize("estilo", ["ORIGINAL", "COMIC"])
def test_painel_desenha_com_cabecalho_e_area_de_conteudo(estilo):
    layout = Layout(900, 700)
    tela = _surface()
    painel = Painel(
        (80, 80, 520, 320),
        titulo="ARQUIVO DE VOO",
        subtitulo="// TESTE",
    )
    with usar_visual({"estilo_visual": estilo}):
        painel.desenhar(tela, layout)
    area = painel.area_conteudo(layout)
    assert area.top > painel.rect.top
    assert area.left > painel.rect.left
    assert area.right < painel.rect.right
    assert area.bottom < painel.rect.bottom


@pytest.mark.parametrize("estilo", ["ORIGINAL", "COMIC"])
def test_botao_atualiza_hover_foco_e_desenha(estilo):
    layout = Layout(900, 700)
    tela = _surface()
    botao = Botao("VOLTAR", (100, 100, 160, 46), foco=True)
    botao.atualizar((120, 120))
    assert botao.hover is True
    with usar_visual({"estilo_visual": estilo}):
        botao.desenhar(tela, layout)
    botao.atualizar((0, 0))
    assert botao.hover is False


def test_lista_rola_seleciona_e_desenha_estado_vazio():
    layout = Layout(900, 700)
    tk = tokens_para("ORIGINAL")
    tela = _surface()
    itens = [
        ItemLista(titulo=f"PILOTO {indice}", subtitulo="NV 01", valor="100")
        for indice in range(20)
    ]
    lista = Lista(
        (20, 20, 240, 100),
        itens,
        altura_linha=20,
        espaco=2,
        estado_vazio=EstadoVazio("VAZIO", "Nada por aqui."),
    )
    assert lista.max_offset(layout, tk) > 0
    lista.rolar(10_000, layout, tk)
    assert lista.offset == lista.max_offset(layout, tk)
    lista.mover_selecao(19, layout, tk)
    assert lista.selecao == 19
    lista.desenhar(tela, layout, tokens=tk)
    vazia = Lista((20, 20, 240, 100), [], estado_vazio=EstadoVazio("VAZIO"))
    vazia.desenhar(tela, layout, tokens=tk)


def test_barra_de_rolagem_proporcional():
    layout = Layout(900, 700)
    barra = BarraRolagem()
    area = pygame.Rect(0, 0, 200, 100)
    trilho, topo = barra.geometria(area, 100, 20, 0, layout)
    _, fundo = barra.geometria(area, 100, 20, 80, layout)
    assert topo is not None and fundo is not None
    assert trilho.right <= area.right
    assert fundo.y > topo.y
    _, sem_rolagem = barra.geometria(area, 10, 20, 0, layout)
    assert sem_rolagem is None


def test_cabecalho_rodape_e_caixa_desenham_nos_dois_estilos():
    layout = Layout(900, 700)
    tela = _surface()
    for estilo in ("ORIGINAL", "COMIC"):
        with usar_visual({"estilo_visual": estilo}):
            CabecalhoTela("RECORDES").desenhar(tela, layout)
            RodapeAcoes([Botao("VOLTAR", (300, 600, 160, 46))]).desenhar(
                tela, layout
            )
            desenhar_caixa(
                tela,
                pygame.Rect(20, 20, 100, 40),
                (10, 20, 30),
                borda=(200, 200, 200),
            )


def _novo_menu():
    from game.core import Jogo

    jogo = Jogo()
    menu = jogo.menu
    menu.alpha_entrada = 255
    return jogo, menu


@pytest.mark.parametrize("estilo", ["ORIGINAL", "COMIC"])
def test_recordes_usa_kit_e_preserva_hitbox_do_voltar(estilo):
    jogo, menu = _novo_menu()
    jogo.recordes = [
        {"nome": f"Piloto {indice}", "nivel": indice + 1, "pontos": 1000 - indice}
        for indice in range(5)
    ]
    tela = pygame.Surface(jogo.tela_ui.get_size(), pygame.SRCALPHA)
    with usar_visual({"estilo_visual": estilo}):
        menu.tela_recordes.desenhar(tela)
    esperado = menu._botoes_rodape(["VOLTAR"])[0].rect
    assert menu.tela_recordes.botao_voltar().rect == esperado


def test_recordes_sem_registros_desenha_estado_vazio():
    jogo, menu = _novo_menu()
    jogo.recordes = []
    tela = pygame.Surface(jogo.tela_ui.get_size(), pygame.SRCALPHA)
    with usar_visual({"estilo_visual": "COMIC"}):
        menu.tela_recordes.desenhar(tela)


@pytest.mark.parametrize("estilo", ["ORIGINAL", "COMIC"])
def test_truncar_texto_respeita_largura_disponivel(estilo):
    layout = Layout(900, 700)
    tk = tokens_para(estilo)
    fonte_teste = fonte(layout, tk.tipografia.corpo, tokens=tk)
    texto = "ARVORE ESTELAR 9NV 18"
    largura = medir_texto("ARVORE", fonte_teste, tokens=tk)

    cortado = truncar_texto(texto, fonte_teste, largura, tokens=tk)

    assert cortado != texto
    assert cortado.endswith("…")
    assert medir_texto(cortado, fonte_teste, tokens=tk) <= largura


@pytest.mark.parametrize("estilo", ["ORIGINAL", "COMIC"])
def test_tipografia_secundaria_legivel_em_900x700(estilo):
    layout = Layout(1280, 720)
    tk = tokens_para(estilo)
    escala_saida = 900 / 1280
    for tamanho in (tk.tipografia.legenda, tk.tipografia.subtitulo):
        fonte_teste = fonte(layout, tamanho, tokens=tk)
        altura = fonte_teste.render("Ag0", True, (255, 255, 255)).get_bounding_rect().height
        assert altura * escala_saida >= 10.5
