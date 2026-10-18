"""Compatibilidade com o antigo ponto de entrada ``python main.py``."""

from __future__ import annotations

import sys

from incarnate import cli as _cli_incarnate
from incarnate import executar_smoke_test


def cli(argumentos: list[str] | None = None) -> int:
    """Mantém a interface CLI histórica enquanto encaminha ao launcher novo."""
    argumentos = list(sys.argv[1:] if argumentos is None else argumentos)
    if "--smoke-test" in argumentos:
        return executar_smoke_test()
    return _cli_incarnate(argumentos)

if __name__ == "__main__":
    raise SystemExit(cli())
