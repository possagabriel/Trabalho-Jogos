"""UI components: neon buttons, text drawing, hearts, bars.

Unique visual style: neon-glass with L-shaped brackets and glow borders.
All accent colours come from the active theme (NEON/AURORA/MAGMA).
Positioning uses the responsive layout system.

Migrated from game/ui.py -- every function and class preserved with full
logic.
"""

import math
from typing import Dict, Optional, Tuple, Union

import pygame

from src.infrastructure.graphics.fonts import fonte_texto, fonte_titulo
from src.infrastructure.graphics.smooth_rendering import (
    barra_suave,
    desenhar_cantos,
    desenhar_circulo,
    desenhar_glow,
    desenhar_painel,
    desenhar_texto_suave,
    retangulo_suave,
)
from src.infrastructure.graphics.theme import cor_tema

# Logical width used for alignment.
LARGURA_LOGICA = 900

# Brand white.
BRANCO = (244, 244, 247)


# ---------------------------------------------------------------------------
# Theme colour accessors
# ---------------------------------------------------------------------------

def cor_primaria() -> tuple:
    return cor_tema(chave="primaria")


def cor_secundaria() -> tuple:
    return cor_tema(chave="secundaria")


def cor_fundo_painel() -> tuple:
    return cor_tema(chave="fundo_painel")


def cor_borda_forte() -> tuple:
    return cor_tema(chave="borda_forte")


# ---------------------------------------------------------------------------
# Neon button
# ---------------------------------------------------------------------------

class BotaoNeon:
    """Button with hover, in the two visual variants of the game.

    - With explicit ``cor``/``cor_hover``: solid style used in sub-screens
      (rounded panel + border).
    - Without explicit colours: glass style using the active theme colours.
    """

    def __init__(self, texto: str, rect: Union[pygame.Rect, tuple],
                 cor: "tuple | None" = None,
                 cor_hover: "tuple | None" = None):
        self.texto = texto
        self.rect = pygame.Rect(rect)
        self.cor = cor
        self.cor_hover = cor_hover
        self.hover: bool = False

    def atualizar(self, mouse_pos: Tuple[int, int]) -> None:
        self.hover = self.rect.collidepoint(mouse_pos)

    def desenhar(self, tela: pygame.Surface, fonte: pygame.font.Font) -> None:
        if self.cor is not None:
            self._desenhar_solido(tela, fonte)
        else:
            self._desenhar_glass(tela, fonte)

    def _desenhar_solido(self, tela: pygame.Surface,
                         fonte: pygame.font.Font) -> None:
        cor = self.cor_hover if self.hover else self.cor
        borda = BRANCO if self.hover else (150, 130, 255)
        retangulo_suave(tela, cor, self.rect, 10,
                        glow_cor=cor if self.hover else None,
                        glow_raio=max(4, self.rect.h) if self.hover else 0)
        pygame.draw.rect(tela, borda, self.rect, 2, border_radius=10)
        desenhar_texto_suave(tela, fonte, self.texto, self.rect.center,
                             BRANCO, glow_raio=2)

    def _desenhar_glass(self, tela: pygame.Surface,
                        fonte: pygame.font.Font) -> None:
        cor = cor_primaria()
        if self.hover:
            cor = cor_borda_forte()
        desenhar_painel(tela, cor, self.rect,
                        cor_fundo=cor_fundo_painel(), raio_canto=12,
                        glow_raio=20 if self.hover else 8)
        desenhar_cantos(tela, BRANCO, self.rect, tamanho=10)
        desenhar_texto_suave(tela, fonte, self.texto, self.rect.center,
                             BRANCO, glow_cor=cor, glow_raio=2)


# ---------------------------------------------------------------------------
# Text drawing helpers
# ---------------------------------------------------------------------------

def desenhar_texto(tela: pygame.Surface, texto: str,
                   pos: Tuple[float, float], cor: tuple,
                   tamanho: int = 28, alinhar: str = "centro",
                   fontes: "Dict[int, pygame.font.Font] | None" = None) -> pygame.Rect:
    """Draw text on screen.  Returns the rect."""
    if fontes and tamanho in fontes:
        fonte = fontes[tamanho]
    else:
        fonte = fonte_texto(tamanho)
    return desenhar_texto_suave(tela, fonte, texto, pos, cor,
                                alinhar=alinhar)


def desenhar_titulo(tela: pygame.Surface, texto: str,
                    pos: Tuple[float, float], cor: "tuple | None" = None,
                    tamanho: int = 44) -> pygame.Rect:
    """Title in Orbitron font with glow."""
    fonte = fonte_titulo(tamanho)
    if cor is None:
        cor = cor_primaria()
    return desenhar_texto_suave(tela, fonte, texto, pos, cor,
                                glow_cor=cor, glow_raio=6, sombra=True)


# ---------------------------------------------------------------------------
# Hearts (health display)
# ---------------------------------------------------------------------------

def desenhar_coracoes(tela: pygame.Surface, vida: int, x: int, y: int,
                      cor: Tuple[int, int, int] = (255, 50, 50)) -> None:
    """Draw a row of hearts."""
    for i in range(vida):
        desenhar_coracao(tela, x + i * 26, y, cor)


def desenhar_coracao(tela: pygame.Surface, x: int, y: int,
                     cor: tuple, tamanho: int = 8) -> None:
    desenhar_glow(tela, cor, (x, y), tamanho * 1.5, 0.6)
    desenhar_circulo(tela, cor, (x - tamanho // 2, y - tamanho // 2),
                     tamanho // 2, brilho=1.1)
    desenhar_circulo(tela, cor, (x + tamanho // 2, y - tamanho // 2),
                     tamanho // 2, brilho=1.1)
    pygame.draw.polygon(tela, cor,
                        [(x - tamanho, y + tamanho // 2),
                         (x + tamanho, y + tamanho // 2),
                         (x, y + tamanho * 1.6)])


# ---------------------------------------------------------------------------
# Progress bar
# ---------------------------------------------------------------------------

def desenhar_barra(tela: pygame.Surface, x: int, y: int,
                   largura: int, altura: int, fracao: float,
                   cor: tuple,
                   fundo: Tuple[int, int, int] = (40, 40, 70)) -> None:
    barra_suave(tela, x, y, largura, altura, fracao, cor, fundo=fundo)


# ---------------------------------------------------------------------------
# Panel title header (used across menu screens)
# ---------------------------------------------------------------------------

def desenhar_painel_titulo(tela: pygame.Surface, titulo: str,
                           subtitulo: "str | None" = None, y: int = 55,
                           cor: "tuple | None" = None,
                           subtitulo_cor: "tuple | None" = None) -> None:
    """Standard header for menu screens: title + decorative line."""
    if cor is None:
        cor = cor_primaria()
    desenhar_titulo(tela, titulo, (LARGURA_LOGICA // 2, y), cor)
    t = pygame.time.get_ticks() * 0.002
    x0 = LARGURA_LOGICA // 2 - 150
    largura = 300
    desenhar_glow(tela, cor, (LARGURA_LOGICA // 2, y + 34), 20, 0.4)
    for i in range(0, largura, 6):
        brilho = 0.4 + 0.6 * abs(math.sin(i / 40 + t))
        cor_linha = tuple(int(c * brilho) for c in cor)
        pygame.draw.line(tela, cor_linha,
                         (x0 + i, y + 34), (x0 + i + 4, y + 40), 2)
    if subtitulo:
        if subtitulo_cor is None:
            subtitulo_cor = (200, 205, 240)
        surface = fonte_texto(20).render(subtitulo, True, subtitulo_cor)
        surface.set_alpha(200)
        tela.blit(surface, surface.get_rect(
            center=(LARGURA_LOGICA // 2, y + 62)))
