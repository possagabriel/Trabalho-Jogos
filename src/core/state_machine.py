"""Maquina de estados baseada no padrao State.

Fornece:
- ``GameState``: classe abstrata base para todos os estados.
- ``GameContext``: gerenciador de transicoes que controla qual estado
  esta ativo e delega as chamadas de ciclo de vida.
- Estados concretos: ``MenuState``, ``PlayingState``, ``PausedState``,
  ``GameOverState``, ``LoadingState``.

A maquina e desacoplada do pygame — cada estado recebe a superficie de
desenho como parametro nos metodos ``update`` / ``render``, mantendo a
camada de core testavel.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pygame


# ---------------------------------------------------------------------------
# Estado abstrato
# ---------------------------------------------------------------------------

class GameState(abc.ABC):
    """Interface base para todos os estados do jogo.

    Cada estado concreto deve implementar os metodos abstratos. O metodo
    ``handle_event`` tem implementacao padrao (ignora tudo) para conveniencia.
    """

    def __init__(self, context: GameContext) -> None:
        self.context = context

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def enter(self) -> None:
        """Chamado quando o estado se torna ativo.

        Ideal para inicializar recursos, resetar variaveis, etc.
        """

    @abc.abstractmethod
    def exit(self) -> None:
        """Chamado quando o estado e desativado.

        Ideal para liberar recursos pesados.
        """

    def handle_event(self, event: pygame.event.Event) -> None:
        """Trata um evento do pygame.

        Implementacao padrao: ignora o evento. Sobrescreva conforme necessario.
        """

    @abc.abstractmethod
    def update(self, dt: float) -> None:
        """Atualiza a logica do estado.

        Args:
            dt: Tempo decorrido desde o ultimo frame (em segundos).
        """

    @abc.abstractmethod
    def render(self, surface: pygame.Surface) -> None:
        """Desenha o estado na superficie fornecida.

        Args:
            surface: Superficie logica de desenho (tamanho constante).
        """


# ---------------------------------------------------------------------------
# Contexto (gerenciador de transicoes)
# ---------------------------------------------------------------------------

class GameContext:
    """Gerencia a transicao entre estados e delega chamadas de ciclo de vida.

    Uso::

        ctx = GameContext()
        ctx.change_state(MenuState(ctx))
        # no loop principal:
        ctx.handle_event(event)
        ctx.update(dt)
        ctx.render(surface)
    """

    def __init__(self) -> None:
        self._current_state: GameState | None = None
        self._previous_state: GameState | None = None

    # ------------------------------------------------------------------
    # Transicoes
    # ------------------------------------------------------------------

    @property
    def current_state(self) -> GameState | None:
        """Estado ativo atualmente (ou ``None`` se nenhum foi definido)."""
        return self._current_state

    @property
    def previous_state(self) -> GameState | None:
        """Ultimo estado ativo antes da transicao atual."""
        return self._previous_state

    def change_state(self, new_state: GameState) -> None:
        """Finaliza o estado atual e ativa ``new_state``.

        Chama ``exit()`` no estado antigo e ``enter()`` no novo.
        """
        if self._current_state is not None:
            self._current_state.exit()
        self._previous_state = self._current_state
        self._current_state = new_state
        self._current_state.enter()

    def pop_state(self) -> None:
        """Volta ao estado anterior (se existir)."""
        if self._previous_state is not None:
            self.change_state(self._previous_state)

    # ------------------------------------------------------------------
    # Delegacao
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Delega o evento ao estado ativo."""
        if self._current_state is not None:
            self._current_state.handle_event(event)

    def update(self, dt: float) -> None:
        """Delega a atualizacao ao estado ativo."""
        if self._current_state is not None:
            self._current_state.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        """Delega o desenho ao estado ativo."""
        if self._current_state is not None:
            self._current_state.render(surface)


# ---------------------------------------------------------------------------
# Estados concretos — placeholders com stubs basicos
# ---------------------------------------------------------------------------

class MenuState(GameState):
    """Estado do menu principal."""

    def enter(self) -> None:
        pass

    def exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        pass


class PlayingState(GameState):
    """Estado de gameplay ativo."""

    def enter(self) -> None:
        pass

    def exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        pass


class PausedState(GameState):
    """Estado de pausa (sobrepor ao PlayingState)."""

    def enter(self) -> None:
        pass

    def exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        pass


class GameOverState(GameState):
    """Estado de fim de jogo."""

    def enter(self) -> None:
        pass

    def exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        pass


class LoadingState(GameState):
    """Estado de carregamento entre cenarios."""

    def __init__(self, context: GameContext, next_state: GameState | None = None,
                 duration: float = 1.5) -> None:
        super().__init__(context)
        self._next_state = next_state
        self._duration = duration
        self._elapsed: float = 0.0

    def enter(self) -> None:
        self._elapsed = 0.0

    def exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        self._elapsed += dt
        if self._elapsed >= self._duration and self._next_state is not None:
            self.context.change_state(self._next_state)

    def render(self, surface: pygame.Surface) -> None:
        pass
