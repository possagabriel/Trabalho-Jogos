"""Interface Collidable - Para entidades que participam de colisoes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame


class Collidable(ABC):
    """Interface para entidades que podem colidir."""

    @abstractmethod
    def get_rect(self) -> pygame.Rect:
        """ Retorna o retangulo de colisao. """
        pass

    @abstractmethod
    def on_collision(self, other: Collidable) -> None:
        """ Callback chamado ao colidir com outra entidade. """
        pass
