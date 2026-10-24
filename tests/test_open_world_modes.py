"""Cobertura do deslocamento do mundo e da retomada do modo aberto."""

from __future__ import annotations

import pygame

from src.runtime.domain.world.open_world import OpenWorldRuntime

pygame.font.init()


class Teclas:
    """Stub pequeno para simular teclas pressionadas sem janela SDL."""

    def __init__(self, *pressed: int) -> None:
        self.pressed = set(pressed)

    def __getitem__(self, key: int) -> bool:
        return key in self.pressed


def test_decoracao_tem_semente_fixa_por_regiao():
    primeiro = OpenWorldRuntime()
    segundo = OpenWorldRuntime()

    assert primeiro._stars == segundo._stars
    assert primeiro._landmarks == segundo._landmarks


def test_camera_acompanha_movimento_e_vazio_repele_a_nave():
    world = OpenWorldRuntime()
    initial_camera = world.camera_x
    world.update(1 / 60, Teclas(pygame.K_RIGHT), {})
    assert world.x > world.SPAWN[0]
    assert world.camera_x > initial_camera

    edge = OpenWorldRuntime((60, 900))
    edge.update(1 / 60, Teclas(pygame.K_LEFT), {})
    assert edge.x > 60


def test_estado_salvo_contém_região_posição_e_checkpoint():
    world = OpenWorldRuntime((1200, 800), elapsed=90)

    assert world.save_state() == {
        "regiao": "espaco_profundo",
        "posicao": [1200.0, 800.0],
        "checkpoint": "inicio",
        "tempo": 90,
    }
