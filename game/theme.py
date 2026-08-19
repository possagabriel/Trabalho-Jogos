"""Tema visual unificado: paleta de acentos por tema e utilitarios de cor.

Define as cores de destaque (neon) que dao identidade visual ao jogo.
Todos os elementos da UI (menu, HUD, botoes, paineis) usam estas cores.
"""

import math

from .config import QUANTUM_CYAN, RIFT_MAGENTA, DIMENSION_GOLD, VOID_BLACK

# Paleta de acentos por tema (todos derivados da marca VOID//SHIFT)
TEMAS_CORES = {
    "NEON": {
        "primaria": RIFT_MAGENTA,        # assinatura da marca
        "secundaria": QUANTUM_CYAN,      # HUD e tecnologia
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

_ANIMACAO_GLOBAL = 0.0


def atualizar_animacao(dt=1.0):
    """Avança o relogio global usado por gradientes animados."""
    global _ANIMACAO_GLOBAL
    _ANIMACAO_GLOBAL += dt


def tempo():
    """Tempo global em segundos para animacoes sincronizadas."""
    return _ANIMACAO_GLOBAL


def tema_atual(nome=None):
    """Retorna a paleta de cores do tema atual (com fallback NEON)."""
    nome = nome or DEFAULT_TEMA
    return TEMAS_CORES.get(nome.upper(), TEMAS_CORES[DEFAULT_TEMA])


def cor_tema(nome=None, chave="primaria"):
    """Cor unica do tema atual."""
    return tema_atual(nome)[chave]


def cor_misturar(cor1, cor2, t):
    """Interpola duas cores com easing (t entre 0 e 1)."""
    t = max(0.0, min(1.0, t))
    t = t * t * (3 - 2 * t)
    return tuple(int(a + (b - a) * t) for a, b in zip(cor1[:3], cor2[:3]))


def cor_ciclar(cor1, cor2, velocidade=0.5, offset=0.0):
    """Alterna suavemente entre duas cores ao longo do tempo."""
    t = 0.5 + 0.5 * math.sin(tempo() * velocidade + offset)
    return cor_misturar(cor1, cor2, t)