"""Diretório gravável para configurações e progresso do jogador."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def diretorio_dados() -> str:
    """Retorna um diretório gravável, inclusive no executável Windows."""
    configurado = (os.environ.get("INCARNATE_DATA_DIR") or
                   os.environ.get("SPACEFURY_DATA_DIR"))
    if configurado:
        return configurado
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if base:
            return os.path.join(base, "VoidShift")
        return os.fspath(Path.home() / "AppData" / "Local" / "VoidShift")
    return os.fspath(Path(__file__).resolve().parents[2] / "data")
