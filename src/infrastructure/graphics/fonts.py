"""Font manager: sci-fi fonts with safe fallback.

Loads Orbitron (titles) and Rajdhani (body text) from ``data/fonts``.
If the fonts are not found, falls back to the default Pygame font.

Migrated from game/fonts.py -- every function preserved with full logic.
"""

import os
from typing import Dict, Optional

import pygame

from src.shared.paths import PASTA_FONTES

ARQUIVO_TITULO = os.fspath(PASTA_FONTES / "Orbitron.ttf")
ARQUIVO_TEXTO = os.fspath(PASTA_FONTES / "Rajdhani.ttf")

_CACHE: Dict[tuple, pygame.font.Font] = {}


def _carregar(caminho: str, tamanho: int) -> pygame.font.Font:
    try:
        return pygame.font.Font(caminho, tamanho)
    except (pygame.error, OSError, FileNotFoundError):
        return pygame.font.Font(None, tamanho)


def fonte_titulo(tamanho: int) -> pygame.font.Font:
    """Title font (Orbitron)."""
    chave = ("titulo", tamanho)
    if chave not in _CACHE:
        _CACHE[chave] = _carregar(ARQUIVO_TITULO, tamanho)
    return _CACHE[chave]


def fonte_texto(tamanho: int) -> pygame.font.Font:
    """Body text font (Rajdhani)."""
    chave = ("texto", tamanho)
    if chave not in _CACHE:
        _CACHE[chave] = _carregar(ARQUIVO_TEXTO, tamanho)
    return _CACHE[chave]


def limpar_cache() -> None:
    _CACHE.clear()
