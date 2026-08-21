"""Interface Updatable - Para entidades que precisam de atualizacao."""

from abc import ABC, abstractmethod


class Updatable(ABC):
    """Interface para entidades que precisam ser atualizadas a cada frame."""

    @abstractmethod
    def update(self, delta_time: float) -> None:
        """ Atualiza o estado da entidade. """
        pass
