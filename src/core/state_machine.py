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
from typing import TYPE_CHECKING, Callable

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

class CallbackState(GameState):
    """Estado concreto configurado por callbacks de uma tela ou controlador.

    Evita que a maquina de estados conheca pygame, menu ou sistemas de
    dominio. Os adaptadores de apresentacao fornecem apenas as operacoes de
    ciclo de vida de que precisam.
    """

    def __init__(
        self,
        context: GameContext,
        on_enter: Callable[[], None] | None = None,
        on_exit: Callable[[], None] | None = None,
        on_event: Callable[[pygame.event.Event], None] | None = None,
        on_update: Callable[[float], None] | None = None,
        on_render: Callable[[pygame.Surface], None] | None = None,
    ) -> None:
        super().__init__(context)
        self._on_enter = on_enter
        self._on_exit = on_exit
        self._on_event = on_event
        self._on_update = on_update
        self._on_render = on_render

    def enter(self) -> None:
        if self._on_enter is not None:
            self._on_enter()

    def exit(self) -> None:
        if self._on_exit is not None:
            self._on_exit()

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._on_event is not None:
            self._on_event(event)

    def update(self, dt: float) -> None:
        if self._on_update is not None:
            self._on_update(dt)

    def render(self, surface: pygame.Surface) -> None:
        if self._on_render is not None:
            self._on_render(surface)


class MenuState(CallbackState):
    """Estado do menu principal, conectado pela camada de apresentacao."""


class PlayingState(CallbackState):
    """Estado de gameplay ativo, conectado pelo controlador de partida."""


class PausedState(CallbackState):
    """Estado de pausa, conectado pelo controlador da sobreposicao."""


class GameOverState(CallbackState):
    """Estado de fim de jogo, conectado pela tela de resultados."""


class LoadingState(CallbackState):
    """Estado de carregamento entre cenarios."""

    def __init__(self, context: GameContext, next_state: GameState | None = None,
                 duration: float = 1.5,
                 on_render: Callable[[pygame.Surface], None] | None = None) -> None:
        super().__init__(context, on_render=on_render)
        self._next_state = next_state
        self._duration = duration
        self._elapsed: float = 0.0

    def enter(self) -> None:
        super().enter()
        self._elapsed = 0.0

    def exit(self) -> None:
        super().exit()

    def update(self, dt: float) -> None:
        super().update(dt)
        self._elapsed += dt
        if self._elapsed >= self._duration and self._next_state is not None:
            self.context.change_state(self._next_state)

    def render(self, surface: pygame.Surface) -> None:
        super().render(surface)
