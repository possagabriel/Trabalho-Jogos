"""Composicao da cena, HUD e overlays do jogo legado."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pygame

from src.core.constants import NEGRO, VOID_BLACK, EstadoJogo
from src.core.settings import escala_visual
from src.infrastructure.graphics.comic_theme import usar_visual

if TYPE_CHECKING:
    from src.runtime.application.core import Jogo


class ControladorRenderizacao:
    """Define a ordem de renderizacao sem concentrar regras de gameplay."""

    def __init__(self, jogo: Jogo) -> None:
        self.jogo = jogo
        self._cursor_visivel: bool | None = None
        self._preparar_sprites()

    def sincronizar_cursor(self) -> None:
        """Mostra o cursor SDL fora do combate com mira ativa."""
        jogo = self.jogo
        visivel = (jogo.estado is not EstadoJogo.JOGANDO
                   or jogo.menu_equipamento or not jogo.config["mira_ativa"])
        if visivel != self._cursor_visivel:
            pygame.mouse.set_visible(visivel)
            self._cursor_visivel = visivel

    def _preparar_sprites(self) -> None:
        from src.infrastructure.graphics.comic_pipeline import preparar_rotacoes
        from src.runtime.domain.entities.player import _sprite_padrao

        sprite = _sprite_padrao()
        if sprite is not None:
            for hachuras in (False, True):
                for variacao in (0, 1):
                    preparar_rotacoes(sprite, hachuras, variacao)

    def desenhar_hud(self) -> None:
        """Desenha o HUD na superficie logica de jogo."""
        self.jogo.hud.desenhar(self.jogo.tela, self.jogo)

    def _desenhar_campo(self) -> None:
        """Mostra o combate ou a animação dimensional, com HUD quando aplicável."""
        jogo = self.jogo
        if jogo.progressao_controller.transicao is not None:
            jogo.progressao_controller.frame_transicao()
        else:
            jogo._desenhar_jogo()
            self.desenhar_hud()

    def aplicar_shake(self) -> None:
        """Aplica o deslocamento visual acumulado pelo feedback de combate."""
        jogo = self.jogo
        if jogo.trauma <= 0:
            return
        escala = escala_visual(jogo.config["intensidade_tremor"])
        magnitude = jogo.trauma ** 2 * 16 * escala
        if magnitude == 0:
            jogo.trauma = max(0.0, jogo.trauma - 0.035)
            return
        deslocamento = (random.uniform(-magnitude, magnitude),
                        random.uniform(-magnitude, magnitude))
        jogo._tela_shake.fill(NEGRO)
        jogo._tela_shake.blit(jogo.tela, (int(deslocamento[0]), int(deslocamento[1])))
        jogo.tela.blit(jogo._tela_shake, (0, 0))
        jogo.trauma = max(0.0, jogo.trauma - 0.035)

    def desenhar(self) -> None:
        """Compoe a tela conforme o estado ativo e apresenta o quadro."""
        with usar_visual(self.jogo.config):
            self._compor()

    def _compor(self) -> None:
        jogo = self.jogo
        self.sincronizar_cursor()
        if jogo.estado in ("MENU", "CONTINUAR", "LOJA", "RECORDES", "CONFIG"):
            jogo.tela.fill(VOID_BLACK)
            jogo.menu.desenhar(jogo.tela)
        elif jogo.estado is EstadoJogo.PREPARANDO:
            jogo._desenhar_carregando()
        elif jogo.estado is EstadoJogo.JOGANDO:
            self._desenhar_campo()
        elif jogo.estado is EstadoJogo.MELHORIA:
            jogo._desenhar_jogo()
            self.desenhar_hud()
            jogo.tela_melhorias.desenhar(jogo.tela, jogo)
        elif jogo.estado is EstadoJogo.PAUSA:
            self._desenhar_campo()
            jogo._desenhar_pausa()
        elif jogo.estado is EstadoJogo.GAME_OVER:
            jogo._desenhar_jogo()
            self.desenhar_hud()
            jogo._desenhar_game_over()
        self._desenhar_overlays_logicos()
        self.aplicar_shake()
        self._desenhar_mira_e_debug()
        jogo._apresentar()
        pygame.display.flip()

    def _desenhar_mira_e_debug(self) -> None:
        """Mantém a mira presa ao mouse mesmo quando a câmera treme."""
        jogo = self.jogo
        if jogo.estado is not EstadoJogo.JOGANDO:
            return
        posicao = jogo.posicao_mira()
        if posicao is not None:
            jogo.mira.desenhar(
                jogo.tela, posicao, jogo.cenario.cor_transicao,
                jogo.mira_sobre_inimigo(posicao),
            )
        if jogo.debug_ativo:
            jogo.overlay_debug.desenhar(jogo.tela, jogo, posicao)

    def _desenhar_overlays_logicos(self) -> None:
        jogo = self.jogo
        if jogo.flash > 0:
            escala = escala_visual(jogo.config["intensidade_flash"])
            if escala:
                jogo._tela_flash.fill((255, 0, 0, int(jogo.flash * 15 * escala)))
                jogo.tela.blit(jogo._tela_flash, (0, 0))
        if jogo.fade > 0:
            jogo._tela_fade.fill(NEGRO)
            jogo._tela_fade.set_alpha(jogo.fade)
            jogo.tela.blit(jogo._tela_fade, (0, 0))
