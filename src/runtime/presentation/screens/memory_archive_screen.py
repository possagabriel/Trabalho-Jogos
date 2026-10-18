"""Arquivo de Memórias: replay somente de cenas desbloqueadas."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.core.constants import QUANTUM_CYAN, SHIFT_WHITE
from src.runtime.infrastructure.graphics.smooth import desenhar_painel_cartoon

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

    def desenhar(self, tela: pygame.Surface) -> None:
        """Desenha cenas desbloqueadas na área lógica do menu."""
        menu = self.menu
        layout = menu.layout
        painel = pygame.Rect(layout.x(0.14), layout.y(0.10), layout.px(650), layout.px(515))
        desenhar_painel_cartoon(tela, QUANTUM_CYAN, painel)
        cabecalho = menu.fonte_cabecalho.render("ARQUIVO DE MEMÓRIAS", True, QUANTUM_CYAN)
        tela.blit(cabecalho, (painel.x + 30, painel.y + 25))
        ids = self._ids()
        if not ids:
            texto = menu.fonte_media.render("Nenhuma memória desbloqueada.", True, SHIFT_WHITE)
            tela.blit(texto, (painel.x + 35, painel.y + 115))
        for indice in range(self.inicio, min(len(ids), self.inicio + 8)):
            cor = QUANTUM_CYAN if indice == self.selecao else SHIFT_WHITE
            cena = menu.jogo.cutscene_controller.catalogo.cena(ids[indice])
            texto = menu.fonte_media.render(cena.nome, True, cor)
            tela.blit(texto, (painel.x + 42, painel.y + 105 + (indice - self.inicio) * 46))
        dica = menu.fonte_pequena.render("ENTER: REVER   ESC: VOLTAR", True, SHIFT_WHITE)
        tela.blit(dica, (painel.x + 35, painel.bottom - 50))

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
        ids = self._ids()
        layout = self.menu.layout
        painel_y = layout.y(0.10)
        indice = self.inicio + (pos[1] - painel_y - 105) // 46
        if 0 <= indice < len(ids) and 0 <= indice - self.inicio < 8:
            self.selecao = indice
            self.menu.jogo.cutscene_controller.rever(ids[indice])
