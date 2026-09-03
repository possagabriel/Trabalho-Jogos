"""Gerenciador de fontes: fontes sci-fi com fallback seguro.

Carrega Orbitron (titulos) e Rajdhani (texto corrido) de data/fonts.
Se as fontes nao existirem, usa a fonte padrao do Pygame.
"""

import os

import pygame

from src.runtime.infrastructure.paths import PASTA_FONTES

ARQUIVO_TITULO = os.fspath(PASTA_FONTES / "Orbitron.ttf")
ARQUIVO_TEXTO = os.fspath(PASTA_FONTES / "Rajdhani.ttf")

_CACHE = {}


def _carregar(caminho, tamanho):
    try:
        return pygame.font.Font(caminho, tamanho)
    except (pygame.error, OSError, FileNotFoundError):
        return pygame.font.Font(None, tamanho)


def fonte_titulo(tamanho):
    """Fonte para titulos (Orbitron)."""
    chave = ("titulo", tamanho)
    if chave not in _CACHE:
        _CACHE[chave] = _carregar(ARQUIVO_TITULO, tamanho)
    return _CACHE[chave]


def fonte_texto(tamanho):
    """Fonte para textos (Rajdhani)."""
    chave = ("texto", tamanho)
    if chave not in _CACHE:
        _CACHE[chave] = _carregar(ARQUIVO_TEXTO, tamanho)
    return _CACHE[chave]


def limpar_cache():
    _CACHE.clear()
