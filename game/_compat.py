"""Utilitario para manter imports do pacote legado durante a migracao."""

import sys
from importlib import import_module


def substituir_modulo(nome_fachada: str, nome_canonico: str) -> None:
    """Faz o import legado referenciar o modulo canonico sem duplicar estado."""
    sys.modules[nome_fachada] = import_module(nome_canonico)
