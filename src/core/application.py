"""Ponto de entrada oficial da aplicação.

O loop de produção mora no runtime canônico. Esta classe é deliberadamente
pequena: ela compõe o jogo sem manter um segundo loop, janela ou máquina de
estados paralela.
"""

from __future__ import annotations

from collections.abc import Callable

from src.runtime.application.core import Jogo


FabricaJogo = Callable[[], Jogo]


class Application:
    """Compõe e inicia o runtime canônico do VOID//SHIFT."""

    def __init__(self, fabrica_jogo: FabricaJogo | None = None) -> None:
        self._fabrica_jogo = fabrica_jogo or Jogo
        self._jogo: Jogo | None = None

    @property
    def jogo(self) -> Jogo:
        """Retorna a única instância do runtime, criando-a sob demanda."""
        if self._jogo is None:
            self._jogo = self._fabrica_jogo()
        return self._jogo

    def run(self) -> None:
        """Executa o ciclo de produção do jogo."""
        self.jogo.executar()

    def quit(self) -> None:
        """Solicita que o runtime encerre no próximo ciclo de eventos."""
        self.jogo.rodando = False


def main() -> None:
    """Entry point instalável e equivalente a executar ``python main.py``."""
    Application().run()


if __name__ == "__main__":
    main()
