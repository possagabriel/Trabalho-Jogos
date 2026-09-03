"""Testes do ponto de entrada oficial da aplicação."""

from __future__ import annotations

from src.core.application import Application


class JogoFalso:
    """Runtime mínimo para validar composição sem abrir uma janela."""

    def __init__(self) -> None:
        self.executado = False
        self.rodando = True

    def executar(self) -> None:
        self.executado = True


def test_application_cria_uma_unica_instancia_e_delega_execucao() -> None:
    criados: list[JogoFalso] = []

    def fabricar() -> JogoFalso:
        jogo = JogoFalso()
        criados.append(jogo)
        return jogo

    app = Application(fabricar)
    assert app.jogo is app.jogo
    app.run()
    assert len(criados) == 1
    assert criados[0].executado is True


def test_application_solicita_encerramento_ao_runtime() -> None:
    jogo = JogoFalso()
    app = Application(lambda: jogo)
    app.quit()
    assert jogo.rodando is False
