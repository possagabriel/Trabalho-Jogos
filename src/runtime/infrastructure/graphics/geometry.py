"""Funcoes de geometria para desenhar as formas dos inimigos e da nave."""

import math


def poligono(centro, raio, lados, angulo=0.0):
    """Gera os vertices de um poligono regular."""
    cx, cy = centro
    return [(cx + math.cos(angulo + i * math.tau / lados) * raio,
             cy + math.sin(angulo + i * math.tau / lados) * raio)
            for i in range(lados)]


def estrela(centro, raio, pontas=5, angulo=0.0, interno=None):
    """Gera os vertices de uma estrela (poligrama)."""
    interno = raio * 0.45 if interno is None else interno
    cx, cy = centro
    pontos = []
    for i in range(pontas * 2):
        r = raio if i % 2 == 0 else interno
        a = angulo + i * math.pi / pontas
        pontos.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pontos


def losango(centro, raio_x, raio_y, angulo=0.0):
    """Gera os vertices de um losango."""
    cx, cy = centro
    base = [(0, -raio_y), (raio_x, 0), (0, raio_y), (-raio_x, 0)]
    c, s = math.cos(angulo), math.sin(angulo)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in base]


def triangulo(centro, raio, angulo=0.0):
    return poligono(centro, raio, 3, angulo)


def quadrado(centro, raio, angulo=0.0):
    return poligono(centro, raio, 4, angulo + math.pi / 4)


def pentagono(centro, raio, angulo=0.0):
    return poligono(centro, raio, 5, angulo - math.pi / 2)


def cruz(centro, raio):
    """Gera os pontos de uma cruz (usada como estrela no Plano Divino)."""
    cx, cy = centro
    e = raio * 0.3
    return [(cx - raio, cy - e), (cx - e, cy - e), (cx - e, cy - raio),
            (cx + e, cy - raio), (cx + e, cy - e), (cx + raio, cy - e),
            (cx + raio, cy + e), (cx + e, cy + e), (cx + e, cy + raio),
            (cx - e, cy + raio), (cx - e, cy + e), (cx - raio, cy + e)]