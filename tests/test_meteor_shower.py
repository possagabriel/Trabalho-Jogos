"""Regras determinísticas das chuvas curtas de meteoros do cenário."""

import pygame

from src.runtime.infrastructure.graphics.meteor_shower import (
    MeteoroVisual,
    desenhar_meteoro,
    gerar_chuva,
    janela_chuva,
)


def test_janela_de_chuva_tem_pausa_entre_grupos() -> None:
    assert janela_chuva(4.9) is None
    assert janela_chuva(5.0) == (0, 0.0)
    assert janela_chuva(7.5) is None
    assert janela_chuva(19.0) == (1, 0.0)


def test_chuva_pequena_reproduz_velocidade_e_espacamento() -> None:
    primeira = gerar_chuva(4101, 1280, 720, 4)

    assert primeira == gerar_chuva(4101, 1280, 720, 4)
    assert primeira != gerar_chuva(4102, 1280, 720, 4)
    assert len(primeira) == 4
    assert all(m.vx < 0 < m.vy and 0 <= m.atraso < 1.0 for m in primeira)


def test_meteoro_desenha_cabeca_e_cauda_sem_alocar_outro_canvas() -> None:
    tela = pygame.Surface((320, 240), pygame.SRCALPHA)
    meteoro = MeteoroVisual(220, 25, -300, 250, 0, 42)

    desenhar_meteoro(tela, meteoro, 0.35)

    assert tela.get_bounding_rect().width >= 20
    assert tela.get_bounding_rect().height >= 20


def test_arte_meteoro_tem_estilos_e_efeitos_distintos_e_cache_preservado() -> None:
    from src.runtime.infrastructure.graphics.meteor_shower import _quadros_meteoro

    original = _quadros_meteoro(48, 40, False, False)
    comic = _quadros_meteoro(48, 40, True, False)
    reduzido = _quadros_meteoro(48, 40, False, True)
    antes = pygame.image.tobytes(original[8], "RGBA")
    assert original is _quadros_meteoro(48, 40, False, False)
    assert antes != pygame.image.tobytes(comic[8], "RGBA")
    assert antes != pygame.image.tobytes(reduzido[8], "RGBA")
    tela = pygame.Surface((320, 240), pygame.SRCALPHA)
    desenhar_meteoro(tela, MeteoroVisual(220, 25, -300, 250, 0, 48), 0.5)
    assert pygame.image.tobytes(original[8], "RGBA") == antes


def test_rochas_cacheadas_preservam_forma_e_diferenciam_estilos() -> None:
    from src.runtime.infrastructure.graphics.world_objects import arte_asteroide

    forma = ((-18, -10), (3, -20), (21, -3), (16, 17), (-9, 19), (-22, 2))
    original = arte_asteroide(forma, 24, False)
    assert original is arte_asteroide(forma, 24, False)
    comic = arte_asteroide(forma, 24, True)
    assert original.get_bounding_rect().width > 30
    assert pygame.image.tobytes(original, "RGBA") != pygame.image.tobytes(comic, "RGBA")
    assert forma[0] == (-18, -10)
