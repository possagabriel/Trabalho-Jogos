"""Utilitarios seguros para persistencia local em JSON."""

import json
import logging
import os
import tempfile


logger = logging.getLogger(__name__)


def salvar_json_atomico(caminho, dados):
    """Grava ``dados`` sem deixar um arquivo parcial em caso de interrupcao."""
    pasta = os.path.dirname(caminho) or "."
    os.makedirs(pasta, exist_ok=True)
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=pasta, prefix=".incarnate-",
                suffix=".tmp", delete=False) as arquivo:
            temporario = arquivo.name
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, caminho)
        return True
    except (OSError, TypeError, ValueError):
        logger.exception("Nao foi possivel salvar %s", caminho)
        if temporario:
            try:
                os.unlink(temporario)
            except OSError:
                pass
        return False
