"""Cobertura do deslocamento do mundo e da retomada do modo aberto."""

from __future__ import annotations

from types import SimpleNamespace

import pygame

from src.core.constants import ALTURA, LARGURA
from src.infrastructure.graphics.comic_theme import usar_visual
from src.runtime.domain.entities.player import Jogador
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


def test_mundo_usa_entidades_visuais_do_modo_linear():
    if not pygame.display.get_init():
        pygame.display.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))
    world = OpenWorldRuntime()
    player = Jogador()
    surface = pygame.Surface((LARGURA, ALTURA))

    with usar_visual({"estilo_visual": "COMIC", "qualidade_comic": "BAIXA"}):
        world.render(surface, player)
    with usar_visual({"estilo_visual": "ORIGINAL"}):
        world.render(surface, player)

    assert len(world.enemies) >= 3
    assert world.miniboss.nome.startswith("CENSOR")
    assert world.boss.nome == "HEXAGONO"
    assert (player.x, player.y) == (LARGURA // 2, ALTURA // 2)
    assert world._minimap.get_size() == (204, 144)
    assert len(world.enemies) == 24


def test_disparo_reutiliza_arma_e_direciona_para_frente_no_mundo():
    world = OpenWorldRuntime()
    game = SimpleNamespace(
        jogador=Jogador(),
        posicao_mira=lambda: None,
        config={"dispersao_duplo_graus": 12, "dispersao_espiral_graus": 14},
        mira=SimpleNamespace(ativar_pulso=lambda: None),
        sons=SimpleNamespace(tocar=lambda _som: None),
    )

    world.update(1 / 60, Teclas(pygame.K_SPACE), {}, game)

    assert world.projectiles
    assert world.projectiles[0].vel_y < 0
