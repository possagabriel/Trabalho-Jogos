"""Testa a fonte única da versão exibida no menu."""

import re
from pathlib import Path

from src.core.version import versao_projeto


def test_versao_do_menu_usa_project_version_do_pyproject() -> None:
    raiz = Path(__file__).resolve().parents[1]
    projeto = (raiz / "pyproject.toml").read_text(encoding="utf-8")
    secao = projeto.split("[project]", maxsplit=1)[1].split("\n[", maxsplit=1)[0]
    correspondencia = re.search(
        r"(?m)^version\s*=\s*['\"]([^'\"]+)['\"]\s*$", secao
    )

    assert correspondencia is not None
    assert versao_projeto() == correspondencia.group(1)
