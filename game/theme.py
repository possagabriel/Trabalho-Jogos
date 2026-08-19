"""Tema visual unificado: paleta de acentos por tema e utilitarios de cor.

Define as cores de destaque (neon) que dao identidade visual ao jogo.
Todos os elementos da UI (menu, HUD, botoes, paineis) usam estas cores.
"""

import math

from .config import CIANO

# Paleta de acentos por tema
TEMAS_CORES = {
    "NEON": {
        "primaria": CIANO,            # (0, 200, 255)
        "secundaria": (160, 60, 255), # magenta-violeta
        "terciaria": (60, 220, 255),
        "detalhe": (255, 60, 200),
        "fundo_painel": (12, 14, 32),
        "borda_forte": (0, 235, 255),
        "borda_fraco": (50, 90, 160),
    },
    "AURORA": {
        "primaria": (0, 255, 170),
        "secundaria": (80, 200, 255),
        "terciaria": (120, 255, 220),
        "detalhe": (200, 80, 255),
        "fundo_painel": (10, 22, 30),
        "borda_forte": (0, 235, 170),
        "borda_fraco": (40, 110, 140),
    },
    "MAGMA": {
        "primaria": (255, 120, 30),
        "secundaria": (255, 60, 60),
        "terciaria": (255, 200, 90),
        "detalhe": (255, 90, 160),
        "fundo_painel": (30, 14, 12),
        "borda_forte": (255, 150, 40),
        "borda_fraco": (150, 70, 40),
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