"""Anomalias procedurais com camadas cacheadas e fluxo sem pulsos de luz."""

from __future__ import annotations

import math
import random
from functools import lru_cache

import pygame

from src.infrastructure.graphics.comic_theme import CIANO, LARANJA, PAPEL, TINTA
from src.runtime.infrastructure.graphics.fonts import fonte_texto
from src.runtime.infrastructure.graphics.smooth import (
    desenhar_circulo,
    linha_suave,
)

COR_NUCLEO = (1, 2, 5)
COR_QUENTE = (255, 237, 201)
COR_DISCO_ESCURO = (100, 36, 18)
COR_LUZ_PORTAL = (201, 244, 255)
COR_DESTINO = (8, 22, 42)
COR_DISCO = (239, 150, 91)
COR_LENTE = (136, 190, 236)
COR_PORTAL = (111, 211, 236)
COR_TUNEL = (188, 139, 231)
TAMANHO = (380, 330)
CENTRO = (190, 150)


def _orbita(angulo: float, rx: float, ry: float, inclinacao: float = 0.0
            ) -> tuple[float, float]:
    x, y = math.cos(angulo) * rx, math.sin(angulo) * ry
    return x, y + x * inclinacao


def _misturar(a: tuple[int, int, int], b: tuple[int, int, int], t: float
              ) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def _sobre(base, cor, alfa):
    alfa = max(0.0, min(1.0, alfa))
    total = alfa + base[3] / 255 * (1 - alfa)
    if total <= 0:
        return (0, 0, 0, 0)
    rgb = tuple(round((cor[i] * alfa + base[i] * base[3] / 255 * (1 - alfa)) / total)
                for i in range(3))
    return (*rgb, round(total * 255))


def _pixel_buraco_negro(x: int, y: int, comic: bool):
    r = math.hypot(x, y)
    if r > 181:
        return (0, 0, 0, 0)
    quente = LARANJA if comic else COR_DISCO
    branco = PAPEL if comic else COR_QUENTE
    halo = math.exp(-((r - 104) / 23) ** 2) * 0.13
    pixel = (*COR_LENTE, round(halo * 255))
    inclinado = y + x * 0.18
    disco = math.hypot(x, inclinado / 0.24)
    alfa_disco = 0.0
    cor_disco = quente
    if 94 < disco < 178:
        borda = min(1.0, (disco - 94) / 5, (178 - disco) / 18)
        textura = 0.85 + 0.15 * math.sin(disco * 1.7 + math.atan2(inclinado, x) * 9)
        # O lado que se aproxima fica mais luminoso: assimetria do disco.
        brilho = (0.58 + 0.42 * (1 - x / 178) / 2) * textura
        cor_disco = _misturar(COR_DISCO_ESCURO, quente, brilho)
        cor_disco = _misturar(cor_disco, branco, max(0.0, 1 - (disco - 94) / 27) * 0.8)
        alfa_disco = borda * 0.98
        pixel = _sobre(pixel, cor_disco, alfa_disco)
    if r < 87:
        pixel = (*COR_NUCLEO, 255)
    # A imagem da parte traseira da acreção é curvada sobre a sombra.
    if y < 0:
        arco = math.exp(-((r - 99) / 5.5) ** 2)
        luz = _misturar(quente, branco, 0.4 + 0.3 * max(0.0, -x / 110))
        pixel = _sobre(pixel, luz, arco * 0.9)
    fotons = math.exp(-((r - 89) / 1.4) ** 2)
    pixel = _sobre(pixel, branco, fotons * 0.88)
    # A metade frontal do disco passa diante da sombra, deixando o centro negro.
    if inclinado > 12 and alfa_disco:
        pixel = _sobre(pixel, cor_disco, alfa_disco)
    return pixel


def _pixel_tunel(x: int, y: int, comic: bool):
    r = math.hypot(x / 84, y / 104)
    if r > 1.34:
        return (0, 0, 0, 0)
    frio = CIANO if comic else COR_PORTAL
    branco = PAPEL if comic else COR_LUZ_PORTAL
    pixel = (*frio, round(40 * math.exp(-((r - 1.02) / 0.12) ** 2)))
    if r < 1:
        angulo = math.atan2(y / 104, x / 84)
        # Curvas espirais estreitam até a garganta; iluminação lateral dá volume.
        curva = 0.5 + 0.5 * math.sin(angulo * 3 - math.log(max(0.025, r)) * 7)
        volume = (0.55 + 0.45 * math.cos(angulo - 0.8)) * r ** 0.6
        cor = _misturar(COR_DESTINO, COR_TUNEL, volume * 0.5)
        cor = _misturar(cor, frio, volume * (0.25 + curva * 0.5))
        garganta = math.exp(-(r / 0.13) ** 2)
        cor = _misturar(cor, COR_DESTINO, garganta)
        pixel = (*cor, 255)
    borda = math.exp(-((r - 1) / 0.035) ** 2)
    pixel = _sobre(pixel, branco, borda * 0.95)
    return pixel


@lru_cache(maxsize=8)
def camada_anomalia(portal: bool, comic: bool, reduzido: bool) -> pygame.Surface:
    """Prepara sombra, acreção ou garganta volumétrica uma vez por estilo."""
    tela = pygame.Surface(TAMANHO, pygame.SRCALPHA)
    pixel = _pixel_tunel if portal else _pixel_buraco_negro
    tela.lock()
    for y in range(5, TAMANHO[1] - 5):
        for x in range(5, TAMANHO[0] - 5):
            cor = pixel(x - CENTRO[0], y - CENTRO[1], comic)
            if cor[3]:
                tela.set_at((x, y), cor)
    tela.unlock()
    # Um campo de estrelas distante aparece curvado através da boca do túnel.
    sorteio = random.Random(807 if portal else 193)
    for _ in range(30 if not reduzido else 14):
        angulo = sorteio.uniform(0, math.tau)
        raio = sorteio.uniform(0.12, 0.88) if portal else sorteio.uniform(1.16, 1.48)
        if portal:
            angulo += math.log(raio) * 0.45
            dx, dy = _orbita(angulo, raio * 84, raio * 104)
        else:
            dx, dy = _orbita(angulo, raio * 90, raio * 90)
            if abs(dy + dx * 0.18) < 47:
                continue
        cor = COR_LUZ_PORTAL if portal else COR_LENTE
        desenhar_circulo(tela, cor, (CENTRO[0] + dx, CENTRO[1] + dy), 1)
    return tela


@lru_cache(maxsize=4)
def _fluxo_anomalia(portal: bool, comic: bool) -> tuple[pygame.Surface, ...]:
    """Filamentos contínuos em quadros cacheados, sem pulsos de intensidade."""
    quadros = []
    cor = (CIANO if comic else COR_PORTAL) if portal else (LARANJA if comic else COR_DISCO)
    for quadro in range(24):
        tela = pygame.Surface(TAMANHO, pygame.SRCALPHA)
        fase = quadro / 24
        for indice in range(6):
            pontos = []
            for passo in range(13):
                t = passo / 12
                if portal:
                    raio = (0.25 + indice * 0.12) * (1 - t * 0.22)
                    angulo = indice * math.tau / 6 + fase * math.tau + t * 0.4
                    angulo += math.log(raio) * 0.45
                    dx, dy = _orbita(angulo, raio * 84, raio * 104)
                else:
                    angulo = indice * math.tau / 6 + fase * math.tau + t * 0.22
                    dx, dy = _orbita(angulo, 145 + indice % 3 * 9,
                                     34 + indice % 3 * 2, -0.18)
                    if math.hypot(dx, dy) < 91 and dy + dx * 0.18 < 12:
                        pontos = []
                        continue
                pontos.append((CENTRO[0] + dx, CENTRO[1] + dy))
            for a, b in zip(pontos, pontos[1:]):
                linha_suave(tela, cor, a, b, 1)
        quadros.append(tela)
    return tuple(quadros)


@lru_cache(maxsize=8)
def legenda_anomalia(texto: str) -> pygame.Surface:
    """Cacheia a legenda com fundo opaco e contraste alto."""
    fonte = fonte_texto(17)
    rotulo = fonte.render(texto, True, PAPEL)
    painel = pygame.Surface((rotulo.get_width() + 16, rotulo.get_height() + 8))
    painel.fill(TINTA)
    painel.blit(rotulo, (8, 4))
    return painel


def desenhar_anomalia(tela: pygame.Surface, centro: tuple[int, int], *, portal: bool,
                      comic: bool, reduzido: bool, tempo: float, legenda: str) -> None:
    """Compõe a arte e partículas de brilho constante, sem alterar física.

    Args:
        tela: Canvas existente.
        centro: Posição projetada da anomalia.
        portal: Seleciona túnel oval ou disco de acreção.
        comic: Usa a paleta comic.
        reduzido: Congela o fluxo e reduz os anéis decorativos.
        tempo: Tempo de simulação; a pausa também pausa o fluxo.
        legenda: Identificação do perigo ou do par de portais.
    """
    arte = camada_anomalia(portal, comic, reduzido)
    tela.blit(arte, (centro[0] - CENTRO[0], centro[1] - CENTRO[1]))
    if not reduzido:
        quadros = _fluxo_anomalia(portal, comic)
        fluxo = quadros[int(tempo * 12) % len(quadros)]
        tela.blit(fluxo, (centro[0] - CENTRO[0], centro[1] - CENTRO[1]))
    rotulo = legenda_anomalia(legenda)
    tela.blit(rotulo, (centro[0] - rotulo.get_width() // 2, centro[1] + 132))
