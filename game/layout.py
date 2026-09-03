"""Sistema de layout responsivo: ancoras, containers, proporcoes e safe areas.

O jogo desenha numa superficie logica (LARGURA x ALTURA) que o core
redimensiona para a janela preservando proporcoes (letterbox / safe areas em
``core.Jogo._apresentar``). Este modulo centraliza o posicionamento de TODA a
UI: nenhuma coordenada rigida em pixels deve ser usada fora dele.

Convencoes de uso:
  - ``Layout.x(f)`` / ``Layout.y(f)``: fracoes da superficie logica (0.0-1.0).
  - ``Layout.px(v)``: converte um valor da *base de design* (900x700) para a
    superficie atual, preservando as proporcoes em qualquer resolucao.
  - ``Layout.rect(ancora, ...)``: containers ancorados na grade 3x3.
  - ``Layout.ponto(ancora, ...)``: pontos ancorados para textos e elementos.
  - ``Layout.fonte(...)``: fontes escaladas pelo mesmo fator de proporcao.
  - ``Layout.margem()``: margem de seguranca (safe area) interna.
"""

import pygame

from .config import ALTURA, LARGURA

# Base de design: valores em "px de design" sao multiplicados pela escala
# (min(largura/900, altura/700)), mantendo a identidade visual em qualquer
# resolucao e formato de janela.
LARGURA_BASE = 900
ALTURA_BASE = 700

# ---------------------------------------------------------------------------
# Ancoras da grade 3x3
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

# Fracoes (fx, fy) de cada ancora dentro da superficie
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
    """Grade responsiva derivada do tamanho da superficie logica."""

    def __init__(self, largura=LARGURA, altura=ALTURA):
        self.largura = max(1, int(largura))
        self.altura = max(1, int(altura))

    # ---------------------------------------------------------- proporcao

    @property
    def escala(self):
        """Fator uniforme (min) que converte valores da base de design."""
        return min(self.largura / LARGURA_BASE, self.altura / ALTURA_BASE)

    @property
    def centro(self):
        """Ponto central da superficie."""
        return (self.largura // 2, self.altura // 2)

    def px(self, valor):
        """Converte um valor da base de design (900x700) para o tamanho atual."""
        return int(round(valor * self.escala))

    def x(self, fracao):
        """Coordenada x proporcional a largura (0.0-1.0)."""
        return int(self.largura * max(0.0, min(1.0, fracao)))

    def y(self, fracao):
        """Coordenada y proporcional a altura (0.0-1.0)."""
        return int(self.altura * max(0.0, min(1.0, fracao)))

    def larg(self, fracao):
        """Largura proporcional a superficie (0.0-1.0)."""
        return int(self.largura * max(0.0, min(1.0, fracao)))

    def alt(self, fracao):
        """Altura proporcional a superficie (0.0-1.0)."""
        return int(self.altura * max(0.0, min(1.0, fracao)))

    def margem(self, base=16):
        """Margem de seguranca (safe area) interna, proporcional ao design."""
        return self.px(base)

    # ------------------------------------------------------ posicionamento

    def ponto(self, ancora, dx=0, dy=0):
        """Ponto ancorado na grade 3x3 com offsets em px de design."""
        fx, fy = _ANCRAS[ancora]
        return (self.x(fx) + self.px(dx), self.y(fy) + self.px(dy))

    def rect(self, ancora, largura_frac, altura_frac, dx=0, dy=0):
        """Container ancorado: tamanho por fracao e offset em px de design.

        O lado correspondente da ancora (esquerda/centro/direita e
        topo/meio/base) do retangulo alinha com o ponto ancorado da superficie.
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

    def fileira(self, itens, largura_frac, altura_frac, espaco,
                ancora=CENTRO, dx=0, dy=0):
        """Distribui ``itens`` containers iguais em linha horizontal.

        ``espaco`` e o espacamento em px de design; o bloco fica centrado na
        ancora escolhida. Retorna uma lista de Rects.
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

    # -------------------------------------------------------------- fontes

    def fonte(self, tamanho_base, titulo=False):
        """Fonte cacheada com tamanho escalado pela proporcao da superficie."""
        from .fonts import fonte_texto, fonte_titulo
        tamanho = max(8, self.px(tamanho_base))
        return fonte_titulo(tamanho) if titulo else fonte_texto(tamanho)

    def fonte_titulo(self, tamanho_base):
        return self.fonte(tamanho_base, titulo=True)

    def fonte_texto(self, tamanho_base):
        return self.fonte(tamanho_base, titulo=False)
