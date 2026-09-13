"""Testes do passo fixo e das métricas de desempenho."""

from src.runtime.application.timing import RelogioSimulacao
from src.runtime.diagnostics.frame_metrics import MetricasQuadro


def test_relogio_acumula_fracoes_sem_depender_do_fps_renderizado() -> None:
    relogio = RelogioSimulacao(passo=0.01, maximo_passos=5)

    assert relogio.consumir(4) == 0
    assert relogio.consumir(6) == 1
    assert relogio.consumir(25) == 2
    assert 0.49 <= relogio.fracao <= 0.51


def test_relogio_limita_recuperacao_de_atraso() -> None:
    relogio = RelogioSimulacao(passo=0.01, maximo_passos=5)

    assert relogio.consumir(5000) == 5
    assert relogio.fracao == 0.0


def test_metricas_calculam_p95_e_um_por_cento_baixo() -> None:
    metricas = MetricasQuadro(tamanho_janela=100)
    for tempo in range(1, 101):
        metricas.registrar(tempo)

    assert metricas.media_ms == 50.5
    assert metricas.p95_ms == 95
    assert round(metricas.fps_1_baixo, 2) == 10.10
