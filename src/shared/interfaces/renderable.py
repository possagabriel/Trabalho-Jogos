"""Interface Renderable - Para entidades que precisam ser desenhadas."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame


class Renderable(ABC):
    """Interface para entidades que precisam ser renderizadas na tela."""

    @abstractmethod
    def render(self, surface: pygame.Surface) -> None:
        """ Renderiza a entidade na superficie. """
        pass
