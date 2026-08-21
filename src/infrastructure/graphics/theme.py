"""Unified visual theme: accent palettes per theme and colour utilities.

Defines the neon accent colours that give the game its visual identity.
All UI elements (menu, HUD, buttons, panels) use these colours.

Migrated from game/theme.py -- every function preserved with full logic.
"""

import math
from typing import Dict, Tuple

# Brand palette constants (from game/config.py)
QUANTUM_CYAN = (25, 217, 255)
RIFT_MAGENTA = (255, 23, 107)
DIMENSION_GOLD = (255, 200, 87)
VOID_BLACK = (8, 8, 13)

# Accent palettes by theme (all derived from the VOID//SHIFT brand)
TEMAS_CORES: Dict[str, Dict[str, tuple]] = {
    "NEON": {
        "primaria": RIFT_MAGENTA,
        "secundaria": QUANTUM_CYAN,
        "terciaria": (255, 120, 200),
        "detalhe": QUANTUM_CYAN,
        "fundo_painel": VOID_BLACK,
        "borda_forte": RIFT_MAGENTA,
        "borda_fraco": (120, 30, 70),
    },
    "AURORA": {
        "primaria": QUANTUM_CYAN,
        "secundaria": RIFT_MAGENTA,
        "terciaria": (120, 255, 220),
        "detalhe": RIFT_MAGENTA,
        "fundo_painel": (6, 14, 20),
        "borda_forte": QUANTUM_CYAN,
        "borda_fraco": (30, 90, 120),
    },
    "MAGMA": {
        "primaria": DIMENSION_GOLD,
        "secundaria": (255, 90, 40),
        "terciaria": (255, 200, 90),
        "detalhe": RIFT_MAGENTA,
        "fundo_painel": (24, 12, 10),
        "borda_forte": DIMENSION_GOLD,
        "borda_fraco": (120, 70, 30),
    },
}

DEFAULT_TEMA = "NEON"

_ANIMACAO_GLOBAL: float = 0.0


def atualizar_animacao(dt: float = 1.0) -> None:
    """Advance the global clock used by animated gradients."""
    global _ANIMACAO_GLOBAL
    _ANIMACAO_GLOBAL += dt


def tempo() -> float:
    """Global time in seconds for synchronised animations."""
    return _ANIMACAO_GLOBAL


def tema_atual(nome: "str | None" = None) -> Dict[str, tuple]:
    """Return the colour palette for the current theme (fallback NEON)."""
    nome = nome or DEFAULT_TEMA
    return TEMAS_CORES.get(nome.upper(), TEMAS_CORES[DEFAULT_TEMA])


def cor_tema(nome: "str | None" = None, chave: str = "primaria") -> tuple:
    """Single colour from the current theme."""
    return tema_atual(nome)[chave]


def cor_misturar(cor1: Tuple[int, ...], cor2: Tuple[int, ...],
                 t: float) -> Tuple[int, int, int]:
    """Interpolate two colours with easing (t between 0 and 1)."""
    t = max(0.0, min(1.0, t))
    t = t * t * (3 - 2 * t)
    return tuple(int(a + (b - a) * t) for a, b in zip(cor1[:3], cor2[:3]))


def cor_ciclar(cor1: Tuple[int, ...], cor2: Tuple[int, ...],
               velocidade: float = 0.5, offset: float = 0.0) -> Tuple[int, int, int]:
    """Smoothly alternate between two colours over time."""
    t = 0.5 + 0.5 * math.sin(tempo() * velocidade + offset)
    return cor_misturar(cor1, cor2, t)
