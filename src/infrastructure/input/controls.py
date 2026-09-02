"""Control configuration from game settings.

Defines the mapping of actions to physical keys and provides a persistent
configuration object that can be serialised to JSON.

Migrated from game/settings.py (``DEFAULT_CONTROLES``, ``Configuracoes``,
``parse_resolucao``).
"""

import json
import os
from typing import Any, Dict, Optional

import pygame

# Default key bindings (Pygame key constants).
DEFAULT_CONTROLES: Dict[str, int] = {
    "cima": pygame.K_UP,
    "baixo": pygame.K_DOWN,
    "esquerda": pygame.K_LEFT,
    "direita": pygame.K_RIGHT,
    "atirar": pygame.K_SPACE,
    "pausar": pygame.K_p,
}

# List of all valid action names.
ACOES_CONTROLE = ["cima", "baixo", "esquerda", "direita", "atirar", "pausar"]

# Available resolutions for the display selector.
RESOLUCOES = [
    "900x700", "1024x768", "1280x720", "1280x800", "1366x768",
    "1440x900", "1600x900", "1680x1050", "1920x1080", "2560x1080",
    "2560x1440", "3440x1440", "3840x2160",
]

TEMAS = ["NEON", "AURORA", "MAGMA"]

# Data directory -- can be overridden via env var for testing.
PASTA_DADOS = (os.environ.get("INCARNATE_DATA_DIR")
               or os.environ.get("SPACE" + "FURY_DATA_DIR")
               or os.path.join(os.path.dirname(os.path.dirname(
                   os.path.abspath(__file__))), "data"))
ARQUIVO_CONFIG = os.path.join(PASTA_DADOS, "settings.json")

# Logical (design) resolution used as the base for scaling.
LARGURA_LOGICA = 900
ALTURA_LOGICA = 700

_DEFAULT: Dict[str, Any] = {
    "musica_volume": 0.8,
    "efeitos_volume": 0.8,
    "resolucao": "900x700",
    "tela_cheia": False,
    "sensibilidade": 1.0,
    "controles": dict(DEFAULT_CONTROLES),
    "tema": "NEON",
    "aspecto": "AJUSTAR",
    "ajuste_escala": 1.0,
    "ajuste_off_x": 0,
    "ajuste_off_y": 0,
}


def parse_resolucao(texto: str) -> tuple:
    """Convert ``'1280x720'`` to ``(1280, 720)``."""
    try:
        larg, alt = texto.lower().split("x")
        return int(larg), int(alt)
    except (ValueError, AttributeError):
        return LARGURA_LOGICA, ALTURA_LOGICA


class ControleConfiguracao:
    """Game settings with JSON load/save persistence.

    Mirrors the original ``Configuracoes`` class but lives in the
    infrastructure layer so the domain layer has no direct file I/O.
    """

    def __init__(self, caminho: "str | None" = None):
        self._caminho = caminho or ARQUIVO_CONFIG
        self._dados: Dict[str, Any] = self._carregar()

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def _carregar(self) -> Dict[str, Any]:
        try:
            with open(self._caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)
            valores = dict(_DEFAULT)
            valores.update(dados)
            controles = dict(DEFAULT_CONTROLES)
            controles.update(valores.get("controles", {}))
            valores["controles"] = controles
            return valores
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {k: (dict(v) if isinstance(v, dict) else v)
                    for k, v in _DEFAULT.items()}

    def salvar(self) -> None:
        os.makedirs(os.path.dirname(self._caminho), exist_ok=True)
        try:
            with open(self._caminho, "w", encoding="utf-8") as f:
                json.dump(self._dados, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Dict-like access
    # ------------------------------------------------------------------

    def __getitem__(self, chave: str) -> Any:
        return self._dados[chave]

    def __setitem__(self, chave: str, valor: Any) -> None:
        self._dados[chave] = valor

    def __contains__(self, chave: str) -> bool:
        return chave in self._dados

    # ------------------------------------------------------------------
    # Convenience properties
    # ------------------------------------------------------------------

    @property
    def controles(self) -> Dict[str, int]:
        return self._dados["controles"]

    @property
    def tema(self) -> str:
        return self._dados.get("tema", "NEON")

    @property
    def resolucao(self) -> str:
        return self._dados.get("resolucao", "900x700")

    @property
    def tela_cheia(self) -> bool:
        return self._dados.get("tela_cheia", False)

    @property
    def sensibilidade(self) -> float:
        return self._dados.get("sensibilidade", 1.0)

    @property
    def musica_volume(self) -> float:
        return self._dados.get("musica_volume", 0.8)

    @property
    def efeitos_volume(self) -> float:
        return self._dados.get("efeitos_volume", 0.8)

    @property
    def aspecto(self) -> str:
        return self._dados.get("aspecto", "AJUSTAR")

    @property
    def ajuste_escala(self) -> float:
        return self._dados.get("ajuste_escala", 1.0)

    @property
    def ajuste_off_x(self) -> int:
        return self._dados.get("ajuste_off_x", 0)

    @property
    def ajuste_off_y(self) -> int:
        return self._dados.get("ajuste_off_y", 0)
