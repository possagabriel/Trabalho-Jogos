"""Regressões do acabamento raster cacheado das cutscenes."""

import pygame

from src.runtime.presentation.cutscene_raster import filtrar_fundo_cutscene


def test_filtro_preserva_origem_dimensoes_e_cache() -> None:
    origem = pygame.Surface((96, 54))
    origem.fill((34, 66, 120))
    pygame.draw.circle(origem, (230, 200, 80), (44, 27), 14)
    original = origem.copy()

    primeiro = filtrar_fundo_cutscene(origem, (120, 160, 255))
    segundo = filtrar_fundo_cutscene(origem, (120, 160, 255))

    assert primeiro.get_size() == origem.get_size()
    assert segundo is primeiro
    assert pygame.image.tobytes(origem, "RGB") == pygame.image.tobytes(original, "RGB")
    assert pygame.image.tobytes(primeiro, "RGB") != pygame.image.tobytes(origem, "RGB")


def test_filtro_aplica_tingimento_por_dimensao() -> None:
    origem = pygame.Surface((96, 54))
    origem.fill((75, 80, 90))

    azul = filtrar_fundo_cutscene(origem, (120, 160, 255))
    cobre = filtrar_fundo_cutscene(origem, (255, 120, 70))

    assert pygame.image.tobytes(azul, "RGB") != pygame.image.tobytes(cobre, "RGB")


def test_quebra_preserva_palavras_paragrafos_e_limita_tokens_longos():
    from src.runtime.infrastructure.graphics.fonts import fonte_texto
    from src.runtime.infrastructure.graphics.menu_panels import linhas_painel

    pygame.font.init()
    fonte = fonte_texto(22)
    texto = "Uma memória distante\n" + "X" * 100
    linhas = linhas_painel(fonte, texto, 160)
    assert all(fonte.size(linha)[0] <= 160 for linha in linhas)
    assert any("memória" in linha for linha in linhas)
    assert "".join(linhas).replace(" ", "") == texto.replace(" ", "").replace("\n", "")



def test_retratos_narrativos_carregam_em_cache_sem_mutar_a_arte():
    from importlib.resources import files

    from src.runtime.domain.story import ler_catalogo
    from src.runtime.presentation.dialogue_box import DialogueBox

    pygame.font.init()
    catalogo = ler_catalogo(files("src.runtime.story") / "cenas_pt_BR.json")
    caixa = DialogueBox(catalogo.personagens)
    for personagem in catalogo.personagens.values():
        icone = personagem["retrato"]
        retrato = caixa.obter_retrato(icone)
        assert retrato.get_size() == (300, 300)
        assert caixa.obter_retrato(icone) is retrato
        assert retrato.get_alpha() in (None, 255)
        assert caixa._retratos_apagados[icone].get_alpha() == 100



def test_todas_as_falas_cabem_na_area_de_leitura_sem_cortes():
    from importlib.resources import files

    from src.core.constants import ALTURA, LARGURA
    from src.runtime.domain.story import ler_catalogo
    from src.runtime.presentation.dialogue_box import DialogueBox

    pygame.font.init()
    catalogo = ler_catalogo(files("src.runtime.story") / "cenas_pt_BR.json")
    caixa = DialogueBox(catalogo.personagens)
    area = caixa.AREA_FALA
    tela = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    leitura = pygame.Rect(area.x + 32, area.y + 65, area.w - 64,
                         round(ALTURA * .86) - area.y - 65)
    for cena in catalogo.cenas.values():
        for passo in cena.passos:
            if passo["tipo"] != "fala":
                continue
            tela.fill((0, 0, 0, 0))
            caixa._texto(tela, passo["texto"], leitura.x, leitura.y,
                         leitura.w, (244, 244, 247), passo["texto"])
            assert leitura.contains(tela.get_bounding_rect()), (cena.id, passo["texto"])
