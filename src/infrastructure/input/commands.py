"""Command pattern for player input.

Defines the ``Command`` abstract base class and concrete command objects that
map raw key presses to semantic game actions.  Commands are created once per
frame by the ``InputManager`` and passed to the game layer for execution.

Migrated from game/settings.py (control actions) and game/core.py (input
handling) -- reified as proper Command objects.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from src.infrastructure.input.controls import ControleConfiguracao


class Command(abc.ABC):
    """Abstract command executed by the game layer."""

    @abc.abstractmethod
    def executar(self) -> None:
        """Execute this command."""


class NullCommand(Command):
    """No-op command (released keys, unknown actions)."""

    def executar(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Movement commands
# ---------------------------------------------------------------------------

class MoveUp(Command):
    """Move the player upward."""

    def __init__(self, estado: bool = True):
        self.estado = estado

    def executar(self) -> None:
        pass  # Game reads ``estado`` to decide behaviour


class MoveDown(Command):
    """Move the player downward."""

    def __init__(self, estado: bool = True):
        self.estado = estado

    def executar(self) -> None:
        pass


class MoveLeft(Command):
    """Move the player left."""

    def __init__(self, estado: bool = True):
        self.estado = estado

    def executar(self) -> None:
        pass


class MoveRight(Command):
    """Move the player right."""

    def __init__(self, estado: bool = True):
        self.estado = estado

    def executar(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Action commands
# ---------------------------------------------------------------------------

class Shoot(Command):
    """Fire the current weapon."""

    def __init__(self, estado: bool = True):
        self.estado = estado

    def executar(self) -> None:
        pass


class Pause(Command):
    """Toggle pause."""

    def executar(self) -> None:
        pass


class Special(Command):
    """Activate the special ability (Vortex Bomb)."""

    def executar(self) -> None:
        pass


class SelectWeapon(Command):
    """Select a weapon by index (0-8)."""

    def __init__(self, indice: int):
        self.indice = indice

    def executar(self) -> None:
        pass


class Boost(Command):
    """Activate speed boost (hold)."""

    def __init__(self, estado: bool = True):
        self.estado = estado

    def executar(self) -> None:
        pass


class Confirm(Command):
    """Confirm / accept (Enter key)."""

    def executar(self) -> None:
        pass


class Back(Command):
    """Go back / cancel (Escape key)."""

    def executar(self) -> None:
        pass


class NavigateUp(Command):
    """Navigate menu upward."""

    def executar(self) -> None:
        pass


class NavigateDown(Command):
    """Navigate menu downward."""

    def executar(self) -> None:
        pass


class NavigateLeft(Command):
    """Navigate menu left (e.g. adjust slider)."""

    def executar(self) -> None:
        pass


class NavigateRight(Command):
    """Navigate menu right (e.g. adjust slider)."""

    def executar(self) -> None:
        pass
