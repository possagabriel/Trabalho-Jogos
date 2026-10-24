"""Botão do kit de UI, compartilhado por menu, submenus e confirmações."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.runtime.presentation.components.primitives import (
    desenhar_caixa,
    desenhar_texto,
    ease_out,
    fonte,
)
from src.runtime.presentation.components.tokens import (
    ESTILO_COMIC,
    UITokens,
    tokens_atuais,
)

if TYPE_CHECKING:
    from src.infrastructure.ui.layout import Layout


class Botao:
    """Botão com hover, foco, estado desabilitado e entrada animada."""

    def __init__(
        self,
        texto: str,
        rect: pygame.Rect | tuple,
        *,
        variante: str = "primario",
        habilitado: bool = True,
        foco: bool = False,
    ) -> None:
        self.texto = texto
        self.rect = pygame.Rect(rect)
        self.variante = variante
        self.habilitado = habilitado
        self.foco = foco
        self.hover = False

    def atualizar(self, mouse_pos: tuple[int, int]) -> None:
        """Atualiza o hover a partir da posição lógica do mouse."""
        self.hover = self.habilitado and self.rect.collidepoint(mouse_pos)

    def desenhar(
        self,
        tela: pygame.Surface,
        layout: Layout,
        *,
        fonte_usada: pygame.font.Font | None = None,
        tokens: UITokens | None = None,
        progresso: float = 1.0,
        dy_design: int = 0,
    ) -> None:
        """Desenha o botão preservando o rect usado para clique."""
        if progresso <= 0:
            return
        tk = tokens or tokens_atuais()
        p = ease_out(progresso)
        if progresso >= 1:
            self._desenhar(tela, self.rect, layout, tk, fonte_usada)
            return
        margem = layout.px(28)
        temp = pygame.Surface(
            (self.rect.w + margem * 2, self.rect.h + margem * 2),
            pygame.SRCALPHA,
        )
        self._desenhar(
            temp,
            self.rect.move(margem, margem),
            layout,
            tk,
            fonte_usada,
        )
        temp.set_alpha(int(255 * p))
        tela.blit(
            temp,
            (
                self.rect.x - margem,
                self.rect.y - margem + int((1 - p) * layout.px(dy_design)),
            ),
        )

    def _desenhar(
        self,
        tela: pygame.Surface,
        rect: pygame.Rect,
        layout: Layout,
        tk: UITokens,
        fonte_usada: pygame.font.Font | None,
    ) -> None:
        if self.variante == "fantasma":
            fundo = tk.superficie.fundo
            borda = None
            cor_texto = tk.superficie.texto
        elif self.variante == "secundario":
            fundo = tk.superficie.fundo_linha
            borda = tk.superficie.borda
            cor_texto = tk.superficie.texto
        else:
            fundo = tk.botao.fundo
            borda = tk.botao.borda
            cor_texto = tk.botao.texto

        if self.hover:
            fundo = tk.botao.fundo_hover
            borda = tk.botao.borda_hover
        if not self.habilitado:
            fundo = tk.superficie.fundo_linha
            borda = tk.superficie.borda
            cor_texto = tk.botao.texto_desabilitado

        raio = layout.px(tk.botao.raio)
        espessura = max(1, layout.px(tk.superficie.espessura))
        glow = layout.px(tk.botao.glow) if self.hover and self.habilitado else 0
        sombra = layout.px(4) if tk.estilo == ESTILO_COMIC else 0
        desenhar_caixa(
            tela,
            rect,
            fundo,
            borda=borda,
            raio=raio,
            espessura=espessura,
            tokens=tk,
            glow_cor=borda if tk.estilo != ESTILO_COMIC else None,
            glow_raio=glow,
            sombra=sombra,
        )
        if self.foco and self.habilitado:
            anel = rect.inflate(layout.px(8), layout.px(8))
            pygame.draw.rect(
                tela,
                tk.superficie.destaque,
                anel,
                max(1, layout.px(2)),
                border_radius=raio + layout.px(4),
            )
        fonte_botao = fonte_usada or fonte(
            layout,
            tk.tipografia.corpo,
            tokens=tk,
        )
        desenhar_texto(
            tela,
            self.texto,
            rect.center,
            fonte_botao,
            cor_texto,
            alinhamento="centro",
            tokens=tk,
            glow_cor=cor_texto if self.hover and tk.estilo != ESTILO_COMIC else None,
            glow_raio=max(1, layout.px(2)) if self.hover else 0,
        )
