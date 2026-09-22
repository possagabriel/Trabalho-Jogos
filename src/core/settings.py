"""Configuracoes persistidas da aplicacao canônica."""

from __future__ import annotations

import json
import os
from typing import Any

import pygame

from src.shared.persistence import carregar_json_resiliente, salvar_json_atomico
from src.shared.user_data import diretorio_dados

from .constants import ALTURA, LARGURA

PASTA_DADOS = diretorio_dados()
ARQUIVO_CONFIG = os.path.join(PASTA_DADOS, "settings.json")
RESOLUCOES = ["900x700", "1024x768", "1280x720", "1280x800", "1366x768",
              "1440x900", "1600x900", "1680x1050", "1920x1080", "2560x1080",
              "2560x1440", "3440x1440", "3840x2160"]
TEMAS = ["NEON", "AURORA", "MAGMA"]
QUALIDADES_GRAFICAS = ["ALTA", "EQUILIBRADA", "DESEMPENHO"]
ACOES_CONTROLE = [
    "cima", "baixo", "esquerda", "direita", "atirar", "esquivar", "pausar",
]
DEFAULT_CONTROLES = {
    "cima": pygame.K_UP, "baixo": pygame.K_DOWN, "esquerda": pygame.K_LEFT,
    "direita": pygame.K_RIGHT, "atirar": pygame.K_SPACE,
    "esquivar": pygame.K_x, "pausar": pygame.K_p,
}
_DEFAULT: dict[str, Any] = {
    "musica_volume": 0.8, "efeitos_volume": 0.8, "resolucao": "1920x1080",
    "tela_cheia": False, "sensibilidade": 1.0, "controles": DEFAULT_CONTROLES,
    "tema": "NEON", "aspecto": "AJUSTAR", "ajuste_escala": 1.0,
    "ajuste_off_x": 0, "ajuste_off_y": 0, "qualidade_grafica": "ALTA",
    "mostrar_desempenho": False,
    "estilo_visual": "COMIC", "qualidade_comic": "MEDIA",
    "comic_papel": True, "comic_halftone": True, "comic_hachuras": True,
    "line_boil": False,
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
            dados = carregar_json_resiliente(ARQUIVO_CONFIG)
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
        return salvar_json_atomico(ARQUIVO_CONFIG, self._dados)

    def __getitem__(self, chave: str) -> Any:
        return self._dados[chave]

    def __setitem__(self, chave: str, valor: Any) -> None:
        self._dados[chave] = valor

    @property
    def controles(self) -> dict[str, int]:
        """Mapeamento de acoes para teclas pygame."""
        return self._dados["controles"]
