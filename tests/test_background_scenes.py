"""Regressões de brilho, identidade visual e separação dos estilos de fundo."""

import math
import random
from types import SimpleNamespace

import pygame
import pytest

from src.core.constants import SHIFT_WHITE, VERMELHO
from src.infrastructure.graphics.comic_theme import usar_visual
from src.runtime.domain.entities.enemies import TIPOS
from src.runtime.domain.entities.weapons import ARMARIA
from src.runtime.domain.world import scenarios


@pytest.fixture(autouse=True)
def visual_e_aleatoriedade_isolados():
    estado = random.getstate()
    try:
        with usar_visual({"estilo_visual": "ORIGINAL"}):
            yield
    finally:
        random.setstate(estado)


def test_filtro_reduz_amplitude_dos_canais():
    pygame.init()
    amostra = pygame.Surface((2, 2))
    amostra.fill((255, 210, 30))
    chroma_inicial = 255 - 30

    scenarios._reduzir_contraste_fundo(amostra)

    canais = amostra.get_at((0, 0))[:3]
    assert max(canais) - min(canais) < chroma_inicial * 0.2


def test_cores_de_referencia_distintas_nos_recortes_de_fundo(monkeypatch):
    pygame.init()
    monkeypatch.setattr(scenarios, "opcoes_atuais", lambda: SimpleNamespace(ativo=False))
    tipos_por_dimensao = (
        "scout", "flamifero", "abissal", "guardiao", "assombra", "celestial",
    )
    estado_aleatorio = random.getstate()
    try:
        for dimensao, tipo in enumerate(tipos_por_dimensao, 1):
            random.seed(20261024 + dimensao)
            cena = scenarios.Cenario(dimensao)
            fundo = pygame.Surface((scenarios.LARGURA, scenarios.ALTURA))
            cena.desenhar(fundo)
            medidas = (
                (TIPOS[tipo]["cor"], (850, 235)),
                (ARMARIA[0]["cor"], (610, 500)),
                (VERMELHO, (850, 235)),
                (SHIFT_WHITE, (850, 235)),
            )
            for cor_frente, (centro_x, centro_y) in medidas:
                distancias = [
                    math.dist(cor_frente, fundo.get_at((x, y))[:3])
                    for y in range(centro_y - 12, centro_y + 13)
                    for x in range(centro_x - 12, centro_x + 13)
                ]
                assert min(distancias) > 100
    finally:
        random.setstate(estado_aleatorio)


def test_parallax_usa_fundo_original_com_veu(monkeypatch):
    pygame.init()
    filtro = scenarios._reduzir_contraste_fundo

    def renderizar_parallax():
        random.seed(20261030)
        cena = scenarios.Cenario(6)
        cena.configurar_avanco("ALTA", (0.0, 1.0), True, semente=0)
        tela = pygame.Surface((scenarios.LARGURA, scenarios.ALTURA))
        cena.desenhar(tela)
        lumas = [
            0.2126 * (cor := tela.get_at((x, y))).r + 0.7152 * cor.g + 0.0722 * cor.b
            for y in range(0, tela.get_height(), 24)
            for x in range(0, tela.get_width(), 24)
        ]
        return sum(lumas) / len(lumas)

    monkeypatch.setattr(scenarios, "_reduzir_contraste_fundo", lambda _surface: None)
    luma_sem_veu = renderizar_parallax()
    monkeypatch.setattr(scenarios, "_reduzir_contraste_fundo", filtro)
    luma_com_veu = renderizar_parallax()

    assert luma_com_veu < luma_sem_veu * 0.8


@pytest.mark.parametrize("com_parallax", [False, True])
def test_comic_preserva_pixels_com_e_sem_veu(monkeypatch, com_parallax):
    pygame.init()
    filtro = scenarios._reduzir_contraste_fundo
    quadros = []
    with usar_visual({"estilo_visual": "COMIC", "qualidade_comic": "MEDIA"}):
        for tratamento in (lambda _surface: None, filtro):
            monkeypatch.setattr(scenarios, "_reduzir_contraste_fundo", tratamento)
            random.seed(20261030)
            cena = scenarios.Cenario(6)
            if com_parallax:
                cena.configurar_avanco("ALTA", (0.0, 1.0), True, semente=0)
            tela = pygame.Surface((scenarios.LARGURA, scenarios.ALTURA))
            cena.desenhar(tela)
            quadros.append(pygame.image.tobytes(tela, "RGB"))
    assert quadros[0] == quadros[1]


def test_filtro_mantem_luma_dos_seis_fundos_abaixo_de_150():
    pygame.init()
    estado_aleatorio = random.getstate()
    try:
        for dimensao in range(1, 7):
            random.seed(20261024 + dimensao)
            fundo = scenarios.Cenario(dimensao).fundo_estatico
            maior_luma = max(
                0.2126 * (cor := fundo.get_at((x, y))).r
                + 0.7152 * cor.g + 0.0722 * cor.b
                for y in range(0, fundo.get_height(), 16)
                for x in range(0, fundo.get_width(), 16)
            )
            assert maior_luma < 150
            media = [0, 0, 0]
            amostras = 0
            for y in range(0, fundo.get_height(), 32):
                for x in range(0, fundo.get_width(), 32):
                    pixel = fundo.get_at((x, y))
                    for canal in range(3):
                        media[canal] += pixel[canal]
                    amostras += 1
            media = [canal / amostras for canal in media]
            if dimensao == 3:
                assert media[2] > media[0]
            if dimensao == 6:
                assert media[0] > media[2] and media[1] > media[2]
    finally:
        random.setstate(estado_aleatorio)
