"""Modelo versionado de um perfil local de jogador."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = 4
MAX_MONEY = 2**63 - 1


def _migrar_modos(progress: dict[str, Any]) -> None:
    """Cria cartões de modo a partir do save antigo sem remover campos."""
    progress.setdefault("modo_ultimo", "linear")
    progress.setdefault("modos", {})
    modes = progress["modos"]
    if not isinstance(modes, dict):
        return
    legacy = progress.get("legacy", {})
    player = legacy.get("jogador", {}) if isinstance(legacy, dict) else {}
    statistics = legacy.get("estatisticas", {}) if isinstance(legacy, dict) else {}
    campaign = player.get("progresso_campanha", {}) if isinstance(player, dict) else {}
    statistics = statistics if isinstance(statistics, dict) else {}
    campaign = campaign if isinstance(campaign, dict) else {}
    bosses = progress.get("bosses_por_tipo", {})
    linear_bosses = (sum(value for value in bosses.values()
                         if type(value) is int and value > 0)
                     if isinstance(bosses, dict) else
                     player.get("bosses_derrotados", 0)
                     if isinstance(player, dict) else 0)
    modes.setdefault("linear", {
        "nivel": progress.get("nivel_maximo", 1),
        "dimensao": progress.get("dimensao_maxima", 1),
        "bosses": linear_bosses,
        "moedas": progress.get("moedas", player.get("moedas", 0)
                               if isinstance(player, dict) else 0),
        "tempo": progress.get("tempo_total", statistics.get("tempo_total", 0)),
        "fase_atual": campaign.get("fase_atual", "lealdade"),
        "nivel_atual": campaign.get("nivel_atual", 1),
    })
    modes.setdefault("mundo_aberto", {
        "regioes_libertas": 0, "ecos": 0, "bosses": 0,
        "moedas": 0, "tempo": 0, "checkpoint": "inicio",
        "posicao": [520.0, 900.0], "partidas_jogadas": 0,
    })


def migrate_schema(data: dict[str, Any]) -> dict[str, Any]:
    """Atualiza formatos antigos em etapas sem sobrescrever dados desconhecidos."""
    version = data.get("schema_version", 0)
    if not isinstance(version, int) or version > SCHEMA_VERSION or version < 0:
        raise ValueError("Versão de perfil não suportada")
    result = dict(data)
    while version < SCHEMA_VERSION:
        if version == 0:
            result.setdefault("preferences", {})
            result.setdefault("progress", {})
            result["schema_version"] = 1
        elif version == 1:
            progress = result.setdefault("progress", {})
            if isinstance(progress, dict):
                progress.setdefault("novidades_vistas", {
                    "memorias": [], "hangar": [],
                })
            result["schema_version"] = 2
        elif version == 2:
            progress = result.setdefault("progress", {})
            if isinstance(progress, dict):
                progress.setdefault("novidades_pendentes", {"hangar": []})
            result["schema_version"] = 3
        elif version == 3:
            progress = result.setdefault("progress", {})
            if isinstance(progress, dict):
                _migrar_modos(progress)
            result["schema_version"] = 4
        version += 1
    return result


def now_iso() -> str:
    """Retorna instante UTC em formato persistível."""
    return datetime.now(timezone.utc).isoformat()


def initial_progress() -> dict[str, Any]:
    """Cria progresso independente para um perfil novo."""
    return {
        "moedas": 0, "nivel_maximo": 1, "dimensao_maxima": 1,
        "bosses_por_tipo": {}, "recorde_pontos": 0, "total_pontos": 0,
        "armas_desbloqueadas": [0], "arma_equipada": 0,
        "skins_desbloqueadas": ["padrao"], "skin_atual": "padrao",
        "melhorias_escolhidas": {}, "cenas_vistas": [], "memorias_desbloqueadas": [],
        "novidades_vistas": {"memorias": [], "hangar": []},
        "novidades_pendentes": {"hangar": []},
        "modo_ultimo": "linear",
        "modos": {
            "linear": {
                "nivel": 1, "dimensao": 1, "bosses": 0, "moedas": 0,
                "tempo": 0, "fase_atual": "lealdade", "nivel_atual": 1,
            },
            "mundo_aberto": {
                "regioes_libertas": 0, "ecos": 0, "bosses": 0,
                "moedas": 0, "tempo": 0, "checkpoint": "inicio",
                "posicao": [520.0, 900.0], "partidas_jogadas": 0,
            },
        },
        "partidas_jogadas": 0, "tempo_total": 0, "inimigos_derrotados": 0,
        "mortes": 0, "recordes": [], "legacy": {},
    }


@dataclass
class Profile:
    """Identidade estável e dados de progresso do jogador."""

    id: str
    name: str
    created_at: str
    last_access: str
    progress: dict[str, Any] = field(default_factory=initial_progress)
    preferences: dict[str, Any] = field(default_factory=dict)
    damaged: bool = False

    @classmethod
    def new(cls, name: str, preferences: dict[str, Any] | None = None) -> Profile:
        """Cria um perfil com UUID e horário UTC."""
        instant = now_iso()
        return cls(str(uuid4()), name, instant, instant, preferences=preferences or {})

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Profile:
        """Lê versão anterior preenchendo campos novos sem perder extras."""
        if not isinstance(data, dict) or not data.get("id") or not data.get("name"):
            raise ValueError("Perfil inválido")
        data = migrate_schema(data)
        progress = initial_progress()
        old_progress = data.get("progress", {})
        if not isinstance(old_progress, dict):
            raise ValueError("Progresso inválido")
        progress.update(old_progress)
        last_mode = progress.get("modo_ultimo")
        if not isinstance(last_mode, str) or last_mode not in {
                "linear", "mundo_aberto"}:
            progress["modo_ultimo"] = "linear"
        defaults = initial_progress()["modos"]
        modes = progress.get("modos")
        if not isinstance(modes, dict):
            modes = {}
        progress["modos"] = {}
        for mode, mode_defaults in defaults.items():
            mode_data = modes.get(mode, {})
            state = {**mode_defaults, **(
                mode_data if isinstance(mode_data, dict) else {})}
            for key, default in mode_defaults.items():
                value = state.get(key)
                if type(default) is int and (
                        type(value) is not int or value < 0):
                    state[key] = default
                elif type(default) is float and (
                        type(value) not in (int, float)
                        or not math.isfinite(value) or value < 0):
                    state[key] = default
                elif isinstance(default, str) and not isinstance(value, str):
                    state[key] = default
            position = state.get("posicao")
            if mode == "mundo_aberto":
                if (not isinstance(position, (list, tuple)) or len(position) != 2
                        or any(type(value) not in (int, float)
                               or not math.isfinite(value) or value < 0
                               for value in position)):
                    state["posicao"] = list(mode_defaults["posicao"])
                else:
                    state["posicao"] = [float(value) for value in position]
            progress["modos"][mode] = state
        return cls(
            str(data["id"]), str(data["name"]),
            str(data.get("created_at") or now_iso()),
            str(data.get("last_access") or now_iso()), progress,
            data.get("preferences", {}) if isinstance(data.get("preferences", {}), dict) else {},
        )

    def to_dict(self) -> dict[str, Any]:
        """Serializa o perfil para o repositório."""
        return {
            "schema_version": SCHEMA_VERSION, "id": self.id, "name": self.name,
            "created_at": self.created_at, "last_access": self.last_access,
            "progress": self.progress, "preferences": self.preferences,
        }
