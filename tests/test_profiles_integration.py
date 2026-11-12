"""Integração da seleção, preferências e save ativo com o jogo."""

from __future__ import annotations

import json
from unittest.mock import Mock

import pygame
import pytest

from src.core import settings
from src.core.settings import DEFAULT_CONTROLES
from src.infrastructure.ui.layout import Layout
from src.runtime.application.core import Jogo
from src.runtime.domain.entities.powerups import PowerUp


@pytest.mark.parametrize('tamanho', [(900, 700), (1920, 1080)])
def test_pilotos_cards_verticais_contidos_e_navegaveis(tmp_path, monkeypatch, tamanho):
    monkeypatch.setenv('INCARNATE_DATA_DIR', str(tmp_path))
    jogo = Jogo(sons=Mock())
    for indice in range(jogo.profile_service.max_profiles):
        jogo.profile_service.create(f'Piloto {indice + 1}')
    jogo.menu.layout = Layout(*tamanho)
    jogo.menu._recriar_fontes()
    screen = jogo.menu.profile_screen
    screen.refresh()
    screen.draw(pygame.Surface(tamanho))
    assert len(screen.cards) == jogo.profile_service.max_profiles + 1
    for card in screen.cards:
        assert card.height > card.width
        assert pygame.Rect((0, 0), tamanho).contains(card)
        assert card.bottom < tamanho[1] - jogo.menu.layout.px(84)
    for i, card in enumerate(screen.cards):
        assert not any(card.colliderect(outro) for outro in screen.cards[i + 1:])
    inicio = screen.selection
    screen.handle_event(pygame.event.Event(
        pygame.KEYDOWN, key=pygame.K_RIGHT, unicode=''))
    assert screen.selection == inicio + 1
    screen.handle_event(pygame.event.Event(
        pygame.KEYDOWN, key=pygame.K_LEFT, unicode=''))
    assert screen.selection == inicio

@pytest.mark.parametrize('estilo', ['ORIGINAL', 'COMIC'])
@pytest.mark.parametrize('flash', ['NORMAL', 'REDUZIDO'])
def test_clique_mundo_aberto_atualiza_desenha_e_continua(
        tmp_path, monkeypatch, estilo, flash):
    monkeypatch.setenv('INCARNATE_DATA_DIR', str(tmp_path))
    jogo = Jogo(sons=Mock())
    perfil = jogo.profile_service.create('Piloto')
    jogo.ativar_perfil(perfil.id)
    jogo.config['estilo_visual'] = estilo
    jogo.config['intensidade_flash'] = flash
    desenho_nave = Mock(wraps=jogo.jogador.desenhar)
    monkeypatch.setattr(jogo.jogador, 'desenhar', desenho_nave)
    jogo.menu._abrir_jogar()
    hub = jogo.menu.jogar_hub
    indice = next(i for i, entry in enumerate(hub.entries) if entry[1] == 'mundo_aberto')
    hub.tratar_clique(hub._rects()[indice].center)
    assert jogo.modo_atual == 'mundo_aberto'
    jogo._atualizar()
    jogo.render_controller.desenhar()
    assert desenho_nave.call_args.kwargs['efeitos_reduzidos'] == (flash != 'NORMAL')
    estrategia = jogo.estrategia_modo
    estrategia.save(jogo)
    assert estrategia.continue_game(jogo)
    jogo._atualizar()
    jogo.render_controller.desenhar()


def test_start_without_profile_uses_default_controls(tmp_path, monkeypatch):
    monkeypatch.setenv("INCARNATE_DATA_DIR", str(tmp_path))
    jogo = Jogo(sons=Mock())
    assert jogo.profile_service.active is None
    assert jogo.menu.subestado == "PERFIS"
    assert jogo.controles == DEFAULT_CONTROLES
    screen = jogo.menu.profile_screen
    assert screen.mode == "create"
    assert screen.text == "Piloto"
    jogo.render_controller.desenhar()
    for _ in screen.text:
        screen.handle_event(pygame.event.Event(
            pygame.KEYDOWN, {"key": pygame.K_BACKSPACE, "unicode": ""}))
    for letter in "Érica":
        screen.handle_event(
            pygame.event.Event(pygame.KEYDOWN, {"key": ord(letter.lower())
                                                if letter.isascii() else pygame.K_UNKNOWN,
                                                "unicode": letter}))
    screen.handle_event(
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
    assert jogo.profile_service.active.id == second.id
    jogo.menu._abrir_perfis()
    jogo.render_controller.desenhar()
    click(screen.cards[0])
    screen.handle_event(pygame.event.Event(
        pygame.KEYDOWN, {"key": pygame.K_r, "unicode": "r"}))
    screen.text = "Ágata"
    screen.handle_event(pygame.event.Event(
        pygame.KEYDOWN, {"key": pygame.K_RETURN, "unicode": ""}))
    assert jogo.profile_service.list_profiles()[0].name == "Ágata"
    jogo.render_controller.desenhar()
    screen.handle_event(pygame.event.Event(
        pygame.KEYDOWN, {"key": pygame.K_DELETE, "unicode": ""}))
    assert screen.dialog_choice == 1
    screen.text = "Ágata"
    screen.handle_event(pygame.event.Event(
        pygame.KEYDOWN, {"key": pygame.K_LEFT, "unicode": ""}))
    screen.handle_event(pygame.event.Event(
        pygame.KEYDOWN, {"key": pygame.K_RETURN, "unicode": ""}))
    assert [p.id for p in jogo.profile_service.list_profiles()] == [second.id]
    assert first.id not in [p.id for p in jogo.profile_service.list_profiles()]


def test_profile_screen_focuses_active_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("INCARNATE_DATA_DIR", str(tmp_path))
    jogo = Jogo(sons=Mock())
    jogo.profile_service.create("Ana")
    second = jogo.profile_service.create("Bia")
    jogo.ativar_perfil(second.id)
    screen = jogo.menu.profile_screen
    screen.refresh()

    assert screen._profiles()[screen.selection].id == second.id
    assert screen.new_profile_disabled is False


def test_new_profile_card_disables_at_configured_limit(tmp_path, monkeypatch):
    monkeypatch.setenv("INCARNATE_DATA_DIR", str(tmp_path))
    jogo = Jogo(sons=Mock())
    service = jogo.profile_service
    for index in range(service.max_profiles):
        service.create(f"Piloto {index + 1}")
    screen = jogo.menu.profile_screen
    screen.refresh()
    screen.selection = len(screen._profiles())
    screen._action("new")

    assert screen.new_profile_disabled
    assert screen.mode is None
    assert screen.message == f"Limite de {service.max_profiles} perfis"
    surface = pygame.Surface((jogo.menu.layout.largura, jogo.menu.layout.altura))
    screen.draw(surface)
    assert len(screen.cards) == service.max_profiles + 1
    assert screen.cards[-1].bottom <= jogo.menu.layout.altura


def test_name_validation_errors_are_inline_and_keep_rename_open(tmp_path, monkeypatch):
    monkeypatch.setenv("INCARNATE_DATA_DIR", str(tmp_path))
    jogo = Jogo(sons=Mock())
    profile = jogo.profile_service.create("Ana")
    jogo.ativar_perfil(profile.id)
    screen = jogo.menu.profile_screen
    screen.refresh()
    screen._action("rename")

    for invalid_name in (" D'Ávila-Sul", "Ana★"):
        screen.text = invalid_name
        screen.handle_event(pygame.event.Event(
            pygame.KEYDOWN, {"key": pygame.K_RETURN, "unicode": ""}))
        assert screen.mode == "rename"
        assert screen.message


def test_escape_cancels_dialog_and_restores_profile_focus(tmp_path, monkeypatch):
    monkeypatch.setenv("INCARNATE_DATA_DIR", str(tmp_path))
    jogo = Jogo(sons=Mock())
    first = jogo.profile_service.create("Ana")
    second = jogo.profile_service.create("Bia")
    jogo.ativar_perfil(first.id)
    screen = jogo.menu.profile_screen
    jogo.menu._abrir_perfis()
    screen.selection = 1
    screen._action("rename")
    screen.handle_event(pygame.event.Event(
        pygame.KEYDOWN, {"key": pygame.K_ESCAPE, "unicode": ""}))

    assert screen.mode is None
    assert screen.selection == 1
    assert screen._profiles()[screen.selection].id == second.id
    menu_focus = jogo.menu.opcao_selecionada
    screen.handle_event(pygame.event.Event(
        pygame.KEYDOWN, {"key": pygame.K_ESCAPE, "unicode": ""}))
    assert jogo.menu.subestado == "MENU"
    assert jogo.menu.opcao_selecionada == menu_focus


def test_profile_hover_moves_keyboard_focus(tmp_path, monkeypatch):
    monkeypatch.setenv("INCARNATE_DATA_DIR", str(tmp_path))
    jogo = Jogo(sons=Mock())
    first = jogo.profile_service.create("Ana")
    second = jogo.profile_service.create("Bia")
    jogo.ativar_perfil(first.id)
    screen = jogo.menu.profile_screen
    jogo.menu._abrir_perfis()
    jogo.render_controller.desenhar()
    scale, off_x, off_y = jogo._transformacao_janela()
    rect = screen.cards[1]
    position = (int(rect.centerx * scale + off_x),
                int(rect.centery * scale + off_y))

    screen.handle_event(pygame.event.Event(
        pygame.MOUSEMOTION, {"pos": position, "rel": (0, 0), "buttons": (0, 0)}))

    assert screen._profiles()[screen.selection].id == second.id


def test_empty_profile_screen_opens_named_creation_dialog(tmp_path, monkeypatch):
    monkeypatch.setenv("INCARNATE_DATA_DIR", str(tmp_path))
    jogo = Jogo(sons=Mock())
    screen = jogo.menu.profile_screen

    assert screen.mode == "create"
    assert screen.text == "Piloto"
    assert screen.new_profile_disabled is False

    screen.handle_event(pygame.event.Event(
        pygame.KEYDOWN, {"key": pygame.K_ESCAPE, "unicode": ""}))
    assert screen.mode is None
