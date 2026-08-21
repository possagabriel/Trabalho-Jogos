"""InputManager: translates raw Pygame events into Command objects.

Uses the Command pattern so the game layer never calls ``pygame.key`` directly.
Each frame the manager builds a list of ``Command`` instances that the game
executes in order.

Migrated from game/core.py (``_tratar_eventos``, ``_atualizar_jogando``) and
game/settings.py (control bindings).
"""

from typing import Dict, List, Optional, Tuple

import pygame

from src.infrastructure.input.commands import (
    Back,
    Boost,
    Command,
    Confirm,
    MoveDown,
    MoveLeft,
    MoveRight,
    MoveUp,
    NavigateDown,
    NavigateLeft,
    NavigateRight,
    NavigateUp,
    NullCommand,
    Pause,
    SelectWeapon,
    Shoot,
    Special,
)
from src.infrastructure.input.controls import ControleConfiguracao


class InputManager:
    """Processes Pygame events and key states into semantic commands.

    Usage::

        im = InputManager(controles)
        # in event loop:
        comandos = im.processar_evento(evento)
        # in update loop:
        comandos_hold = im.processar_hold()
    """

    def __init__(self, controles: "ControleConfiguracao | None" = None):
        self.controles = controles
        self._mapeamento: Dict[int, str] = {}
        if controles is not None:
            self._mapeamento = {v: k for k, v in controles.controles.items()}

    def reconfigurar(self, controles: ControleConfiguracao) -> None:
        """Update the control mapping at runtime."""
        self.controles = controles
        self._mapeamento = {v: k for k, v in controles.controles.items()}

    # ------------------------------------------------------------------
    # Event-based commands (fire once per key press/release)
    # ------------------------------------------------------------------

    def processar_evento(self, evento: pygame.event.Event) -> List[Command]:
        """Convert a single Pygame event into a list of Commands.

        Returns an empty list for unrecognised events.
        """
        comandos: List[Command] = []

        if evento.type == pygame.KEYDOWN:
            comandos.extend(self._tratar_keydown(evento.key))
        elif evento.type == pygame.KEYUP:
            comandos.extend(self._tratar_keyup(evento.key))

        return comandos

    def _tratar_keydown(self, tecla: int) -> List[Command]:
        """Translate a KEYDOWN event to commands."""
        comandos: List[Command] = []

        # Movement (held keys are also checked in processar_hold)
        if tecla in (pygame.K_UP, self.controles.controles.get("cima", -1)):
            comandos.append(MoveUp(True))
        if tecla in (pygame.K_DOWN, self.controles.controles.get("baixo", -1)):
            comandos.append(MoveDown(True))
        if tecla in (pygame.K_LEFT, self.controles.controles.get("esquerda", -1)):
            comandos.append(MoveLeft(True))
        if tecla in (pygame.K_RIGHT, self.controles.controles.get("direita", -1)):
            comandos.append(MoveRight(True))

        # Actions
        if tecla in (pygame.K_SPACE, pygame.K_z,
                     self.controles.controles.get("atirar", -1)):
            comandos.append(Shoot(True))

        if tecla in (pygame.K_p, pygame.K_ESCAPE,
                     self.controles.controles.get("pausar", -1)):
            comandos.append(Pause())

        if tecla == pygame.K_e:
            comandos.append(Special())

        # Boost (held)
        if tecla in (pygame.K_LSHIFT, pygame.K_RSHIFT,
                     pygame.K_LCTRL, pygame.K_RCTRL):
            comandos.append(Boost(True))

        # Weapon selection (1-9)
        if pygame.K_1 <= tecla <= pygame.K_9:
            comandos.append(SelectWeapon(tecla - pygame.K_1))

        # Menu navigation
        if tecla in (pygame.K_RETURN, pygame.K_KP_ENTER):
            comandos.append(Confirm())
        if tecla == pygame.K_ESCAPE:
            comandos.append(Back())
        if tecla == pygame.K_UP:
            comandos.append(NavigateUp())
        if tecla == pygame.K_DOWN:
            comandos.append(NavigateDown())
        if tecla == pygame.K_LEFT:
            comandos.append(NavigateLeft())
        if tecla == pygame.K_RIGHT:
            comandos.append(NavigateRight())

        return comandos

    def _tratar_keyup(self, tecla: int) -> List[Command]:
        """Translate a KEYUP event to commands (mostly release signals)."""
        comandos: List[Command] = []

        if tecla in (pygame.K_UP, self.controles.controles.get("cima", -1)):
            comandos.append(MoveUp(False))
        if tecla in (pygame.K_DOWN, self.controles.controles.get("baixo", -1)):
            comandos.append(MoveDown(False))
        if tecla in (pygame.K_LEFT, self.controles.controles.get("esquerda", -1)):
            comandos.append(MoveLeft(False))
        if tecla in (pygame.K_RIGHT, self.controles.controles.get("direita", -1)):
            comandos.append(MoveRight(False))
        if tecla in (pygame.K_SPACE, pygame.K_z,
                     self.controles.controles.get("atirar", -1)):
            comandos.append(Shoot(False))
        if tecla in (pygame.K_LSHIFT, pygame.K_RSHIFT,
                     pygame.K_LCTRL, pygame.K_RCTRL):
            comandos.append(Boost(False))

        return comandos

    # ------------------------------------------------------------------
    # Held-key queries (called every frame, not per-event)
    # ------------------------------------------------------------------

    def processar_hold(self) -> Dict[str, bool]:
        """Return the current state of movement and action keys.

        This is a convenience method that mirrors the old pattern of
        calling ``pygame.key.get_pressed()`` directly, but structured as
        a dictionary so the game layer can query individual states.
        """
        teclas = pygame.key.get_pressed()
        c = self.controles.controles if self.controles else {}
        return {
            "cima": teclas[pygame.K_UP] or teclas.get(c.get("cima", -1), False),
            "baixo": teclas[pygame.K_DOWN] or teclas.get(c.get("baixo", -1), False),
            "esquerda": teclas[pygame.K_LEFT] or teclas.get(c.get("esquerda", -1), False),
            "direita": teclas[pygame.K_RIGHT] or teclas.get(c.get("direita", -1), False),
            "atirar": (teclas[pygame.K_SPACE] or teclas[pygame.K_z]
                       or teclas.get(c.get("atirar", -1), False)),
            "boost": (teclas[pygame.K_LSHIFT] or teclas[pygame.K_RSHIFT]
                      or teclas[pygame.K_LCTRL] or teclas[pygame.K_RCTRL]),
        }
