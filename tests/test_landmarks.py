"""Testes das regras puras do percurso visual."""

import pytest

from src.runtime.domain.world.landmarks import (
    EstadoDestino,
    EstadoMundoVisual,
    FadeDimensao,
    ProgressTracker,
    RitmoVariavel,
    SorteadorMarcos,
    TransicaoDestino,
    curva_evolucao,
)


def test_sorteio_com_semente_e_reprodutivel_sem_repetir_em_sequencia() -> None:
    primeiro = SorteadorMarcos(("planeta", "estacao", "cristal"), 42, 4, 8)
    segundo = SorteadorMarcos(("planeta", "estacao", "cristal"), 42, 4, 8)

    agenda_a = [primeiro.proximo() for _ in range(12)]
    agenda_b = [segundo.proximo() for _ in range(12)]

    assert agenda_a == agenda_b
    assert all(a.marco != b.marco for a, b in zip(agenda_a, agenda_a[1:]))
    assert all(4 <= marco.intervalo <= 8 for marco in agenda_a)


def test_curva_de_evolucao_respeita_extremos_e_progresso_crescente() -> None:
    pontos = [curva_evolucao(valor, "suave") for valor in (0, 0.25, 0.5, 0.75, 1)]

    assert pontos[0] == 0.0
    assert pontos[-1] == 1.0
    assert pontos == sorted(pontos)
    assert pontos[2] == pytest.approx(0.5)


def test_ritmo_tem_sorteio_reprodutivel_e_limites_de_velocidade() -> None:
    primeiro = RitmoVariavel(
        semente=7, duracao_variacao=2.0, variacao_maxima=0.1, duracao_passagem=1.0
    )
    segundo = RitmoVariavel(
        semente=7, duracao_variacao=2.0, variacao_maxima=0.1, duracao_passagem=1.0
    )

    amostra_a = []
    passagens = []
    amostra_b = []
    for _ in range(40):
        amostra_a.append(primeiro.atualizar(0.25))
        passagens.append(primeiro.em_passagem)
        amostra_b.append(segundo.atualizar(0.25))

    assert amostra_a == amostra_b
    assert all(0.9 <= fator <= 1.1 for fator in amostra_a)
    assert any(passagens)


def test_progresso_nao_regride_quando_a_onda_recebe_spawn_extra() -> None:
    progresso = ProgressTracker(suavizacao=4.0)
    progresso.reiniciar(unidades=10)
    progresso.atualizar(fila=4, ativos=2, dt=0.1)
    antes = progresso.valor

    progresso.atualizar(fila=6, ativos=4, dt=0.25)

    assert progresso.valor == antes
    progresso.atualizar(fila=0, ativos=4, dt=0.1)
    assert progresso.valor > antes
    assert progresso.valor < 1.0


def test_progresso_interpola_em_direcao_ao_fim_de_onda_vazia() -> None:
    progresso = ProgressTracker(suavizacao=2.0)
    progresso.reiniciar(unidades=0)

    primeiro_passo = progresso.atualizar(fila=0, ativos=0, dt=0.1)
    passo_final = progresso.atualizar(fila=0, ativos=0, dt=10.0)

    assert 0.0 < primeiro_passo < 1.0
    assert passo_final == pytest.approx(1.0)


def test_fase_so_com_boss_aguarda_derrota_e_reinicia_no_zero() -> None:
    progresso = ProgressTracker()
    progresso.reiniciar(unidades=0, nivel_de_boss=True)

    assert progresso.atualizar(0, 0, 1.0, chefe_ativo=True) == 0.0
    assert progresso.atualizar(0, 0, 1.0, concluido=True) > 0.0

    progresso.reiniciar(unidades=8)

    assert progresso.valor == 0.0
    assert progresso.atualizar(0, 0, 1.0) == pytest.approx(1.0)


def test_destino_derrotado_durante_frenagem_sai_sem_salto_de_escala() -> None:
    destino = TransicaoDestino(duracao_entrada=2.0, duracao_saida=1.0)
    destino.iniciar_boss()
    destino.atualizar(0.5, EstadoMundoVisual.FREANDO)
    escala = destino.escala
    opacidade = destino.opacidade

    destino.derrotar_boss()
    primeiro_passo = destino.atualizar(0.01, EstadoMundoVisual.ACELERANDO)

    assert destino.estado is EstadoDestino.SAINDO
    assert primeiro_passo is True
    assert destino.escala == pytest.approx(escala, abs=0.01)
    assert destino.opacidade == pytest.approx(opacidade, abs=0.01)


def test_destino_pendente_fica_estavel_ate_fim_da_cutscene() -> None:
    destino = TransicaoDestino()
    destino.iniciar_boss()
    destino.atualizar(1.0, EstadoMundoVisual.FREANDO)
    destino.derrotar_boss(cutscene_pendente=True)
    escala = destino.escala

    destino.atualizar(0.5, EstadoMundoVisual.PARADO)
    assert destino.estado is EstadoDestino.AGUARDANDO_CUTSCENE
    assert destino.escala == escala

    destino.liberar_cutscene()
    assert destino.estado is EstadoDestino.SAINDO


@pytest.mark.parametrize(
    "estado",
    ("PAUSA", "CUTSCENE", "MELHORIA", "GAME_OVER"),
)
def test_transicao_visual_congela_nos_estados_de_tela(estado: str) -> None:
    destino = TransicaoDestino()
    destino.iniciar_boss()
    destino.atualizar(0.2, EstadoMundoVisual.FREANDO, estado_jogo=estado)

    escala = destino.escala
    destino.atualizar(0.5, EstadoMundoVisual.FREANDO, estado_jogo=estado)

    assert destino.escala == escala


def test_fade_de_dimensao_tem_inicio_e_fim_continuos_durante_aceleracao() -> None:
    fade = FadeDimensao(duracao=1.0)
    inicio = fade.antiga

    fade.atualizar(0.25, EstadoMundoVisual.ACELERANDO)
    meio_antiga = fade.antiga
    meio_nova = fade.nova
    fade.atualizar(0.75, EstadoMundoVisual.ACELERANDO)

    assert inicio == 1.0
    assert 0.0 < meio_antiga < 1.0
    assert 0.0 < meio_nova < 1.0
    assert fade.antiga == 0.0
    assert fade.nova == 1.0
