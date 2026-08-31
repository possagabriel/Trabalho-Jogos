"""Caminhos estáveis dos recursos distribuídos com o projeto."""

from __future__ import annotations

from pathlib import Path


RAIZ_PROJETO = Path(__file__).resolve().parents[2]
PASTA_IMAGENS = RAIZ_PROJETO / "images"
PASTA_FONTES = RAIZ_PROJETO / "data" / "fonts"
