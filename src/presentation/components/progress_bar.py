"""Progress bar component with glow, smooth fill, and percentage label.

Migrated from game/smooth.py retangulo_suave and desenhar_barra.
"""

from __future__ import annotations

from typing import Optional

import pygame

from src.core.constants import BRANCO


class ProgressBar:
    """Horizontal progress bar with rounded ends and optional glow.

    Args:
        rect: Position and size as ``pygame.Rect`` or ``(x, y, w, h)``.
        value: Current value (0.0 – 1.0).
        fill_color: Colour of the filled portion.
        bg_color: Colour of the empty track.
        border_color: Outline colour.
        border_width: Width of the outline stroke.
        corner_radius: Radius of rounded ends.
        glow_color: Optional glow colour drawn behind the fill.
        glow_radius: Glow spread in pixels.
        show_percent: If ``True``, render percentage text inside.
    """

    def __init__(
        self,
        rect: pygame.Rect | tuple[int, int, int, int],
        value: float = 0.0,
        fill_color: tuple[int, int, int] = (25, 217, 255),
        bg_color: tuple[int, int, int] = (40, 40, 70),
        border_color: tuple[int, int, int] = BRANCO,
        border_width: int = 1,
        corner_radius: int = 6,
        glow_color: Optional[tuple[int, int, int]] = None,
        glow_radius: int = 8,
        show_percent: bool = False,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.value = max(0.0, min(1.0, value))
        self.fill_color = fill_color
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_width = border_width
        self.corner_radius = corner_radius
        self.glow_color = glow_color or fill_color
        self.glow_radius = glow_radius
        self.show_percent = show_percent
        self._font: Optional[pygame.font.Font] = None

    @property
    def font(self) -> pygame.font.Font:
        if self._font is None:
            self._font = pygame.font.SysFont("monospace", 14, bold=True)
        return self._font

    def set_value(self, value: float) -> None:
        """Clamp the progress to [0, 1]."""
        self.value = max(0.0, min(1.0, value))

    def render(self, surface: pygame.Surface) -> None:
        """Draw the progress bar."""
        r = self.rect
        cr = min(self.corner_radius, r.h // 2)

        # glow behind fill
        fill_w = max(0, int(r.w * self.value))
        if fill_w > 0 and self.glow_radius > 0:
            glow = pygame.Surface(
                (fill_w + self.glow_radius * 2, r.h + self.glow_radius * 2),
                pygame.SRCALPHA,
            )
            pygame.draw.rect(
                glow,
                self.glow_color + (45,),
                (
                    0,
                    0,
                    fill_w + self.glow_radius * 2,
                    r.h + self.glow_radius * 2,
                ),
                border_radius=cr + self.glow_radius,
            )
            surface.blit(
                glow, (r.x - self.glow_radius, r.y - self.glow_radius),
            )

        # background track
        bg = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        pygame.draw.rect(bg, self.bg_color + (255,), (0, 0, r.w, r.h),
                         border_radius=cr)
        surface.blit(bg, r.topleft)

        # filled portion
        if fill_w > 0:
            fill = pygame.Surface((fill_w, r.h), pygame.SRCALPHA)
            pygame.draw.rect(
                fill, self.fill_color + (255,),
                (0, 0, fill_w, r.h), border_radius=cr,
            )
            surface.blit(fill, r.topleft)

        # border
        pygame.draw.rect(
            surface, self.border_color, r, self.border_width,
            border_radius=cr,
        )

        # percentage label
        if self.show_percent:
            pct = f"{int(self.value * 100)}%"
            txt = self.font.render(pct, True, BRANCO)
            surface.blit(txt, txt.get_rect(center=r.center))
