"""Regressões de legibilidade do HUD nos dois estilos e nas resoluções suportadas."""

import math
from types import SimpleNamespace

import pygame
import pytest

from src.core.constants import ALTURA, LARGURA
from src.infrastructure.graphics.comic_theme import usar_visual
from src.infrastructure.ui.layout import Layout
from src.runtime.domain.entities.player import Jogador
from src.runtime.presentation import hud as modulo_hud
from src.runtime.presentation.hud import HudJogo


@pytest.fixture(autouse=True)
def _video_headless():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))


def _jogo(encontro=None):
    jogador = Jogador(nome="Comandante de uma expedição muito distante")
    jogador.vida = 1
    jogador.pontuacao = 123456789
    jogador.arma_atual = 4
    jogador.combo.combo_atual = 25
    jogador.combo.quadros_restantes = jogador.combo.janela_acertos // 2
    chefe = SimpleNamespace(
        nome="Guardião da fronteira dimensional esquecida", vida=57, vida_max=100,
        estado=SimpleNamespace(rotulo="PREPARANDO ATAQUE"),
    )
    return SimpleNamespace(
        jogador=jogador, cenario=SimpleNamespace(id=3, nome="Fronteira dimensional"),
        boss=chefe if encontro == "boss" else None,
        miniboss=chefe if encontro == "miniboss" else None,
        especial=1.0, boost=0.75, energia=50, controles={"esquivar": pygame.K_v},
    )


@pytest.mark.parametrize("estilo", ["ORIGINAL", "COMIC"])
@pytest.mark.parametrize("tamanho", [(800, 600), (900, 700), (1280, 720), (1920, 1080)])
@pytest.mark.parametrize("encontro", [None, "boss", "miniboss"])
def test_textos_e_barras_nao_se_sobrepoem_e_centro_fica_livre(
    monkeypatch, estilo, tamanho, encontro,
):
    pygame.init()
    tela = pygame.Surface(tamanho, pygame.SRCALPHA)
    hud = HudJogo(Layout(*tamanho))
    textos, barras = [], []
    desenhar_texto = hud._texto

    def registrar_texto(*args, **kwargs):
        rect = desenhar_texto(*args, **kwargs)
        textos.append((str(args[1]), rect))
        return rect

    monkeypatch.setattr(hud, "_texto", registrar_texto)

    def observar_barra(funcao):
        def desenhar(*args, **kwargs):
            barras.append(args[2].copy())
            return funcao(*args, **kwargs)
        return desenhar

    for nome in ("_barra_fina", "_barra_segmentada"):
        monkeypatch.setattr(modulo_hud, nome, observar_barra(getattr(modulo_hud, nome)))

    with usar_visual({"estilo_visual": estilo}):
        hud.desenhar(tela, _jogo(encontro), tempo=1.0)

    for indice, (texto, rect) in enumerate(textos):
        assert tela.get_rect().contains(rect), texto
        assert not any(rect.colliderect(outro) for _, outro in textos[indice + 1:]), texto
        assert not any(rect.colliderect(barra) for barra in barras), texto
    centro = pygame.Rect(tamanho[0] // 3, tamanho[1] // 3,
                         tamanho[0] // 3, tamanho[1] // 3)
    assert pygame.mask.from_surface(tela.subsurface(centro)).count() == 0
    rotulos = [texto for texto, _ in textos]
    assert "CASCO CRÍTICO" in rotulos
    assert "[V] ESQUIVA PRONTA" in rotulos
    assert "[E]" in rotulos
    assert any("SETOR" in texto for texto in rotulos) == (encontro is None)
    assert ("AMEAÇA DETECTADA" in rotulos) == (encontro is not None)


def test_arco_cheio_percorre_a_circunferencia_sem_cruzar_o_centro():
    tela = pygame.Surface((100, 100), pygame.SRCALPHA)
    modulo_hud._arc(tela, (50, 50), 30, 0, math.tau, (255, 255, 255), 3)
    for ponto in ((80, 50), (50, 80), (20, 50), (50, 20)):
        assert tela.get_at(ponto).a > 0
    assert tela.get_at((50, 50)).a == 0


def test_painel_especial_nao_cobre_a_nave_na_posicao_inicial():
    hud = HudJogo()
    jogador = Jogador()
    area_nave = jogador.rect.inflate(20, 20)
    assert not hud._regioes()["especial"].colliderect(area_nave)


def test_hud_padrao_usa_tamanho_logico_e_atualiza_fontes_ao_redimensionar():
    pygame.init()
    hud = HudJogo()
    assert (hud.layout.largura, hud.layout.altura) == (LARGURA, ALTURA)
    fonte_anterior = hud._f_numero.get_height()
    hud.layout = Layout(LARGURA * 2, ALTURA * 2)
    tela = pygame.Surface((LARGURA * 2, ALTURA * 2), pygame.SRCALPHA)
    hud.desenhar(tela, _jogo(), tempo=0)
    assert hud._f_numero.get_height() > fonte_anterior


def test_barra_combo_mostra_tempo_restante_e_nao_quantidade_de_acertos():
    pygame.init()
    jogo = _jogo()
    jogo.jogador.combo.janela_acertos = 60
    jogo.jogador.combo.quadros_restantes = 30
    hud = HudJogo()
    assert hud._dados(jogo)["combo_tempo"] == pytest.approx(0.5)
    jogo.jogador.combo.quadros_restantes = 0
    assert hud._dados(jogo)["combo_tempo"] == 0


def test_texto_translucido_preserva_superficie_compartilhada():
    pygame.init()
    tela = pygame.Surface((100, 100), pygame.SRCALPHA)
    fonte = HudJogo()._f_padrao_xs
    surf = modulo_hud._render(fonte, "ESCUDO", (255, 255, 255))
    original = pygame.image.tobytes(surf, "RGBA")
    modulo_hud._blit_alfa(tela, surf, (0, 0), 120)
    assert modulo_hud._render(fonte, "ESCUDO", (255, 255, 255)) is surf
    assert pygame.image.tobytes(surf, "RGBA") == original
    assert surf.get_alpha() == 255
