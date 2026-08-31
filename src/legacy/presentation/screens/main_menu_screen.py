"""Tela principal do menu e suas interacoes diretas."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.legacy.infrastructure.graphics.smooth import ease_out
from src.infrastructure.graphics.theme import tema_atual

if TYPE_CHECKING:
    from src.legacy.presentation.menu import MenuPrincipal


class TelaPrincipalJogo:
    """Renderiza e controla exclusivamente a tela inicial do menu."""

    def __init__(self, menu: MenuPrincipal) -> None:
        self.menu = menu

    def desenhar(self, tela: pygame.Surface) -> None:
        """Desenha titulo, opcoes e rodape da tela inicial."""
        menu = self.menu
        tema = tema_atual(menu.jogo.config["tema"])
        menu._desenhar_linhas_diagonais(tela, tema)
        menu._desenhar_bloco_titulo(tela, tema)
        progresso = menu._frac(0.28, 0.3)
        if progresso > 0:
            rotulo = menu._espacado(menu.fonte_pequena, "// COMANDO DE VOO", 2,
                                    tema["secundaria"])
            menu._blit_alfa(tela, rotulo, (menu.x_opcoes, menu.layout.px(132)),
                            int(255 * ease_out(progresso)))
        if menu.entrada_t > 0.25:
            menu.destaque.desenhar(tela, menu.x_opcoes - menu.layout.px(32), tema)
        for indice, opcao in enumerate(menu.opcoes):
            progresso = menu._frac(0.34 + indice * 0.07, 0.42)
            deslocamento = int((1 - ease_out(progresso)) * 150)
            opcao.desenhar(tela, menu.fonte_opcao, menu.fonte_opcao_sel, tema,
                           menu.x_opcoes, indice == menu.opcao_selecionada,
                           deslocamento, int(255 * ease_out(progresso)), menu.layout)
        menu._desenhar_seta(tela, tema)
        menu._desenhar_rodape(tela, tema)

    def tratar_tecla(self, evento: pygame.event.Event) -> bool:
        """Trata navegacao e digitacao do nome do jogador."""
        menu = self.menu
        if evento.key in (pygame.K_UP, pygame.K_w):
            menu._selecionar((menu.opcao_selecionada - 1) % len(menu.opcoes))
        elif evento.key in (pygame.K_DOWN, pygame.K_s):
            menu._selecionar((menu.opcao_selecionada + 1) % len(menu.opcoes))
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            menu.opcoes[menu.opcao_selecionada].funcao()
        elif evento.key == pygame.K_BACKSPACE:
            menu.jogo.nome_jogador = menu.jogo.nome_jogador[:-1]
        elif evento.key == pygame.K_ESCAPE:
            menu._sair()
        elif evento.unicode and evento.unicode.isprintable() and len(menu.jogo.nome_jogador) < 12:
            menu.jogo.nome_jogador += evento.unicode
        return True

    def tratar_clique(self, pos: tuple[int, int]) -> None:
        """Seleciona e dispara a opcao clicada."""
        menu = self.menu
        for indice, opcao in enumerate(menu.opcoes):
            if opcao.get_rect(menu.x_opcoes, menu.fonte_opcao, menu.layout).collidepoint(pos):
                menu._selecionar(indice)
                opcao.funcao()
                return
