"""Nova linguagem visual do ORIGINAL com a disposição anterior em coluna."""

import pygame

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
