"""MainRenderer: window management, scale-to-fit presentation, screen shake.

Migrated from game/core.py (_apresentar, _escala_janela, _aplicar_shake) and
game/settings.py video configuration. Provides the complete presentation
pipeline for the logical 900x700 surface to any window size.
"""

import random
from typing import Tuple

import pygame

from src.infrastructure.graphics.smooth_rendering import (
    limpar_cache as limpar_cache_suave,
)

# Logical (design) resolution -- the entire game draws on this canvas.
LARGURA_LOGICA = 900
ALTURA_LOGICA = 700

# Safe-area line colour used in letterbox mode.
_COR_SAFE = (32, 28, 48)


class MainRenderer:
    """Central renderer responsible for window setup, presentation and effects.

    The renderer owns the internal logical surface (900x700) and blits it to
    the actual window using *scale-to-fit* with optional manual adjustments.
    Screen-shake is applied by offsetting the blit origin each frame.
    """

    def __init__(self, titulo: str = "INCARNATE - Enter the Rift",
                 icone: "pygame.Surface | None" = None,
                 resolucao: str = "900x700",
                 tela_cheia: bool = False):
        pygame.init()

        self.titulo = titulo
        self._resolucao = resolucao
        self._tela_cheia = tela_cheia

        # Internal logical surface (the game always draws here).
        self.tela: pygame.Surface = pygame.Surface(
            (LARGURA_LOGICA, ALTURA_LOGICA))

        # Actual display window.
        self.janela: pygame.Surface = self._criar_janela()

        pygame.display.set_caption(titulo)
        if icone is not None:
            pygame.display.set_icon(icone)

        self.relogio: pygame.time.Clock = pygame.time.Clock()

        # Screen-shake state (trauma-based).
        self.trauma: float = 0.0
        self._tela_shake: pygame.Surface = pygame.Surface(
            (LARGURA_LOGICA, ALTURA_LOGICA))

    # ------------------------------------------------------------------
    # Window management
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_resolucao(texto: str) -> Tuple[int, int]:
        """Convert ``'1280x720'`` to ``(1280, 720)``."""
        try:
            larg, alt = texto.lower().split("x")
            return int(larg), int(alt)
        except (ValueError, AttributeError):
            return LARGURA_LOGICA, ALTURA_LOGICA

    def _criar_janela(self) -> pygame.Surface:
        """Create the display window (fullscreen or windowed)."""
        if self._tela_cheia:
            try:
                w, h = pygame.display.get_desktop_sizes()[0]
            except (IndexError, pygame.error):
                w, h = self._parse_resolucao(self._resolucao)
            return pygame.display.set_mode((w, h), pygame.FULLSCREEN)
        return pygame.display.set_mode(
            self._parse_resolucao(self._resolucao))

    def reconfigurar(self, resolucao: str, tela_cheia: bool) -> None:
        """Recreate the window with new video settings."""
        self._resolucao = resolucao
        self._tela_cheia = tela_cheia
        self.janela = self._criar_janela()
        pygame.display.set_caption(self.titulo)

    # ------------------------------------------------------------------
    # Scale-to-fit
    # ------------------------------------------------------------------

    def escala_janela(self) -> Tuple[float, float, float]:
        """Compute uniform scale and offsets for letterbox presentation.

        Returns ``(scale, offset_x, offset_y)`` that fit the logical canvas
        (``LARGURA_LOGICA x ALTURA_LOGICA``) into the current window while
        preserving aspect ratio.
        """
        w, h = self.janela.get_size()
        escala = min(w / LARGURA_LOGICA, h / ALTURA_LOGICA)
        off_x = (w - LARGURA_LOGICA * escala) / 2
        off_y = (h - ALTURA_LOGICA * escala) / 2
        return escala, off_x, off_y

    def transformacao_janela(self,
                             ajuste_escala: float = 1.0,
                             ajuste_off_x: int = 0,
                             ajuste_off_y: int = 0,
                             aspecto: str = "AJUSTAR",
                             ) -> Tuple[float, float, float]:
        """Apply manual user adjustments on top of scale-to-fit.

        ``aspecto`` may be ``"AJUSTAR"`` (letterbox) or ``"PREENCHE"``
        (stretch to fill window).
        """
        if aspecto == "PREENCHE":
            return (ajuste_escala, ajuste_off_x, ajuste_off_y)
        escala, off_x, off_y = self.escala_janela()
        escala *= max(0.5, ajuste_escala)
        off_x += ajuste_off_x
        off_y += ajuste_off_y
        return escala, off_x, off_y

    # ------------------------------------------------------------------
    # Presentation
    # ------------------------------------------------------------------

    def apresentar(self,
                   ajuste_escala: float = 1.0,
                   ajuste_off_x: int = 0,
                   ajuste_off_y: int = 0,
                   aspecto: str = "AJUSTAR",
                   cor_fundo: Tuple[int, int, int] = (8, 8, 13)) -> None:
        """Scale the logical surface to the window and flip.

        In ``AJUSTAR`` mode the aspect ratio is preserved with letterbox
        safe-area lines.  In ``PREENCHE`` mode the canvas is stretched.
        """
        w, h = self.janela.get_size()
        if (w, h) == (LARGURA_LOGICA, ALTURA_LOGICA):
            self.janela.blit(self.tela, (0, 0))
            pygame.display.flip()
            return

        if aspecto == "PREENCHE":
            escala = max(0.5, ajuste_escala)
            superficie = pygame.transform.smoothscale(
                self.tela,
                (max(1, int(w * escala)), max(1, int(h * escala))))
            self.janela.fill(cor_fundo)
            self.janela.blit(superficie, (int(ajuste_off_x),
                                          int(ajuste_off_y)))
            pygame.display.flip()
            return

        escala, off_x, off_y = self.transformacao_janela(
            ajuste_escala, ajuste_off_x, ajuste_off_y, aspecto)
        superficie = pygame.transform.smoothscale(
            self.tela,
            (max(1, int(LARGURA_LOGICA * escala)),
             max(1, int(ALTURA_LOGICA * escala))))
        self.janela.fill(cor_fundo)
        self.janela.blit(superficie, (int(off_x), int(off_y)))
        # Safe-area lines (letterbox guides)
        pygame.draw.aaline(
            self.janela, _COR_SAFE,
            (int(off_x), int(off_y)),
            (int(off_x + LARGURA_LOGICA * escala), int(off_y)))
        pygame.draw.aaline(
            self.janela, _COR_SAFE,
            (int(off_x), int(off_y + ALTURA_LOGICA * escala)),
            (int(off_x + LARGURA_LOGICA * escala),
             int(off_y + ALTURA_LOGICA * escala)))
        pygame.display.flip()

    # ------------------------------------------------------------------
    # Screen shake
    # ------------------------------------------------------------------

    def adicionar_trauma(self, quantidade: float) -> None:
        """Add shake intensity (0..1), decays every frame."""
        self.trauma = min(1.0, self.trauma + quantidade)

    def aplicar_shake(self) -> None:
        """Offset the logical surface according to remaining trauma.

        Call *after* all game drawing is done and *before* ``apresentar()``.
        """
        if self.trauma <= 0:
            return
        mag = self.trauma ** 2 * 16
        off_x = random.uniform(-mag, mag)
        off_y = random.uniform(-mag, mag)
        self._tela_shake.fill((0, 0, 0))
        self._tela_shake.blit(self.tela, (int(off_x), int(off_y)))
        self.tela.blit(self._tela_shake, (0, 0))
        self.trauma = max(0.0, self.trauma - 0.035)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def limpar_cache(self) -> None:
        """Flush all rendering caches (call on resolution change)."""
        limpar_cache_suave()

    def destruir(self) -> None:
        """Release resources."""
        limpar_cache_suave()
        pygame.quit()
