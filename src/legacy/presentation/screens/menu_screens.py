"""Telas independentes do menu legado.

As telas encapsulam o despacho de desenho e entrada de cada subestado. A
logica visual continua em ``MenuPrincipal`` durante a migracao gradual, mas
agora cada fluxo tem um ponto de extensao proprio e testavel.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from src.legacy.presentation.menu import MenuPrincipal


class TelaMenuBase:
    """Contrato comum para uma tela do menu."""

    nome: str

    def __init__(self, menu: MenuPrincipal) -> None:
        self.menu = menu

    def desenhar(self, tela: pygame.Surface) -> None:
        """Desenha a tela na superficie logica."""
        raise NotImplementedError

    def tratar_tecla(self, evento: pygame.event.Event) -> bool:
        """Trata uma tecla e informa se o jogo deve continuar aberto."""
        return True

    def tratar_clique(self, pos: tuple[int, int]) -> None:
        """Trata um clique nas coordenadas logicas."""


class TelaPrincipal(TelaMenuBase):
    """Tela inicial do menu."""

    nome = "MENU"

    def desenhar(self, tela: pygame.Surface) -> None:
        self.menu.tela_principal.desenhar(tela)

    def tratar_tecla(self, evento: pygame.event.Event) -> bool:
        return self.menu.tela_principal.tratar_tecla(evento)

    def tratar_clique(self, pos: tuple[int, int]) -> None:
        self.menu.tela_principal.tratar_clique(pos)


class TelaContinuar(TelaMenuBase):
    """Tela de continuar ou reiniciar o progresso."""

    nome = "CONTINUAR"

    def desenhar(self, tela: pygame.Surface) -> None:
        self.menu.tela_continuar.desenhar(tela)

    def tratar_tecla(self, evento: pygame.event.Event) -> bool:
        if evento.key in (pygame.K_UP, pygame.K_DOWN):
            self.menu.continuar_selecao = 1 - self.menu.continuar_selecao
            self.menu._som("navegar")
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.menu.tela_continuar.acao(self.menu.continuar_selecao)
        elif evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.menu._voltar_menu()
        return True

    def tratar_clique(self, pos: tuple[int, int]) -> None:
        for indice, botao in enumerate(self.menu.tela_continuar.botoes()):
            if botao.rect.collidepoint(pos):
                self.menu.tela_continuar.acao(indice)
                return


class TelaLoja(TelaMenuBase):
    """Tela de compra e selecao de skins."""

    nome = "LOJA"

    def desenhar(self, tela: pygame.Surface) -> None:
        self.menu.tela_loja.desenhar(tela)

    def tratar_tecla(self, evento: pygame.event.Event) -> bool:
        return self.menu.tela_loja.tratar_tecla(evento)

    def tratar_clique(self, pos: tuple[int, int]) -> None:
        self.menu.tela_loja.tratar_clique(pos)


class TelaRecordes(TelaMenuBase):
    """Tela de recordes."""

    nome = "RECORDES"

    def desenhar(self, tela: pygame.Surface) -> None:
        self.menu.tela_recordes.desenhar(tela)

    def tratar_tecla(self, evento: pygame.event.Event) -> bool:
        return self.menu._tecla_recordes(evento)

    def tratar_clique(self, pos: tuple[int, int]) -> None:
        if self.menu.tela_recordes.botao_voltar().rect.collidepoint(pos):
            self.menu._voltar_menu()


class TelaConfiguracoes(TelaMenuBase):
    """Tela de configuracoes, controles e video."""

    nome = "CONFIG"

    def desenhar(self, tela: pygame.Surface) -> None:
        self.menu.tela_configuracoes.desenhar(tela)

    def tratar_tecla(self, evento: pygame.event.Event) -> bool:
        return self.menu.tela_configuracoes.tratar_tecla(evento)

    def tratar_clique(self, pos: tuple[int, int]) -> None:
        self.menu.tela_configuracoes.tratar_clique(pos)
