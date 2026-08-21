"""Funcoes matematicas utilitarias."""

import math


def clamp(value: float, min_val: float, max_val: float) -> float:
    """ Limita um valor entre min e max. """
    return max(min_val, min(max_val, value))


def lerp(a: float, b: float, t: float) -> float:
    """ Interpolacao linear entre a e b. """
    return a + (b - a) * t


def ease_in_out(t: float) -> float:
    """ Smoothstep: aceleracao suave na entrada e saida. """
    t = clamp(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def ease_out(t: float) -> float:
    """ Desaceleracao suave na saida. """
    t = clamp(t, 0.0, 1.0)
    return 1 - (1 - t) * (1 - t)


def ease_in(t: float) -> float:
    """ Aceleracao suave na entrada. """
    t = clamp(t, 0.0, 1.0)
    return t * t


def ease_out_back(t: float) -> float:
    """ Saida com overshoot (bounce). """
    c1 = 1.70158
    c3 = c1 + 1
    t = clamp(t, 0.0, 1.0)
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """ Distancia euclidiana entre dois pontos. """
    return math.hypot(x2 - x1, y2 - y1)


def angle_between(x1: float, y1: float, x2: float, y2: float) -> float:
    """ Angulo em radianos entre dois pontos. """
    return math.atan2(y2 - y1, x2 - x1)
