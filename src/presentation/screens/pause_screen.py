"""Pause screen — interactive pause menu with settings sub-panel.

Migrated from game/core.py _desenhar_pausa* and _tratar_eventos_pausa*.
"""

from __future__ import annotations

import math
from typing import Any

import pygame

from src.core.constants import BRANCO, CIANO, LARGURA, ALTURA, VERDE
from src.core.settings import TEMAS


class PauseScreen:
    """Interactive pause menu with continue, settings, and exit options."""

    def __init__(self) -> None:
        self.selecao: int = 0
        self.mostrando_config: bool = False
        self.config_selecao: int = 0
        self.dialogo: Any = None
        self.mouse_pos: tuple[int, int] = (0, 0)

    def handle_event(self, evento: pygame.event.Event,
                     game: Any) -> str | None:
        """Process a pygame event. Returns action string or None."""
        if self.dialogo and self.dialogo.ativo:
            self.dialogo.tratar_evento(evento, mouse_pos=self.mouse_pos)
            if not self.dialogo.ativo:
                self.dialogo = None
            return None

        if self.mostrando_config:
            return self._handle_config_event(evento, game)

        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_p, pygame.K_ESCAPE):
                return "resume"
            elif evento.key == pygame.K_UP:
                self.selecao = (self.selecao - 1) % 3
            elif evento.key == pygame.K_DOWN:
                self.selecao = (self.selecao + 1) % 3
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return self._acao(game)
        elif evento.type == pygame.MOUSEMOTION:
            self.mouse_pos = evento.pos
            idx = self._colidir(evento.pos)
            if idx is not None:
                self.selecao = idx
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            idx = self._colidir(evento.pos)
            if idx is not None:
                self.selecao = idx
                return self._acao(game)
        return None

    def _acao(self, game: Any) -> str:
        if self.selecao == 0:
            return "resume"
        if self.selecao == 1:
            self.mostrando_config = True
            self.config_selecao = 0
            return None
        return "exit_menu"

    def _colidir(self, pos: tuple[int, int]) -> int | None:
        pw, ph = 440, 420
        painel = pygame.Rect(LARGURA // 2 - pw // 2, ALTURA // 2 - ph // 2,
                             pw, ph)
        btn_w, btn_h = 320, 54
        btn_x = LARGURA // 2 - btn_w // 2
        btn_y0 = painel.y + 118
        for i in range(3):
            by = btn_y0 + i * 74
            rect = pygame.Rect(btn_x, by, btn_w, btn_h)
            if rect.collidepoint(pos):
                return i
        return None

    def _handle_config_event(self, evento: pygame.event.Event,
                             game: Any) -> str | None:
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                self.mostrando_config = False
            elif evento.key == pygame.K_UP:
                self.config_selecao = (self.config_selecao - 1) % 4
            elif evento.key == pygame.K_DOWN:
                self.config_selecao = (self.config_selecao + 1) % 4
            elif evento.key in (pygame.K_LEFT, pygame.K_RIGHT):
                delta = 1 if evento.key == pygame.K_RIGHT else -1
                self._ajustar(game, self.config_selecao, delta)
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self._clique_config(evento.pos, game)
        return None

    def _ajustar(self, game: Any, indice: int, delta: int) -> None:
        cfg = game.config
        if indice == 0:
            v = max(0.0, min(1.0, cfg["musica_volume"] + delta * 0.05))
            cfg["musica_volume"] = round(v, 2)
            game.sons.set_volume_musica(v)
        elif indice == 1:
            v = max(0.0, min(1.0, cfg["efeitos_volume"] + delta * 0.05))
            cfg["efeitos_volume"] = round(v, 2)
            game.sons.set_volume_efeitos(v)
        elif indice == 2:
            idx = TEMAS.index(cfg["tema"]) if cfg["tema"] in TEMAS else 0
            cfg["tema"] = TEMAS[(idx + delta) % len(TEMAS)]
        elif indice == 3 and delta > 0:
            cfg["tela_cheia"] = not cfg["tela_cheia"]
            game._aplicar_modo_video()
        cfg.salvar()

    def _clique_config(self, pos: tuple[int, int], game: Any) -> None:
        pw, ph = 540, 430
        painel = pygame.Rect(LARGURA // 2 - pw // 2, ALTURA // 2 - ph // 2,
                             pw, ph)
        btn_h = 44
        y0 = painel.y + 76
        espaco = 70
        for i in range(4):
            by = y0 + i * espaco
            linha = pygame.Rect(painel.x + 24, by - 6, pw - 48, btn_h)
            if linha.collidepoint(pos):
                self.config_selecao = i
                self._ajustar(game, i, 1)
                return
        b_voltar = pygame.Rect(painel.x + 30, painel.bottom - 56, 150, 42)
        if b_voltar.collidepoint(pos):
            self.mostrando_config = False
