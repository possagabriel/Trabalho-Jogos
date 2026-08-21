"""Panel component with cartoon-style thick border, rounded corners and glow.

Migrated from game/smooth.py painel_glass / desenhar_painel_cartoon.
"""

from __future__ import annotations

import pygame


class Panel:
    """Styled panel container with optional glow and alpha.

    Args:
        rect: Position and size as ``pygame.Rect`` or tuple ``(x, y, w, h)``.
        color: Border / accent colour.
        bg_color: Fill colour (defaults to near-black).
        corner_radius: Radius of rounded corners.
        border_width: Thickness of the cartoon border.
        alpha: Background alpha (0-255).
        glow_radius: Outer glow radius in pixels (0 to disable).
    """

    def __init__(
        self,
        rect: pygame.Rect | tuple[int, int, int, int],
        color: tuple[int, int, int] = (255, 23, 107),
        bg_color: tuple[int, int, int] = (10, 10, 26),
        corner_radius: int = 16,
        border_width: int = 5,
        alpha: int = 240,
        glow_radius: int = 0,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.color = color
        self.bg_color = bg_color
        self.corner_radius = corner_radius
        self.border_width = border_width
        self.alpha = alpha
        self.glow_radius = glow_radius

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, surface: pygame.Surface) -> None:
        """Draw the panel on *surface*."""
        r = self.rect
        # glow
        if self.glow_radius > 0:
            glow_surf = pygame.Surface(
                (r.w + self.glow_radius * 2, r.h + self.glow_radius * 2),
                pygame.SRCALPHA,
            )
            pygame.draw.rect(
                glow_surf,
                self.color + (40,),
                (
                    0,
                    0,
                    r.w + self.glow_radius * 2,
                    r.h + self.glow_radius * 2,
                ),
                border_radius=self.corner_radius + self.glow_radius,
            )
            surface.blit(
                glow_surf,
                (r.x - self.glow_radius, r.y - self.glow_radius),
            )

        # background fill
        bg = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        pygame.draw.rect(
            bg,
            self.bg_color + (self.alpha,),
            (0, 0, r.w, r.h),
            border_radius=self.corner_radius,
        )
        surface.blit(bg, r.topleft)

        # cartoon border
        pygame.draw.rect(
            surface, self.color, r, self.border_width,
            border_radius=self.corner_radius,
        )

    def contains(self, point: tuple[int, int]) -> bool:
        """Check if *point* is inside the panel."""
        return self.rect.collidepoint(point)
