"""Configuracoes persistidas da aplicacao canônica."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import pygame

from .constants import ALTURA, LARGURA

PASTA_DADOS = (os.environ.get("SPACEFURY_DATA_DIR") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data"))
ARQUIVO_CONFIG = os.path.join(PASTA_DADOS, "settings.json")
LOGGER = logging.getLogger(__name__)

RESOLUCOES = ["900x700", "1024x768", "1280x720", "1280x800", "1366x768",
              "1440x900", "1600x900", "1680x1050", "1920x1080", "2560x1080",
              "2560x1440", "3440x1440", "3840x2160"]
TEMAS = ["NEON", "AURORA", "MAGMA"]
ACOES_CONTROLE = ["cima", "baixo", "esquerda", "direita", "atirar", "pausar"]
DEFAULT_CONTROLES = {
    "cima": pygame.K_UP, "baixo": pygame.K_DOWN, "esquerda": pygame.K_LEFT,
    "direita": pygame.K_RIGHT, "atirar": pygame.K_SPACE, "pausar": pygame.K_p,
}
_DEFAULT: dict[str, Any] = {
    "musica_volume": 0.8, "efeitos_volume": 0.8, "resolucao": "900x700",
    "tela_cheia": False, "sensibilidade": 1.0, "controles": DEFAULT_CONTROLES,
    "tema": "NEON", "aspecto": "AJUSTAR", "ajuste_escala": 1.0,
    "ajuste_off_x": 0, "ajuste_off_y": 0,
}


def parse_resolucao(texto: str | None) -> tuple[int, int]:
    """Converte uma resolucao textual, usando a superficie logica no fallback."""
    try:
        largura, altura = texto.lower().split("x")
        return int(largura), int(altura)
    except (ValueError, AttributeError):
        return LARGURA, ALTURA


class Configuracoes:
    """Configuracoes do jogador com carregamento e persistencia em JSON."""

    def __init__(self) -> None:
        self._dados = self._carregar()

    def _carregar(self) -> dict[str, Any]:
        try:
            with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
            valores = dict(_DEFAULT)
            valores.update(dados)
            controles = dict(DEFAULT_CONTROLES)
            controles.update(valores.get("controles", {}))
            valores["controles"] = controles
            return valores
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {chave: dict(valor) if isinstance(valor, dict) else valor
                    for chave, valor in _DEFAULT.items()}

    def salvar(self) -> bool:
        """Persiste as configuracoes e informa se a gravacao foi concluida."""
        os.makedirs(PASTA_DADOS, exist_ok=True)
        try:
            with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as arquivo:
                json.dump(self._dados, arquivo, ensure_ascii=False, indent=2)
        except OSError as erro:
            LOGGER.warning("Nao foi possivel salvar configuracoes: %s", erro)
            return False
        return True

    def __getitem__(self, chave: str) -> Any:
        return self._dados[chave]

    def __setitem__(self, chave: str, valor: Any) -> None:
        self._dados[chave] = valor

    @property
    def controles(self) -> dict[str, int]:
        """Mapeamento de acoes para teclas pygame."""
        return self._dados["controles"]
