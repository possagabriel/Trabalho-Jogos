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
        "_criar_modo_gpu",
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


def test_janela_gpu_deixa_cadencia_para_relogio_do_loop(monkeypatch):
    """Não soma uma espera de VSync ao limite já aplicado pelo game loop."""
    janela = pygame.Surface((640, 480))
    criar = mock.Mock(return_value=janela)
    monkeypatch.setattr(pygame.display, "set_mode", criar)
    flags = pygame.OPENGL | pygame.DOUBLEBUF

    assert core.Jogo._criar_modo_gpu((640, 480), flags) is janela
    criar.assert_called_once_with((640, 480), flags, vsync=0)


def test_janela_gpu_preserva_fallback_sem_argumento_vsync(monkeypatch):
    """Builds antigos e drivers que rejeitam a opção continuam funcionando."""
    janela = pygame.Surface((640, 480))
    flags = pygame.OPENGL | pygame.DOUBLEBUF
    for erro in (TypeError("vsync indisponível"), pygame.error("driver incompatível")):
        criar = mock.Mock(side_effect=[erro, janela])
        monkeypatch.setattr(pygame.display, "set_mode", criar)
        assert core.Jogo._criar_modo_gpu((640, 480), flags) is janela
        assert criar.call_args_list == [mock.call((640, 480), flags, vsync=0),
                                       mock.call((640, 480), flags)]
