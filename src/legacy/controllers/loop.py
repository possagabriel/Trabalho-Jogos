"""Controle do ciclo principal e dos eventos do jogo legado."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pygame

from src.core.constants import EstadoJogo, FPS, INCREMENTO_CARREGAMENTO

if TYPE_CHECKING:
    from src.legacy.application.core import Jogo


class ControladorLoop:
    """Coordena atualizacao, entrada e cadencia sem possuir o estado do jogo."""

    def __init__(self, jogo: Jogo) -> None:
        self.jogo = jogo

    def atualizar(self) -> None:
        """Atualiza o estado ativo e os efeitos que independem da tela."""
        jogo = self.jogo
        if jogo.estado is EstadoJogo.JOGANDO:
            jogo.tempo_partida += 1 / FPS
            jogo._atualizar_jogando()
        elif jogo.estado is EstadoJogo.PREPARANDO:
            jogo.carregamento += INCREMENTO_CARREGAMENTO
            if jogo.carregamento >= 100:
                jogo.carregamento = 100
                jogo.estado = EstadoJogo.JOGANDO
        elif jogo.estado in ("MENU", "CONTINUAR", "LOJA", "RECORDES", "CONFIG"):
            jogo.menu.atualizar()
        jogo.particulas.atualizar()
        jogo.cenario.atualizar()
        self._atualizar_textos_e_mensagens()
        jogo.fade = max(0, jogo.fade - 18) if jogo.fade > 0 else jogo.fade
        jogo.flash = max(0, jogo.flash - 1) if jogo.flash > 0 else jogo.flash
        jogo.boss_intro = max(0, jogo.boss_intro - 1) if jogo.boss_intro > 0 else jogo.boss_intro

    def _atualizar_textos_e_mensagens(self) -> None:
        jogo = self.jogo
        for texto in jogo.textos_acao[:]:
            texto.atualizar()
            if not texto.ativo:
                jogo.textos_acao.remove(texto)
        for mensagem in jogo.mensagens[:]:
            mensagem.atualizar()
            if not mensagem.viva:
                jogo.mensagens.remove(mensagem)

    def tratar_eventos(self) -> bool:
        """Processa os eventos recebidos e informa se o jogo continua ativo."""
        jogo = self.jogo
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                jogo._salvar_tudo()
                return False
            if jogo.estado in ("MENU", "CONTINUAR", "LOJA", "RECORDES", "CONFIG"):
                if not jogo.menu.tratar_eventos(evento):
                    return False
                continue
            if evento.type != pygame.KEYDOWN:
                continue
            if jogo.estado is EstadoJogo.JOGANDO:
                tecla_pausar = jogo.controles.get("pausar", 0)
                if evento.key in (pygame.K_p, pygame.K_ESCAPE, tecla_pausar):
                    jogo.estado = EstadoJogo.PAUSA
                elif evento.key == pygame.K_e:
                    jogo._ativar_especial()
                elif pygame.K_1 <= evento.key <= pygame.K_9:
                    jogo.jogador.selecionar_arma(evento.key - pygame.K_1)
            elif jogo.estado is EstadoJogo.PAUSA:
                jogo.pausa_controller.tratar_evento(evento)
            elif jogo.estado is EstadoJogo.GAME_OVER:
                if evento.key == pygame.K_RETURN:
                    jogo._preparar_jogo()
                elif evento.key == pygame.K_ESCAPE:
                    jogo.estado = EstadoJogo.MENU
                    jogo.fade = 255
        return jogo.rodando

    def executar(self) -> None:
        """Mantem o loop ate o encerramento solicitado pelo usuario."""
        jogo = self.jogo
        rodando = True
        while rodando:
            rodando = self.tratar_eventos()
            if not rodando:
                break
            if jogo.hitstop > 0:
                jogo.hitstop -= 1
            else:
                self.atualizar()
            jogo.render_controller.desenhar()
            jogo.relogio.tick(FPS)
        pygame.quit()
        sys.exit(0)
