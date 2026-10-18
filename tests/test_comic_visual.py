"""Contratos do tema comic, preparação de assets e isolamento do gameplay."""

import random
from unittest.mock import patch

import pygame
import pytest

from src.infrastructure.graphics.comic_pipeline import contornar, posterizar
from src.infrastructure.graphics.comic_theme import carregar_opcoes, usar_visual


@pytest.fixture(autouse=True)
def video():
    pygame.init()
    pygame.display.set_mode((1280, 720))


def test_config_invalida_tem_fallback_e_baixa_desliga_efeitos():
    assert carregar_opcoes({"estilo_visual": "invalido"}).estilo == "COMIC"
    baixa = carregar_opcoes({"qualidade_comic": "BAIXA", "line_boil": True})
    assert not baixa.hachuras and not baixa.papel and not baixa.halftone
    assert not baixa.line_boil
    assert carregar_opcoes({}).qualidade == "MEDIA"


def test_posterizacao_preserva_alpha_e_original():
    origem = pygame.Surface((3, 1), pygame.SRCALPHA).convert_alpha()
    origem.set_at((0, 0), (33, 151, 231, 127))
    origem.set_at((1, 0), (250, 22, 112, 255))
    antes = pygame.image.tobytes(origem, "RGBA")
    resultado = posterizar(origem)
    assert pygame.image.tobytes(origem, "RGBA") == antes
    assert resultado.get_at((0, 0)).a == 127
    assert resultado.get_at((2, 0)).a == 0
    assert set(resultado.get_at((0, 0))[:3]) <= {0, 85, 170, 255}


def test_contorno_usa_mascara_uma_vez_sem_mutar_sprite():
    origem = pygame.Surface((9, 9), pygame.SRCALPHA).convert_alpha()
    origem.fill((180, 90, 30), (3, 3, 3, 3))
    antes = pygame.image.tobytes(origem, "RGBA")
    with patch("pygame.mask.from_surface", wraps=pygame.mask.from_surface) as mascara:
        a = contornar(origem, 3)
        b = contornar(origem, 3)
        assert a is b
        assert mascara.call_count == 1
    assert a.get_size() == (15, 15)
    assert a.get_at((4, 6)).a > 0
    assert pygame.image.tobytes(origem, "RGBA") == antes


def test_contexto_visual_restaura_estilo():
    from src.infrastructure.graphics.comic_theme import opcoes_atuais

    anterior = opcoes_atuais()
    with usar_visual({"estilo_visual": "COMIC"}):
        assert opcoes_atuais().ativo
    assert opcoes_atuais() == anterior


def test_texturas_nao_consumem_random_do_gameplay():
    from src.infrastructure.graphics.comic_render import fundo_comic

    estado = random.getstate()
    fundo_comic((320, 180), 1, "MEDIA")
    assert random.getstate() == estado


def test_cada_dimensao_tem_composicao_comic_propria():
    from src.infrastructure.graphics.comic_render import fundo_comic
    from src.infrastructure.graphics.comic_theme import COMPOSICOES_FUNDO

    fundos = [fundo_comic((320, 180), setor, "BAIXA") for setor in range(1, 7)]
    imagens = [pygame.image.tobytes(fundo, "RGB") for fundo in fundos]
    assert len(set(imagens)) == 6
    assert len(set(COMPOSICOES_FUNDO)) == 6


def test_projeteis_inimigos_mantem_contorno_de_alto_contraste():
    from src.infrastructure.graphics.comic_render import fundo_comic
    from src.runtime.domain.entities.weapons import Projetil
    from src.runtime.infrastructure.graphics.style_tokens import (
        CONTORNO_PROJETIL_CLARO,
        CONTORNO_PROJETIL_ESCURO,
        CONTRASTE_PROJETIL_MINIMO,
    )
    from src.runtime.presentation.hud import razao_contraste

    pygame.init()
    for setor in range(1, 7):
        tela = fundo_comic((320, 180), setor, "BAIXA").copy()
        projetil = Projetil(160, 90, 0, 4, 1, (255, 80, 90), 4,
                            origem="inimigo")
        hitbox = projetil.rect.copy()
        projetil.desenhar(tela)
        cores = {tuple(tela.get_at((x, y))[:3])
                 for y in range(180) for x in range(320)}
        assert CONTORNO_PROJETIL_ESCURO in cores
        assert CONTORNO_PROJETIL_CLARO in cores
        assert projetil.rect == hitbox
        for y in range(0, 180, 12):
            for x in range(0, 320, 12):
                cor_fundo = tuple(fundo_comic((320, 180), setor, "BAIXA")
                                  .get_at((x, y))[:3])
                contraste_borda = max(
                    razao_contraste(cor_fundo, CONTORNO_PROJETIL_ESCURO),
                    razao_contraste(cor_fundo, CONTORNO_PROJETIL_CLARO),
                )
                assert contraste_borda >= CONTRASTE_PROJETIL_MINIMO


def test_paleta_tem_tres_faixas_ordenadas():
    from src.infrastructure.graphics.comic_pipeline import gerar_paleta

    sombra, base, luz = gerar_paleta((80, 160, 240))
    assert all(s < b < claro for s, b, claro in zip(sombra, base, luz))


@pytest.mark.parametrize("chave", ["comic_papel", "comic_halftone", "comic_hachuras"])
def test_toggles_independentes(chave):
    opcao = carregar_opcoes({chave: False})
    assert not getattr(opcao, chave.removeprefix("comic_"))


def test_line_boil_reutiliza_mascara_e_preserva_centro():
    origem = pygame.Surface((8, 8), pygame.SRCALPHA).convert_alpha()
    origem.fill((90, 200, 250), (2, 2, 4, 4))
    with patch("pygame.mask.from_surface", wraps=pygame.mask.from_surface) as mascara:
        a = contornar(origem, variacao=0)
        b = contornar(origem, variacao=1)
        assert mascara.call_count == 1
    assert a.get_size() == b.get_size()
    assert a.get_at((7, 7)) == b.get_at((7, 7))


def test_desenho_comic_preserva_hitboxes_atributos_e_random():
    from src.runtime.domain.entities.enemies import TIPOS, Inimigo
    from src.runtime.domain.entities.player import Jogador
    from src.runtime.domain.entities.powerups import PowerUp
    from src.runtime.domain.entities.weapons import ARMARIA, Projetil

    entidades = [Jogador(), PowerUp("arma", 50, 50)]
    entidades += [Inimigo(tipo, 1, x=100, y=100) for tipo in TIPOS]
    entidades += [Projetil(50, 50, 0, -8, 1, a["cor"], a["raio"], tipo=a["tipo"])
                  for a in ARMARIA]
    tela = pygame.display.get_surface()
    antes = [(e.rect.copy(), vars(e).copy()) for e in entidades]
    estado = random.getstate()
    with usar_visual({"estilo_visual": "COMIC"}):
        for entidade in entidades:
            entidade.desenhar(tela)
    assert random.getstate() == estado
    for entidade, (rect, atributos) in zip(entidades, antes):
        assert entidade.rect == rect
        assert vars(entidade) == atributos


def test_numeros_refletem_dano_aplicado_sem_alterar_alvo():
    from types import SimpleNamespace

    from src.infrastructure.graphics.comic_theme import ELEMENTOS
    from src.runtime.presentation.damage_feedback import registrar_impacto

    alvo = SimpleNamespace(x=30, y=40, vida=4)
    sessao = SimpleNamespace(mensagens=[], jogador=SimpleNamespace(bonus_dano=0))
    proj = SimpleNamespace(tipo="padrao", dano=2)
    estado = random.getstate()
    registrar_impacto(sessao, alvo, proj, 6)
    assert sessao.mensagens[0].texto == "2!"
    assert sessao.mensagens[0].cor == ELEMENTOS["critico"]
    registrar_impacto(sessao, alvo, proj, 4)
    assert len(sessao.mensagens) == 1
    assert alvo.vida == 4 and random.getstate() == estado


def test_menu_alterna_visual_e_restauracao_sem_modificar_controles():
    from src.runtime.application.core import Jogo

    jogo = Jogo()
    controles = dict(jogo.config.controles)
    jogo.config["estilo_visual"] = "COMIC"
    menu = jogo.menu
    menu.config_selecao = next(i for i, linha in enumerate(menu._linhas_config())
                              if linha[1] == "estilo_visual")
    with patch.object(jogo.config, "salvar"):
        menu._ajustar_config(1)
        assert jogo.config["estilo_visual"] == "ORIGINAL"
        menu._ajustar_config(1)
        assert jogo.config["estilo_visual"] == "COMIC"
    assert jogo.config.controles == controles


def test_menu_controla_shader_e_intensidade_em_tempo_real():
    from src.runtime.application.core import Jogo

    jogo = Jogo()
    menu = jogo.menu
    indice_shader = next(i for i, linha in enumerate(menu._linhas_config())
                          if linha[1] == "shader_comic")
    indice_intensidade = next(i for i, linha in enumerate(menu._linhas_config())
                              if linha[1] == "intensidade_shader")
    with patch.object(jogo.config, "salvar"):
        menu.config_selecao = indice_shader
        anterior = jogo.config["shader_comic"]
        menu._ajustar_config(1)
        assert jogo.config["shader_comic"] is not anterior

        menu.config_selecao = indice_intensidade
        jogo.config["intensidade_shader"] = 0.98
        menu._ajustar_config(1)
        assert jogo.config["intensidade_shader"] == 1.0
        menu._aplicar_slider(indice_intensidade, 0.42)
        assert jogo.config["intensidade_shader"] == 0.42


def test_gpu_evitar_repetir_grao_e_hachura_do_cpu():
    opcoes = carregar_opcoes({
        "estilo_visual": "COMIC",
        "qualidade_comic": "ALTA",
        "comic_papel": True,
        "comic_hachuras": True,
        "grao_shader": 0.5,
        "hachuras_shader": True,
    }, acabamento_gpu=True)

    assert opcoes.papel is False
    assert opcoes.hachuras is False
    assert opcoes.halftone is True


def test_menu_controla_parametros_avancados_do_shader():
    from src.runtime.application.core import Jogo

    jogo = Jogo()
    menu = jogo.menu
    indices = {tipo: i for i, (_, tipo) in enumerate(menu._linhas_config())}
    with patch.object(jogo.config, "salvar"):
        menu.config_selecao = indices["tons_shader"]
        menu._ajustar_config(1)
        assert jogo.config["tons_shader"] == 4

        menu.config_selecao = indices["preservar_interface"]
        menu._ajustar_config(1)
        assert jogo.config["preservar_interface"] is False

        menu._aplicar_slider(indices["contorno_shader"], 0.25)
        menu._aplicar_slider(indices["grao_shader"], 0.6)
        menu._aplicar_slider(indices["saturacao_shader"], 0.8)
        assert jogo.config["contorno_shader"] == 0.25
        assert jogo.config["grao_shader"] == 0.6
        assert jogo.config["saturacao_shader"] == 1.3


def test_asset_ausente_tem_fallback_procedural():
    from src.runtime.domain.entities import player

    with patch.object(player, "_sprite_padrao", return_value=None):
        jogador = player.Jogador()
        tela = pygame.Surface((100, 100), pygame.SRCALPHA).convert_alpha()
        jogador.x = jogador.y = 50
        jogador.invencivel = 0
        with usar_visual({"estilo_visual": "COMIC"}):
            jogador.desenhar(tela)
        assert pygame.mask.from_surface(tela).count() > 0


def test_nave_nao_recalcula_mascara_ao_animar():
    from src.runtime.application.core import Jogo

    jogo = Jogo()
    jogo._preparar_jogo()
    jogo.jogador.invencivel = 0
    with usar_visual({"estilo_visual": "COMIC", "qualidade_comic": "ALTA", "line_boil": True}):
        with patch("pygame.mask.from_surface", side_effect=AssertionError("máscara por quadro")):
            for tilt in (-5, -2, 0, 2, 5):
                jogo.jogador.tilt = tilt
                jogo.jogador.desenhar(jogo.tela)


def test_replay_comic_e_original_tem_mesmo_gameplay():
    from src.runtime.application.core import Jogo

    def executar(estilo):
        random.seed(551)
        jogo = Jogo()
        jogo._preparar_jogo()
        jogo.jogador.invencivel = 0
        with patch("pygame.time.get_ticks", return_value=1000):
            with usar_visual({"estilo_visual": estilo}):
                for _ in range(35):
                    jogo.projeteis.extend(jogo.jogador.atirar())
                    jogo._atualizar_jogando()
                    jogo._desenhar_jogo()
        return (
            jogo.jogador.x, jogo.jogador.y, jogo.jogador.vida,
            jogo.jogador.pontuacao, jogo.jogador.cooldown_tiro,
            [(i.tipo, i.x, i.y, i.vida) for i in jogo.inimigos],
            [(p.tipo, p.x, p.y, p.dano) for p in jogo.projeteis],
            random.getstate(),
        )

    assert executar("COMIC") == executar("ORIGINAL")


def test_cache_do_titulo_separa_estilos_e_reutiliza_original():
    from src.infrastructure.graphics.theme import tema_atual
    from src.runtime.application.core import Jogo

    menu = Jogo().menu
    with usar_visual({"estilo_visual": "ORIGINAL"}):
        original = menu._titulo_surfaces(tema_atual())
    with usar_visual({"estilo_visual": "COMIC"}):
        comic = menu._titulo_surfaces(tema_atual())
    with usar_visual({"estilo_visual": "ORIGINAL"}):
        assert menu._titulo_surfaces(tema_atual()) is original
    assert comic is not original


def test_lettering_limita_cor_durante_easing_da_pausa():
    from src.infrastructure.graphics.comic_render import texto_tinta

    superficie = texto_tinta("RETOMAR", 14, (-3, 280, 90))
    assert superficie.get_width() > 0


def test_confirmacoes_usam_o_modelo_angular_do_menu():
    from src.runtime.infrastructure.graphics.smooth import desenhar_botao_cartoon
    from src.runtime.presentation.menu import Dialogo

    tela = pygame.Surface((900, 700), pygame.SRCALPHA).convert_alpha()
    rect = pygame.Rect(260, 430, 180, 50)
    with usar_visual({"estilo_visual": "COMIC"}):
        desenhado = desenhar_botao_cartoon(
            tela, "SIM", rect, (30, 160, 80), fonte=pygame.font.Font(None, 24))
        dialogo = Dialogo("Sair do jogo", "Tem certeza que deseja sair?",
                          lambda: None, lambda: None)
        dialogo.desenhar(tela, pygame.font.Font(None, 34),
                         pygame.font.Font(None, 24))
    assert desenhado == rect
    assert pygame.mask.from_surface(tela).count() > 0
