"""Regras de negócio dos perfis e migração do save único."""

from __future__ import annotations

import json
import logging
import unicodedata
from copy import deepcopy
from importlib.resources import files
from pathlib import Path
from typing import Any

from src.domain.profiles import MAX_MONEY, Profile, initial_progress, now_iso
from src.domain.repository.profile_repository import ProfileRepository
from src.shared.persistence import carregar_json_resiliente, salvar_json_atomico

LOGGER = logging.getLogger(__name__)


class ProfileService:
    """Aplica validações e guarda o perfil ativo sem conhecer a UI."""

    def __init__(self, repository: ProfileRepository, max_profiles: int = 5,
                 max_name_length: int = 16) -> None:
        self.repository = repository
        self.max_profiles = max_profiles
        self.max_name_length = max_name_length
        self.index = repository.read_index()
        self.active: Profile | None = None
        self.dirty = False
        self.last_save: str | None = None
        self.save_error = False
        self.migration_error: str | None = None
        repository.clean_orphans({row["id"] for row in self.index["profiles"]})

    def _name(self, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Nome inválido")
        name = unicodedata.normalize("NFC", value.strip())
        if not name or len(name) > self.max_name_length:
            raise ValueError("Nome vazio ou longo demais")
        if any(not (ch.isalnum() or ch in " _-") for ch in name):
            raise ValueError("Caractere inválido")
        return name

    def _unique(self, name: str, except_id: str | None = None) -> None:
        if any(row["name"].casefold() == name.casefold() and row["id"] != except_id
               for row in self.index["profiles"]):
            raise ValueError("Nome já utilizado")

    def list_profiles(self) -> list[Profile]:
        """Lista perfis, preservando entradas danificadas para aviso na tela."""
        profiles = []
        for row in self.index["profiles"]:
            try:
                profile = self.repository.load(row["id"])
                self._validate_catalogs(profile)
                profiles.append(profile)
            except (ValueError, OSError, KeyError, TypeError):
                profiles.append(Profile(row["id"], row.get("name", "DANIFICADO"),
                                        "", "", damaged=True))
        return profiles

    def create(self, name: str, preferences: dict[str, Any] | None = None) -> Profile:
        """Cria perfil quando nome e limite permitem."""
        name = self._name(name)
        self._unique(name)
        if len(self.index["profiles"]) >= self.max_profiles:
            raise ValueError("Limite de perfis atingido")
        profile = Profile.new(name, deepcopy(preferences) if preferences else {})
        if not self.repository.save(profile):
            raise OSError("Não foi possível gravar o perfil")
        self.index["profiles"].append({"id": profile.id, "name": name})
        if not self.repository.write_index(self.index):
            self.index["profiles"].pop()
            raise OSError("Não foi possível atualizar o índice")
        return profile

    def select(self, profile_id: str) -> Profile:
        """Seleciona apenas um perfil válido e atualiza último acesso."""
        if profile_id not in {row["id"] for row in self.index["profiles"]}:
            raise KeyError(profile_id)
        profile = self.repository.load(profile_id)
        self._validate_catalogs(profile)
        profile.last_access = now_iso()
        self.active = profile
        self.index["last_used"] = profile_id
        self.repository.write_index(self.index)
        self._save()
        return profile

    def select_last(self) -> Profile | None:
        """Usa o último perfil apenas se ele puder ser carregado."""
        profile_id = self.index.get("last_used")
        if profile_id:
            try:
                return self.select(profile_id)
            except (KeyError, ValueError):
                pass
        return None

    def rename(self, profile_id: str, name: str) -> Profile:
        """Renomeia sem mudar o identificador estável."""
        name = self._name(name)
        self._unique(name, profile_id)
        profile = self.repository.load(profile_id)
        profile.name = name
        if not self.repository.save(profile):
            raise OSError("Não foi possível gravar o nome")
        for row in self.index["profiles"]:
            if row["id"] == profile_id:
                row["name"] = name
        self.repository.write_index(self.index)
        if self.active and self.active.id == profile_id:
            self.active = profile
        return profile

    def delete(self, profile_id: str, confirmation: str, in_game: bool = False) -> None:
        """Exige nome exato e remove índice antes do arquivo e backup."""
        if in_game and self.active and self.active.id == profile_id:
            raise ValueError("Perfil em uso durante a partida")
        row = next((row for row in self.index["profiles"] if row["id"] == profile_id), None)
        if row is None:
            raise KeyError(profile_id)
        if confirmation != row["name"]:
            raise ValueError("Confirmação incorreta")
        previous = deepcopy(self.index)
        self.index["profiles"] = [row for row in self.index["profiles"]
                                  if row["id"] != profile_id]
        if self.index.get("last_used") == profile_id:
            self.index["last_used"] = None
        if not self.repository.write_index(self.index):
            self.index = previous
            raise OSError("Não foi possível excluir do índice")
        self.repository.delete(profile_id)
        if self.active and self.active.id == profile_id:
            self.active = None
            self.dirty = False

    def _active(self) -> Profile:
        if self.active is None:
            raise KeyError("Nenhum perfil ativo")
        return self.active

    def _save(self) -> bool:
        self.dirty = True
        success = self.repository.save(self._active())
        self.save_error = not success
        if success:
            self.dirty = False
            self.last_save = now_iso()
        return success

    def flush(self) -> bool:
        """Tenta novamente a gravação pendente no encerramento."""
        return self._save() if self.active and self.dirty else True

    def credit(self, amount: int) -> int:
        """Credita moedas sem permitir números negativos ou excesso."""
        if type(amount) is not int or amount < 0:
            raise ValueError("Quantia inválida")
        progress = self._active().progress
        current = progress["moedas"]
        if amount > MAX_MONEY - current:
            raise ValueError("Saldo excede o limite")
        progress["moedas"] = current + amount
        self._save()
        return progress["moedas"]

    def spend(self, amount: int) -> int:
        """Debita somente quantia disponível."""
        if type(amount) is not int or amount < 0:
            raise ValueError("Quantia inválida")
        progress = self._active().progress
        if amount > progress["moedas"]:
            raise ValueError("Moedas insuficientes")
        progress["moedas"] -= amount
        self._save()
        return progress["moedas"]

    def unlock_skin(self, skin_id: str) -> bool:
        """Adiciona skin válida uma única vez."""
        from src.runtime.domain.entities.player import SKINS

        if skin_id not in {row["id"] for row in SKINS}:
            LOGGER.warning("Skin inexistente descartada: %s", skin_id)
            return False
        collection = self._active().progress["skins_desbloqueadas"]
        if skin_id in collection:
            return False
        collection.append(skin_id)
        self._save()
        return True

    def update_progress(self, **values: Any) -> bool:
        """Atualiza campos derivados de um evento e persiste uma vez."""
        progress = self._active().progress
        progress.update(values)
        self._validate_catalogs(self._active())
        return self._save()

    def increment_upgrade(self, key: str) -> None:
        """Conta escolha de módulo sem torná-lo melhoria permanente."""
        from src.runtime.domain.systems.upgrades import MELHORIAS

        if key not in MELHORIAS:
            LOGGER.warning("Melhoria inexistente descartada: %s", key)
            return
        counts = self._active().progress["melhorias_escolhidas"]
        counts[key] = counts.get(key, 0) + 1
        self._save()

    def _validate_catalogs(self, profile: Profile) -> None:
        from src.runtime.domain.entities.player import SKINS
        from src.runtime.domain.entities.bosses import BOSSES_POR_CENARIO
        from src.runtime.domain.entities.weapons import ARMARIA
        from src.runtime.domain.systems.upgrades import MELHORIAS

        progress = profile.progress
        skins = {row["id"] for row in SKINS}
        weapons = set(range(len(ARMARIA)))
        for field, valid, default in (
            ("skins_desbloqueadas", skins, "padrao"),
            ("armas_desbloqueadas", weapons, 0),
        ):
            source = progress.get(field, [])
            if not isinstance(source, list):
                source = []
            cleaned = []
            for item in source:
                try:
                    exists = item in valid
                except TypeError:
                    exists = False
                if exists and item not in cleaned:
                    cleaned.append(item)
                elif not exists:
                    LOGGER.warning("Item inexistente descartado de %s: %s", field, item)
            if default not in cleaned:
                cleaned.insert(0, default)
            progress[field] = cleaned
        for equipped, unlocked, default in (
            ("skin_atual", "skins_desbloqueadas", "padrao"),
            ("arma_equipada", "armas_desbloqueadas", 0),
        ):
            if progress.get(equipped) not in progress[unlocked]:
                progress[equipped] = default
        choices = progress.get("melhorias_escolhidas", {})
        if isinstance(choices, dict):
            for key in choices:
                if key not in MELHORIAS:
                    LOGGER.warning("Melhoria inexistente descartada: %s", key)
        progress["melhorias_escolhidas"] = {
            key: count for key, count in choices.items()
            if key in MELHORIAS and type(count) is int and count >= 0
        } if isinstance(choices, dict) else {}
        money = progress.get("moedas", 0)
        progress["moedas"] = money if type(money) is int and 0 <= money <= MAX_MONEY else 0
        valid_bosses = {row["nome"] for row in BOSSES_POR_CENARIO.values()}
        counts = progress.get("bosses_por_tipo", {})
        if isinstance(counts, dict):
            for key in counts:
                if key not in valid_bosses:
                    LOGGER.warning("Boss inexistente descartado: %s", key)
        progress["bosses_por_tipo"] = {
            key: count for key, count in counts.items()
            if key in valid_bosses and type(count) is int and count >= 0
        } if isinstance(counts, dict) else {}
        story = json.loads((files("src.runtime.story") / "cenas_pt_BR.json").read_text(
            encoding="utf-8"))
        scene_ids = {row["id"] for row in story["cenas"]}
        for field in ("cenas_vistas", "memorias_desbloqueadas"):
            source = progress.get(field, [])
            if not isinstance(source, list):
                source = []
            cleaned = []
            for item in source:
                if isinstance(item, str) and item in scene_ids and item not in cleaned:
                    cleaned.append(item)
                else:
                    LOGGER.warning("Cena inexistente descartada de %s: %s", field, item)
            progress[field] = cleaned
        records = progress.get("recordes", [])
        clean_records = []
        if isinstance(records, list):
            for record in records:
                if not isinstance(record, dict) or not isinstance(record.get("pontos"), int):
                    LOGGER.warning("Recorde inválido descartado: %s", record)
                    continue
                row = dict(record)
                if row.get("skin") not in {item["nome"] for item in SKINS}:
                    LOGGER.warning("Skin de recorde inexistente descartada: %s", row.get("skin"))
                    row["skin"] = SKINS[0]["nome"]
                clean_records.append(row)
        progress["recordes"] = clean_records[:10]

    def migrate_legacy(self, interrupt_after_profile: bool = False,
                       preferences: dict[str, Any] | None = None) -> None:
        """Importa uma vez o save único; nunca altera arquivos legados."""
        if self.index.get("migration_complete"):
            return
        if self.index["profiles"]:
            self.index["migration_complete"] = True
            self.repository.write_index(self.index)
            return
        path = Path(self.repository.data_dir) / "save.json"
        try:
            legacy = carregar_json_resiliente(path)
            if not isinstance(legacy, dict) or not isinstance(legacy.get("jogador"), dict):
                raise ValueError("Save legado inválido")
        except FileNotFoundError:
            self.index["migration_complete"] = True
            self.repository.write_index(self.index)
            return
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self.migration_error = str(exc)
            return
        try:
            records = carregar_json_resiliente(Path(self.repository.data_dir) / "records.json")
            records = records.get("recordes", []) if isinstance(records, dict) else []
        except (OSError, ValueError, json.JSONDecodeError):
            records = []
        profile = self._from_legacy(legacy, "JOGADOR"[:self.max_name_length],
                                    records, preferences)
        if not self.repository.save(profile):
            self.migration_error = "Falha ao gravar perfil importado"
            return
        self.index["profiles"].append({"id": profile.id, "name": profile.name})
        if not self.repository.write_index(self.index):
            self.index["profiles"].pop()
            self.migration_error = "Falha ao atualizar índice importado"
            return
        if interrupt_after_profile:
            return
        self.index["migration_complete"] = True
        self.repository.write_index(self.index)

    def _from_legacy(self, legacy: dict[str, Any], name: str,
                     records: list[dict], preferences: dict[str, Any] | None = None) -> Profile:
        """Converte os campos de um save antigo sem modificar a origem."""
        old = legacy["jogador"]
        profile = Profile.new(name, deepcopy(preferences) if preferences else {})
        progress = initial_progress()
        campaign = old.get("progresso_campanha")
        campaign = campaign if isinstance(campaign, dict) else {}
        dimensions = old.get("cenarios_desbloqueados", [1])
        dimensions = [value for value in dimensions if type(value) is int and 1 <= value <= 6] \
            if isinstance(dimensions, list) else [1]
        progress.update({
            "moedas": old.get("moedas", 0),
            "nivel_maximo": old.get("nivel_maximo", 1),
            "dimensao_maxima": max(dimensions or [1]),
            "total_pontos": old.get("total_pontos", 0),
            "skins_desbloqueadas": old.get("skins_desbloqueadas", ["padrao"]),
            "skin_atual": old.get("skin_atual", "padrao"),
            "cenas_vistas": campaign.get("cenas_vistas", []),
            "memorias_desbloqueadas": campaign.get("cenas_vistas", []),
            "legacy": deepcopy(legacy),
        })
        defeated = campaign.get("bosses_derrotados", [])
        from src.runtime.domain.entities.bosses import BOSSES_POR_CENARIO
        if isinstance(defeated, list):
            for index in defeated:
                if type(index) is int and index in BOSSES_POR_CENARIO:
                    name = BOSSES_POR_CENARIO[index]["nome"]
                    counts = progress["bosses_por_tipo"]
                    counts[name] = counts.get(name, 0) + 1
        statistics = legacy.get("estatisticas", {})
        statistics = statistics if isinstance(statistics, dict) else {}
        for key in ("tempo_total", "inimigos_derrotados"):
            progress[key] = statistics.get(key, 0)
        progress["recordes"] = records
        progress["recorde_pontos"] = max(
            (row["pontos"] for row in records if isinstance(row, dict)
             and type(row.get("pontos")) is int and row["pontos"] >= 0), default=0)
        profile.progress = progress
        self._validate_catalogs(profile)
        return profile

    def export_active(self, path: str | Path) -> bool:
        """Exporta uma cópia portátil do perfil selecionado."""
        return salvar_json_atomico(path, self._active().to_dict(), criar_backup=False)

    def import_file(self, path: str | Path) -> Profile:
        """Importa perfil exportado ou save legado como novo UUID local."""
        data = carregar_json_resiliente(path)
        if not isinstance(data, dict):
            raise ValueError("Arquivo de progresso inválido")
        if "jogador" in data and isinstance(data["jogador"], dict):
            name = self._available_import_name()
            profile = self._from_legacy(data, name, [])
        else:
            source = Profile.from_dict(data)
            profile = Profile.new(self._available_import_name(), deepcopy(source.preferences))
            profile.progress = deepcopy(source.progress)
            self._validate_catalogs(profile)
        if len(self.index["profiles"]) >= self.max_profiles:
            raise ValueError("Limite de perfis atingido")
        if not self.repository.save(profile):
            raise OSError("Não foi possível gravar o perfil importado")
        self.index["profiles"].append({"id": profile.id, "name": profile.name})
        if not self.repository.write_index(self.index):
            self.index["profiles"].pop()
            raise OSError("Não foi possível atualizar o índice")
        return profile

    def _available_import_name(self) -> str:
        for number in range(1, self.max_profiles + 2):
            suffix = "" if number == 1 else f" {number}"
            if len(suffix) >= self.max_name_length:
                name = str(number)[:self.max_name_length]
            else:
                name = "IMPORTADO"[:self.max_name_length - len(suffix)] + suffix
            if all(row["name"].casefold() != name.casefold()
                   for row in self.index["profiles"]):
                return name
        raise ValueError("Sem nome disponível para importação")
