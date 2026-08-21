"""Game over screen — statistics, records, and retry prompt.

Migrated from game/core.py _desenhar_game_over.
"""

from __future__ import annotations

import math
from typing import Any

import pygame

from src.core.constants import (
    ALTURA, BRANCO, DOURADO, LARGURA, RIFT_MAGENTA, VERDE,
)


class GameOverScreen:
    """Displays mission statistics, top records, and navigation hints."""

    def __init__(self) -> None:
        self._tela_sombra = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)

    def render(self, surface: pygame.Surface, game: Any,
               tema: dict) -> None:
        """Draw the game-over overlay."""
        self._tela_sombra.fill((0, 0, 0, 185))
        surface.blit(self._tela_sombra, (0, 0))

        t = pygame.time.get_ticks() * 0.001
        f_title = pygame.font.SysFont("monospace", 48, bold=True)
        f_sub = pygame.font.SysFont("monospace", 24, bold=True)
        f_med = pygame.font.SysFont("monospace", 22)
        f_sm = pygame.font.SysFont("monospace", 18)

        # titulo
        ts = f_title.render("RIFT COLLAPSED", True, RIFT_MAGENTA)
        surface.blit(ts, ts.get_rect(center=(LARGURA // 2, 84)))

        # painel
        pw, ph = 500, 300
        painel = pygame.Rect(LARGURA // 2 - pw // 2, 140, pw, ph)
        bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(bg, (10, 10, 26, 225),
                         (0, 0, pw, ph), border_radius=16)
        surface.blit(bg, painel.topleft)
        pygame.draw.rect(surface, tema["secundaria"], painel, 2,
                         border_radius=16)

        header = f_sub.render("ESTATISTICAS DA MISSAO", True,
                              tema["primaria"])
        surface.blit(header, header.get_rect(center=(LARGURA // 2,
                                                      painel.y + 24)))

        stats = [
            ("Pontuacao", f"{game.jogador.pontuacao} pts"),
            ("Nivel", str(game.jogador.nivel)),
            ("Bosses Derrotados", str(game.bosses_abates)),
            ("Moedas Ganhas", f"+{game.moedas_ganhas}"),
            ("Inimigos Mortos", str(game.inimigos_abates)),
            ("Combo Maximo", f"{game.jogador.combo.combo_maximo}x"),
            ("Tempo de Jogo", self._fmt(game.tempo_partida)),
        ]
        y = painel.y + 56
        for rotulo, valor in stats:
            rl = f_med.render(rotulo, True, (185, 190, 225))
            surface.blit(rl, (painel.x + 36, y))
            vl = f_med.render(valor, True, BRANCO)
            surface.blit(vl, vl.get_rect(topright=(painel.right - 36, y)))
            y += 36

        # novo recorde
        if game.novo_recorde:
            pulso = 0.7 + 0.3 * math.sin(t * 6)
            cor = tuple(int(c * pulso) for c in DOURADO)
            nr = f_sub.render("NOVO RECORDE!", True, cor)
            surface.blit(nr, nr.get_rect(center=(LARGURA // 2, 452)))

        # top 5
        top_l = f_sub.render("TOP 5", True, tema["terciaria"])
        surface.blit(top_l, top_l.get_rect(center=(LARGURA // 2, 504)))
        y = 534
        for i, reg in enumerate(game.recordes[:5]):
            cor = DOURADO if i == 0 else BRANCO if i < 3 else (150, 150, 170)
            linha = (f"{i+1}. {reg['nome']} - {reg['pontos']} pts "
                     f"(Nivel {reg['nivel']}, {reg['skin']})")
            s = f_med.render(linha, True, cor)
            surface.blit(s, s.get_rect(center=(LARGURA // 2, y)))
            y += 24

        # hints
        hint = f_med.render(
            "ENTER: jogar de novo   ESC: menu", True, VERDE)
        surface.blit(hint, hint.get_rect(center=(LARGURA // 2,
                                                  ALTURA - 50)))

    @staticmethod
    def _fmt(segundos: float) -> str:
        m, s = divmod(int(segundos), 60)
        return f"{m:02d}:{s:02d}"
