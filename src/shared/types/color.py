"""RGB Color - Representacao de cores tipada."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RGB:
    """Cor RGB imutavel com utilitarios de manipulacao."""

    r: int = 0
    g: int = 0
    b: int = 0

    def to_tuple(self) -> tuple[int, int, int]:
        """ Converte para tupla Pygame. """
        return (self.r, self.g, self.b)

    def to_tuple_alpha(self, alpha: int = 255) -> tuple[int, int, int, int]:
        """ Converte para tupla RGBA. """
        return (self.r, self.g, self.b, alpha)

    def darken(self, factor: float = 0.6) -> RGB:
        """ Retorna versao mais escura da cor. """
        return RGB(
            r=max(0, min(255, int(self.r * factor))),
            g=max(0, min(255, int(self.g * factor))),
            b=max(0, min(255, int(self.b * factor))),
        )

    def lighten(self, factor: float = 0.4) -> RGB:
        """ Retorna versao mais clara da cor. """
        return RGB(
            r=min(255, int(self.r + (255 - self.r) * factor)),
            g=min(255, int(self.g + (255 - self.g) * factor)),
            b=min(255, int(self.b + (255 - self.b) * factor)),
        )

    @classmethod
    def from_tuple(cls, colors: tuple[int, ...]) -> RGB:
        """ Cria RGB a partir de tupla. """
        return cls(r=colors[0], g=colors[1], b=colors[2])
