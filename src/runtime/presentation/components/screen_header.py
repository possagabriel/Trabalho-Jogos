"""Cabeçalho central das telas do menu."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.infrastructure.graphics.comic_render import texto_tinta
from src.runtime.infrastructure.graphics.smooth import (
    desenhar_glow,
    desenhar_poligono,
)
from src.runtime.presentation.components.primitives import ease_out, fonte
from src.runtime.presentation.components.tokens import (
    ESTILO_COMIC,
    UITokens,
    tokens_atuais,
)
from src.runtime.presentation.menu_scene import texto_espacado

if TYPE_CHECKING:
    from src.infrastructure.ui.layout import Layout


class CabecalhoTela:
    """Título central com bloco diagonal, glow e entrada animada."""

    def __init__(
        self,
        texto: str,
        *,
        cor: tuple | None = None,
        y: int = 58,
        espacamento: int = 3,
    ) -> None:
        self.texto = texto
        self.cor = cor
        self.y = y
        self.espacamento = espacamento
        self._cache_bloco: dict[tuple, pygame.Surface] = {}

    def desenhar(
        self,
        tela: pygame.Surface,
        layout: Layout,
        *,
        tokens: UITokens | None = None,
        progresso: float = 1.0,
    ) -> None:
        """Desenha o cabeçalho com fade e descida de entrada."""
        if progresso <= 0:
            return
        tk = tokens or tokens_atuais()
        p = ease_out(progresso)
        cor = self.cor or tk.superficie.borda_forte
        fonte_titulo = fonte(
            layout,
            tk.tipografia.titulo_tela,
            titulo=True,
            tokens=tk,
        )
        if tk.estilo == ESTILO_COMIC:
            titulo = texto_tinta(
                self.texto,
                max(10, int(fonte_titulo.get_height() * 0.8)),
                tk.superficie.texto,
            )
        else:
            titulo = texto_espacado(
                fonte_titulo,
                self.texto,
                layout.px(self.espacamento),
                tk.superficie.texto,
            )
        if p < 1:
            titulo = titulo.copy()
            titulo.set_alpha(int(255 * p))
        bloco = self._bloco(cor, titulo.get_width() + layout.px(80), layout)
        if p < 1:
            bloco = bloco.copy()
            bloco.set_alpha(int(255 * p))
        cx = layout.x(0.5)
        y = layout.px(self.y) + int((1 - p) * layout.px(-28))
        desenhar_glow(
            tela,
            cor,
            (cx, y + layout.px(6)),
            max(layout.px(24), bloco.get_width() // 8),
            0.35 * p,
        )
        tela.blit(bloco, bloco.get_rect(center=(cx, y + layout.px(6))))
        tela.blit(titulo, titulo.get_rect(center=(cx, y)))

    def _bloco(
        self,
        cor: tuple,
        largura: int,
        layout: Layout,
    ) -> pygame.Surface:
        altura = layout.px(56)
        inclinacao = layout.px(12)
        chave = (tuple(cor[:3]), int(largura), altura, inclinacao)
        if chave in self._cache_bloco:
            return self._cache_bloco[chave]
        surf = pygame.Surface((max(1, int(largura)), altura + inclinacao), pygame.SRCALPHA)
        pontos = [
            (0, inclinacao),
            (int(largura), 0),
            (int(largura), altura),
            (0, altura + inclinacao),
        ]
        desenhar_poligono(surf, tuple(cor[:3]) + (50,), pontos)
        desenhar_poligono(
            surf,
            tuple(cor[:3]) + (200,),
            pontos,
            max(1, layout.px(2)),
        )
        self._cache_bloco[chave] = surf
        return surf
