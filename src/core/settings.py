"""Configuracoes persistidas da aplicacao canônica."""

from __future__ import annotations

import json
import math
import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pygame

from src.shared.persistence import carregar_json_resiliente, salvar_json_atomico
from src.shared.user_data import diretorio_dados

if TYPE_CHECKING:
    from src.domain.systems.profile_service import ProfileService

from .constants import (
    ALTURA, DISPERSAO_DUPLO_GRAUS, DISPERSAO_ESPIRAL_GRAUS, LARGURA,
)

PASTA_DADOS = diretorio_dados()
ARQUIVO_CONFIG = os.path.join(PASTA_DADOS, "settings.json")
RESOLUCOES = ["900x700", "1024x768", "1280x720", "1280x800", "1366x768",
              "1440x900", "1600x900", "1680x1050", "1920x1080", "2560x1080",
              "2560x1440", "3440x1440", "3840x2160"]
TEMAS = ["NEON", "AURORA", "MAGMA"]
QUALIDADES_GRAFICAS = ["ALTA", "EQUILIBRADA", "DESEMPENHO"]
INTENSIDADES_VISUAIS = ("NORMAL", "REDUZIDO", "DESLIGADO")
ESCALAS_VISUAIS = {"NORMAL": 1.0, "REDUZIDO": 0.3, "DESLIGADO": 0.0}
ACOES_CONTROLE = [
    "cima", "baixo", "esquerda", "direita", "atirar", "esquivar", "pausar",
]
DEFAULT_CONTROLES = {
    "cima": pygame.K_UP, "baixo": pygame.K_DOWN, "esquerda": pygame.K_LEFT,
    "direita": pygame.K_RIGHT, "atirar": pygame.K_SPACE,
    "esquivar": pygame.K_x, "pausar": pygame.K_p,
}
VELOCIDADES_AVANCO_PADRAO = {"1": 120, "2": 135, "3": 105,
                             "4": 115, "5": 145, "6": 125}
_DEFAULT: dict[str, Any] = {
    "musica_volume": 0.8, "efeitos_volume": 0.8, "resolucao": "1920x1080",
    "tela_cheia": False, "sensibilidade": 1.0, "controles": DEFAULT_CONTROLES,
    "tema": "NEON", "aspecto": "AJUSTAR", "ajuste_escala": 1.0,
    "ajuste_off_x": 0, "ajuste_off_y": 0, "qualidade_grafica": "ALTA",
    "mostrar_desempenho": False,
    "mira_ativa": True,
    "velocidade_dialogo": 42,
    "dispersao_duplo_graus": DISPERSAO_DUPLO_GRAUS,
    "dispersao_espiral_graus": DISPERSAO_ESPIRAL_GRAUS,
    "estilo_visual": "COMIC", "qualidade_comic": "MEDIA",
    "comic_papel": True, "comic_halftone": True, "comic_hachuras": True,
    "line_boil": False,
    "intensidade_flash": "NORMAL", "intensidade_tremor": "NORMAL",
    "mostrar_hitbox": False,
    "avanco_camadas": True, "avanco_linhas": True,
    "avanco_pico": True, "avanco_parada_boss": True,
    "avanco_qualidade": "MEDIA", "avanco_intensidade": 1.0,
    "avanco_direcao": [0, 1],
    "avanco_freada_s": 1.5, "avanco_aceleracao_s": 1.2,
    "avanco_pico_s": 0.3, "avanco_pico_intensidade": 0.25,
    "avanco_salto_s": 1.0, "avanco_salto_intensidade": 0.5,
    "avanco_linhas_intensidade": 1.0,
    "avanco_desvio_parado": 0.04,
    "avanco_miniboss_percentual": 0.5,
    "avanco_miniboss_tipos": {},
    "avanco_velocidades": VELOCIDADES_AVANCO_PADRAO,
    "limite_perfis": 5,
    "limite_nome_perfil": 16,
    "shader_comic": True, "intensidade_shader": 0.7,
    "contorno_shader": 0.75, "tons_shader": 3,
    "hachuras_shader": True, "grao_shader": 0.35,
    "saturacao_shader": 1.1, "preservar_interface": True,
}
PREFERENCIAS_PERFIL = ("controles", "sensibilidade", "mira_ativa")


def escala_visual(intensidade: str) -> float:
    """Converte uma intensidade salva em escala visual com fallback seguro."""
    return ESCALAS_VISUAIS.get(intensidade, 1.0)


def _limitar_numero(valor: Any, padrao: float, minimo: float, maximo: float) -> float:
    """Lê um número de JSON com limites seguros para a simulação."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return padrao
    return max(minimo, min(maximo, numero)) if math.isfinite(numero) else padrao


def _normalizar_avanco(valores: dict[str, Any]) -> None:
    """Mescla e valida parâmetros de avanço sem perder opções de saves antigos."""
    qualidade = str(valores.get("avanco_qualidade", "MEDIA")).upper()
    valores["avanco_qualidade"] = qualidade if qualidade in ("BAIXA", "MEDIA", "ALTA") \
        else "MEDIA"
    direcao = valores.get("avanco_direcao", [0, 1])
    try:
        x, y = float(direcao[0]), float(direcao[1])
        if not (math.isfinite(x) and math.isfinite(y) and (x or y)):
            raise ValueError
        valores["avanco_direcao"] = [x, y]
    except (IndexError, KeyError, TypeError, ValueError):
        valores["avanco_direcao"] = [0, 1]
    limites = {
        "avanco_intensidade": (1, 0, 2),
        "avanco_freada_s": (1.5, 0.1, 5),
        "avanco_aceleracao_s": (1.2, 0.1, 5),
        "avanco_pico_s": (0.3, 0, 2),
        "avanco_pico_intensidade": (0.25, 0, 1),
        "avanco_salto_s": (1, 0, 3),
        "avanco_salto_intensidade": (0.5, 0, 2),
        "avanco_linhas_intensidade": (1, 0, 2),
        "avanco_desvio_parado": (0.04, 0, 0.1),
        "avanco_miniboss_percentual": (0.5, 0, 1),
    }
    for chave, (padrao, minimo, maximo) in limites.items():
        valores[chave] = _limitar_numero(valores.get(chave), padrao, minimo, maximo)
    velocidades = valores.get("avanco_velocidades", {})
    velocidades = velocidades if isinstance(velocidades, dict) else {}
    valores["avanco_velocidades"] = {
        chave: _limitar_numero(velocidades.get(chave), padrao, 0, 500)
        for chave, padrao in VELOCIDADES_AVANCO_PADRAO.items()
    }
    tipos = valores.get("avanco_miniboss_tipos", {})
    valores["avanco_miniboss_tipos"] = (
        {str(chave): _limitar_numero(valor, 0.5, 0, 1)
         for chave, valor in tipos.items()} if isinstance(tipos, dict) else {}
    )



def limitar_float(
    valor: object,
    padrao: float,
    minimo: float = 0.0,
    maximo: float = 1.0,
) -> float:
    """Converte e limita um valor numerico persistido."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        numero = padrao
    return max(minimo, min(maximo, numero))


def _ler_config(config: Mapping[str, Any] | Any, chave: str, padrao: Any) -> Any:
    try:
        return config[chave]
    except (KeyError, TypeError):
        return padrao


@dataclass(frozen=True)
class OpcoesShaderComic:
    """Estado validado do acabamento comic enviado ao apresentador GPU."""

    ativo: bool = True
    intensidade: float = 0.7
    qualidade: str = "MEDIA"
    contorno: float = 0.75
    tons: int = 3
    hachuras: bool = True
    grao: float = 0.35
    saturacao: float = 1.1
    preservar_interface: bool = True

    @classmethod
    def de_config(cls, config: Mapping[str, Any] | Any) -> "OpcoesShaderComic":
        """Cria opções seguras a partir de um mapeamento ou Configuracoes."""
        qualidade = str(_ler_config(config, "qualidade_comic", "MEDIA")).upper()
        if qualidade not in ("BAIXA", "MEDIA", "ALTA"):
            qualidade = "MEDIA"
        try:
            tons = int(_ler_config(config, "tons_shader", 3))
        except (TypeError, ValueError):
            tons = 3
        return cls(
            ativo=(
                _ler_config(config, "estilo_visual", "COMIC") == "COMIC"
                and bool(_ler_config(config, "shader_comic", True))
            ),
            intensidade=limitar_float(
                _ler_config(config, "intensidade_shader", 0.7), 0.7),
            qualidade=qualidade,
            contorno=limitar_float(
                _ler_config(config, "contorno_shader", 0.75), 0.75),
            tons=tons if tons in (3, 4, 6) else 3,
            hachuras=bool(_ler_config(config, "hachuras_shader", True)),
            grao=limitar_float(
                _ler_config(config, "grao_shader", 0.35), 0.35),
            saturacao=limitar_float(
                _ler_config(config, "saturacao_shader", 1.1), 1.1, 0.5, 1.5),
            preservar_interface=bool(
                _ler_config(config, "preservar_interface", True)),
        )


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
        self.profile_service = None
        self._dados = self._carregar()

    def _carregar(self) -> dict[str, Any]:
        try:
            dados = carregar_json_resiliente(ARQUIVO_CONFIG)
            valores = dict(_DEFAULT)
            valores.update(dados)
            controles = dict(DEFAULT_CONTROLES)
            controles.update(valores.get("controles", {}))
            valores["controles"] = controles
            _normalizar_avanco(valores)
            valores["velocidade_dialogo"] = _limitar_numero(
                valores.get("velocidade_dialogo"), 42, 10, 120)
            valores["limite_perfis"] = int(_limitar_numero(
                valores.get("limite_perfis"), 5, 1, 20))
            valores["limite_nome_perfil"] = int(_limitar_numero(
                valores.get("limite_nome_perfil"), 16, 1, 32))
            valores["shader_comic"] = bool(valores.get("shader_comic", True))
            shader = OpcoesShaderComic.de_config(valores)
            valores.update({
                "intensidade_shader": shader.intensidade,
                "contorno_shader": shader.contorno,
                "tons_shader": shader.tons,
                "hachuras_shader": shader.hachuras,
                "grao_shader": shader.grao,
                "saturacao_shader": shader.saturacao,
                "preservar_interface": shader.preservar_interface,
            })
            return valores
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            valores = {chave: dict(valor) if isinstance(valor, dict) else valor
                       for chave, valor in _DEFAULT.items()}
            _normalizar_avanco(valores)
            valores["velocidade_dialogo"] = _limitar_numero(
                valores.get("velocidade_dialogo"), 42, 10, 120)
            valores["limite_perfis"] = 5
            valores["limite_nome_perfil"] = 16
            return valores

    def salvar(self) -> bool:
        """Persiste as configuracoes e informa se a gravacao foi concluida."""
        if self.profile_service is not None and self.profile_service.active is not None:
            self.profile_service.active.preferences = {
                key: self._dados[key] for key in PREFERENCIAS_PERFIL
            }
            self.profile_service._save()
        globais = {key: value for key, value in self._dados.items()
                   if key not in PREFERENCIAS_PERFIL}
        return salvar_json_atomico(ARQUIVO_CONFIG, globais)

    def aplicar_perfil(self, profile_service: ProfileService) -> None:
        """Aplica comandos e preferências do perfil selecionado."""
        self.profile_service = profile_service
        profile = profile_service.active
        preferences = profile.preferences if profile else {}
        controls = dict(DEFAULT_CONTROLES)
        controls.update(preferences.get("controles", {}))
        self._dados["controles"] = controls
        self._dados["sensibilidade"] = preferences.get("sensibilidade", 1.0)
        self._dados["mira_ativa"] = preferences.get("mira_ativa", True)

    def __getitem__(self, chave: str) -> Any:
        return self._dados[chave]

    def __setitem__(self, chave: str, valor: Any) -> None:
        self._dados[chave] = valor

    @property
    def controles(self) -> dict[str, int]:
        """Mapeamento de acoes para teclas pygame."""
        return self._dados["controles"]
