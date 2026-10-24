"""Rodapé com fileira de ações e dicas de teclado."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

import pygame

from src.runtime.presentation.components.button import Botao
from src.runtime.presentation.components.primitives import desenhar_texto, fonte
from src.runtime.presentation.components.tokens import UITokens, tokens_atuais

if TYPE_CHECKING:
    from src.infrastructure.ui.layout import Layout


class RodapeAcoes:
    """Agrupa botões de rodapé e dicas contextuais."""

    def __init__(
        self,
        botoes: Iterable[Botao],
        dicas: Iterable[str] = (),
    ) -> None:
        self.botoes = list(botoes)
        self.dicas = list(dicas)

    def atualizar(self, mouse_pos: tuple[int, int]) -> None:
        """Atualiza o hover de todos os botões."""
        for botao in self.botoes:
            botao.atualizar(mouse_pos)

    def desenhar(
        self,
        tela: pygame.Surface,
        layout: Layout,
        *,
        fonte_usada: pygame.font.Font | None = None,
        tokens: UITokens | None = None,
        progresso: float = 1.0,
    ) -> None:
        """Desenha os botões e as dicas, com entrada escalonada."""
        tk = tokens or tokens_atuais()
        for indice, botao in enumerate(self.botoes):
            inicio = indice * 0.06
            restante = max(0.01, 1 - inicio)
            p = (progresso - inicio) / restante
            botao.desenhar(
                tela,
                layout,
                fonte_usada=fonte_usada,
                tokens=tk,
                progresso=p,
                dy_design=22,
            )
        if self.dicas:
            fonte_dica = fonte(layout, tk.tipografia.legenda, tokens=tk)
            desenhar_texto(
                tela,
                "   ".join(self.dicas),
                (layout.px(26), layout.altura - layout.px(42)),
                fonte_dica,
                tk.superficie.texto_secundario,
                alinhamento="midleft",
                tokens=tk,
            )
