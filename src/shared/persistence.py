"""Persistência JSON atômica e recuperação por backup."""

from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)


def caminho_backup(caminho: str | os.PathLike[str]) -> str:
    """Retorna o nome do backup associado ao arquivo."""
    return f"{os.fspath(caminho)}.bak"


def salvar_json_atomico(
        caminho: str | os.PathLike[str],
        dados: Any,
        criar_backup: bool = True) -> bool:
    """Grava JSON por substituição atômica e preserva a versão anterior."""
    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario: str | None = None
    try:
        descritor, temporario = tempfile.mkstemp(
            dir=destino.parent, prefix=f".{destino.name}.", suffix=".tmp")
        with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        if criar_backup and destino.is_file():
            shutil.copy2(destino, caminho_backup(destino))
        os.replace(temporario, destino)
        return True
    except (OSError, TypeError, ValueError):
        LOGGER.exception("Nao foi possivel salvar %s", destino)
        if temporario:
            try:
                os.unlink(temporario)
            except OSError:
                pass
        return False


def carregar_json_resiliente(caminho: str | os.PathLike[str]) -> Any:
    """Carrega o arquivo principal e usa ``.bak`` se ele estiver corrompido."""
    ultimo_erro: Exception | None = None
    for candidato in (os.fspath(caminho), caminho_backup(caminho)):
        try:
            with open(candidato, "r", encoding="utf-8") as arquivo:
                return json.load(arquivo)
        except (FileNotFoundError, json.JSONDecodeError, OSError) as erro:
            ultimo_erro = erro
    if ultimo_erro is not None:
        raise ultimo_erro
    raise FileNotFoundError(os.fspath(caminho))
