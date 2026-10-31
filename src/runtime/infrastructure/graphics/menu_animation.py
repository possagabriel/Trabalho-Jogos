"""Movimento contínuo e foco do menu ORIGINAL, com alternativa estática."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from functools import lru_cache

import pygame

from src.infrastructure.ui.layout import Layout
from src.runtime.infrastructure.graphics.nebula_background import desenhar_planeta
from src.runtime.infrastructure.graphics.smooth import desenhar_circulo, linha_suave

COR_ESTRELA = (137, 169, 198)
COR_ORBITA = (54, 90, 119)
COR_PLANETA = (84, 137, 183)
COR_FOCO = (153, 217, 242)


def cartoes_menu_original(layout: Layout) -> tuple[pygame.Rect, ...]:
    """Reserva duas fileiras de três cartões sob a nave, antes do rodapé."""
    margem, gap = layout.margem(30), layout.px(12)
    largura = (layout.largura - margem * 2 - gap * 2) // 3
    altura = layout.px(78)
    return tuple(pygame.Rect(margem + (indice % 3) * (largura + gap),
                             layout.y(0.61) + (indice // 3) * (altura + gap),
                             largura, altura) for indice in range(6))


@dataclass
class FocoAnimado:
    """Interpola o foco sem mover a área clicável do botão."""

    valor: float = 0.0

    def atualizar(self, selecionado: bool, dt: float, *, reduzido: bool = False) -> None:
        """Aproxima do alvo por tempo decorrido ou aplica o estado estático."""
        alvo = float(selecionado)
        if reduzido:
            self.valor = alvo
        elif math.isfinite(dt) and dt > 0:
            self.valor += (alvo - self.valor) * (1 - math.exp(-14 * dt))


@lru_cache(maxsize=4)
def _planeta_menu(lado: int) -> pygame.Surface:
    arte = pygame.Surface((lado, lado), pygame.SRCALPHA)
    centro = lado // 2
    raio = lado // 3
    orbita = pygame.Rect(2, centro - raio // 2, lado - 4, raio)
    pygame.draw.ellipse(arte, COR_ORBITA, orbita, 1)
    desenhar_planeta(arte, (centro, centro), raio, COR_PLANETA, craters=True)
    return arte


class CenaMenuAnimada:
    """Camada de estrelas, planeta e satélites com parallax suave pelo mouse."""

    def __init__(self) -> None:
        rng = random.Random(6142)
        self.estrelas = tuple((rng.random(), rng.random(), rng.randrange(1, 4))
                              for _ in range(64))
        self.tempo = 0.0
        self.parallax = (0.0, 0.0)

    def atualizar(self, dt: float, mouse: tuple[float, float], *,
                  reduzido: bool = False) -> None:
        """Avança a cena visual; efeitos reduzidos usam uma composição fixa."""
        if reduzido:
            self.tempo, self.parallax = 0.0, (0.0, 0.0)
            return
        if not math.isfinite(dt) or dt <= 0:
            return
        self.tempo += dt
        fator = 1 - math.exp(-5 * dt)
        px, py = self.parallax
        mx, my = max(-1.0, min(1.0, mouse[0])), max(-1.0, min(1.0, mouse[1]))
        self.parallax = (px + (mx - px) * fator, py + (my - py) * fator)

    def desenhar(self, tela: pygame.Surface, layout: Layout) -> None:
        """Reutiliza arte cacheada e anima posição, sem pulsos de luminosidade."""
        for x, y, camada in self.estrelas:
            sx = ((x - self.tempo * 0.003 * camada) % 1) * layout.largura
            sy = ((y + self.tempo * 0.0015 * camada) % 1) * layout.altura
            ponto = (sx + self.parallax[0] * layout.px(camada * 4),
                     sy + self.parallax[1] * layout.px(camada * 4))
            desenhar_circulo(tela, COR_ESTRELA, ponto, max(1, layout.px(camada / 2)))
        cx = layout.x(0.73) + layout.px(math.sin(self.tempo * 0.25) * 10)
        cy = layout.y(0.39) + layout.px(math.cos(self.tempo * 0.22) * 5)
        cx += layout.px(self.parallax[0] * 8)
        cy += layout.px(self.parallax[1] * 5)
        arte = _planeta_menu(max(64, layout.px(210)))
        tela.blit(arte, arte.get_rect(center=(cx, cy)))
        for indice in range(3):
            angulo = self.tempo * (0.3 + indice * 0.08) + indice * math.tau / 3
            x = cx + math.cos(angulo) * layout.px(102)
            y = cy + math.sin(angulo) * layout.px(34)
            desenhar_circulo(tela, COR_FOCO, (x, y), max(1, layout.px(2)))


def desenhar_trilha_foco(tela: pygame.Surface, rect: pygame.Rect, layout: Layout,
                         tempo: float, foco: float, *, reduzido: bool = False) -> None:
    """Desliza um acento pela base do botão sem brilho intermitente."""
    if reduzido or foco < 0.02:
        return
    margem, comprimento = layout.px(18), layout.px(34)
    percurso = max(0, rect.width - margem * 2 - comprimento)
    x = rect.left + margem + round(percurso * ((tempo / 2.8) % 1))
    cor = tuple(round(c * foco) for c in COR_FOCO)
    linha_suave(tela, cor, (x, rect.bottom - layout.px(5)),
                 (x + comprimento, rect.bottom - layout.px(5)), max(1, layout.px(2)))
