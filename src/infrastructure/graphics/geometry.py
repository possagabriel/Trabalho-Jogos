"""Geometry functions for drawing enemy and ship shapes.

Migrated from game/geometry.py -- every function preserved with full logic.
"""

import math
from typing import List, Tuple


def poligono(centro: Tuple[float, float], raio: float, lados: int,
             angulo: float = 0.0) -> List[Tuple[float, float]]:
    """Generate the vertices of a regular polygon."""
    cx, cy = centro
    return [(cx + math.cos(angulo + i * math.tau / lados) * raio,
             cy + math.sin(angulo + i * math.tau / lados) * raio)
            for i in range(lados)]


def estrela(centro: Tuple[float, float], raio: float, pontas: int = 5,
            angulo: float = 0.0,
            interno: "float | None" = None) -> List[Tuple[float, float]]:
    """Generate the vertices of a star (polygram)."""
    interno = raio * 0.45 if interno is None else interno
    cx, cy = centro
    pontos: list = []
    for i in range(pontas * 2):
        r = raio if i % 2 == 0 else interno
        a = angulo + i * math.pi / pontas
        pontos.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pontos


def losango(centro: Tuple[float, float], raio_x: float, raio_y: float,
            angulo: float = 0.0) -> List[Tuple[float, float]]:
    """Generate the vertices of a rhombus."""
    cx, cy = centro
    base = [(0, -raio_y), (raio_x, 0), (0, raio_y), (-raio_x, 0)]
    c, s = math.cos(angulo), math.sin(angulo)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in base]


def triangulo(centro: Tuple[float, float], raio: float,
              angulo: float = 0.0) -> List[Tuple[float, float]]:
    return poligono(centro, raio, 3, angulo)


def quadrado(centro: Tuple[float, float], raio: float,
             angulo: float = 0.0) -> List[Tuple[float, float]]:
    return poligono(centro, raio, 4, angulo + math.pi / 4)


def pentagono(centro: Tuple[float, float], raio: float,
              angulo: float = 0.0) -> List[Tuple[float, float]]:
    return poligono(centro, raio, 5, angulo - math.pi / 2)


def cruz(centro: Tuple[float, float], raio: float) -> List[Tuple[float, float]]:
    """Generate the points of a cross (used as a star in the Divine Plane)."""
    cx, cy = centro
    e = raio * 0.3
    return [(cx - raio, cy - e), (cx - e, cy - e), (cx - e, cy - raio),
            (cx + e, cy - raio), (cx + e, cy - e), (cx + raio, cy - e),
            (cx + raio, cy + e), (cx + e, cy + e), (cx + e, cy + raio),
            (cx - e, cy + raio), (cx - e, cy + e), (cx - raio, cy + e)]
