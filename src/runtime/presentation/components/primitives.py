"""Primitivas compartilhadas pelos componentes do kit de UI."""

from __future__ import annotations

from typing import Any

import pygame

from src.infrastructure.graphics.comic_render import fonte_comic, texto_tinta
from src.runtime.infrastructure.graphics.smooth import (
    retangulo_suave,
    texto_suave,
)
from src.runtime.presentation.components.tokens import (
    ESTILO_COMIC,
    UITokens,
    tokens_atuais,
)


def ease_out(progresso: float) -> float:
    """Suaviza uma entrada sem alterar o estado da tela."""
    p = max(0.0, min(1.0, progresso))
    return 1 - (1 - p) * (1 - p)


def fonte(
    layout: Any,
    tamanho: int,
    *,
    titulo: bool = False,
    tokens: UITokens | None = None,
):
    """Fonte do kit, escalada pelo layout e pelo estilo atual."""
    tk = tokens or tokens_atuais()
    if tk.estilo == ESTILO_COMIC:
        return fonte_comic(max(10, layout.px(tamanho)))
    if titulo:
        return layout.fonte_titulo(tamanho)
    return layout.fonte_texto(tamanho)


def superficie_texto(
    texto: str,
    fonte_usada: pygame.font.Font,
    cor: tuple,
    *,
    tokens: UITokens | None = None,
    glow_cor: tuple | None = None,
    glow_raio: int = 0,
    sombra: bool = True,
) -> pygame.Surface:
    """Renderiza texto no estilo atual, com cache das rotinas existentes."""
    tk = tokens or tokens_atuais()
    if tk.estilo == ESTILO_COMIC:
        tamanho = max(10, int(fonte_usada.get_height() * 0.8))
        return texto_tinta(str(texto), tamanho, tuple(cor[:3]))
    return texto_suave(
        fonte_usada,
        str(texto),
        cor,
        glow_cor=glow_cor,
        glow_raio=glow_raio,
        sombra=sombra,
    )


def alinhar_rect(rect: pygame.Rect, pos: tuple, alinhamento: str) -> None:
    """Aplica um alinhamento nomeado a um rect."""
    mapa = {
        "centro": "center",
        "center": "center",
        "esquerda": "topleft",
        "direita": "topright",
        "topleft": "topleft",
        "topright": "topright",
        "midleft": "midleft",
        "midright": "midright",
        "midtop": "midtop",
        "midbottom": "midbottom",
        "bottomleft": "bottomleft",
        "bottomright": "bottomright",
    }
    atributo = mapa.get(alinhamento, alinhamento)
    setattr(rect, atributo, pos)


def medir_texto(
    texto: str,
    fonte_usada: pygame.font.Font,
    *,
    tokens: UITokens | None = None,
    glow_cor: tuple | None = None,
    glow_raio: int = 0,
    sombra: bool = True,
) -> int:
    """Retorna a largura real do texto como ele será desenhado."""
    surf = superficie_texto(
        texto,
        fonte_usada,
        (255, 255, 255),
        tokens=tokens,
        glow_cor=glow_cor,
        glow_raio=glow_raio,
        sombra=sombra,
    )
    return surf.get_width()


def truncar_texto(
    texto: str,
    fonte_usada: pygame.font.Font,
    largura_max: int,
    *,
    tokens: UITokens | None = None,
    sufixo: str = "…",
    sombra: bool = True,
) -> str:
    """Corta o texto com reticências para caber em ``largura_max``."""
    if largura_max <= 0:
        return ""
    if medir_texto(texto, fonte_usada, tokens=tokens, sombra=sombra) <= largura_max:
        return texto
    if medir_texto(sufixo, fonte_usada, tokens=tokens, sombra=sombra) > largura_max:
        return ""
    limite_baixo, limite_alto = 0, len(texto)
    while limite_baixo < limite_alto:
        meio = (limite_baixo + limite_alto + 1) // 2
        candidato = texto[:meio].rstrip() + sufixo
        if medir_texto(candidato, fonte_usada, tokens=tokens, sombra=sombra) <= largura_max:
            limite_baixo = meio
        else:
            limite_alto = meio - 1
    return texto[:limite_baixo].rstrip() + sufixo


def desenhar_texto(
    tela: pygame.Surface,
    texto: str,
    pos: tuple,
    fonte_usada: pygame.font.Font,
    cor: tuple,
    *,
    alinhamento: str = "topleft",
    tokens: UITokens | None = None,
    glow_cor: tuple | None = None,
    glow_raio: int = 0,
    sombra: bool = True,
) -> pygame.Rect:
    """Desenha texto e retorna o rect ocupado."""
    surf = superficie_texto(
        texto,
        fonte_usada,
        cor,
        tokens=tokens,
        glow_cor=glow_cor,
        glow_raio=glow_raio,
        sombra=sombra,
    )
    rect = surf.get_rect()
    alinhar_rect(rect, pos, alinhamento)
    tela.blit(surf, rect)
    return rect


def desenhar_caixa(
    tela: pygame.Surface,
    rect: pygame.Rect,
    fundo: tuple,
    *,
    borda: tuple | None = None,
    raio: int = 8,
    espessura: int = 1,
    tokens: UITokens | None = None,
    glow_cor: tuple | None = None,
    glow_raio: int = 0,
    sombra: int = 0,
) -> None:
    """Desenha uma caixa com o acabamento do estilo atual."""
    tk = tokens or tokens_atuais()
    if tk.estilo == ESTILO_COMIC:
        if sombra > 0:
            pygame.draw.rect(
                tela,
                tk.superficie.sombra,
                rect.move(sombra, sombra),
                border_radius=raio,
            )
        pygame.draw.rect(tela, fundo, rect, border_radius=raio)
        if borda is not None and espessura > 0:
            pygame.draw.rect(
                tela,
                borda,
                rect,
                max(1, espessura),
                border_radius=raio,
            )
        return
    retangulo_suave(tela, fundo, rect, raio)
    if borda is not None and espessura > 0:
        retangulo_suave(
            tela,
            borda,
            rect,
            raio,
            espessura,
            glow_cor=glow_cor,
            glow_raio=glow_raio,
        )
