"""Compatibilidade de caminhos, builds e buffers em Linux e Windows."""

from __future__ import annotations

import pygame

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


def test_build_desktop_usa_separador_correto_por_sistema(tmp_path) -> None:
    windows = argumentos_distribuicao("win32", tmp_path)
    linux = argumentos_distribuicao("linux", tmp_path)

    assert f"{tmp_path / 'images'};images" in windows
    assert f"{tmp_path / 'images'}:images" in linux
    assert "--icon" in windows
    assert "--icon" not in linux
    assert windows[-1] == str(tmp_path / "main.py")
    assert linux[-1] == str(tmp_path / "main.py")


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
