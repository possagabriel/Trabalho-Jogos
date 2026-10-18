"""Contratos puros para perfis, recuperação e migração legada."""

from __future__ import annotations

import json

import pytest

from src.domain.systems.profile_service import ProfileService
from src.infrastructure.persistence.profile_repository import JsonProfileRepository


@pytest.fixture
def service(tmp_path):
    return ProfileService(JsonProfileRepository(tmp_path), max_profiles=5, max_name_length=16)


@pytest.mark.parametrize("name", ["", "   ", "A/ B", "A@B", "A\nB", "A\tB", "X" * 17])
def test_invalid_names(service, name):
    with pytest.raises(ValueError):
        service.create(name)


def test_names_unicode_trim_duplicates_and_limit(service):
    first = service.create("  José da Silva  ")
    assert first.name == "José da Silva"
    with pytest.raises(ValueError):
        service.create("josé DA SILVA")
    assert service.create("Á" * 16).name == "Á" * 16
    with pytest.raises(ValueError):
        service.rename(first.id, "á" * 16)
    assert service.rename(first.id, " JOÃO ").name == "JOÃO"


def test_crud_limit_and_active_delete(service):
    profiles = [service.create(f"P{i}") for i in range(5)]
    with pytest.raises(ValueError):
        service.create("P5")
    service.select(profiles[0].id)
    with pytest.raises(ValueError):
        service.delete(profiles[0].id, profiles[0].name, in_game=True)
    with pytest.raises(ValueError):
        service.delete(profiles[0].id, "errado")
    service.delete(profiles[0].id, profiles[0].name)
    assert profiles[0].id not in [p.id for p in service.list_profiles()]
    with pytest.raises(KeyError):
        service.credit(1)


def test_money_unlocks_and_catalog_validation(service, caplog):
    profile = service.create("Jogadora")
    service.select(profile.id)
    service.credit(10)
    with pytest.raises(ValueError):
        service.spend(11)
    with pytest.raises(ValueError):
        service.credit(2**63)
    assert service.spend(4) == 6
    assert service.unlock_skin("padrao") is False
    assert service.unlock_skin("skin-invalida") is False
    raw = service.active.to_dict()
    raw["progress"]["skins_desbloqueadas"] += ["skin-invalida"]
    raw["progress"]["armas_desbloqueadas"] += [999]
    raw["progress"]["melhorias_escolhidas"] = {"inexistente": 3}
    raw["progress"]["cenas_vistas"] = ["inexistente", "introducao"]
    raw["progress"]["bosses_por_tipo"] = {"inexistente": 2}
    raw["progress"]["skin_atual"] = "skin-invalida"
    service.repository.write_raw(profile.id, raw)
    reloaded = ProfileService(service.repository)
    reloaded.select(profile.id)
    assert "skin-invalida" not in reloaded.active.progress["skins_desbloqueadas"]
    assert 999 not in reloaded.active.progress["armas_desbloqueadas"]
    assert reloaded.active.progress["skin_atual"] == "padrao"
    assert reloaded.active.progress["melhorias_escolhidas"] == {}
    assert reloaded.active.progress["cenas_vistas"] == ["introducao"]
    assert reloaded.active.progress["bosses_por_tipo"] == {}
    assert "descartado" in caplog.text


def test_rebuild_index_and_corrupt_profile(tmp_path):
    repo = JsonProfileRepository(tmp_path)
    service = ProfileService(repo)
    good = service.create("Bom")
    bad = service.create("Ruim")
    repo.profile_path(bad.id).write_text("{", encoding="utf-8")
    repo.backup_path(bad.id).write_text("{", encoding="utf-8")
    repo.index_path.write_text("{", encoding="utf-8")
    recovered = ProfileService(JsonProfileRepository(tmp_path))
    entries = {item.id: item for item in recovered.list_profiles()}
    assert entries[good.id].damaged is False
    assert entries[bad.id].damaged is True
    with pytest.raises(ValueError):
        recovered.select(bad.id)


def test_corrupt_primary_uses_backup(tmp_path):
    service = ProfileService(JsonProfileRepository(tmp_path))
    profile = service.create("Ana")
    service.select(profile.id)
    service.credit(3)
    service.repository.profile_path(profile.id).write_text("{", encoding="utf-8")
    recovered = ProfileService(JsonProfileRepository(tmp_path))
    recovered.select(profile.id)
    assert recovered.active.progress["moedas"] == 0
    assert json.loads(recovered.repository.backup_path(profile.id).read_text(
        encoding="utf-8"))["progress"]["moedas"] == 0


def test_damaged_last_used_is_not_selected(tmp_path):
    service = ProfileService(JsonProfileRepository(tmp_path))
    profile = service.create("Ana")
    service.select(profile.id)
    service.repository.profile_path(profile.id).write_text("{", encoding="utf-8")
    service.repository.backup_path(profile.id).write_text("{", encoding="utf-8")
    recovered = ProfileService(JsonProfileRepository(tmp_path))
    assert recovered.select_last() is None
    assert recovered.active is None


@pytest.mark.parametrize("legacy", [
    {"jogador": {"moedas": 12, "skins_desbloqueadas": ["padrao"],
                 "progresso_campanha": {"cenas_vistas": ["introducao"]}}},
    {"jogador": {"moedas": 7}},
])
def test_legacy_migration_idempotent(tmp_path, legacy):
    (tmp_path / "save.json").write_text(json.dumps(legacy), encoding="utf-8")
    service = ProfileService(JsonProfileRepository(tmp_path))
    service.migrate_legacy()
    assert len(service.list_profiles()) == 1
    profile = service.list_profiles()[0]
    service.delete(profile.id, profile.name)
    ProfileService(JsonProfileRepository(tmp_path)).migrate_legacy()
    assert not ProfileService(JsonProfileRepository(tmp_path)).list_profiles()
    assert (tmp_path / "save.json").read_text(encoding="utf-8") == json.dumps(legacy)


def test_migration_from_backup_and_both_corrupt(tmp_path):
    (tmp_path / "save.json").write_text("{", encoding="utf-8")
    (tmp_path / "save.json.bak").write_text('{"jogador":{"moedas":9}}', encoding="utf-8")
    service = ProfileService(JsonProfileRepository(tmp_path))
    service.migrate_legacy()
    assert service.list_profiles()[0].progress["moedas"] == 9
    other = tmp_path / "other"
    other.mkdir()
    (other / "save.json").write_text("{", encoding="utf-8")
    (other / "save.json.bak").write_text("{", encoding="utf-8")
    failed = ProfileService(JsonProfileRepository(other))
    failed.migrate_legacy()
    assert failed.migration_error
    assert not failed.list_profiles()


def test_interrupted_migration_recovers_without_duplicate(tmp_path):
    (tmp_path / "save.json").write_text('{"jogador":{"moedas":4}}', encoding="utf-8")
    service = ProfileService(JsonProfileRepository(tmp_path))
    service.migrate_legacy(interrupt_after_profile=True)
    assert len(service.list_profiles()) == 1
    resumed = ProfileService(JsonProfileRepository(tmp_path))
    resumed.migrate_legacy()
    assert len(resumed.list_profiles()) == 1
    assert resumed.repository.read_index()["migration_complete"] is True


def test_old_schema_and_deleted_last_profile_do_not_reimport(tmp_path):
    legacy = '{"jogador":{"moedas":4}}'
    (tmp_path / "save.json").write_text(legacy, encoding="utf-8")
    service = ProfileService(JsonProfileRepository(tmp_path))
    service.migrate_legacy()
    profile = service.list_profiles()[0]
    raw = profile.to_dict()
    raw["schema_version"] = 0
    raw["progress"].pop("mortes")
    service.repository.write_raw(profile.id, raw)
    loaded = ProfileService(JsonProfileRepository(tmp_path))
    assert loaded.list_profiles()[0].progress["mortes"] == 0
    loaded.delete(profile.id, profile.name)
    loaded.repository.index_path.unlink()
    again = ProfileService(JsonProfileRepository(tmp_path))
    again.migrate_legacy()
    assert again.list_profiles() == []


def test_orphan_is_cleaned_on_startup(tmp_path):
    service = ProfileService(JsonProfileRepository(tmp_path))
    profile = service.create("Ana")
    orphan = service.repository.folder / "00000000-0000-0000-0000-000000000001.json"
    orphan.write_text(json.dumps(profile.to_dict()), encoding="utf-8")
    ProfileService(JsonProfileRepository(tmp_path))
    assert not orphan.exists()


def test_missing_index_recovers_backup_only_profile(tmp_path):
    service = ProfileService(JsonProfileRepository(tmp_path))
    profile = service.create("Ana")
    service.select(profile.id)
    service.repository.profile_path(profile.id).unlink()
    service.repository.index_path.unlink()
    recovered = ProfileService(JsonProfileRepository(tmp_path))
    assert [item.id for item in recovered.list_profiles()] == [profile.id]


def test_delete_damaged_profile_by_displayed_name(tmp_path):
    service = ProfileService(JsonProfileRepository(tmp_path))
    profile = service.create("Ana")
    service.repository.profile_path(profile.id).write_text("{", encoding="utf-8")
    damaged = service.list_profiles()[0]
    assert damaged.damaged
    service.delete(damaged.id, damaged.name)
    assert service.list_profiles() == []
