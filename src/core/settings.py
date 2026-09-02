"""Gerenciador de configuracoes persistido em JSON.

Singleton que carrega e salva as preferencias do jogador (volume, video,
controles, tema). O arquivo de configuracao fica em ``data/settings.json``
relativo a raiz do projeto, mas pode ser redirecionado pela variavel de
ambiente ``INCARNATE_DATA_DIR``.
"""

from __future__ import annotations

import json
import os
from typing import Any

import pygame

from .constants import ALTURA, LARGURA

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------

PASTA_DADOS: str = (
    os.environ.get("INCARNATE_DATA_DIR")
    or os.environ.get("SPACE" + "FURY_DATA_DIR")
    or os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "data")
)
"""Diretorio de dados do jogo (JSON, saves, etc.)."""

ARQUIVO_CONFIG: str = os.path.join(PASTA_DADOS, "settings.json")
"""Caminho completo do arquivo de configuracoes."""

# ---------------------------------------------------------------------------
# Listas de opcoes
# ---------------------------------------------------------------------------

RESOLUCOES: list[str] = [
    "900x700", "1024x768", "1280x720", "1280x800", "1366x768",
    "1440x900", "1600x900", "1680x1050", "1920x1080", "2560x1080",
    "2560x1440", "3440x1440", "3840x2160",
]
"""Resolucoes suportadas para modo janela."""

TEMAS: list[str] = ["NEON", "AURORA", "MAGMA"]
"""Temas visuais disponiveis."""

ACOES_CONTROLE: list[str] = [
    "cima", "baixo", "esquerda", "direita", "atirar", "pausar",
]
"""Nomes das acoes mapeaveis nos controles."""

# ---------------------------------------------------------------------------
# Controles padrao (valores pygame.K_*)
# ---------------------------------------------------------------------------

DEFAULT_CONTROLES: dict[str, int] = {
    "cima": pygame.K_UP,
    "baixo": pygame.K_DOWN,
    "esquerda": pygame.K_LEFT,
    "direita": pygame.K_RIGHT,
    "atirar": pygame.K_SPACE,
    "pausar": pygame.K_p,
}
"""Mapeamento padrao de acoes para teclas pygame."""

# ---------------------------------------------------------------------------
# Valores padrao
# ---------------------------------------------------------------------------

_DEFAULT: dict[str, Any] = {
    "musica_volume": 0.8,
    "efeitos_volume": 0.8,
    "resolucao": "900x700",
    "tela_cheia": False,
    "sensibilidade": 1.0,
    "controles": DEFAULT_CONTROLES,
    "tema": "NEON",
    "aspecto": "AJUSTAR",
    "ajuste_escala": 1.0,
    "ajuste_off_x": 0,
    "ajuste_off_y": 0,
}


# ---------------------------------------------------------------------------
# Funcoes auxiliares
# ---------------------------------------------------------------------------

def parse_resolucao(texto: str) -> tuple[int, int]:
    """Converte ``'1280x720'`` em tupla ``(1280, 720)``.

    Em caso de falha retorna a resolucao logica padrao ``(LARGURA, ALTURA)``.
    """
    try:
        larg, alt = texto.lower().split("x")
        return int(larg), int(alt)
    except (ValueError, AttributeError):
        return LARGURA, ALTURA


# ---------------------------------------------------------------------------
# Configuracoes (Singleton)
# ---------------------------------------------------------------------------

class Configuracoes:
    """Configuracoes do jogador com carregamento e persistencia em JSON.

    Uso::

        cfg = Configuracoes()
        cfg["musica_volume"] = 0.5
        cfg.salvar()
    """

    _instancia: Configuracoes | None = None

    def __new__(cls) -> Configuracoes:
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._initialized = False
        return cls._instancia

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._dados: dict[str, Any] = self._carregar()

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    def _carregar(self) -> dict[str, Any]:
        """Le o JSON do disco e mescla com os valores padrao."""
        try:
            with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as fh:
                dados = json.load(fh)
            valores = dict(_DEFAULT)
            valores.update(dados)
            controles = dict(DEFAULT_CONTROLES)
            controles.update(valores.get("controles", {}))
            valores["controles"] = controles
            return valores
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {
                k: (dict(v) if isinstance(v, dict) else v)
                for k, v in _DEFAULT.items()
            }

    def salvar(self) -> None:
        """Serializa as configuracoes atuais no disco."""
        os.makedirs(PASTA_DADOS, exist_ok=True)
        try:
            with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as fh:
                json.dump(self._dados, fh, ensure_ascii=False, indent=2)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Acesso
    # ------------------------------------------------------------------

    def __getitem__(self, chave: str) -> Any:
        return self._dados[chave]

    def __setitem__(self, chave: str, valor: Any) -> None:
        self._dados[chave] = valor

    @property
    def controles(self) -> dict[str, int]:
        """Dicionario de mapeamento acao -> tecla pygame."""
        return self._dados["controles"]
