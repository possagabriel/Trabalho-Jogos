"""Mede o orçamento mínimo de desempenho das consultas de colisão."""

from __future__ import annotations

import argparse
import json
import random
import time
from dataclasses import dataclass

import pygame

from src.runtime.domain.spatial import GradeEspacial

LIMITE_SEGUNDOS = 2.0
LIMITE_MEDIO_CANDIDATOS = 150


@dataclass
class _Entidade:
    rect: pygame.Rect


def executar_benchmark(
    quantidade_entidades: int = 5_000,
    quantidade_consultas: int = 2_500,
) -> dict[str, float | int]:
    """Reconstrói e consulta uma cena densa com uma semente reproduzível."""
    aleatorio = random.Random(42)
    entidades = [
        _Entidade(pygame.Rect(
            aleatorio.randrange(0, 3_840),
            aleatorio.randrange(0, 2_160),
            aleatorio.randrange(12, 72),
            aleatorio.randrange(12, 72),
        ))
        for _ in range(quantidade_entidades)
    ]
    consultas = [
        pygame.Rect(
            aleatorio.randrange(0, 3_840),
            aleatorio.randrange(0, 2_160),
            48,
            48,
        )
        for _ in range(quantidade_consultas)
    ]
    grade: GradeEspacial[_Entidade] = GradeEspacial(96)

    inicio = time.perf_counter()
    grade.reconstruir(entidades)
    total_candidatos = sum(len(grade.consultar(area)) for area in consultas)
    duracao = time.perf_counter() - inicio
    return {
        "entidades": quantidade_entidades,
        "consultas": quantidade_consultas,
        "duracao_segundos": round(duracao, 6),
        "media_candidatos": round(total_candidatos / quantidade_consultas, 2),
    }


def main() -> int:
    """Exibe as métricas e falha apenas diante de uma regressão severa."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    argumentos = parser.parse_args()
    metricas = executar_benchmark()
    print(json.dumps(metricas, ensure_ascii=False, indent=2))
    if argumentos.check and (
        metricas["duracao_segundos"] > LIMITE_SEGUNDOS
        or metricas["media_candidatos"] > LIMITE_MEDIO_CANDIDATOS
    ):
        print("Orçamento de desempenho excedido.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
