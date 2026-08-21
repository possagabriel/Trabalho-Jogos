"""Responsive layout system: anchors, containers, proportions and safe areas.

The game draws on a logical surface (900x700) that the core renderer scales
to the window preserving proportions (letterbox / safe areas).  This module
centralises the positioning of ALL UI: no rigid pixel coordinates should be
used outside of it.

Conventions:
  - ``Layout.x(f)`` / ``Layout.y(f)``: fractions of the logical surface (0.0-1.0).
  - ``Layout.px(v)``: converts a value from the *design base* (900x700) to the
    current surface, preserving proportions at any resolution.
  - ``Layout.rect(anchor, ...)``: anchored containers on a 3x3 grid.
  - ``Layout.ponto(anchor, ...)``: anchored points for text and elements.
  - ``Layout.fonte(...)``: fonts scaled by the same proportion factor.
  - ``Layout.margem()``: internal safe-area margin.

Migrated from game/layout.py -- every function and class preserved with full
logic.
"""

import pygame

from src.infrastructure.graphics.fonts import fonte_texto, fonte_titulo

# Design base: values in "design px" are multiplied by the scale
# (min(width/900, height/700)), maintaining visual identity at any resolution.
LARGURA_BASE = 900
ALTURA_BASE = 700

# ---------------------------------------------------------------------------
# 3x3 grid anchors
# ---------------------------------------------------------------------------

TOPO_ESQUERDA = "topo_esquerda"
TOPO_CENTRO = "topo_centro"
TOPO_DIREITA = "topo_direita"
MEIO_ESQUERDA = "meio_esquerda"
CENTRO = "centro"
MEIO_DIREITA = "meio_direita"
BASE_ESQUERDA = "base_esquerda"
BASE_CENTRO = "base_centro"
BASE_DIREITA = "base_direita"

ANCRAS = (TOPO_ESQUERDA, TOPO_CENTRO, TOPO_DIREITA, MEIO_ESQUERDA, CENTRO,
          MEIO_DIREITA, BASE_ESQUERDA, BASE_CENTRO, BASE_DIREITA)

_ANCRAS = {
    TOPO_ESQUERDA: (0.0, 0.0),
    TOPO_CENTRO: (0.5, 0.0),
    TOPO_DIREITA: (1.0, 0.0),
    MEIO_ESQUERDA: (0.0, 0.5),
    CENTRO: (0.5, 0.5),
    MEIO_DIREITA: (1.0, 0.5),
    BASE_ESQUERDA: (0.0, 1.0),
    BASE_CENTRO: (0.5, 1.0),
    BASE_DIREITA: (1.0, 1.0),
}


class Layout:
    """Responsive grid derived from the logical surface size."""

    def __init__(self, largura: int = 900, altura: int = 700):
        self.largura: int = max(1, int(largura))
        self.altura: int = max(1, int(altura))

    # ---------------------------------------------------------- proportion

    @property
    def escala(self) -> float:
        """Uniform factor (min) that converts design-base values."""
        return min(self.largura / LARGURA_BASE, self.altura / ALTURA_BASE)

    @property
    def centro(self) -> tuple:
        """Centre point of the surface."""
        return (self.largura // 2, self.altura // 2)

    def px(self, valor: int) -> int:
        """Convert a design-base value to current size."""
        return int(round(valor * self.escala))

    def x(self, fracao: float) -> int:
        """Width-proportional coordinate (0.0-1.0)."""
        return int(self.largura * max(0.0, min(1.0, fracao)))

    def y(self, fracao: float) -> int:
        """Height-proportional coordinate (0.0-1.0)."""
        return int(self.altura * max(0.0, min(1.0, fracao)))

    def larg(self, fracao: float) -> int:
        """Width proportional to the surface (0.0-1.0)."""
        return int(self.largura * max(0.0, min(1.0, fracao)))

    def alt(self, fracao: float) -> int:
        """Height proportional to the surface (0.0-1.0)."""
        return int(self.altura * max(0.0, min(1.0, fracao)))

    def margem(self, base: int = 16) -> int:
        """Safe-area margin, proportional to the design base."""
        return self.px(base)

    # ------------------------------------------------------ positioning

    def ponto(self, ancora: str, dx: int = 0, dy: int = 0) -> tuple:
        """Anchored point on the 3x3 grid with design-px offsets."""
        fx, fy = _ANCRAS[ancora]
        return (self.x(fx) + self.px(dx), self.y(fy) + self.px(dy))

    def rect(self, ancora: str, largura_frac: float, altura_frac: float,
             dx: int = 0, dy: int = 0) -> pygame.Rect:
        """Anchored container: size by fraction and offset in design px.

        The side of the rectangle corresponding to the anchor
        (left/centre/right and top/middle/bottom) aligns with the anchored
        point on the surface.
        """
        largura = max(1, self.larg(largura_frac))
        altura = max(1, self.alt(altura_frac))
        ret = pygame.Rect(0, 0, largura, altura)
        ax, ay = self.ponto(ancora, dx, dy)
        if ancora.endswith("esquerda"):
            ret.left = ax
        elif ancora.endswith("direita"):
            ret.right = ax
        else:
            ret.centerx = ax
        if ancora.startswith("topo"):
            ret.top = ay
        elif ancora.startswith("base"):
            ret.bottom = ay
        else:
            ret.centery = ay
        return ret

    def fileira(self, itens: int, largura_frac: float, altura_frac: float,
                espaco: int, ancora: str = CENTRO,
                dx: int = 0, dy: int = 0) -> list:
        """Distribute *itens* equal containers in a horizontal row.

        ``espaco`` is the spacing in design px; the block is centred on the
        chosen anchor.  Returns a list of ``pygame.Rect``.
        """
        larg = self.larg(largura_frac)
        alt = self.alt(altura_frac)
        passo = larg + self.px(espaco)
        total = larg * itens + self.px(espaco) * (itens - 1)
        fx, fy = _ANCRAS[ancora]
        x0 = self.x(fx) - total // 2 + self.px(dx)
        y0 = self.y(fy) - alt // 2 + self.px(dy)
        return [pygame.Rect(x0 + i * passo, y0, larg, alt)
                for i in range(itens)]

    # -------------------------------------------------------------- fonts

    def fonte(self, tamanho_base: int, titulo: bool = False):
        """Cached font with size scaled by the surface proportion."""
        tamanho = max(8, self.px(tamanho_base))
        return fonte_titulo(tamanho) if titulo else fonte_texto(tamanho)

    def fonte_titulo(self, tamanho_base: int):
        return self.fonte(tamanho_base, titulo=True)

    def fonte_texto(self, tamanho_base: int):
        return self.fonte(tamanho_base, titulo=False)
