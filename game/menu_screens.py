"""Telas independentes do menu legado.

As telas encapsulam o despacho de desenho e entrada de cada subestado. A
logica visual continua em ``MenuPrincipal`` durante a migracao gradual, mas
agora cada fluxo tem um ponto de extensao proprio e testavel.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame

    from .menu import MenuPrincipal


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
        self.menu._desenhar_menu(tela)

    def tratar_tecla(self, evento: pygame.event.Event) -> bool:
        return self.menu._tecla_menu_principal(evento)

    def tratar_clique(self, pos: tuple[int, int]) -> None:
        self.menu._clique_menu_principal(pos)


class TelaContinuar(TelaMenuBase):
    """Tela de continuar ou reiniciar o progresso."""

    nome = "CONTINUAR"

    def desenhar(self, tela: pygame.Surface) -> None:
        self.menu._desenhar_continuar(tela)

    def tratar_tecla(self, evento: pygame.event.Event) -> bool:
        return self.menu._tecla_continuar(evento)

    def tratar_clique(self, pos: tuple[int, int]) -> None:
        self.menu._clique_continuar(pos)


class TelaLoja(TelaMenuBase):
    """Tela de compra e selecao de skins."""

    nome = "LOJA"

    def desenhar(self, tela: pygame.Surface) -> None:
        self.menu._desenhar_loja(tela)

    def tratar_tecla(self, evento: pygame.event.Event) -> bool:
        return self.menu._tecla_loja(evento)

    def tratar_clique(self, pos: tuple[int, int]) -> None:
        self.menu._clique_loja(pos)


class TelaRecordes(TelaMenuBase):
    """Tela de recordes."""

    nome = "RECORDES"

    def desenhar(self, tela: pygame.Surface) -> None:
        self.menu._desenhar_recordes(tela)

    def tratar_tecla(self, evento: pygame.event.Event) -> bool:
        return self.menu._tecla_recordes(evento)

    def tratar_clique(self, pos: tuple[int, int]) -> None:
        self.menu._clique_recordes(pos)


class TelaConfiguracoes(TelaMenuBase):
    """Tela de configuracoes, controles e video."""

    nome = "CONFIG"

    def desenhar(self, tela: pygame.Surface) -> None:
        self.menu._desenhar_config(tela)

    def tratar_tecla(self, evento: pygame.event.Event) -> bool:
        return self.menu._tecla_config(evento)

    def tratar_clique(self, pos: tuple[int, int]) -> None:
        self.menu._clique_config(pos)
