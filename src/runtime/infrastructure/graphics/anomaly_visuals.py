"""Anomalias procedurais com camadas cacheadas e fluxo sem pulsos de luz."""

from __future__ import annotations

import math
from functools import lru_cache

import pygame

from src.infrastructure.graphics.comic_theme import CIANO, LARANJA, PAPEL, TINTA
from src.runtime.infrastructure.graphics.fonts import fonte_texto
from src.runtime.infrastructure.graphics.smooth import (
    desenhar_circulo,
    desenhar_poligono,
    linha_suave,
)

COR_NUCLEO = (8, 11, 24)
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


def _arco(tela: pygame.Surface, cor: tuple[int, int, int], rx: float, ry: float,
          inicio: float = 0.0, fim: float = math.tau, espessura: int = 1,
          inclinacao: float = 0.0) -> None:
    pontos = [_orbita(inicio + (fim - inicio) * i / 72, rx, ry, inclinacao)
              for i in range(73)]
    for a, b in zip(pontos, pontos[1:]):
        linha_suave(tela, cor, (CENTRO[0] + a[0], CENTRO[1] + a[1]),
                    (CENTRO[0] + b[0], CENTRO[1] + b[1]), espessura)


@lru_cache(maxsize=8)
def camada_anomalia(portal: bool, comic: bool, reduzido: bool) -> pygame.Surface:
    """Retorna a arte imutável; a renderização só reutiliza esta superfície."""
    tela = pygame.Surface(TAMANHO, pygame.SRCALPHA)
    quente = LARANJA if comic else COR_DISCO
    frio = CIANO if comic else COR_PORTAL
    lente = PAPEL if comic else COR_LENTE
    if not portal:
        # Lente e parte traseira do disco ficam atrás do horizonte escuro.
        for raio in (116, 129, 143) if not reduzido else (129,):
            cor = tuple(c // 3 for c in lente)
            _arco(tela, cor, raio, raio * 0.83, inclinacao=-0.12)
        for rx, ry in ((170, 39), (159, 34), (146, 29)):
            _arco(tela, quente, rx, ry, espessura=2, inclinacao=-0.18)
        desenhar_circulo(tela, quente, CENTRO, 98, espessura=3)
        desenhar_circulo(tela, COR_NUCLEO, CENTRO, 90)
        _arco(tela, lente, 94, 94, math.pi, math.tau, espessura=2)
        # O arco frontal cruza o núcleo e deixa clara a inclinação do disco.
        for rx, ry in ((170, 39), (159, 34), (146, 29)):
            _arco(tela, quente, rx, ry, 0, math.pi, 2, -0.18)
        _arco(tela, PAPEL, 159, 34, 0.15, math.pi - 0.15, 1, -0.18)
    else:
        # A abertura oval e os anéis internos convergem para um centro profundo.
        pontos = [(CENTRO[0] + math.cos(i * math.tau / 72) * 65,
                   CENTRO[1] + math.sin(i * math.tau / 72) * 104) for i in range(72)]
        desenhar_poligono(tela, COR_NUCLEO, pontos)
        for indice in range(5):
            escala = 0.78 ** indice
            cor = frio if indice == 0 else tuple(c // (indice + 1) for c in COR_TUNEL)
            _arco(tela, cor, 64 * escala, 103 * escala, espessura=2)
        _arco(tela, PAPEL, 68, 108, -1.3, 0.9, 2)
        _arco(tela, frio, 73, 115, 1.0, 3.8, 2)
        # Quatro marcas cardinais tornam a passagem reconhecível por forma.
        for angulo in (0, math.pi / 2, math.pi, math.pi * 1.5):
            dx, dy = _orbita(angulo, 84, 123)
            x, y = CENTRO[0] + dx, CENTRO[1] + dy
            desenhar_poligono(tela, PAPEL,
                              ((x, y - 5), (x + 4, y), (x, y + 5), (x - 4, y)))
    return tela


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
        for indice in range(6):
            angulo = tempo * 0.45 + indice * math.tau / 6
            dx, dy = _orbita(angulo, 61 if portal else 159,
                             99 if portal else 34, 0 if portal else -0.18)
            # Fragmentos da metade traseira não atravessam o horizonte.
            if not portal and math.sin(angulo) < 0 and math.hypot(dx, dy) < 94:
                continue
            desenhar_circulo(tela, PAPEL, (centro[0] + dx, centro[1] + dy), 2)
    rotulo = legenda_anomalia(legenda)
    tela.blit(rotulo, (centro[0] - rotulo.get_width() // 2, centro[1] + 132))
