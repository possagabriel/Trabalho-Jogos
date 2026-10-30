"""Painel do kit de UI, com cabeçalho opcional e entrada animada."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.infrastructure.graphics.comic_render import painel_tinta
from src.runtime.infrastructure.graphics.menu_panels import painel_original
from src.runtime.infrastructure.graphics.smooth import (
    desenhar_cantos,
)
from src.runtime.presentation.components.primitives import (
    desenhar_caixa,
    desenhar_texto,
    ease_out,
    fonte,
)
from src.runtime.presentation.components.tokens import (
    ESTILO_COMIC,
    ESTILO_ORIGINAL,
    UITokens,
    tokens_atuais,
)

if TYPE_CHECKING:
    from src.infrastructure.ui.layout import Layout


class Painel:
    """Superfície com moldura, cabeçalho interno e área de conteúdo."""

    def __init__(
        self,
        rect: pygame.Rect | tuple,
        *,
        titulo: str | None = None,
        subtitulo: str | None = None,
        cor_borda: tuple | None = None,
        cor_fundo: tuple | None = None,
        raio: int | None = None,
        espessura: int | None = None,
        alpha: int | None = None,
        glow: int | None = None,
        mostrar_cantos: bool = True,
        padding: int = 18,
        gap_cabecalho: int = 17,
        altura_cabecalho: int = 66,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.titulo = titulo
        self.subtitulo = subtitulo
        self.cor_borda = cor_borda
        self.cor_fundo = cor_fundo
        self.raio = raio
        self.espessura = espessura
        self.alpha = alpha
        self.glow = glow
        self.mostrar_cantos = mostrar_cantos
        self.padding = padding
        self.gap_cabecalho = gap_cabecalho
        self.altura_cabecalho = altura_cabecalho

    def area_conteudo(self, layout: Layout) -> pygame.Rect:
        """Retorna a área interna abaixo do cabeçalho."""
        pad = layout.px(self.padding)
        topo = self.rect.y + pad
        if self.titulo:
            topo += layout.px(self.altura_cabecalho) + layout.px(
                self.gap_cabecalho
            )
        return pygame.Rect(
            self.rect.x + pad,
            topo,
            self.rect.w - pad * 2,
            max(1, self.rect.bottom - pad - topo),
        )

    def desenhar(
        self,
        tela: pygame.Surface,
        layout: Layout,
        *,
        tokens: UITokens | None = None,
        progresso: float = 1.0,
    ) -> None:
        """Desenha o painel; ``progresso`` controla fade e subida."""
        if progresso <= 0:
            return
        tk = tokens or tokens_atuais()
        p = ease_out(progresso)
        if progresso >= 1:
            self._desenhar(tela, self.rect, layout, tk)
            return
        margem = layout.px(30)
        temp = pygame.Surface(
            (self.rect.w + margem * 2, self.rect.h + margem * 2),
            pygame.SRCALPHA,
        )
        self._desenhar(temp, self.rect.move(margem, margem), layout, tk)
        temp.set_alpha(int(255 * p))
        tela.blit(
            temp,
            (
                self.rect.x - margem,
                self.rect.y - margem + int((1 - p) * layout.px(22)),
            ),
        )

    def _desenhar(
        self,
        tela: pygame.Surface,
        rect: pygame.Rect,
        layout: Layout,
        tk: UITokens,
    ) -> None:
        borda = self.cor_borda or tk.superficie.borda_forte
        fundo = self.cor_fundo or tk.superficie.fundo
        raio = layout.px(self.raio or tk.superficie.raio)
        espessura = layout.px(self.espessura or tk.superficie.espessura)
        if tk.estilo == ESTILO_COMIC:
            tela.blit(painel_tinta(rect.size, tuple(borda[:3])), (rect.x - 12, rect.y - 12))
        else:
            tela.blit(painel_original(
                rect.size, tuple(fundo[:3]), tuple(borda[:3]), raio=raio,
                alpha=self.alpha or tk.superficie.alpha), rect)
            if self.mostrar_cantos:
                desenhar_cantos(
                    tela,
                    tk.superficie.destaque_secundario,
                    rect,
                    tamanho=layout.px(14),
                    espessura=espessura,
                )
        if self.titulo:
            self._desenhar_cabecalho(tela, rect, layout, tk, borda)

    def _desenhar_cabecalho(
        self,
        tela: pygame.Surface,
        rect: pygame.Rect,
        layout: Layout,
        tk: UITokens,
        borda: tuple,
    ) -> None:
        pad = layout.px(self.padding)
        cabecalho = pygame.Rect(
            rect.x + pad,
            rect.y + pad,
            rect.w - pad * 2,
            layout.px(self.altura_cabecalho),
        )
        desenhar_caixa(
            tela,
            cabecalho,
            tk.superficie.fundo_cabecalho,
            borda=borda,
            raio=layout.px(tk.superficie.raio_pequeno),
            espessura=espessura_borda(layout, tk),
            tokens=tk,
            glow_cor=borda if tk.estilo == ESTILO_ORIGINAL else None,
            glow_raio=layout.px(13) if tk.estilo == ESTILO_ORIGINAL else 0,
        )
        centro_icone = (cabecalho.x + layout.px(34), cabecalho.centery)
        pygame.draw.circle(
            tela,
            tk.superficie.destaque_secundario,
            centro_icone,
            max(2, layout.px(7)),
        )
        fonte_titulo = fonte(
            layout,
            tk.tipografia.titulo_painel,
            titulo=True,
            tokens=tk,
        )
        desenhar_texto(
            tela,
            self.titulo,
            (cabecalho.x + layout.px(58), cabecalho.centery),
            fonte_titulo,
            tk.superficie.texto,
            alinhamento="midleft",
            tokens=tk,
        )
        if self.subtitulo:
            fonte_sub = fonte(layout, tk.tipografia.subtitulo, tokens=tk)
            desenhar_texto(
                tela,
                self.subtitulo,
                (cabecalho.right - layout.px(18), cabecalho.centery),
                fonte_sub,
                tk.superficie.destaque,
                alinhamento="midright",
                tokens=tk,
            )


def espessura_borda(layout: Layout, tk: UITokens) -> int:
    """Espessura mínima legível para a borda de cartões."""
    return max(1, layout.px(tk.superficie.espessura))
