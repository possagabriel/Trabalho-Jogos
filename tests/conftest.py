"""Configuracao do pytest para a suite de testes.

Garante que o ambiente headless (drivers dummy do SDL) e o diretorio de
dados temporario sejam definidos ANTES de qualquer modulo do jogo ser
importado, independente da ordem de coleta dos arquivos.
"""

import os
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault(
    "INCARNATE_DATA_DIR",
    tempfile.mkdtemp(prefix="incarnate_pytest_"))

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import pytest  # noqa: E402

import pygame  # noqa: E402


@pytest.fixture(autouse=True)
def _limpar_eventos_pygame():
    """Drena a fila de eventos do pygame entre testes (evita vazamento)."""
    yield
    if pygame.get_init():
        pygame.event.clear()