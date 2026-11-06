"""Arquivo de Memórias: replay somente de cenas desbloqueadas."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.runtime.infrastructure.graphics.menu_panels import (
    ACENTO_ORIGINAL,
    TEXTO_ATIVO_ORIGINAL,
    TEXTO_ORIGINAL,
    painel_menu,
    texto_painel,
)

if TYPE_CHECKING:
    from src.runtime.presentation.menu import MenuPrincipal


class TelaArquivoMemorias:
    """Lista IDs vistos e inicia replay sem mexer no progresso da campanha."""

    def __init__(self, menu: MenuPrincipal) -> None:
        self.menu = menu
        self.selecao = 0
        self.inicio = 0

    def _ids(self) -> list[str]:
        jogo = self.menu.jogo
        return [identificador for identificador in jogo.progresso.cenas_vistas
                if jogo.cutscene_controller.catalogo.cena(identificador) is not None]

    def _painel(self) -> pygame.Rect:
        layout = self.menu.layout
        rect = pygame.Rect(0, 0, layout.px(740), layout.px(550))
        rect.center = (layout.x(.5), layout.y(.5))
        return rect

    def _linhas(self) -> list[pygame.Rect]:
        painel, layout = self._painel(), self.menu.layout
        return [pygame.Rect(painel.x + layout.px(24),
                            painel.y + layout.px(108 + i * 46),
                            painel.w - layout.px(48), layout.px(40)) for i in range(8)]

    def _voltar(self) -> pygame.Rect:
        painel, layout = self._painel(), self.menu.layout
        return pygame.Rect(painel.x + layout.px(24), painel.bottom - layout.px(54),
                           painel.w - layout.px(48), layout.px(34))

    def desenhar(self, tela: pygame.Surface) -> None:
        """Apresenta capítulos em cartões com texto contido e foco legível."""
        menu, layout, painel = self.menu, self.menu.layout, self._painel()
        tela.blit(painel_menu(painel.size, (0, 0, 0), ACENTO_ORIGINAL), painel)

        def texto(rotulo: str, rect: pygame.Rect, cor: tuple = TEXTO_ORIGINAL) -> None:
            arte = texto_painel(menu.fonte_media, rotulo, cor,
                                rect.w - layout.px(20), rect.h - layout.px(6))
            tela.blit(arte, arte.get_rect(center=rect.center))

        texto("ARQUIVO DE MEMÓRIAS", pygame.Rect(
            painel.x, painel.y + layout.px(24), painel.w, layout.px(34)), ACENTO_ORIGINAL)
        ids = self._ids()
        texto(f"{len(ids)} CENAS DESBLOQUEADAS · REVEJA SUA HISTÓRIA", pygame.Rect(
            painel.x, painel.y + layout.px(66), painel.w, layout.px(24)))
        if not ids:
            texto("Explore a campanha para recuperar suas memórias.", self._linhas()[2])
        for indice, rect in zip(range(self.inicio, len(ids)), self._linhas()):
            selecionada = indice == self.selecao
            tela.blit(painel_menu(rect.size, (0, 0, 0), ACENTO_ORIGINAL,
                                  selecionado=selecionada, botao=True, segmentado=False), rect)
            cena = menu.jogo.cutscene_controller.catalogo.cena(ids[indice])
            texto(f"{indice + 1:02d}  /  {cena.nome}", rect,
                  TEXTO_ATIVO_ORIGINAL if selecionada else TEXTO_ORIGINAL)
        texto("↑↓ SELECIONAR · ENTER REVER · ESC VOLTAR", self._voltar())

    def tratar_tecla(self, evento: pygame.event.Event) -> bool:
        """Navega e reproduz uma cena com as teclas usuais do menu."""
        ids = self._ids()
        if evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.menu._voltar_menu()
        elif ids and evento.key in (pygame.K_DOWN, pygame.K_s):
            self.selecao = (self.selecao + 1) % len(ids)
        elif ids and evento.key in (pygame.K_UP, pygame.K_w):
            self.selecao = (self.selecao - 1) % len(ids)
        elif ids and evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.menu.jogo.cutscene_controller.rever(ids[self.selecao])
        self.inicio = max(0, self.selecao - 7)
        return True

    def tratar_clique(self, pos: tuple[int, int]) -> None:
        """Reproduz a linha clicada, se estiver desbloqueada."""
        if self._voltar().collidepoint(pos):
            self.menu._voltar_menu()
            return
        ids = self._ids()
        for indice, rect in zip(range(self.inicio, len(ids)), self._linhas()):
            if rect.collidepoint(pos):
                self.selecao = indice
                self.menu.jogo.cutscene_controller.rever(ids[indice])
                return
