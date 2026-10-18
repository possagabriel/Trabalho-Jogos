"""Tests do fallback da janela GPU para a apresentação CPU."""

from unittest import mock

import pygame

from src.runtime.application import core


def test_falha_gpu_fecha_contexto_antes_de_criar_janela_cpu(monkeypatch, caplog):
    """Uma falha após criar o contexto precisa reiniciar o subsistema de vídeo."""
    jogo = object.__new__(core.Jogo)
    janela_gpu = pygame.Surface((640, 480))
    janela_cpu = pygame.Surface((640, 480))
    chamadas = []

    monkeypatch.setattr(core, "GPU_DISPONIVEL", True)
    monkeypatch.setattr(core, "ApresentadorGPU", mock.Mock(return_value=object()))
    monkeypatch.setattr(
        core.Jogo,
        "_criar_modo_com_vsync",
        staticmethod(lambda tamanho, flags: chamadas.append("gpu") or janela_gpu),
    )
    monkeypatch.setattr(
        jogo,
        "_configurar_shader_gpu",
        mock.Mock(side_effect=RuntimeError("contexto incompatível")),
    )
    monkeypatch.setattr(
        pygame.display, "quit", lambda: chamadas.append("quit")
    )
    monkeypatch.setattr(
        pygame.display, "init", lambda: chamadas.append("init")
    )

    def criar_cpu(tamanho, flags):
        chamadas.append("cpu")
        return janela_cpu

    monkeypatch.setattr(pygame.display, "set_mode", criar_cpu)

    with caplog.at_level("WARNING", logger=core.__name__):
        resultado = jogo._criar_janela_video((640, 480), 0)

    assert resultado is janela_cpu
    assert chamadas == ["gpu", "quit", "init", "cpu"]
    assert "usando fallback CPU" in caplog.text
