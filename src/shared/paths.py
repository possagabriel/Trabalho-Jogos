"""Caminhos estáveis dos recursos distribuídos com o projeto."""

from __future__ import annotations

import sys
from pathlib import Path


# PyInstaller extrai os recursos do executável para ``_MEIPASS``. Em modo de
# desenvolvimento, mantém a raiz normal do repositório.
RAIZ_PROJETO = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
PASTA_IMAGENS = RAIZ_PROJETO / "images"
PASTA_FONTES = RAIZ_PROJETO / "data" / "fonts"
