"""Chuvas decorativas curtas, determinísticas e desenhadas em 2D."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from functools import lru_cache

import pygame

from src.infrastructure.graphics.comic_theme import LARANJA, PAPEL, TINTA, opcoes_atuais
from src.runtime.infrastructure.graphics.smooth import (
    desenhar_circulo,
    desenhar_glow,
    desenhar_poligono,
)

INICIO_CHUVA = 5.0
INTERVALO_CHUVA = 14.0
DURACAO_CHUVA = 2.2
VIDA_METEORO = 0.95

CAUDA_EXTERNA = (94, 119, 150)
CAUDA_INTERNA = (158, 202, 223)
CABECA_QUENTE = (255, 225, 180)
FRAGMENTO = (173, 170, 160)


@lru_cache(maxsize=12)
def _quadros_meteoro(comprimento: int, angulo: int, comic: bool,
                     reduzido: bool) -> tuple[pygame.Surface, ...]:
    """Prepara cauda afilada e núcleo com fade suave em quadros reutilizáveis."""
    base = pygame.Surface((144, 144), pygame.SRCALPHA)
    centro = (72, 72)
    externa = LARANJA if comic else CAUDA_EXTERNA
    interna = PAPEL if comic else CAUDA_INTERNA
    if not reduzido:
        desenhar_glow(base, externa, centro, 11, 0.4)
        desenhar_poligono(base, externa,
                          ((68, 72), (84, 65), (72 + comprimento, 72), (84, 79)))
    desenhar_poligono(base, interna,
                      ((69, 72), (80, 69), (72 + comprimento, 72), (80, 75)))
    desenhar_circulo(base, TINTA if comic else externa, centro, 5)
    desenhar_circulo(base, CABECA_QUENTE, centro, 3)
    if not reduzido:
        desenhar_circulo(base, externa, (92, 81), 2)
        desenhar_circulo(base, interna, (107, 68), 1)
    base = pygame.transform.rotate(base, angulo)
    quadros = []
    for indice in range(16):
        quadro = base.copy()
        t = (indice + 0.5) / 16
        quadro.set_alpha(round(255 * min(1.0, t * 5, (1 - t) * 5)))
        quadros.append(quadro)
    return tuple(quadros)


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
    centro = (round(meteoro.x + meteoro.vx * idade),
              round(meteoro.y + meteoro.vy * idade))
    angulo = round(math.degrees(math.atan2(meteoro.vy, -meteoro.vx)) / 5) * 5
    comprimento = min(56, max(8, round(meteoro.comprimento / 8) * 8))
    quadros = _quadros_meteoro(comprimento, angulo, opcoes_atuais().ativo, reduzido)
    arte = quadros[min(15, int(idade / VIDA_METEORO * 16))]
    tela.blit(arte, arte.get_rect(center=centro))
