"""Apresentação da pausa ORIGINAL e geometria usada pelos controles."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.infrastructure.graphics.theme import MENU_COR_TEXTO, MENU_COR_TEXTO_SECUNDARIO
from src.runtime.infrastructure.graphics.menu_panels import painel_original, texto_painel
from src.runtime.infrastructure.graphics.smooth import barra_suave

if TYPE_CHECKING:
    from src.infrastructure.ui.layout import Layout
    from src.runtime.application.core import Jogo


def geometria_pausa(layout: Layout) -> tuple[pygame.Rect, tuple[pygame.Rect, ...]]:
    """Compartilha as áreas desenhadas e clicáveis da pausa principal."""
    painel = pygame.Rect(0, 0, layout.px(440), layout.px(420))
    painel.center = (layout.x(0.5), layout.y(0.5))
    botoes = tuple(pygame.Rect(painel.centerx - layout.px(160),
                               painel.y + layout.px(118 + indice * 74),
                               layout.px(320), layout.px(54)) for indice in range(3))
    return painel, botoes


def geometria_config_pausa(layout: Layout
                           ) -> tuple[pygame.Rect, tuple[pygame.Rect, ...],
                                      tuple[pygame.Rect, ...]]:
    """Compartilha linhas e ações das configurações rápidas."""
    painel = pygame.Rect(0, 0, layout.px(540), layout.px(430))
    painel.center = (layout.x(0.5), layout.y(0.5))
    linhas = tuple(pygame.Rect(painel.x + layout.px(24),
                               painel.y + layout.px(70 + indice * 70),
                               painel.w - layout.px(48), layout.px(44)) for indice in range(4))
    botoes = (pygame.Rect(painel.x + layout.px(30), painel.bottom - layout.px(56),
                          layout.px(150), layout.px(42)),
               pygame.Rect(painel.right - layout.px(180), painel.bottom - layout.px(56),
                           layout.px(150), layout.px(42)))
    return painel, linhas, botoes


def desenhar_pausa_original(jogo: Jogo, tema: dict, *, configuracoes: bool = False) -> None:
    """Desenha ações, sessão e opções rápidas em superfícies cacheadas."""
    layout, tela = jogo.layout, jogo.tela
    fundo, borda = tuple(tema["fundo_painel"][:3]), tuple(tema["primaria"][:3])

    def texto(rotulo, rect, tamanho=20, titulo=False, cor=MENU_COR_TEXTO):
        fonte = layout.fonte_titulo(tamanho) if titulo else layout.fonte_texto(tamanho)
        arte = texto_painel(fonte, rotulo, tuple(cor[:3]), rect.w, rect.h)
        tela.blit(arte, arte.get_rect(center=rect.center))

    def caixa(rect, selecionado=False, cor=borda):
        tela.blit(painel_original(rect.size, fundo, tuple(cor[:3]), selecionado=selecionado,
                                  raio=layout.px(10), alpha=248), rect)

    if configuracoes:
        painel, linhas, botoes = geometria_config_pausa(layout)
        caixa(painel)
        texto("CONFIGURAÇÕES", pygame.Rect(painel.x + layout.px(20),
              painel.y + layout.px(15), painel.w - layout.px(40), layout.px(38)), 28, True)
        itens = (("MÚSICA", f"{jogo.config['musica_volume']:.0%}"),
                 ("EFEITOS", f"{jogo.config['efeitos_volume']:.0%}"),
                 ("TEMA", str(jogo.config["tema"])),
                 ("TELA CHEIA", "LIGADA" if jogo.config["tela_cheia"] else "DESLIGADA"))
        for indice, ((rotulo, valor), linha) in enumerate(zip(itens, linhas)):
            caixa(linha, indice == jogo._pausa_config_selecao)
            esquerda = linha.inflate(-layout.px(24), -layout.px(8))
            esquerda.w = linha.w // 2 - layout.px(24)
            direita = esquerda.move(linha.w // 2, 0)
            texto(rotulo, esquerda)
            texto(valor, direita, cor=tema["secundaria"])
            if indice < 2:
                chave = "musica_volume" if indice == 0 else "efeitos_volume"
                barra_suave(tela, linha.x + layout.px(14), linha.bottom + layout.px(6),
                            linha.w - layout.px(28), layout.px(3), jogo.config[chave],
                            borda, fundo=fundo, glow=False)
        for rotulo, botao in zip(("VOLTAR", "RESTAURAR"), botoes):
            caixa(botao)
            texto(rotulo, botao.inflate(-layout.px(12), -layout.px(10)), 18)
        return

    painel, botoes = geometria_pausa(layout)
    caixa(painel)
    texto("PAUSADO", pygame.Rect(painel.x + layout.px(20), painel.y + layout.px(24),
                                 painel.w - layout.px(40), layout.px(40)), 34, True)
    texto("ESC RETOMA A MISSÃO", pygame.Rect(painel.x + layout.px(20),
          painel.y + layout.px(77), painel.w - layout.px(40), layout.px(22)),
          16, cor=MENU_COR_TEXTO_SECUNDARIO)
    itens = (("CONTINUAR", "Retomar a missão"), ("CONFIGURAÇÕES", "Áudio, tema e vídeo"),
             ("VOLTAR AO MENU", "Salvar a sessão e sair"))
    for indice, ((rotulo, dica), botao) in enumerate(zip(itens, botoes)):
        caixa(botao, indice == jogo._pausa_selecao,
              tema["terciaria"] if indice == 2 else borda)
        titulo = botao.inflate(-layout.px(20), 0)
        titulo.y += layout.px(5)
        titulo.h = layout.px(25)
        texto(rotulo, titulo, 22, True)
        texto(dica, pygame.Rect(titulo.x, botao.y + layout.px(33), titulo.w, layout.px(16)),
              14, cor=MENU_COR_TEXTO_SECUNDARIO)
    info = pygame.Rect(painel.x + layout.px(24), painel.bottom - layout.px(80),
                       painel.w - layout.px(48), layout.px(45))
    texto(f"NÍVEL {jogo.jogador.nivel}   ·   {jogo.jogador.pontuacao} PTS",
          pygame.Rect(info.x, info.y, info.w, layout.px(20)), 17)
    texto(f"VISUAL {jogo.jogador.skin.nome.upper()}",
          pygame.Rect(info.x, info.y + layout.px(23), info.w, layout.px(18)),
          15, cor=MENU_COR_TEXTO_SECUNDARIO)
    texto("↑ / ↓  NAVEGAR   ·   ENTER  SELECIONAR",
          pygame.Rect(painel.x + layout.px(16), painel.bottom - layout.px(25),
                      painel.w - layout.px(32), layout.px(18)),
          14, cor=MENU_COR_TEXTO_SECUNDARIO)
