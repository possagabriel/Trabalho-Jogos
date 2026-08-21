"""Label component with optional glow / shadow for HUD and menus.

Migrated from game/smooth.py texto_suave and texto_espacado.
"""

from __future__ import annotations

from typing import Optional

import pygame

from src.core.constants import BRANCO


class Label:
    """Single-line text renderer with optional glow and shadow.

    Args:
        text: String to render.
        position: ``(x, y)`` anchor position.
        color: Text colour (defaults to white).
        size: Font size in pixels.
        glow_color: Optional glow / shadow colour (applied behind text).
        glow_radius: Blur radius for the glow effect.
        bold: Use bold font.
        align: Horizontal alignment (``"left"``, ``"center"``, ``"right"``).
    """

    def __init__(
        self,
        text: str = "",
        position: tuple[int, int] = (0, 0),
        color: tuple[int, int, int] = BRANCO,
        size: int = 22,
        glow_color: Optional[tuple[int, int, int]] = None,
        glow_radius: int = 3,
        bold: bool = False,
        align: str = "center",
    ) -> None:
        self.text = text
        self.position = position
        self.color = color
        self.size = size
        self.glow_color = glow_color
        self.glow_radius = glow_radius
        self.bold = bold
        self.align = align
        self._font: Optional[pygame.font.Font] = None
        self._cache_key: str = ""
        self._cache_surface: Optional[pygame.Surface] = None

    # ------------------------------------------------------------------
    # Font
    # ------------------------------------------------------------------

    @property
    def font(self) -> pygame.font.Font:
        if self._font is None:
            self._font = pygame.font.SysFont(
                "monospace", self.size, bold=self.bold,
            )
        return self._font

    def set_text(self, text: str) -> None:
        """Update text and invalidate cache."""
        if text != self.text:
            self.text = text
            self._cache_surface = None

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, surface: pygame.Surface) -> None:
        """Draw the label onto *surface*."""
        if not self.text:
            return
        key = (self.text, self.color, self.size, self.bold)
        if self._cache_surface is None or key != self._cache_key:
            self._cache_surface = self.font.render(self.text, True, self.color)
            self._cache_key = key

        surf = self._cache_surface
        x, y = self.position

        if self.align == "center":
            rect = surf.get_rect(center=(x, y))
        elif self.align == "right":
            rect = surf.get_rect(topright=(x, y))
        else:
            rect = surf.get_rect(topleft=(x, y))

        # glow / shadow
        if self.glow_color is not None and self.glow_radius > 0:
            shadow = self.font.render(self.text, True, self.glow_color)
            for dx in range(-self.glow_radius, self.glow_radius + 1):
                for dy in range(-self.glow_radius, self.glow_radius + 1):
                    if dx * dx + dy * dy <= self.glow_radius * self.glow_radius:
                        surface.blit(shadow, (rect.x + dx, rect.y + dy))

        surface.blit(surf, rect)

    def get_rect(self) -> pygame.Rect:
        """Return the bounding rect of the rendered text."""
        surf = self.font.render(self.text, True, self.color)
        if self.align == "center":
            return surf.get_rect(center=self.position)
        if self.align == "right":
            return surf.get_rect(topright=self.position)
        return surf.get_rect(topleft=self.position)
