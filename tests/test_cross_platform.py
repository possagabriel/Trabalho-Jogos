"""Compatibilidade de caminhos, builds e buffers em Linux e Windows."""

from __future__ import annotations

from pathlib import Path

import pygame

import main
from src.infrastructure.graphics.renderer import MainRenderer
from src.runtime.application.core import Jogo
from src.shared import user_data
from tools.build_desktop import argumentos_distribuicao


def _limpar_variaveis_dados(monkeypatch) -> None:
    monkeypatch.delenv("INCARNATE_DATA_DIR", raising=False)
    monkeypatch.delenv("SPACEFURY_DATA_DIR", raising=False)


def test_diretorio_dados_windows_usa_localappdata(monkeypatch) -> None:
    _limpar_variaveis_dados(monkeypatch)
    monkeypatch.setattr(user_data.sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\Teste\AppData\Local")

    resultado = user_data.diretorio_dados().replace("\\", "/")
    assert resultado == "C:/Users/Teste/AppData/Local/VoidShift"


def test_diretorio_dados_linux_respeita_xdg(monkeypatch) -> None:
    _limpar_variaveis_dados(monkeypatch)
    monkeypatch.setattr(user_data.sys, "platform", "linux")
    monkeypatch.setenv("XDG_DATA_HOME", "/dados/usuario")

    assert user_data.diretorio_dados() == "/dados/usuario/void-shift"


def test_diretorio_configurado_tem_prioridade(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("INCARNATE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SPACEFURY_DATA_DIR", "/ignorado")

    assert user_data.diretorio_dados() == str(tmp_path)


def test_diretorio_dados_aceita_variavel_legada(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("INCARNATE_DATA_DIR", raising=False)
    monkeypatch.setenv("SPACEFURY_DATA_DIR", str(tmp_path))

    assert user_data.diretorio_dados() == str(tmp_path)


def test_build_desktop_usa_separador_correto_por_sistema(tmp_path) -> None:
    windows = argumentos_distribuicao("win32", tmp_path)
    linux = argumentos_distribuicao("linux", tmp_path)

    assert f"{tmp_path / 'images'};images" in windows
    assert f"{tmp_path / 'images'}:images" in linux
    assert f"{tmp_path / 'pyproject.toml'};." in windows
    assert f"{tmp_path / 'pyproject.toml'}:." in linux
    assert "--icon" in windows
    assert "--icon" not in linux
    assert "--onefile" in windows
    assert "--onedir" in linux
    assert windows[windows.index("--name") + 1] == "INCARNATE"
    assert linux[linux.index("--name") + 1] == "INCARNATE"
    assert windows[-1] == str(tmp_path / "incarnate.py")
    assert linux[-1] == str(tmp_path / "incarnate.py")


def test_installer_preserva_identidade_de_upgrade_e_usa_marca_nova() -> None:
    instalador = (Path(__file__).resolve().parents[1] /
                  "installer" / "incarnate.iss").read_text(encoding="utf-8")

    assert "AppId={{B74AE7B0-9A9F-4C93-9A30-0D51F7C91000}" in instalador
    assert "AppName=INCARNATE" in instalador
    assert "UsePreviousAppDir=yes" in instalador


def test_renderer_reutiliza_buffer_de_escala() -> None:
    renderer = object.__new__(MainRenderer)
    renderer.tela = pygame.Surface((128, 72))
    renderer._superficie_escalada = None

    primeiro = renderer._escalar_quadro((256, 144))
    segundo = renderer._escalar_quadro((256, 144))
    redimensionado = renderer._escalar_quadro((320, 180))

    assert primeiro is segundo
    assert redimensionado is not primeiro
    assert redimensionado.get_size() == (320, 180)


def test_runtime_reutiliza_buffer_no_fallback_sem_gpu() -> None:
    jogo = object.__new__(Jogo)
    jogo.tela = pygame.Surface((128, 72))
    jogo._superficie_escalada = None
    jogo._escala_rapida = False

    primeiro = jogo._escalar_quadro_cpu((256, 144))
    segundo = jogo._escalar_quadro_cpu((256, 144))
    jogo._escala_rapida = True
    rapido = jogo._escalar_quadro_cpu((256, 144))

    assert primeiro is segundo
    assert rapido is primeiro


def test_cli_executa_smoke_test_sem_abrir_jogo(monkeypatch) -> None:
    chamado = []
    monkeypatch.setattr(main, "executar_smoke_test", lambda: chamado.append(True) or 0)

    assert main.cli(["--smoke-test"]) == 0
    assert chamado == [True]
