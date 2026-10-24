"""Barra de rolagem do kit de UI."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.runtime.presentation.components.primitives import desenhar_caixa
from src.runtime.presentation.components.tokens import UITokens, tokens_atuais

if TYPE_CHECKING:
    from src.infrastructure.ui.layout import Layout


class BarraRolagem:
    """Trilho e polegar proporcionais ao conteúdo visível."""

    def __init__(
        self,
        *,
        largura: int = 6,
        margem: int = 4,
        altura_minima: int = 24,
    ) -> None:
        self.largura = largura
        self.margem = margem
        self.altura_minima = altura_minima

    def geometria(
        self,
        area: pygame.Rect,
        total: int,
        visivel: int,
        offset: int,
        layout: Layout,
    ) -> tuple[pygame.Rect, pygame.Rect | None]:
        """Retorna ``(trilho, polegar)``; polegar é None sem rolagem."""
        largura = max(2, layout.px(self.largura))
        margem = layout.px(self.margem)
        trilho = pygame.Rect(
            area.right - largura - margem,
            area.y,
            largura,
            area.h,
        )
        if total <= visivel or visivel <= 0:
            return trilho, None
        altura = max(
            layout.px(self.altura_minima),
            int(trilho.h * visivel / total),
        )
        altura = min(trilho.h, altura)
        max_offset = max(0, total - visivel)
        proporcao = offset / max_offset if max_offset else 0.0
        y = trilho.y + int((trilho.h - altura) * max(0.0, min(1.0, proporcao)))
        return trilho, pygame.Rect(trilho.x, y, largura, altura)

    def desenhar(
        self,
        tela: pygame.Surface,
        area: pygame.Rect,
        total: int,
        visivel: int,
        offset: int,
        layout: Layout,
        *,
        tokens: UITokens | None = None,
    ) -> None:
        """Desenha a barra apenas quando há conteúdo excedente."""
        tk = tokens or tokens_atuais()
        trilho, polegar = self.geometria(area, total, visivel, offset, layout)
        if polegar is None:
            return
        raio = max(2, trilho.w // 2)
        desenhar_caixa(
            tela,
            trilho,
            tk.superficie.fundo_linha,
            raio=raio,
            tokens=tk,
        )
        desenhar_caixa(
            tela,
            polegar,
            tk.superficie.destaque,
            raio=raio,
            tokens=tk,
        )
