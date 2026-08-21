"""Funcoes de manipulacao de cores."""

from __future__ import annotations

import colorsys
from typing import Tuple


def darken(cor: Tuple[int, ...], fator: float = 0.6) -> Tuple[int, int, int]:
    """Retorna uma versao mais escura da cor."""
    return tuple(max(0, min(255, int(c * fator))) for c in cor[:3])  # type: ignore[return-value]


def lighten(cor: Tuple[int, ...], fator: float = 0.4) -> Tuple[int, int, int]:
    """Retorna uma versao mais clara da cor."""
    return tuple(min(255, int(c + (255 - c) * fator)) for c in cor[:3])  # type: ignore[return-value]


def interpolate(cor1: Tuple[int, ...], cor2: Tuple[int, ...],
                t: float) -> Tuple[int, int, int]:
    """Interpola entre duas cores."""
    t = max(0.0, min(1.0, t))
    return tuple(int(c1 + (c2 - c1) * t) for c1, c2 in zip(cor1[:3], cor2[:3]))  # type: ignore[return-value]


def vivid(cor: Tuple[int, ...], brilho: float = 0.82,
          saturacao: float = 0.62) -> Tuple[int, int, int]:
    """Eleva brilho/saturacao para leitura sobre fundo escuro."""
    r, g, b = (max(0, min(255, int(c))) for c in cor[:3])
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    v = max(v, brilho)
    s = max(s, saturacao)
    r2, g2, b2 = colorsys.hsv_to_rgb(h, min(1.0, s), min(1.0, v))
    return (int(r2 * 255), int(g2 * 255), int(b2 * 255))
