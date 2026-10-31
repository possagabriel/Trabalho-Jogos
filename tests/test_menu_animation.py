"""Animação do menu com foco estável e alternativa sem movimento."""

import pygame
import pytest

from src.infrastructure.ui.layout import Layout
from src.runtime.infrastructure.graphics.menu_animation import (
    CenaMenuAnimada,
    FocoAnimado,
)


def test_foco_avanca_sem_saltar_ou_ultrapassar_e_regride_ao_sair():
    foco = FocoAnimado()
    foco.atualizar(True, 1 / 60)
    assert 0 < foco.valor < 1
    for _ in range(60):
        foco.atualizar(True, 1 / 60)
    assert 0.99 < foco.valor <= 1
    antes = foco.valor
    foco.atualizar(False, 1 / 60)
    assert 0 < foco.valor < antes


def test_foco_independe_da_taxa_de_atualizacao_e_reducao_remove_movimento():
    a, b = FocoAnimado(), FocoAnimado()
    for _ in range(60):
        a.atualizar(True, 1 / 60)
    for _ in range(30):
        b.atualizar(True, 1 / 30)
    assert a.valor == pytest.approx(b.valor)
    a.atualizar(False, 1 / 60, reduzido=True)
    assert a.valor == 0
    a.atualizar(True, 1 / 60, reduzido=True)
    assert a.valor == 1


def test_cena_suaviza_parallax_e_congela_com_efeitos_reduzidos():
    cena = CenaMenuAnimada()
    cena.atualizar(1 / 60, (1.0, -1.0))
    assert 0 < cena.parallax[0] < 1
    assert -1 < cena.parallax[1] < 0
    assert cena.tempo > 0
    cena.atualizar(1 / 60, (-1.0, 1.0), reduzido=True)
    assert cena.tempo == 0 and cena.parallax == (0.0, 0.0)


@pytest.mark.parametrize("resolucao", [(900, 700), (1920, 1080)])
def test_fundo_animado_muda_e_modo_reduzido_permanece_estatico(resolucao):
    tela = pygame.Surface(resolucao, pygame.SRCALPHA)
    layout = Layout(*resolucao)
    cena = CenaMenuAnimada()
    cena.desenhar(tela, layout)
    antes = pygame.image.tobytes(tela, "RGBA")
    cena.atualizar(1.0, (0.8, 0.3))
    tela.fill((0, 0, 0, 0))
    cena.desenhar(tela, layout)
    assert antes != pygame.image.tobytes(tela, "RGBA")
    cena.atualizar(1 / 60, (1, 1), reduzido=True)
    tela.fill((0, 0, 0, 0))
    cena.desenhar(tela, layout)
    reduzido = pygame.image.tobytes(tela, "RGBA")
    cena.atualizar(1, (-1, -1), reduzido=True)
    tela.fill((0, 0, 0, 0))
    cena.desenhar(tela, layout)
    assert reduzido == pygame.image.tobytes(tela, "RGBA")
