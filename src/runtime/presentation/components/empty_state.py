"""Estado vazio reutilizável para listas e coleções."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.runtime.presentation.components.primitives import desenhar_texto, fonte
from src.runtime.presentation.components.tokens import UITokens, tokens_atuais

if TYPE_CHECKING:
    from src.infrastructure.ui.layout import Layout


class EstadoVazio:
    """Mensagem central com ícone geométrico e dica opcional."""

    def __init__(self, texto: str, dica: str = "") -> None:
        self.texto = texto
        self.dica = dica

    def desenhar(
        self,
        tela: pygame.Surface,
        rect: pygame.Rect,
        layout: Layout,
        *,
        tokens: UITokens | None = None,
    ) -> None:
        """Desenha o estado vazio centralizado em ``rect``."""
        tk = tokens or tokens_atuais()
        centro = rect.center
        raio = max(6, layout.px(16))
        topo = centro[1] - layout.px(40)
        pygame.draw.circle(
            tela,
            tk.superficie.borda,
            (centro[0], topo),
            raio,
            max(1, layout.px(2)),
        )
        pygame.draw.line(
            tela,
            tk.superficie.borda,
            (centro[0] - raio // 2, topo + raio // 2),
            (centro[0] + raio // 2, topo - raio // 2),
            max(1, layout.px(2)),
        )
        fonte_texto = fonte(layout, tk.tipografia.corpo, titulo=True, tokens=tk)
        desenhar_texto(
            tela,
            self.texto,
            (centro[0], centro[1] - layout.px(10)),
            fonte_texto,
            tk.superficie.texto,
            alinhamento="centro",
            tokens=tk,
        )
        if self.dica:
            fonte_dica = fonte(layout, tk.tipografia.legenda, tokens=tk)
            desenhar_texto(
                tela,
                self.dica,
                (centro[0], centro[1] + layout.px(22)),
                fonte_dica,
                tk.superficie.texto_secundario,
                alinhamento="centro",
                tokens=tk,
            )
