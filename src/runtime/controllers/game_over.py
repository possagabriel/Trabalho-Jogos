"""Fluxo de encerramento de uma partida."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.runtime.infrastructure.persistence.save_system import SistemaProgressao

if TYPE_CHECKING:
    from src.runtime.application.core import Jogo


class ControladorGameOver:
    """Consolida resultado, persistencia e transicao para game over."""

    def __init__(self, jogo: Jogo) -> None:
        self.jogo = jogo

    def encerrar_partida(self) -> None:
        """Registra a partida encerrada e dispara seu feedback final."""
        jogo = self.jogo
        melhor_anterior = SistemaProgressao.melhor_pontuacao()
        jogo.recordes = SistemaProgressao.salvar_recorde(
            jogo.jogador.nome, jogo.jogador.pontuacao, jogo.jogador.nivel,
            jogo.jogador.skin.nome)
        jogo.novo_recorde = jogo.jogador.pontuacao > melhor_anterior
        jogo.moedas_ganhas = jogo.jogador.moedas_jogo + jogo.progresso._moedas_fim_jogo(
            jogo.cenario.id, jogo.bosses_abates)
        jogo.progresso.registrar_fim_jogo(
            jogo.jogador, jogo.tempo_partida, jogo.inimigos_abates,
            jogo.cenario.id, jogo.bosses_abates)
        jogo.loja.moedas += jogo.moedas_ganhas
        jogo._salvar_tudo()
        jogo.sons.tocar("gameover")
        jogo.particulas.explosao_dupla(jogo.jogador.x, jogo.jogador.y)
        jogo.estado = "GAME_OVER"
