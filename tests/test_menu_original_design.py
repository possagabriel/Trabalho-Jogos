"""Nova linguagem visual do ORIGINAL com a disposição anterior em coluna."""

import pygame
import pytest

from src.runtime.infrastructure.graphics.menu_panels import (
    ACENTO_ORIGINAL,
    PAINEL_ORIGINAL,
    TEXTO_ATIVO_ORIGINAL,
    TEXTO_ORIGINAL,
    icone_menu_original,
    painel_original,
)


def test_botao_original_usa_recortes_e_selecao_ambar_com_texto_escuro():
    normal = painel_original((320, 64), (0, 0, 0), (0, 0, 0), botao=True)
    ativo = painel_original((320, 64), (0, 0, 0), (0, 0, 0),
                             botao=True, selecionado=True)
    assert normal.get_at((319, 0)).a == 0
    assert normal.get_at((0, 63)).a == 0
    assert ativo.get_at((160, 32))[:3] == ACENTO_ORIGINAL
    assert max(TEXTO_ATIVO_ORIGINAL) < 50
    assert ACENTO_ORIGINAL[0] > 220 and ACENTO_ORIGINAL[1] > 150
    antes = pygame.image.tobytes(ativo, "RGBA")
    assert ativo is painel_original((320, 64), (0, 0, 0), (0, 0, 0),
                                     botao=True, selecionado=True)
    assert antes == pygame.image.tobytes(ativo, "RGBA")


def test_icones_dos_cinco_destinos_sao_distintos_e_cacheados():
    artes = [icone_menu_original(str(i), False, 32) for i in range(1, 6)]
    assert len({pygame.image.tobytes(arte, "RGBA") for arte in artes}) == 5
    assert all(arte.get_bounding_rect().w > 8 for arte in artes)
    assert artes[0] is icone_menu_original("1", False, 32)


def test_textos_essenciais_tem_contraste_minimo_em_ambos_os_estados():
    def luminancia(cor):
        canais = [v / 255 for v in cor]
        linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
                  for v in canais]
        return sum(a * b for a, b in zip(linear, (.2126, .7152, .0722)))

    for texto, fundo in ((TEXTO_ORIGINAL, PAINEL_ORIGINAL),
                          (TEXTO_ATIVO_ORIGINAL, ACENTO_ORIGINAL)):
        maior, menor = sorted((luminancia(texto), luminancia(fundo)), reverse=True)
        assert (maior + .05) / (menor + .05) >= 4.5


@pytest.mark.parametrize("resolucao", ["900x700", "1920x1080"])
def test_descricao_da_acao_cabe_entre_titulo_perfil_e_botoes(resolucao):
    from game.core import Jogo

    jogo = Jogo()
    menu = jogo.menu
    jogo.config["estilo_visual"] = "ORIGINAL"
    jogo.config["resolucao"] = resolucao
    menu._aplicar_layout_opcoes()
    painel = menu.tela_principal.contexto_rect()
    perfil = pygame.Rect(*menu.tela_principal.cartao_rect())
    assert painel.top >= menu.layout.px(340)
    assert painel.bottom < perfil.top
    assert painel.right < menu.opcoes[0].get_rect(
        menu.x_opcoes, menu.fonte_opcao, menu.layout).left
    for indice in range(5):
        menu.opcao_selecionada = indice
        titulo, linhas = menu.tela_principal.contexto_opcao()
        assert titulo == menu.opcoes[indice].texto.split("//", 1)[-1].strip()
        assert len(linhas) == 2 and all(linhas)
        tela = pygame.Surface((menu.layout.largura, menu.layout.altura), pygame.SRCALPHA)
        menu.tela_principal.desenhar_contexto_original(tela)
        assert painel.contains(tela.get_bounding_rect())


def test_icones_secundarios_e_desabilitados_preservam_o_cache():
    normal = icone_menu_original("recordes", False, 32)
    desabilitado = icone_menu_original("recordes", False, 32, desabilitado=True)
    livro = icone_menu_original("memorias", False, 32)
    assert normal is icone_menu_original("recordes", False, 32)
    assert pygame.image.tobytes(normal, "RGBA") != pygame.image.tobytes(desabilitado, "RGBA")
    assert pygame.image.tobytes(normal, "RGBA") != pygame.image.tobytes(livro, "RGBA")
