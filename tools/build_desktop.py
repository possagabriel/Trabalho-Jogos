"""Gera um executável desktop do VOID//SHIFT no sistema atual."""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parents[1]


def argumentos_distribuicao(
        plataforma: str | None = None,
        raiz: Path = RAIZ_PROJETO) -> list[str]:
    """Monta argumentos portáteis para o PyInstaller.

    O separador de ``--add-data`` varia entre Windows e sistemas POSIX. Manter
    essa diferença aqui permite usar exatamente o mesmo comando de build nos
    dois sistemas.
    """
    plataforma = plataforma or sys.platform
    separador = ";" if plataforma.startswith("win") else ":"
    formato = "--onefile" if plataforma.startswith("win") else "--onedir"
    argumentos = [
        "--noconfirm",
        "--clean",
        formato,
        "--windowed",
        "--name",
        "VOID-SHIFT",
        "--add-data",
        f"{raiz / 'images'}{separador}images",
        "--add-data",
        f"{raiz / 'data' / 'fonts'}{separador}data/fonts",
        "--collect-submodules",
        "src",
        "--collect-submodules",
        "game",
        "--collect-submodules",
        "OpenGL",
        "--hidden-import",
        "game.phase_select",
    ]
    if plataforma.startswith("win"):
        argumentos.extend([
            "--icon",
            str(raiz / "assets" / "windows" / "void-shift.ico"),
        ])
    argumentos.append(str(raiz / "main.py"))
    return argumentos


def main() -> None:
    """Executa o build para o sistema operacional atual."""
    try:
        from PyInstaller.__main__ import run
    except ImportError as erro:
        raise SystemExit(
            'PyInstaller ausente. Instale com: pip install -e ".[desktop]"'
        ) from erro
    run(argumentos_distribuicao())


if __name__ == "__main__":
    main()
