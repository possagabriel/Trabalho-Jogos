"""Miniaturas reconhecíveis, cache e orientação sem mutação do gameplay."""

from unittest.mock import Mock

import pygame
import pytest

from src.core.constants import ALTURA, LARGURA
from src.infrastructure.graphics.comic_theme import usar_visual
from src.runtime.domain.entities.player import Jogador
from src.runtime.domain.world.open_world import OpenWorldRuntime
from src.runtime.infrastructure.graphics.map_art import (
    miniatura_anomalia,
    miniatura_entidade,
    miniatura_nave,
)
from src.runtime.infrastructure.graphics.menu_panels import (
    ACENTO_ORIGINAL,
    FOCO_ORIGINAL,
    TEXTO_ORIGINAL,
    painel_original,
)
from src.runtime.infrastructure.graphics.meteor_shower import _arte_meteoro_ativo


@pytest.fixture(autouse=True)
def fontes():
    pygame.font.init()


@pytest.mark.parametrize("comic", [False, True])
def test_miniaturas_cacheiam_arte_real_sem_mover_entidades(comic):
    mundo = OpenWorldRuntime()
    antes = (mundo.boss.x, mundo.boss.y, mundo.boss.angulo, mundo.boss.flash, mundo.boss.entrando)
    arte = miniatura_entidade(mundo.boss, comic, 38)
    assert arte is miniatura_entidade(mundo.boss, comic, 38)
    assert max(arte.get_size()) == 38
    assert arte.get_bounding_rect().w > 10
    assert antes == (mundo.boss.x, mundo.boss.y, mundo.boss.angulo, mundo.boss.flash,
                     mundo.boss.entrando)
    buraco = miniatura_anomalia(False, comic, 30)
    portal = miniatura_anomalia(True, comic, 30)
    assert pygame.image.tobytes(buraco, "RGBA") != pygame.image.tobytes(portal, "RGBA")


def test_mapa_e_minimapa_usam_casco_e_direcao_da_nave_sem_muta_la(monkeypatch):
    from src.runtime.domain.world import open_world

    mundo, jogador = OpenWorldRuntime(), Jogador()
    mundo._aim_screen = (LARGURA // 2 + 100, ALTURA // 2 - 20)
    antes = (jogador.x, jogador.y, jogador.angulo_mira, jogador.vida)
    desenhos = []

    def registrar(skin, angulo, comic, tamanho):
        desenhos.append((skin, angulo, tamanho))
        return pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)

    monkeypatch.setattr(open_world, "miniatura_nave", registrar)
    tela = pygame.Surface((LARGURA, ALTURA))
    mundo.render_map(tela, jogador)
    mundo._draw_minimap(tela)
    assert (jogador.skin, 90, 32) in desenhos
    assert desenhos[-1] == (jogador.skin, 90, 20)
    assert antes == (jogador.x, jogador.y, jogador.angulo_mira, jogador.vida)


def test_miniatura_da_nave_muda_com_direcao_e_cache_nao_e_mutado():
    jogador = Jogador()
    cima = miniatura_nave(jogador.skin, 0, False, 32)
    antes = pygame.image.tobytes(cima, "RGBA")
    direita = miniatura_nave(jogador.skin, 90, False, 32)
    assert antes != pygame.image.tobytes(direita, "RGBA")
    assert cima is miniatura_nave(jogador.skin, 0, False, 32)
    assert antes == pygame.image.tobytes(cima, "RGBA")


def test_corpo_do_meteoro_perigoso_permanece_opaco_com_efeitos_reduzidos():
    normal = _arte_meteoro_ativo(18, 0, False, False)
    reduzido = _arte_meteoro_ativo(18, 0, False, True)
    for dx, dy in ((0, 0), (4, 0), (0, -4), (-4, 4)):
        assert normal.get_at((72 + dx, 72 + dy)) == reduzido.get_at((72 + dx, 72 + dy))
        assert reduzido.get_at((72 + dx, 72 + dy)).a == 255


def test_menu_original_recortado_com_foco_lateral_e_contraste():
    painel = painel_original((300, 70), (0, 0, 0), (255, 0, 255), selecionado=True)
    assert painel.get_at((150, 20))[:3] == FOCO_ORIGINAL
    assert painel.get_at((150, 45))[:3] == FOCO_ORIGINAL
    assert painel.get_at((3, 35))[:3] == ACENTO_ORIGINAL
    assert max(FOCO_ORIGINAL) < 80 and min(TEXTO_ORIGINAL) > 220


def test_meteoro_atinge_pelo_controlador_existente_e_respeita_intangibilidade():
    from types import SimpleNamespace

    mundo = OpenWorldRuntime()
    chuva = mundo.tempestade
    chuva.atualizar(chuva.proxima_chuva, (mundo.x, mundo.y), (LARGURA, ALTURA))
    chuva.atualizar(chuva.DURACAO_AVISO + 0.1, (mundo.x, mundo.y), (LARGURA, ALTURA))
    meteoro = chuva.meteoros[0]
    mundo.x, mundo.y = meteoro.x, meteoro.y
    jogador = SimpleNamespace(tempo_intangivel=5, raio=16, vivo=True)
    jogo = SimpleNamespace(jogador=jogador, combate_controller=Mock())
    mundo._colidir_meteoros(jogo)
    jogo.combate_controller.aplicar_dano_jogador.assert_not_called()
    jogador.tempo_intangivel = 0
    mundo._colidir_meteoros(jogo)
    jogo.combate_controller.aplicar_dano_jogador.assert_called_once_with()


def test_render_da_tempestade_nao_altera_fisica_nem_em_reducao_de_efeitos():
    mundo = OpenWorldRuntime()
    chuva = mundo.tempestade
    chuva.atualizar(chuva.proxima_chuva, (mundo.x, mundo.y), (LARGURA, ALTURA))
    chuva.atualizar(chuva.DURACAO_AVISO + 0.5, (mundo.x, mundo.y), (LARGURA, ALTURA))
    antes = [(m.x, m.y, m.vx, m.vy, m.raio) for m in chuva.meteoros]
    for efeitos in ("NORMAL", "REDUZIDO", "DESLIGADO"):
        mundo.visual_config = {"qualidade_grafica": "ALTA", "intensidade_flash": efeitos}
        with usar_visual({"estilo_visual": "ORIGINAL"}):
            mundo._draw_meteor_shower(pygame.Surface((LARGURA, ALTURA)))
    assert antes == [(m.x, m.y, m.vx, m.vy, m.raio) for m in chuva.meteoros]
