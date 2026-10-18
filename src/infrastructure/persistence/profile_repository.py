"""Repositório JSON de perfis no diretório de dados da aplicação."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from uuid import UUID

from src.domain.profiles import Profile
from src.shared.persistence import salvar_json_atomico
from src.shared.user_data import diretorio_dados

LOGGER = logging.getLogger(__name__)


class JsonProfileRepository:
    """Armazena um JSON por UUID com escrita atômica e cópia anterior."""

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir or diretorio_dados())
        self.folder = self.data_dir / "profiles"
        self.index_path = self.folder / "index.json"
        self.migration_marker = self.folder / ".migration-complete"
        self.folder.mkdir(parents=True, exist_ok=True)

    def profile_path(self, profile_id: str) -> Path:
        """Resolve somente UUID válido dentro da pasta de perfis."""
        return self.folder / f"{UUID(profile_id)}.json"

    def backup_path(self, profile_id: str) -> Path:
        """Resolve o backup de um perfil."""
        return Path(f"{self.profile_path(profile_id)}.bak")

    def load(self, profile_id: str) -> Profile:
        """Carrega arquivo principal ou backup e valida seu UUID."""
        path = self.profile_path(profile_id)
        for candidate in (path, self.backup_path(profile_id)):
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                profile = Profile.from_dict(data)
                if profile.id != profile_id:
                    raise ValueError("ID divergente")
                if candidate != path:
                    salvar_json_atomico(path, profile.to_dict(), criar_backup=False)
                return profile
            except (OSError, ValueError, TypeError) as exc:
                LOGGER.warning("Perfil ilegível em %s: %s", candidate, exc)
        raise ValueError(f"Perfil danificado: {profile_id}")

    def save(self, profile: Profile) -> bool:
        """Salva o perfil sem alterar o arquivo antigo em caso de falha."""
        return salvar_json_atomico(self.profile_path(profile.id), profile.to_dict())

    def write_raw(self, profile_id: str, data: dict[str, Any]) -> None:
        """Grava dados de fixture para testes de compatibilidade."""
        self.profile_path(profile_id).write_text(json.dumps(data), encoding="utf-8")

    def read_index(self) -> dict[str, Any]:
        """Carrega o índice ou o reconstrói dos arquivos de perfil."""
        try:
            index = json.loads(self.index_path.read_text(encoding="utf-8"))
            if not isinstance(index, dict) or not isinstance(index.get("profiles"), list):
                raise ValueError("Índice inválido")
            for row in index["profiles"]:
                if (not isinstance(row, dict) or not isinstance(row.get("name"), str)
                        or not isinstance(row.get("id"), str)):
                    raise ValueError("Entrada inválida no índice")
                UUID(row["id"])
            index.setdefault("last_used", None)
            index.setdefault("migration_complete", self.migration_marker.exists())
            return index
        except (OSError, ValueError, json.JSONDecodeError):
            index = {"schema_version": 1, "profiles": [], "last_used": None,
                     "migration_complete": self.migration_marker.exists()}
            candidates = sorted(set(self.folder.glob("*.json")) |
                                set(self.folder.glob("*.json.bak")))
            seen: set[str] = set()
            for path in candidates:
                if path.name.startswith("index.json"):
                    continue
                try:
                    raw_id = path.name.removesuffix(".json.bak").removesuffix(".json")
                    profile_id = str(UUID(raw_id))
                    if profile_id in seen:
                        continue
                    seen.add(profile_id)
                    try:
                        profile = self.load(profile_id)
                        name = profile.name
                    except (ValueError, OSError):
                        name = f"DANIFICADO {profile_id[:8]}"
                    index["profiles"].append({"id": profile_id, "name": name})
                except (ValueError, OSError):
                    LOGGER.warning("Arquivo de perfil órfão inválido: %s", path)
            self.write_index(index)
            return index

    def write_index(self, index: dict[str, Any]) -> bool:
        """Atualiza metadados derivados e marcador de migração."""
        if not salvar_json_atomico(self.index_path, index):
            return False
        if index.get("migration_complete"):
            try:
                self.migration_marker.touch(exist_ok=True)
            except OSError as exc:
                LOGGER.warning("Não foi possível marcar migração: %s", exc)
                return False
        return True

    def delete(self, profile_id: str) -> None:
        """Apaga arquivo e backup após atualização do índice."""
        for path in (self.profile_path(profile_id), self.backup_path(profile_id)):
            path.unlink(missing_ok=True)

    def clean_orphans(self, known_ids: set[str]) -> None:
        """Remove arquivos que não constam no índice válido."""
        candidates = set(self.folder.glob("*.json")) | set(self.folder.glob("*.json.bak"))
        for path in candidates:
            if path.name.startswith("index.json"):
                continue
            try:
                raw_id = path.name.removesuffix(".json.bak").removesuffix(".json")
                profile_id = str(UUID(raw_id))
            except ValueError:
                continue
            if profile_id not in known_ids:
                try:
                    self.delete(profile_id)
                except OSError as exc:
                    LOGGER.warning("Não foi possível limpar perfil órfão %s: %s",
                                   profile_id, exc)
