"""Testes do índice espacial usado nas colisões."""

import pygame

from src.runtime.domain.spatial import GradeEspacial


class EntidadeFalsa:
    def __init__(self, rect: pygame.Rect) -> None:
        self._rect = rect

    @property
    def rect(self) -> pygame.Rect:
        return self._rect


def test_grade_retorna_apenas_candidatos_das_celulas_tocadas() -> None:
    perto = EntidadeFalsa(pygame.Rect(10, 10, 20, 20))
    longe = EntidadeFalsa(pygame.Rect(500, 500, 20, 20))
    grade: GradeEspacial[EntidadeFalsa] = GradeEspacial(64)
    grade.reconstruir([perto, longe])

    assert grade.consultar(pygame.Rect(0, 0, 40, 40)) == [perto]


def test_entidade_em_varias_celulas_nao_e_duplicada() -> None:
    grande = EntidadeFalsa(pygame.Rect(40, 40, 100, 100))
    grade: GradeEspacial[EntidadeFalsa] = GradeEspacial(64)
    grade.reconstruir([grande])

    assert grade.consultar(pygame.Rect(0, 0, 200, 200)) == [grande]
