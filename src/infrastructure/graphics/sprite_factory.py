"""Sprite loading and caching system.

Centralises path resolution for the ``images/`` directory (project root) so
that modules do not duplicate path logic.  ``carregar_imagem`` returns
``None`` when the file does not exist, allowing procedural fallbacks without
propagating exceptions.

Migrated from game/assets.py -- every function preserved with full logic.
"""

import os
from typing import Dict, Optional

import pygame

PASTA_IMAGENS = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "images")


def caminho_imagem(nome: str) -> str:
    """Absolute path of an asset inside the ``images/`` directory."""
    return os.path.join(PASTA_IMAGENS, nome)


def carregar_imagem(nome: str) -> Optional[pygame.Surface]:
    """Load ``images/<nome>`` as 32-bit, or ``None`` if it doesn't exist.

    Converting to 32-bit ensures ``pygame.transform.smoothscale`` works
    even when the file is an 8-bit paletted PNG.
    """
    caminho = caminho_imagem(nome)
    try:
        img = pygame.image.load(caminho)
    except (pygame.error, OSError, FileNotFoundError):
        return None
    try:
        img = img.convert(32)
    except pygame.error:
        pass
    return img


def carregar_imagem_alpha(nome: str) -> Optional[pygame.Surface]:
    """Load ``images/<nome>`` preserving per-pixel alpha (SRCALPHA).

    Used for sprites with transparency; ``None`` if the file doesn't exist.
    """
    caminho = caminho_imagem(nome)
    try:
        img = pygame.image.load(caminho)
    except (pygame.error, OSError, FileNotFoundError):
        return None
    try:
        img = img.convert_alpha()
    except pygame.error:
        pass
    return img


class SpriteFactory:
    """Cache and factory for loaded sprites.

    Usage::

        factory = SpriteFactory()
        ship = factory.obter("nave_padrao.png")
        ship_alpha = factory.obter_alpha("nave_alpha.png")
    """

    def __init__(self):
        self._cache: Dict[str, pygame.Surface] = {}
        self._cache_alpha: Dict[str, pygame.Surface] = {}

    def obter(self, nome: str) -> Optional[pygame.Surface]:
        """Return a cached 32-bit sprite or load + cache it."""
        if nome in self._cache:
            return self._cache[nome]
        img = carregar_imagem(nome)
        if img is not None:
            self._cache[nome] = img
        return img

    def obter_alpha(self, nome: str) -> Optional[pygame.Surface]:
        """Return a cached SRCALPHA sprite or load + cache it."""
        if nome in self._cache_alpha:
            return self._cache_alpha[nome]
        img = carregar_imagem_alpha(nome)
        if img is not None:
            self._cache_alpha[nome] = img
        return img

    def escalar(self, nome: str, largura: int,
                altura: int) -> Optional[pygame.Surface]:
        """Load, cache, and return a scaled sprite."""
        img = self.obter(nome)
        if img is None:
            return None
        return pygame.transform.smoothscale(img, (largura, altura))

    def escalar_alpha(self, nome: str, largura: int,
                      altura: int) -> Optional[pygame.Surface]:
        """Load (alpha), cache, and return a scaled sprite."""
        img = self.obter_alpha(nome)
        if img is None:
            return None
        return pygame.transform.smoothscale(img, (largura, altura))

    def limpar_cache(self) -> None:
        self._cache.clear()
        self._cache_alpha.clear()
