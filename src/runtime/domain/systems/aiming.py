"""Cálculos puros de direção e dispersão dos disparos do jogador."""

from __future__ import annotations

import math

from src.core.constants import QUADROS_NAVE_DIRECIONAL


def angulo_para_alvo(
    origem: tuple[float, float], alvo: tuple[float, float],
) -> float:
    """Calcula o ângulo visual da nave, com zero apontando para cima."""
    dx, dy = alvo[0] - origem[0], alvo[1] - origem[1]
    if dx == 0 and dy == 0:
        return 0.0
    return math.degrees(math.atan2(dx, -dy)) % 360


def indice_sprite_direcional(
    angulo: float, quantidade: int = QUADROS_NAVE_DIRECIONAL,
) -> int:
    """Escolhe a sprite pré-renderizada mais próxima, incluindo o wrap 360°."""
    if quantidade <= 0:
        raise ValueError("A quantidade de sprites direcionais deve ser positiva")
    passo = 360 / quantidade
    return int(((angulo % 360) + passo / 2) // passo) % quantidade

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
