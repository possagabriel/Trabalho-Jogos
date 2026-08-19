"""Configuracoes do jogo persistidas em JSON (volume, video, controles)."""

import json
import os

import pygame

from .config import ALTURA, LARGURA

# Diretorio de dados (JSON) do jogo. Pode ser redirecionado via variavel de
# ambiente (ex.: testes) sem afetar a leitura das fontes em data/fonts.
PASTA_DADOS = (os.environ.get("SPACEFURY_DATA_DIR")
               or os.path.join(os.path.dirname(os.path.dirname(
                   os.path.abspath(__file__))), "data"))
ARQUIVO_CONFIG = os.path.join(PASTA_DADOS, "settings.json")

RESOLUCOES = ["900x700", "1280x720", "1600x900", "1920x1080"]
TEMAS = ["NEON", "AURORA", "MAGMA"]

ACOES_CONTROLE = ["cima", "baixo", "esquerda", "direita", "atirar", "pausar"]

DEFAULT_CONTROLES = {
    "cima": pygame.K_UP,
    "baixo": pygame.K_DOWN,
    "esquerda": pygame.K_LEFT,
    "direita": pygame.K_RIGHT,
    "atirar": pygame.K_SPACE,
    "pausar": pygame.K_p,
}

_DEFAULT = {
    "musica_volume": 0.8,
    "efeitos_volume": 0.8,
    "resolucao": "900x700",
    "tela_cheia": False,
    "sensibilidade": 1.0,
    "controles": DEFAULT_CONTROLES,
    "tema": "NEON",
}


def parse_resolucao(texto):
    """Converte '1280x720' em tupla (1280, 720)."""
    try:
        larg, alt = texto.lower().split("x")
        return int(larg), int(alt)
    except (ValueError, AttributeError):
        return LARGURA, ALTURA


class Configuracoes:
    """Configuracoes do jogador com carregamento e persistencia em JSON."""

    def __init__(self):
        self._dados = self._carregar()

    def _carregar(self):
        try:
            with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
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

    def salvar(self):
        os.makedirs(PASTA_DADOS, exist_ok=True)
        try:
            with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
                json.dump(self._dados, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def __getitem__(self, chave):
        return self._dados[chave]

    def __setitem__(self, chave, valor):
        self._dados[chave] = valor

    @property
    def controles(self):
        return self._dados["controles"]