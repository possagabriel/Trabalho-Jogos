"""Regras das tempestades desviáveis, independentes de desenho e qualidade."""

import random

import pytest

from src.runtime.domain.world.meteor_storm import TempestadeMeteoros


def iniciar(semente=41):
    tempestade = TempestadeMeteoros(random.Random(semente))
    tempestade.atualizar(tempestade.proxima_chuva, (5000, 5000), (1280, 720))
    return tempestade


def test_tempestade_avisa_antes_de_liberar_muitos_meteoros():
    chuva = iniciar()
    assert chuva.estado == "aviso"
    assert len(chuva.meteoros) >= 30
    assert not chuva.atinge((5000, 5000), 16)
    chuva.atualizar(chuva.DURACAO_AVISO, (5000, 5000), (1280, 720))
    assert chuva.estado == "ativa"


def test_tempestades_variam_com_semente_e_intervalo_sem_rng_global():
    estado = random.getstate()
    a, b, c = iniciar(7), iniciar(7), iniciar(8)
    assert a.meteoros == b.meteoros
    assert a.meteoros != c.meteoros
    assert a.proxima_chuva != c.proxima_chuva
    assert random.getstate() == estado


@pytest.mark.parametrize("semente", range(12))
def test_corredor_livre_permanece_entre_as_trajetorias(semente):
    chuva = iniciar(semente)
    for meteoro in chuva.meteoros:
        transversal = meteoro.x if chuva.vertical else meteoro.y
        assert abs(transversal - chuva.corredor) >= chuva.LARGURA_CORREDOR / 2 + meteoro.raio
        assert meteoro.atraso >= 0
        assert 400 <= abs(meteoro.vx or meteoro.vy) <= 560


def test_colisao_usa_segmento_e_meteoro_so_acerta_uma_vez():
    chuva = iniciar()
    chuva.atualizar(chuva.DURACAO_AVISO, (5000, 5000), (1280, 720))
    meteoro = chuva.meteoros[0]
    chuva.atualizar(0.2, (5000, 5000), (1280, 720))
    ponto = ((meteoro.anterior_x + meteoro.x) / 2, (meteoro.anterior_y + meteoro.y) / 2)
    assert chuva.atinge(ponto, 16)
    assert meteoro not in chuva.meteoros


def test_pausa_nao_avanca_e_tempestade_termina_com_intervalo():
    chuva = iniciar()
    estado = (chuva.estado, chuva.tempo, [(m.x, m.y) for m in chuva.meteoros])
    chuva.atualizar(0, (5000, 5000), (1280, 720))
    assert (chuva.estado, chuva.tempo, [(m.x, m.y) for m in chuva.meteoros]) == estado
    chuva.atualizar(chuva.DURACAO_AVISO + chuva.DURACAO_CHUVA, (5000, 5000), (1280, 720))
    assert chuva.estado == "calma"
    assert not chuva.meteoros
    assert 14 <= chuva.proxima_chuva <= 28
