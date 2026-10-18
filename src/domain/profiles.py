"""Modelo versionado de um perfil local de jogador."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = 1
MAX_MONEY = 2**63 - 1


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
