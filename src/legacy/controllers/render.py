"""Composicao da cena, HUD e overlays do jogo legado."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pygame

from src.core.constants import EstadoJogo, NEGRO, VOID_BLACK

if TYPE_CHECKING:
    from src.legacy.application.core import Jogo


class ControladorRenderizacao:
    """Define a ordem de renderizacao sem concentrar regras de gameplay."""

    def __init__(self, jogo: Jogo) -> None:
        self.jogo = jogo

    def desenhar_hud(self) -> None:
        """Desenha o HUD na superficie logica de jogo."""
        self.jogo.hud.desenhar(self.jogo.tela, self.jogo)

    def aplicar_shake(self) -> None:
        """Aplica o deslocamento visual acumulado pelo feedback de combate."""
        jogo = self.jogo
        if jogo.trauma <= 0:
            return
        magnitude = jogo.trauma ** 2 * 16
        deslocamento = (random.uniform(-magnitude, magnitude),
                        random.uniform(-magnitude, magnitude))
        jogo._tela_shake.fill(NEGRO)
        jogo._tela_shake.blit(jogo.tela, (int(deslocamento[0]), int(deslocamento[1])))
        jogo.tela.blit(jogo._tela_shake, (0, 0))
        jogo.trauma = max(0.0, jogo.trauma - 0.035)

    def desenhar(self) -> None:
        """Compoe a tela conforme o estado ativo e apresenta o quadro."""
        jogo = self.jogo
        if jogo.estado in ("MENU", "CONTINUAR", "LOJA", "RECORDES", "CONFIG"):
            jogo.tela_ui.fill(VOID_BLACK)
            jogo.menu.desenhar(jogo.tela_ui)
            jogo.janela.blit(jogo.tela_ui, (0, 0))
            self._desenhar_overlays_janela()
            pygame.display.flip()
            return
        if jogo.estado is EstadoJogo.PREPARANDO:
            jogo._desenhar_carregando()
        elif jogo.estado is EstadoJogo.JOGANDO:
            jogo._desenhar_jogo()
        elif jogo.estado is EstadoJogo.PAUSA:
            jogo._desenhar_jogo()
            self.desenhar_hud()
            jogo._desenhar_pausa()
        elif jogo.estado is EstadoJogo.GAME_OVER:
            jogo._desenhar_jogo()
            self.desenhar_hud()
            jogo._desenhar_game_over()
        self._desenhar_overlays_logicos()
        self.aplicar_shake()
        jogo._apresentar()
        if jogo.estado is EstadoJogo.JOGANDO:
            jogo.hud.desenhar(jogo.janela, jogo)
        pygame.display.flip()

    def _desenhar_overlays_janela(self) -> None:
        jogo = self.jogo
        if jogo.flash > 0:
            jogo._janela_flash.fill((255, 0, 0, jogo.flash * 18))
            jogo.janela.blit(jogo._janela_flash, (0, 0))
        if jogo.fade > 0:
            jogo._janela_fade.fill(NEGRO)
            jogo._janela_fade.set_alpha(jogo.fade)
            jogo.janela.blit(jogo._janela_fade, (0, 0))

    def _desenhar_overlays_logicos(self) -> None:
        jogo = self.jogo
        if jogo.flash > 0:
            jogo._tela_flash.fill((255, 0, 0, jogo.flash * 15))
            jogo.tela.blit(jogo._tela_flash, (0, 0))
        if jogo.fade > 0:
            jogo._tela_fade.fill(NEGRO)
            jogo._tela_fade.set_alpha(jogo.fade)
            jogo.tela.blit(jogo._tela_fade, (0, 0))
