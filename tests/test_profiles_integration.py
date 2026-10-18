"""Integração da seleção, preferências e save ativo com o jogo."""

from __future__ import annotations

import json
from unittest.mock import Mock

import pygame

from src.core import settings
from src.core.settings import DEFAULT_CONTROLES
from src.runtime.application.core import Jogo
from src.runtime.domain.entities.powerups import PowerUp


def test_start_without_profile_uses_default_controls(tmp_path, monkeypatch):
    monkeypatch.setenv("INCARNATE_DATA_DIR", str(tmp_path))
    jogo = Jogo(sons=Mock())
    assert jogo.profile_service.active is None
    assert jogo.menu.subestado == "PERFIS"
    assert jogo.controles == DEFAULT_CONTROLES
    jogo.render_controller.desenhar()
    jogo.menu.profile_screen.handle_event(
        pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_n, "unicode": "n"}))
    for letter in "Érica":
        jogo.menu.profile_screen.handle_event(
            pygame.event.Event(pygame.KEYDOWN, {"key": ord(letter.lower())
                                                if letter.isascii() else pygame.K_UNKNOWN,
                                                "unicode": letter}))
    jogo.menu.profile_screen.handle_event(
        pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN, "unicode": ""}))
    assert jogo.profile_service.active.name == "Érica"
    assert jogo.menu.subestado == "MENU"


def test_two_profiles_keep_progress_and_controls_separate(tmp_path, monkeypatch):
    monkeypatch.setenv("INCARNATE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "ARQUIVO_CONFIG", str(tmp_path / "settings.json"))
    jogo = Jogo(sons=Mock())
    first = jogo.profile_service.create("Ana")
    second = jogo.profile_service.create("Bia")
    jogo.ativar_perfil(first.id)
    jogo.loja.moedas = 34
    jogo._salvar_tudo()
    jogo.config["mira_ativa"] = False
    jogo.config.controles["atirar"] = pygame.K_z
    jogo.config.salvar()
    jogo.ativar_perfil(second.id)
    assert jogo.loja.moedas == 0
    assert jogo.config["mira_ativa"] is True
    assert jogo.controles["atirar"] == pygame.K_SPACE
    jogo.ativar_perfil(first.id)
    assert jogo.loja.moedas == 34
    assert jogo.config["mira_ativa"] is False
    assert jogo.controles["atirar"] == pygame.K_z
    global_settings = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    assert "mira_ativa" not in global_settings
    assert "controles" not in global_settings


def test_coleta_de_moedas_persiste_ao_sair_da_missao(tmp_path, monkeypatch):
    monkeypatch.setenv("INCARNATE_DATA_DIR", str(tmp_path))
    jogo = Jogo(sons=Mock())
    perfil = jogo.profile_service.create("Ana")
    jogo.ativar_perfil(perfil.id)
    jogo._novo_jogo("Ana")
    jogo.powerups = [PowerUp("moedas", jogo.jogador.x, jogo.jogador.y)]

    jogo._atualizar_powerups()

    assert jogo.jogador.moedas_jogo == 100
    assert jogo.loja.moedas == 100
    assert jogo.profile_service.repository.load(perfil.id).progress["moedas"] == 100

    jogo.pausa_controller.confirmar_saida()
    reiniciado = Jogo(sons=Mock())
    reiniciado.ativar_perfil(perfil.id)
    assert reiniciado.loja.moedas == 100


def test_failed_profile_write_keeps_pending(tmp_path, monkeypatch):
    monkeypatch.setenv("INCARNATE_DATA_DIR", str(tmp_path))
    jogo = Jogo(sons=Mock())
    profile = jogo.profile_service.create("Ana")
    jogo.ativar_perfil(profile.id)
    monkeypatch.setattr(jogo.profile_service.repository, "save", lambda profile: False)
    jogo.profile_service.credit(2)
    assert jogo.profile_service.dirty
    assert jogo.profile_service.save_error
    jogo.loop_controller.atualizar()
    assert jogo._aviso_save_exibido


def test_mouse_select_and_keyboard_rename_delete(tmp_path, monkeypatch):
    monkeypatch.setenv("INCARNATE_DATA_DIR", str(tmp_path))
    jogo = Jogo(sons=Mock())
    first = jogo.profile_service.create("Ana")
    second = jogo.profile_service.create("Bia")
    screen = jogo.menu.profile_screen
    screen.refresh()
    jogo.render_controller.desenhar()
    scale, off_x, off_y = jogo._transformacao_janela()

    def click(rect):
        pos = (int(rect.centerx * scale + off_x), int(rect.centery * scale + off_y))
        screen.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": pos}))

    click(screen.cards[1])
    click(screen.buttons[0])
    assert jogo.profile_service.active.id == second.id
    jogo.menu._abrir_perfis()
    jogo.render_controller.desenhar()
    click(screen.cards[0])
    click(screen.buttons[2])
    screen.text = "Ágata"
    screen.handle_event(pygame.event.Event(
        pygame.KEYDOWN, {"key": pygame.K_RETURN, "unicode": ""}))
    assert jogo.profile_service.list_profiles()[0].name == "Ágata"
    jogo.render_controller.desenhar()
    click(screen.buttons[3])
    screen.text = "Ágata"
    screen.handle_event(pygame.event.Event(
        pygame.KEYDOWN, {"key": pygame.K_RETURN, "unicode": ""}))
    assert [p.id for p in jogo.profile_service.list_profiles()] == [second.id]
    assert first.id not in [p.id for p in jogo.profile_service.list_profiles()]
