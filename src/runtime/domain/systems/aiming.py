"""Cálculos puros de direção e dispersão dos disparos do jogador."""

from __future__ import annotations

import math

def direcao_para_alvo(
    origem: tuple[float, float], alvo: tuple[float, float], velocidade: float,
) -> tuple[float, float]:
    """Retorna velocidade de módulo fixo rumo ao alvo.

    Args:
        origem: Posição lógica de nascimento do projétil.
        alvo: Posição lógica da mira.
        velocidade: Módulo da velocidade da arma.

    Returns:
        Componentes de velocidade; para alvo coincidente, direção vertical.
    """
    dx, dy = alvo[0] - origem[0], alvo[1] - origem[1]
    distancia = math.hypot(dx, dy)
    if distancia == 0:
        return 0.0, -velocidade
    fator = velocidade / distancia
    return dx * fator, dy * fator


def dispersar_direcao(
    direcao: tuple[float, float], angulo_graus: float,
) -> tuple[float, float]:
    """Gira uma velocidade em torno da direção central da mira."""
    angulo = math.radians(angulo_graus)
    seno, cosseno = math.sin(angulo), math.cos(angulo)
    x, y = direcao
    return x * cosseno - y * seno, x * seno + y * cosseno
