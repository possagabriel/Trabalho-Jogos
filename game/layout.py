"""Fachada de compatibilidade para o layout responsivo migrado a ``src``.

Novos consumidores devem usar ``src.infrastructure.ui.layout`` diretamente.
"""

from src.infrastructure.ui.layout import (ALTURA_BASE, ANCRAS, BASE_CENTRO,
                                          BASE_DIREITA, BASE_ESQUERDA, CENTRO,
                                          LARGURA_BASE, Layout, MEIO_DIREITA,
                                          MEIO_ESQUERDA, TOPO_CENTRO,
                                          TOPO_DIREITA, TOPO_ESQUERDA)

__all__ = [
    "ALTURA_BASE", "ANCRAS", "BASE_CENTRO", "BASE_DIREITA",
    "BASE_ESQUERDA", "CENTRO", "LARGURA_BASE", "Layout", "MEIO_DIREITA",
    "MEIO_ESQUERDA", "TOPO_CENTRO", "TOPO_DIREITA", "TOPO_ESQUERDA",
]
