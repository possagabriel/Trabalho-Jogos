"""Lista vertical com seleção, rolagem e estado vazio."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable

import pygame

from src.core.constants import DOURADO
from src.runtime.presentation.components.empty_state import EstadoVazio
from src.runtime.presentation.components.primitives import (
    desenhar_caixa,
    desenhar_texto,
    fonte,
    medir_texto,
    truncar_texto,
)
from src.runtime.presentation.components.scrollbar import BarraRolagem
from src.runtime.presentation.components.tokens import UITokens, tokens_atuais

if TYPE_CHECKING:
    from src.infrastructure.ui.layout import Layout


@dataclass(frozen=True)
class ItemLista:
    """Conteúdo de uma linha da lista."""

    titulo: str
    subtitulo: str = ""
    valor: str = ""
    destaque: bool = False
    cor: tuple | None = None


class Lista:
    """Lista reutilizável com linhas, seleção e barra de rolagem."""

    def __init__(
        self,
        rect: pygame.Rect | tuple,
        itens: Iterable[ItemLista] = (),
        *,
        altura_linha: int | None = None,
        espaco: int | None = None,
        mostrar_indice: bool = True,
        mostrar_fundo: bool = True,
        estado_vazio: EstadoVazio | None = None,
        selecao: int | None = None,
        padding: int = 10,
        barra: BarraRolagem | None = None,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.itens = list(itens)
        self.altura_linha = altura_linha
        self.espaco = espaco
        self.mostrar_indice = mostrar_indice
        self.mostrar_fundo = mostrar_fundo
        self.estado_vazio = estado_vazio
        self.selecao = selecao
        self.padding = padding
        self.barra = barra or BarraRolagem()
        self.offset = 0

    def definir_itens(self, itens: Iterable[ItemLista]) -> None:
        """Substitui os itens e reajusta seleção e rolagem."""
        self.itens = list(itens)
        if self.selecao is not None:
            self.selecao = max(0, min(self.selecao, len(self.itens) - 1))
        self.offset = 0

    def _metricas(
        self,
        layout: Layout,
        tk: UITokens,
    ) -> tuple[int, int, int]:
        altura = layout.px(self.altura_linha or tk.altura_lista)
        espaco = layout.px(self.espaco if self.espaco is not None else tk.espaco_lista)
        return altura, espaco, max(1, altura + espaco)

    def altura_total(self, layout: Layout, tk: UITokens) -> int:
        """Altura de todas as linhas, incluindo os espaços."""
        if not self.itens:
            return 0
        altura, espaco, _ = self._metricas(layout, tk)
        return len(self.itens) * altura + (len(self.itens) - 1) * espaco

    def max_offset(self, layout: Layout, tk: UITokens) -> int:
        """Deslocamento máximo permitido para o conteúdo."""
        return max(0, self.altura_total(layout, tk) - self.rect.h)

    def _precisa_barra(self, layout: Layout, tk: UITokens) -> bool:
        return self.altura_total(layout, tk) > self.rect.h

    def _largura_conteudo(self, layout: Layout, tk: UITokens) -> int:
        if not self._precisa_barra(layout, tk):
            return self.rect.w
        return max(1, self.rect.w - layout.px(tk.largura_barra + 10))

    def rolar(self, delta: int, layout: Layout, tokens: UITokens | None = None) -> None:
        """Rola a lista em pixels, respeitando os limites."""
        tk = tokens or tokens_atuais()
        maximo = self.max_offset(layout, tk)
        self.offset = max(0, min(maximo, self.offset + delta))

    def mover_selecao(
        self,
        delta: int,
        layout: Layout,
        tokens: UITokens | None = None,
    ) -> None:
        """Move a seleção e garante que a linha fique visível."""
        if not self.itens:
            return
        tk = tokens or tokens_atuais()
        atual = self.selecao if self.selecao is not None else 0
        novo = max(0, min(len(self.itens) - 1, atual + delta))
        self.selecao = novo
        altura, espaco, passo = self._metricas(layout, tk)
        topo = novo * passo
        if topo < self.offset:
            self.offset = topo
        elif topo + altura > self.offset + self.rect.h:
            self.offset = topo + altura - self.rect.h
        self.offset = max(0, min(self.max_offset(layout, tk), self.offset))

    def desenhar(
        self,
        tela: pygame.Surface,
        layout: Layout,
        *,
        tokens: UITokens | None = None,
    ) -> None:
        """Desenha as linhas visíveis e a barra de rolagem."""
        tk = tokens or tokens_atuais()
        if not self.itens:
            if self.estado_vazio is not None:
                self.estado_vazio.desenhar(tela, self.rect, layout, tokens=tk)
            return
        altura, espaco, passo = self._metricas(layout, tk)
        largura = self._largura_conteudo(layout, tk)
        clip_antigo = tela.get_clip()
        tela.set_clip(self.rect)
        for indice, item in enumerate(self.itens):
            y = self.rect.y + indice * passo - self.offset
            if y + altura < self.rect.top:
                continue
            if y > self.rect.bottom:
                break
            linha = pygame.Rect(self.rect.x, y, largura, altura)
            self._desenhar_linha(tela, linha, indice, item, layout, tk)
        tela.set_clip(clip_antigo)
        self.barra.desenhar(
            tela,
            self.rect,
            self.altura_total(layout, tk),
            self.rect.h,
            self.offset,
            layout,
            tokens=tk,
        )

    def _desenhar_linha(
        self,
        tela: pygame.Surface,
        linha: pygame.Rect,
        indice: int,
        item: ItemLista,
        layout: Layout,
        tk: UITokens,
    ) -> None:
        destaque = item.destaque or indice == self.selecao
        cor = item.cor or (
            DOURADO
            if indice == 0
            else tk.superficie.destaque
            if indice < 3
            else tk.superficie.texto_secundario
        )
        fundo = (
            tk.superficie.fundo_destaque
            if destaque or (indice == 0 and tk.estilo != "COMIC")
            else tk.superficie.fundo_linha
        )
        if self.mostrar_fundo:
            desenhar_caixa(
                tela,
                linha,
                fundo,
                borda=cor,
                raio=layout.px(tk.superficie.raio_pequeno),
                espessura=max(1, layout.px(tk.superficie.espessura)),
                tokens=tk,
                glow_cor=cor if destaque or indice == 0 else None,
                glow_raio=layout.px(8) if destaque or indice == 0 else 0,
                sombra=layout.px(3) if tk.estilo == "COMIC" else 0,
            )
        pad = layout.px(self.padding)
        x_texto = linha.x + pad
        if self.mostrar_indice:
            centro = (linha.x + pad + layout.px(14), linha.centery)
            pygame.draw.circle(
                tela,
                cor,
                centro,
                max(4, layout.px(12)),
            )
            fonte_indice = fonte(layout, tk.tipografia.legenda, tokens=tk)
            desenhar_texto(
                tela,
                str(indice + 1),
                centro,
                fonte_indice,
                tk.superficie.sombra,
                alinhamento="centro",
                tokens=tk,
                sombra=False,
            )
            x_texto = linha.x + pad + layout.px(34)
        fonte_titulo = fonte(layout, tk.tipografia.corpo, tokens=tk)
        fonte_valor = (
            fonte(layout, tk.tipografia.valor, titulo=True, tokens=tk)
            if item.valor
            else None
        )
        gap = layout.px(12)
        limite_direito = linha.right - pad
        if fonte_valor is not None:
            largura_valor = medir_texto(item.valor, fonte_valor, tokens=tk)
            limite_direito -= largura_valor + gap
        x_subtitulo = linha.x + int(linha.w * 0.58)
        limite_titulo = (
            x_subtitulo - gap if item.subtitulo else limite_direito
        )
        titulo = truncar_texto(
            item.titulo,
            fonte_titulo,
            limite_titulo - x_texto,
            tokens=tk,
        )
        desenhar_texto(
            tela,
            titulo,
            (x_texto, linha.centery),
            fonte_titulo,
            tk.superficie.texto,
            alinhamento="midleft",
            tokens=tk,
        )
        if item.subtitulo:
            fonte_sub = fonte(layout, tk.tipografia.legenda, tokens=tk)
            subtitulo = truncar_texto(
                item.subtitulo,
                fonte_sub,
                limite_direito - x_subtitulo,
                tokens=tk,
            )
            desenhar_texto(
                tela,
                subtitulo,
                (x_subtitulo, linha.centery),
                fonte_sub,
                tk.superficie.texto_secundario,
                alinhamento="midleft",
                tokens=tk,
            )
        if fonte_valor is not None:
            desenhar_texto(
                tela,
                item.valor,
                (linha.right - pad, linha.centery),
                fonte_valor,
                cor,
                alinhamento="midright",
                tokens=tk,
            )
