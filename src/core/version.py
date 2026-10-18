"""Leitura da versão canônica definida em ``pyproject.toml``."""

from __future__ import annotations

import re
import sys
from pathlib import Path

VERSAO_DESENVOLVIMENTO = "0.0.0-dev"


def versao_projeto() -> str:
    """Retorna ``project.version`` sem manter uma segunda versão no código.

    No executável PyInstaller, o build inclui ``pyproject.toml`` na raiz dos
    arquivos internos. Em execução pelo código-fonte, o arquivo é encontrado
    a partir deste módulo.
    """
    candidatos = []
    diretorio_empacotado = getattr(sys, "_MEIPASS", None)
    if diretorio_empacotado:
        candidatos.append(Path(diretorio_empacotado) / "pyproject.toml")
    candidatos.append(Path(__file__).resolve().parents[2] / "pyproject.toml")

    for caminho in candidatos:
        try:
            conteudo = caminho.read_text(encoding="utf-8")
        except OSError:
            continue
        secao_projeto = conteudo.split("[project]", maxsplit=1)
        if len(secao_projeto) != 2:
            continue
        secao = secao_projeto[1].split("\n[", maxsplit=1)[0]
        correspondencia = re.search(
            r"(?m)^version\s*=\s*['\"]([^'\"]+)['\"]\s*$", secao
        )
        if correspondencia:
            return correspondencia.group(1)
    return VERSAO_DESENVOLVIMENTO
