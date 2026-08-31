"""Compatibilidade para caminhos do runtime.

Os caminhos são centralizados em :mod:`src.shared.paths` para que o runtime e
os adaptadores reutilizáveis sempre carreguem os mesmos recursos.
"""

from src.shared.paths import PASTA_FONTES, PASTA_IMAGENS, RAIZ_PROJETO

__all__ = ["PASTA_FONTES", "PASTA_IMAGENS", "RAIZ_PROJETO"]
