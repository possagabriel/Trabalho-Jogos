"""Gerenciador de assets visuais: caminhos e carregamento de imagens.

Centraliza a resolucao de caminhos da pasta ``images/`` (raiz do projeto)
para que os modulos nao dupliquem logica de caminho. ``carregar_imagem``
devolve ``None`` quando o arquivo nao existe, permitindo fallbacks
procedurais sem propagar excecoes.
"""

import os

import pygame

from src.runtime.infrastructure.paths import PASTA_IMAGENS


def caminho_imagem(nome):
    """Caminho absoluto de um asset dentro da pasta ``images/``."""
    return os.fspath(PASTA_IMAGENS / nome)


def carregar_imagem(nome):
    """Carrega ``images/<nome>`` em 32-bit, ou ``None`` se nao existir.

    A conversao para 32-bit garante que ``pygame.transform.smoothscale``
    funcione mesmo quando o arquivo e PNG de paleta (8-bit).
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


def carregar_imagem_alpha(nome):
    """Carrega ``images/<nome>`` preservando alpha por pixel (SRCALPHA).

    Usado em sprites com transparencia; ``None`` se o arquivo nao existir.
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
