"""Diretório gravável para configurações e progresso do jogador."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def diretorio_dados() -> str:
    """Retorna o diretório gravável recomendado pelo sistema operacional.

    Variáveis de ambiente continuam tendo prioridade para testes, versões
    portáteis e instalações administradas. Fora disso, saves nunca ficam ao
    lado do executável, que pode estar em uma pasta sem permissão de escrita.
    """
    configurado = (os.environ.get("INCARNATE_DATA_DIR") or
                   os.environ.get("SPACEFURY_DATA_DIR"))
    if configurado:
        return os.fspath(Path(configurado).expanduser())
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if base:
            return os.path.join(base, "VoidShift")
        return os.fspath(Path.home() / "AppData" / "Local" / "VoidShift")
    if sys.platform == "darwin":
        return os.fspath(Path.home() / "Library" / "Application Support" /
                         "VoidShift")
    base_xdg = os.environ.get("XDG_DATA_HOME")
    if base_xdg:
        return os.fspath(Path(base_xdg).expanduser() / "void-shift")
    return os.fspath(Path.home() / ".local" / "share" / "void-shift")
