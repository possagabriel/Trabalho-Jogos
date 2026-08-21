"""Reusable button component with neon glow and hover effects.

Migrated from game/ui.py BotaoNeon and game/smooth.py drawing helpers.
"""

from __future__ import annotations

from typing import Optional

import pygame

from src.core.constants import BRANCO


class Button:
    """Neon-styled button with hover glow, pressed state, and rounded rect.

    Args:
        text: Label rendered on the button.
        rect: Position and size as ``pygame.Rect`` or tuple ``(x, y, w, h)``.
        color: Primary accent colour for borders and glow.
        on_click: Optional callback invoked when the button is activated.
    """

    def __init__(
        self,
        text: str,
        rect: pygame.Rect | tuple[int, int, int, int],
        color: tuple[int, int, int] = (255, 23, 107),
        on_click: Optional[callable] = None,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color
        self.on_click = on_click
        self.hover: bool = False
        self.pressed: bool = False
        self._font: Optional[pygame.font.Font] = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def font(self) -> pygame.font.Font:
        """Lazy-loaded font sized to button height."""
        if self._font is None:
            size = max(12, self.rect.height // 3)
            self._font = pygame.font.SysFont("monospace", size, bold=True)
        return self._font

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------

    def update(self, mouse_pos: tuple[int, int]) -> None:
        """Update hover state based on *mouse_pos*."""
        self.hover = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Process a single event. Returns ``True`` if the button was clicked."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
                if self.on_click is not None:
                    self.on_click()
                return True
        if event.type == pygame.MOUSEBUTTONUP:
            self.pressed = False
        return False

    def activate(self) -> None:
        """Programmatically trigger the button (e.g. keyboard confirm)."""
        if self.on_click is not None:
            self.on_click()

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, surface: pygame.Surface) -> None:
        """Draw the button with glow, border, and centered label."""
        r = self.rect
        w, h = r.w, r.h
        cx, cy = r.centerx, r.centery

        # glow on hover
        if self.hover:
            glow_surf = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
            pygame.draw.rect(
                glow_surf,
                self.color + (50,),
                (0, 0, w + 20, h + 20),
                border_radius=h // 2,
            )
            surface.blit(glow_surf, (r.x - 10, r.y - 10))

        # background
        bg_color = self.color if self.hover else (30, 30, 55)
        bg_alpha = 230 if self.pressed else 200
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(
            bg,
            tuple(bg_color[:3]) + (bg_alpha,),
            (0, 0, w, h),
            border_radius=h // 2,
        )
        surface.blit(bg, r.topleft)

        # border
        border_color = BRANCO if self.hover else self.color
        pygame.draw.rect(surface, border_color, r, 2, border_radius=h // 2)

        # label
        label = self.font.render(self.text, True, BRANCO)
        surface.blit(label, label.get_rect(center=(cx, cy)))

    def get_rect(self) -> pygame.Rect:
        """Return the bounding rect."""
        return self.rect
