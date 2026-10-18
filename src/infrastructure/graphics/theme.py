"""Unified visual theme: accent palettes per theme and colour utilities.

Defines the neon accent colours that give the game its visual identity.
All UI elements (menu, HUD, buttons, panels) use these colours.

Migrated from game/theme.py -- every function preserved with full logic.
"""

import math
import time
from typing import Dict, Tuple

from src.core.constants import DIMENSION_GOLD, QUANTUM_CYAN, RIFT_MAGENTA, VOID_BLACK
from src.infrastructure.graphics.comic_theme import PALETA_UI, opcoes_atuais

# Accent palettes by theme (all derived from the INCARNATE brand)
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

# Tokens do menu ORIGINAL. O canvas continua lógico; o renderer aplica a
# mesma escala da área jogável para todas as resoluções.
MENU_MARGEM_SEGURANCA = 18
MENU_LARGURA_COLUNA = 590
MENU_ALTURA_PRINCIPAL = 64
MENU_ALTURA_SECUNDARIA = 32
MENU_X_COLUNA_FRACAO = 0.61
MENU_Y_PRINCIPAIS = (0.205, 0.305, 0.405)
MENU_Y_SECUNDARIOS = (0.56, 0.615, 0.67, 0.725, 0.78)
MENU_Y_DIVISOR = 0.50
MENU_X_NAVE = 450
MENU_Y_NAVE = 470
MENU_FONTE_PRINCIPAL = 32
MENU_FONTE_PRINCIPAL_SELECIONADA = 36
MENU_FONTE_SECUNDARIA = 22
MENU_FONTE_SECUNDARIA_SELECIONADA = 24
MENU_COR_DIVISOR = (45, 62, 105)
MENU_COR_TEXTO = (245, 248, 255)
MENU_COR_TEXTO_SECUNDARIO = (220, 230, 250)
MENU_COR_TEXTO_DESABILITADO = (145, 158, 184)
MENU_COR_BOTAO_DESABILITADO = (25, 31, 49)
MENU_COR_BOTAO_DESABILITADO_HOVER = (39, 47, 68)
MENU_COR_PAINEL_RODAPE = (5, 8, 24)
MENU_ALPHA_PAINEL_RODAPE = 255
MENU_ALPHA_BOTAO_NORMAL = 200
MENU_ALPHA_BOTAO_SELECIONADO = 236
MENU_ESPESSURA_BOTAO = 2
MENU_GLITCH_INTERVALO_MS = 650
MENU_GLITCH_INTERVALO_REDUZIDO_MS = 1000
MENU_GLITCH_DURACAO_MS = 42
MENU_GLITCH_OFFSET = 2
MENU_GLITCH_AJUSTE_NORMAL = 1
MENU_GLITCH_ALPHA_NORMAL = 85
MENU_GLITCH_ALPHA_REDUZIDO = 45
MENU_MARCADOR_LADO = 18
MENU_MARCADOR_RECUO = 26
MENU_FONTE_MINIMA_ROTULO = 20
MENU_LAYOUT_4_3_MAX_RAZAO = 1.45
MENU_4_3_X_COLUNA_FRACAO = 0.57
MENU_4_3_LARGURA_COLUNA = 540
MENU_4_3_Y_PRINCIPAIS = (0.22, 0.34, 0.46)
MENU_4_3_Y_SECUNDARIOS = (0.61, 0.69)
MENU_CARTAO_PERFIL_RECT = (30, 476, 580, 120)
MENU_CARTAO_PERFIL_RECT_4_3 = (30, 480, 530, 120)
MENU_CARTAO_PERFIL_COR = (4, 9, 27)
MENU_CARTAO_PERFIL_ALPHA = 225
MENU_CARTAO_PERFIL_ESPESSURA = 2
MENU_CARTAO_PERFIL_TEXTO = (225, 235, 255)
MENU_CARTAO_PERFIL_TEXTO_SECUNDARIO = (165, 190, 225)
MENU_CARTAO_PERFIL_FONT_SIZE = 26
MENU_CARTAO_PERFIL_FONT_SIZE_PEQUENA = 20
MENU_SELO_LARGURA = 78
MENU_SELO_ALTURA = 27
MENU_SELO_FONT_SIZE = 20
MENU_RESUMO_CONTINUAR_FONT_SIZE = 20

def atualizar_animacao(dt: float = 1.0) -> None:
    """Compatibility API; animations use a monotonic clock instead.

    The parameter is retained for existing callers without keeping mutable
    module state.
    """


def tempo() -> float:
    """Global time in seconds for synchronised animations."""
    return time.monotonic()


def tema_atual(nome: "str | None" = None) -> Dict[str, tuple]:
    """Return the colour palette for the current theme (fallback NEON)."""
    if opcoes_atuais().ativo:
        return dict(PALETA_UI)
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
