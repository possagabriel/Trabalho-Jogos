"""Chuvas decorativas curtas, determinísticas e desenhadas em 2D."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

INICIO_CHUVA = 5.0
INTERVALO_CHUVA = 14.0
DURACAO_CHUVA = 2.2
VIDA_METEORO = 0.95

CAUDA_EXTERNA = (94, 119, 150)
CAUDA_INTERNA = (158, 202, 223)
CABECA_QUENTE = (255, 225, 180)
FRAGMENTO = (173, 170, 160)


@dataclass(frozen=True, slots=True)
class MeteoroVisual:
    """Trajetória curta de um meteoro sem colisão ou efeito de jogo."""

    x: float
    y: float
    vx: float
    vy: float
    atraso: float
    comprimento: float


def janela_chuva(tempo: float) -> tuple[int, float] | None:
    """Informa o ciclo e seu tempo local durante uma chuva.

    Args:
        tempo: Segundos de simulação do cenário.

    Returns:
        Índice e tempo local, ou ``None`` durante a pausa entre chuvas.
    """
    if not math.isfinite(tempo) or tempo < INICIO_CHUVA:
        return None
    decorrido = tempo - INICIO_CHUVA
    ciclo = int(decorrido // INTERVALO_CHUVA)
    fase = decorrido - ciclo * INTERVALO_CHUVA
    return (ciclo, fase) if fase < DURACAO_CHUVA else None


def gerar_chuva(semente: int, largura: int, altura: int,
                quantidade: int = 4) -> tuple[MeteoroVisual, ...]:
    """Cria uma pequena chuva reproduzível sem alterar estado global de RNG.

    Args:
        semente: Semente estável do cenário e do ciclo.
        largura: Largura do canvas.
        altura: Altura do canvas.
        quantidade: Número de meteoros, limitado a seis.

    Returns:
        Trajetórias espaçadas no tempo e no espaço.
    """
    rng = random.Random(semente)
    return tuple(
        MeteoroVisual(
            x=rng.uniform(largura * 0.38, largura * 1.08),
            y=rng.uniform(-altura * 0.08, altura * 0.24),
            vx=rng.uniform(-470.0, -300.0),
            vy=rng.uniform(235.0, 390.0),
            atraso=index * 0.19 + rng.uniform(0.0, 0.06),
            comprimento=rng.uniform(24.0, 54.0),
        )
        for index in range(max(0, min(6, quantidade)))
    )


def desenhar_meteoro(tela: pygame.Surface, meteoro: MeteoroVisual,
                     idade: float, *, reduzido: bool = False) -> None:
    """Desenha cabeça quente, cauda afilada e poucos fragmentos sem flash.

    Args:
        tela: Canvas 2D já existente.
        meteoro: Trajetória gerada para o ciclo.
        idade: Segundos desde o início individual do meteoro.
        reduzido: Remove brilho externo e fragmentos decorativos.
    """
    if not 0.0 < idade < VIDA_METEORO:
        return
    velocidade = math.hypot(meteoro.vx, meteoro.vy)
    comprimento = min(meteoro.comprimento, idade * velocidade * 0.8)
    if comprimento < 2.0:
        return
    brilho = min(1.0, idade * 8.0, (VIDA_METEORO - idade) * 5.0)
    centro = (round(meteoro.x + meteoro.vx * idade),
              round(meteoro.y + meteoro.vy * idade))
    cauda = (round(centro[0] - meteoro.vx / velocidade * comprimento),
             round(centro[1] - meteoro.vy / velocidade * comprimento))
    meio = (round(centro[0] - meteoro.vx / velocidade * comprimento * 0.45),
            round(centro[1] - meteoro.vy / velocidade * comprimento * 0.45))

    def atenuar(cor: tuple[int, int, int]) -> tuple[int, int, int]:
        return tuple(round(canal * brilho) for canal in cor)

    if not reduzido:
        pygame.draw.line(tela, atenuar(CAUDA_EXTERNA), cauda, centro, 4)
    pygame.draw.line(tela, atenuar(CAUDA_INTERNA), cauda, centro, 2)
    pygame.draw.line(tela, atenuar(CABECA_QUENTE), meio, centro, 1)
    pygame.draw.circle(tela, atenuar(CABECA_QUENTE), centro, 2)
    if not reduzido:
        fragmento = (round((cauda[0] * 2 + centro[0]) / 3),
                     round((cauda[1] * 2 + centro[1]) / 3) + 3)
        pygame.draw.circle(tela, atenuar(FRAGMENTO), fragmento, 1)
