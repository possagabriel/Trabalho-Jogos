"""Vector2D - Representacao vetorial bidimensional."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Vector2:
    """Vetor 2D imutavel com operacoes comuns de jogo."""

    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: Vector2) -> Vector2:
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2) -> Vector2:
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vector2:
        return Vector2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> Vector2:
        return self.__mul__(scalar)

    def __neg__(self) -> Vector2:
        return Vector2(-self.x, -self.y)

    def __truediv__(self, scalar: float) -> Vector2:
        if scalar == 0:
            raise ValueError("Division by zero")
        return Vector2(self.x / scalar, self.y / scalar)

    def magnitude(self) -> float:
        """ Retorna a magnitude do vetor. """
        return math.hypot(self.x, self.y)

    def magnitude_squared(self) -> float:
        """ Retorna o quadrado da magnitude (evita sqrt). """
        return self.x * self.x + self.y * self.y

    def normalized(self) -> Vector2:
        """ Retorna o vetor unitario. """
        mag = self.magnitude()
        if mag == 0:
            return Vector2(0.0, 0.0)
        return self / mag

    def distance_to(self, other: Vector2) -> float:
        """ Distancia euclidiana ate outro vetor. """
        return (self - other).magnitude()

    def dot(self, other: Vector2) -> float:
        """ Produto escalar. """
        return self.x * other.x + self.y * other.y

    def to_tuple(self) -> tuple[int, int]:
        """ Converte para tupla de inteiros (para Pygame). """
        return (int(self.x), int(self.y))

    def to_tuple_float(self) -> tuple[float, float]:
        """ Converte para tupla de floats. """
        return (self.x, self.y)

    @classmethod
    def from_angle(cls, angle: float, magnitude: float = 1.0) -> Vector2:
        """ Cria um vetor a partir de um angulo (radianos). """
        return cls(
            x=math.cos(angle) * magnitude,
            y=math.sin(angle) * magnitude,
        )

    @classmethod
    def zero(cls) -> Vector2:
        """ Vetor nulo. """
        return cls(0.0, 0.0)
