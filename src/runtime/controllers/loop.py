"""Controle do ciclo principal e dos eventos do jogo legado."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pygame

from src.core.constants import FPS, INCREMENTO_CARREGAMENTO, EstadoJogo
from src.core.event_bus import GameEventType, publicar_evento
from src.runtime.application.timing import PASSO_FIXO, RelogioSimulacao

if TYPE_CHECKING:
    from src.runtime.application.core import Jogo


class ControladorLoop:
    """Coordena atualizacao, entrada e cadencia sem possuir o estado do jogo."""

    def __init__(self, jogo: Jogo) -> None:
        self.jogo = jogo

    def atualizar(self) -> None:
        """Atualiza o estado ativo e os efeitos que independem da tela."""
        jogo = self.jogo
        strategy = jogo.estrategia_modo
        if strategy is not None:
            strategy.update(jogo, PASSO_FIXO)
        world_managed = bool(strategy and strategy.handles_gameplay)
        if jogo.profile_service.save_error and not getattr(jogo, "_aviso_save_exibido", False):
            jogo.menu.notificacoes.adicionar("Falha ao salvar perfil", "erro")
            jogo._aviso_save_exibido = True
        elif not jogo.profile_service.save_error:
            jogo._aviso_save_exibido = False
        if jogo.estado is EstadoJogo.JOGANDO:
            if world_managed:
                pass
            elif jogo.progressao_controller.transicao is not None:
                jogo.progressao_controller.atualizar_transicao()
            else:
                jogo.tempo_partida += PASSO_FIXO
                jogo._atualizar_jogando()
                jogo.progressao_controller.atualizar_progresso_visual(
                    PASSO_FIXO, concluido=jogo.estado is EstadoJogo.MELHORIA)
        elif jogo.estado is EstadoJogo.MELHORIA:
            jogo.progressao_controller.atualizar_progresso_visual(
                PASSO_FIXO, concluido=True)
        elif jogo.estado is EstadoJogo.CUTSCENE:
            jogo.cutscene_controller.atualizar(PASSO_FIXO)
            return
        elif jogo.estado is EstadoJogo.PREPARANDO:
            jogo.carregamento += INCREMENTO_CARREGAMENTO
            if jogo.carregamento >= 100:
                jogo.carregamento = 100
                jogo.estado = EstadoJogo.JOGANDO
                publicar_evento(GameEventType.GAME_START, sessao=jogo)
        elif jogo.estado in ("MENU", "CONTINUAR", "LOJA", "RECORDES", "CONFIG"):
            jogo.menu.atualizar()
        # O fundo de combate e suas partículas não são visíveis no menu.
        # Evitar esse trabalho fora da partida reduz uso de CPU em idle.
        mundo_visivel = not world_managed and jogo.estado in (
            EstadoJogo.JOGANDO, EstadoJogo.MELHORIA,
            EstadoJogo.PAUSA, EstadoJogo.GAME_OVER)
        if (mundo_visivel and not jogo.menu_equipamento
                and jogo.progressao_controller.transicao is None):
            jogo.particulas.atualizar()
            jogo.cenario.atualizar()
            if jogo.estado is EstadoJogo.JOGANDO:
                jogo.avanco_controller.atualizar(jogo.cenario, PASSO_FIXO)
        self._atualizar_textos_e_mensagens()
        jogo.fade = max(0, jogo.fade - 18) if jogo.fade > 0 else jogo.fade
        jogo.flash = max(0, jogo.flash - 1) if jogo.flash > 0 else jogo.flash
        jogo.boss_intro = max(0, jogo.boss_intro - 1) if jogo.boss_intro > 0 else jogo.boss_intro

    def _atualizar_textos_e_mensagens(self) -> None:
        jogo = self.jogo
        textos_ativos = []
        for texto in jogo.textos_acao:
            texto.atualizar()
            if texto.ativo:
                textos_ativos.append(texto)
        jogo.textos_acao[:] = textos_ativos
        mensagens_vivas = []
        for mensagem in jogo.mensagens:
            mensagem.atualizar()
            if mensagem.viva:
                mensagens_vivas.append(mensagem)
        jogo.mensagens[:] = mensagens_vivas

    def simular(self, passos: int) -> None:
        """Executa passos fixos, incluindo o hitstop determinístico."""
        jogo = self.jogo
        for _ in range(passos):
            if jogo.hitstop > 0:
                jogo.hitstop -= 1
            else:
                self.atualizar()

    def tratar_eventos(self) -> bool:
        """Processa os eventos recebidos e informa se o jogo continua ativo."""
        jogo = self.jogo
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                jogo.menu.cancelar_confirmacao_resolucao()
                jogo._salvar_tudo()
                jogo.profile_service.flush()
                return False
            if jogo.estado is EstadoJogo.CUTSCENE:
                jogo.cutscene_controller.tratar_evento(evento)
                continue
            strategy = jogo.estrategia_modo
            if (jogo.estado in (EstadoJogo.JOGANDO, EstadoJogo.MELHORIA,
                                EstadoJogo.PAUSA, EstadoJogo.GAME_OVER)
                    and strategy is not None
                    and strategy.handle_event(jogo, evento)):
                continue
            if jogo.estado in ("MENU", "CONTINUAR", "LOJA", "RECORDES", "CONFIG"):
                if not jogo.menu.tratar_eventos(evento):
                    return False
                continue
            if evento.type != pygame.KEYDOWN:
                continue
            if jogo.estado is EstadoJogo.JOGANDO:
                tecla_pausar = jogo.controles.get("pausar", 0)
                if evento.key == pygame.K_F3:
                    jogo.debug_ativo = not jogo.debug_ativo
                elif evento.key == pygame.K_F8 and jogo.debug_ativo:
                    jogo.cutscene_controller.abrir_seletor_debug()
                elif jogo.progressao_controller.transicao is not None:
                    if evento.key in (pygame.K_p, pygame.K_ESCAPE, tecla_pausar):
                        jogo.estado = EstadoJogo.PAUSA
                    continue
                elif evento.key == pygame.K_TAB:
                    jogo.menu_equipamento = not jogo.menu_equipamento
                elif jogo.menu_equipamento:
                    jogo._tratar_menu_equipamento(evento)
                elif evento.key in (pygame.K_p, pygame.K_ESCAPE, tecla_pausar):
                    jogo.estado = EstadoJogo.PAUSA
                elif evento.key == pygame.K_e:
                    jogo._ativar_especial()
                elif pygame.K_1 <= evento.key <= pygame.K_9:
                    jogo.jogador.selecionar_arma(evento.key - pygame.K_1)
                    if jogo.profile_service.active:
                        jogo.profile_service.update_progress(
                            arma_equipada=jogo.jogador.arma_atual)
            elif jogo.estado is EstadoJogo.MELHORIA:
                if evento.key in (pygame.K_LEFT, pygame.K_a):
                    jogo.melhoria_selecionada = (jogo.melhoria_selecionada - 1) % 3
                elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                    jogo.melhoria_selecionada = (jogo.melhoria_selecionada + 1) % 3
                elif evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    jogo.progressao_controller.selecionar_melhoria(
                        jogo.melhoria_selecionada,
                    )
                elif pygame.K_1 <= evento.key <= pygame.K_3:
                    jogo.progressao_controller.selecionar_melhoria(
                        evento.key - pygame.K_1,
                    )
            elif jogo.estado is EstadoJogo.PAUSA:
                jogo.pausa_controller.tratar_evento(evento)
            elif jogo.estado is EstadoJogo.GAME_OVER:
                if evento.key == pygame.K_RETURN:
                    jogo._preparar_jogo()
                elif evento.key == pygame.K_ESCAPE:
                    jogo.estado = EstadoJogo.MENU
                    jogo.fade = 255
        return bool(jogo.rodando)

    def executar(self) -> None:
        """Mantem o loop ate o encerramento solicitado pelo usuario."""
        jogo = self.jogo
        simulacao = RelogioSimulacao()
        rodando = True
        while rodando:
            tempo_decorrido_ms = jogo.relogio.tick(FPS)
            rodando = self.tratar_eventos()
            if not rodando:
                break
            self.simular(simulacao.consumir(tempo_decorrido_ms))
            jogo.render_controller.desenhar()
            jogo.fps_atual = jogo.relogio.get_fps()
            jogo.tempo_quadro_ms = tempo_decorrido_ms
            jogo.metricas_quadro.registrar(tempo_decorrido_ms)
            jogo.p95_quadro_ms = jogo.metricas_quadro.p95_ms
            jogo.fps_1_baixo = jogo.metricas_quadro.fps_1_baixo
            jogo._atualizar_modo_desempenho(jogo.relogio.get_rawtime())
        pygame.mouse.set_visible(True)
        pygame.quit()
        sys.exit(0)
