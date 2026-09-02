"""Game screen — coordinates gameplay rendering during active play.

This screen renders the scenario, player, enemies, projectiles, particles,
HUD, and manages the in-game overlays (boss intro, vignette, flash).
"""

from __future__ import annotations

import math
import random
from typing import Any

import pygame

from src.core.constants import (
    ALTURA, BRANCO, CIANO, DIMENSION_GOLD, DOURADO, LARGURA, NEGRO,
    QUANTUM_CYAN, RIFT_MAGENTA, VERDE,
)


class GameScreen:
    """Renders the active gameplay state.

    This is a thin rendering coordinator.  The actual game logic
    (spawning, collision, scoring) lives in the domain / core layers.
    """

    def __init__(self) -> None:
        self._tela_sombra = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        self._tela_flash = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        self._tela_fade = pygame.Surface((LARGURA, ALTURA))

    # ------------------------------------------------------------------
    # Fonts (lazy)
    # ------------------------------------------------------------------

    def _font(self, size: int, bold: bool = False) -> pygame.font.Font:
        return pygame.font.SysFont("monospace", size, bold=bold)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render_jogo(self, surface: pygame.Surface, game: Any) -> None:
        """Draw the full game scene: scenario, entities, HUD."""
        game.cenario.desenhar(surface)
        for powerup in game.powerups:
            powerup.desenhar(surface)
        for inimigo in game.inimigos:
            inimigo.desenhar(surface)
        if game.boss:
            game.boss.desenhar(surface)
        for proj in game.projeteis:
            proj.desenhar(surface)
        game.jogador.desenhar(surface, game.particulas)
        for mensagem in game.mensagens:
            mensagem.desenhar(surface)
        for texto in game.textos_acao:
            texto.desenhar(surface)
        game.particulas.desenhar(surface)

    def render_hud(self, surface: pygame.Surface, game: Any) -> None:
        """Draw the in-game HUD overlay."""
        game.hud.desenhar(surface, game)

    def render_boss_intro(self, surface: pygame.Surface, game: Any) -> None:
        """Overlay de apresentacao da entidade RIFT."""
        boss = game.boss
        alfa = max(0.0, min(1.0, game.boss_intro / 45.0))
        if alfa <= 0 or boss is None:
            return
        pw, ph = 460, 240
        x = LARGURA // 2 - pw // 2
        y = ALTURA // 2 - ph // 2
        painel = pygame.Rect(x, y, pw, ph)
        bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(bg, (16, 12, 6, int(215 * alfa)),
                         (0, 0, pw, ph), border_radius=12)
        surface.blit(bg, painel.topleft)
        pygame.draw.rect(surface, DIMENSION_GOLD, painel, 2,
                         border_radius=12)
        f = self._font
        self._draw(surface, "RIFT ENTITY DETECTED",
                   (LARGURA // 2, y + 30), DIMENSION_GOLD, f(24))
        self._draw(surface, f"ENTITY // {boss.nivel // 5:02d}",
                   (LARGURA // 2, y + 64), QUANTUM_CYAN, f(20))
        self._draw(surface, boss.nome, (LARGURA // 2, y + 102),
                   BRANCO, f(34, True))
        barra = pygame.Rect(x + 120, y + 172, pw - 240, 12)
        pygame.draw.rect(surface, (40, 40, 70), barra, border_radius=6)
        pygame.draw.rect(surface, DIMENSION_GOLD,
                         (barra.x, barra.y, int(barra.w * 0.8), barra.h),
                         border_radius=6)
        self._draw(surface, f"DIMENSION 0{boss.cenario_id}",
                   (LARGURA // 2, y + 206), boss.cor, f(18))

    def render_pausa(self, surface: pygame.Surface, game: Any,
                     tema: dict) -> None:
        """Render the pause menu overlay."""
        self._tela_sombra.fill((0, 0, 0, 210))
        surface.blit(self._tela_sombra, (0, 0))
        pw, ph = 440, 420
        painel = pygame.Rect(LARGURA // 2 - pw // 2, ALTURA // 2 - ph // 2,
                             pw, ph)
        bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(bg, (10, 10, 26, 248),
                         (0, 0, pw, ph), border_radius=28)
        surface.blit(bg, painel.topleft)
        pygame.draw.rect(surface, tema["primaria"], painel, 6,
                         border_radius=28)
        t = pygame.time.get_ticks() * 0.001
        ix, iy = LARGURA // 2, painel.y + 36
        for offset in (-16, 6):
            pygame.draw.rect(surface, tema["primaria"],
                             (ix + offset, iy - 14, 10, 28), border_radius=4)
        f = self._font
        self._draw(surface, "PAUSADO",
                   (LARGURA // 2, painel.y + 76), tema["primaria"],
                   f(38, True))
        for i, (sx, sy, sr) in enumerate([
            (painel.x + 24, painel.y + 24, 9),
            (painel.right - 24, painel.y + 24, 7),
            (painel.x + 20, painel.bottom - 24, 8),
            (painel.right - 20, painel.bottom - 24, 10),
        ]):
            cor_e = tema["secundaria"] if i % 2 == 0 else tema["terciaria"]
            pygame.draw.circle(surface, cor_e, (sx, sy), sr)
        opcoes = [
            ("CONTINUAR", (25, 150, 75)),
            ("CONFIGURACOES", (50, 90, 170)),
            ("SAIR DA MISSAO", (170, 50, 55)),
        ]
        btn_w, btn_h = 320, 54
        btn_x = LARGURA // 2 - btn_w // 2
        btn_y0 = painel.y + 118
        fb = f(24, True)
        for i, (texto, cor_f) in enumerate(opcoes):
            by = btn_y0 + i * 74
            rect = pygame.Rect(btn_x, by, btn_w, btn_h)
            bgb = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
            pygame.draw.rect(bgb, tuple(cor_f) + (200,),
                             (0, 0, btn_w, btn_h), border_radius=btn_h // 2)
            surface.blit(bgb, rect.topleft)
            pygame.draw.rect(surface, (0, 0, 0), rect, 2,
                             border_radius=btn_h // 2)
            txt = fb.render(texto, True, BRANCO)
            surface.blit(txt, txt.get_rect(center=rect.center))
        fi = f(18)
        info = (f"NIVEL {game.jogador.nivel}  |  "
                f"{game.jogador.pontuacao} PTS  |  "
                f"SKIN {game.jogador.skin}")
        isurf = fi.render(info, True, DOURADO)
        surface.blit(isurf, isurf.get_rect(
            center=(LARGURA // 2, painel.bottom - 80)))

    def render_game_over(self, surface: pygame.Surface, game: Any,
                         tema: dict) -> None:
        """Render the game-over overlay."""
        self._tela_sombra.fill((0, 0, 0, 185))
        surface.blit(self._tela_sombra, (0, 0))
        t = pygame.time.get_ticks() * 0.001
        f = self._font
        self._draw(surface, "RIFT COLLAPSED",
                   (LARGURA // 2, 84), RIFT_MAGENTA, f(48, True))
        pw, ph = 500, 300
        painel = pygame.Rect(LARGURA // 2 - pw // 2, 140, pw, ph)
        bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(bg, (10, 10, 26, 225),
                         (0, 0, pw, ph), border_radius=16)
        surface.blit(bg, painel.topleft)
        pygame.draw.rect(surface, tema["secundaria"], painel, 2,
                         border_radius=16)
        self._draw(surface, "ESTATISTICAS DA MISSAO",
                   (LARGURA // 2, painel.y + 24), tema["primaria"], f(20))
        stats = [
            ("Pontuacao", f"{game.jogador.pontuacao} pts"),
            ("Nivel", str(game.jogador.nivel)),
            ("Bosses Derrotados", str(game.bosses_abates)),
            ("Moedas Ganhas", f"+{game.moedas_ganhas}"),
            ("Inimigos Mortos", str(game.inimigos_abates)),
            ("Combo Maximo", f"{game.jogador.combo.combo_maximo}x"),
            ("Tempo de Jogo", self._formatar_tempo(game.tempo_partida)),
        ]
        y = painel.y + 56
        for rotulo, valor in stats:
            self._draw(surface, rotulo, (painel.x + 36, y),
                       (185, 190, 225), f(22), align="left")
            self._draw(surface, valor, (painel.right - 36, y),
                       BRANCO, f(22), align="right")
            y += 36
        if game.novo_recorde:
            pulso = 0.7 + 0.3 * math.sin(t * 6)
            cor_r = tuple(int(c * pulso) for c in DOURADO)
            self._draw(surface, "NOVO RECORDE!",
                       (LARGURA // 2, 452), cor_r, f(34, True))
        self._draw(surface, "ENTER: jogar de novo  ESC: menu",
                   (LARGURA // 2, ALTURA - 50), VERDE, f(22))

    def render_loading(self, surface: pygame.Surface, game: Any,
                       tema: dict) -> None:
        """Render the loading / preparation screen."""
        game.cenario.desenhar(surface)
        self._tela_sombra.fill((0, 0, 0, 175))
        surface.blit(self._tela_sombra, (0, 0))
        f = self._font
        self._draw(surface, "INCARNATE",
                   (LARGURA // 2, ALTURA // 2 - 130), RIFT_MAGENTA,
                   f(44, True))
        self._draw(surface, "DIMENSIONAL TRANSIT",
                   (LARGURA // 2, ALTURA // 2 - 92), QUANTUM_CYAN, f(22))
        painel = pygame.Rect(LARGURA // 2 - 250, ALTURA // 2 - 60, 500, 120)
        bg = pygame.Surface((500, 120), pygame.SRCALPHA)
        pygame.draw.rect(bg, (10, 10, 26, 200),
                         (0, 0, 500, 120), border_radius=14)
        surface.blit(bg, painel.topleft)
        pygame.draw.rect(surface, tema["primaria"], painel, 2,
                         border_radius=14)
        self._draw(surface, "CALIBRATING RIFT...",
                   (LARGURA // 2, ALTURA // 2 - 44), (200, 205, 235), f(18))
        barra = pygame.Rect(LARGURA // 2 - 210, ALTURA // 2 - 26, 420, 28)
        pygame.draw.rect(surface, (40, 40, 70), barra, border_radius=8)
        preenchido = int(420 * max(0.0, min(1.0, game.carregamento / 100)))
        pygame.draw.rect(surface, tema["primaria"],
                         (barra.x, barra.y, preenchido, 28), border_radius=8)
        pygame.draw.rect(surface, BRANCO, barra, 2, border_radius=8)
        self._draw(surface, f"{int(game.carregamento)}%",
                   (LARGURA // 2, ALTURA // 2 + 12), BRANCO, f(22))
        self._draw(surface,
                   f"RIFT STABILITY  {game.carregamento * 0.8742:.2f}%",
                   (LARGURA // 2, ALTURA // 2 + 46), QUANTUM_CYAN, f(18))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _draw(surface: pygame.Surface, text: str,
              pos: tuple[int, int], color: tuple, font: pygame.font.Font,
              align: str = "center") -> pygame.Rect:
        surf = font.render(text, True, color)
        if align == "center":
            rect = surf.get_rect(center=pos)
        elif align == "right":
            rect = surf.get_rect(topright=pos)
        else:
            rect = surf.get_rect(topleft=pos)
        surface.blit(surf, rect)
        return rect

    @staticmethod
    def _formatar_tempo(segundos: float) -> str:
        m, s = divmod(int(segundos), 60)
        return f"{m:02d}:{s:02d}"
