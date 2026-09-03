"""Interacoes exclusivas da tela de loja de skins."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.core.constants import DOURADO
from src.infrastructure.graphics.theme import tema_atual

if TYPE_CHECKING:
    from src.runtime.presentation.menu import MenuPrincipal


class TelaLojaJogo:
    """Controla selecao, compra, equipagem e preview de skins."""

    def __init__(self, menu: MenuPrincipal) -> None:
        self.menu = menu

    def tratar_tecla(self, evento: pygame.event.Event) -> bool:
        """Trata navegacao da grade e acoes sobre a skin selecionada."""
        menu = self.menu
        if menu.preview_skin:
            if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.acao("equipar")
                menu.preview_skin = None
            elif evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                menu.preview_skin = None
                menu._som("navegar")
            return True
        total = len(menu.jogo.loja.skins)
        if evento.key in (pygame.K_LEFT, pygame.K_a):
            menu.loja_selecao = max(0, menu.loja_selecao - 1)
        elif evento.key in (pygame.K_RIGHT, pygame.K_d):
            menu.loja_selecao = min(total - 1, menu.loja_selecao + 1)
        elif evento.key in (pygame.K_UP, pygame.K_w):
            menu.loja_selecao = max(0, menu.loja_selecao - 4)
        elif evento.key in (pygame.K_DOWN, pygame.K_s):
            menu.loja_selecao = min(total - 1, menu.loja_selecao + 4)
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.acao_principal()
            return True
        elif evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            menu._voltar_menu()
            return True
        else:
            return True
        menu._som("navegar")
        return True

    def desenhar(self, tela: pygame.Surface) -> None:
        """Renderiza o cabecalho, cards, acoes e preview da loja."""
        menu = self.menu
        layout = menu.layout
        tema = tema_atual(menu.jogo.config["tema"])
        menu._cabecalho_sub_animado(tela, "LOJA DE VISUAIS", tema["primaria"])
        dx, dy, alfa = menu._entrada_anim(menu._frac_sub(0.06, 0.3), dx_design=-16)
        moeda = menu.fonte_media.render(f"Moedas: {menu.jogo.loja.moedas:,}".replace(",", "."), True, DOURADO)
        menu._blit_alfa(tela, moeda, (layout.px(20) + dx, layout.px(30) + dy), int(255 * alfa))
        atual = menu.jogo.loja.pegar_skin(menu.jogo.loja.skin_atual)
        skin_atual = menu.fonte_media.render(f"Visual atual: {atual.nome}", True, tema["secundaria"])
        menu._blit_alfa(tela, skin_atual, skin_atual.get_rect(
            topright=(layout.largura - layout.px(20) - dx, layout.px(30) + dy)), int(255 * alfa))
        total = len(menu.jogo.loja.skins)
        desbloqueadas = len(menu.jogo.loja.lista_desbloqueadas())
        resumo = menu.fonte_pequena.render(f"{desbloqueadas}/{total} visuais desbloqueados", True, (150, 155, 200))
        menu._blit_alfa(tela, resumo, resumo.get_rect(
            topright=(layout.largura - layout.px(20), layout.px(56))), int(255 * alfa))
        cards = menu._rects_loja()
        for indice, skin in enumerate(menu.jogo.loja.skins):
            entrada = menu._frac_sub(0.16 + (indice % 4) * 0.05 + (indice // 4) * 0.09, 0.35)
            menu._desenhar_cartao_skin(tela, cards[indice], skin, indice == menu.loja_selecao,
                                       cards[indice].collidepoint(menu.mouse), tema, entrada)
        for indice, botao in enumerate(menu._botoes_loja().values()):
            botao.atualizar(menu.mouse)
            menu._desenhar_botao_entrada(tela, botao, menu.fonte_media,
                                         menu._frac_sub(0.6 + indice * 0.05, 0.25))
        selecionada = menu.jogo.loja.skins[menu.loja_selecao]
        dx, dy, alfa = menu._entrada_anim(menu._frac_sub(0.62, 0.25), dy_design=16)
        descricao = menu.fonte_pequena.render(selecionada.descricao, True, (170, 175, 220))
        menu._blit_alfa(tela, descricao, descricao.get_rect(
            center=(layout.x(0.5) + dx, layout.altura - layout.px(36) + dy)), int(255 * alfa))
        if menu.preview_skin:
            menu._desenhar_preview_overlay(tela)

    def acao_principal(self) -> None:
        """Compra, equipa ou abre preview conforme o estado da skin."""
        menu = self.menu
        skin = menu.jogo.loja.skins[menu.loja_selecao]
        self.acao("comprar" if not skin.desbloqueada else
                  "preview" if skin.id == menu.jogo.loja.skin_atual else "equipar")

    def acao(self, nome: str) -> None:
        """Executa uma acao explicita da loja."""
        menu = self.menu
        loja = menu.jogo.loja
        skin = loja.skins[menu.loja_selecao]
        if nome == "comprar":
            sucesso, _ = loja.comprar_skin(menu.loja_selecao)
            menu.notificacoes.adicionar(
                f"Visual {skin.nome} comprado!" if sucesso else "Moedas insuficientes!",
                "sucesso" if sucesso else "erro")
            menu._som("comprar" if sucesso else "erro")
            if sucesso:
                menu.jogo._salvar_tudo()
        elif nome == "equipar" and skin.desbloqueada:
            loja.equipar_skin(menu.loja_selecao)
            menu.notificacoes.adicionar(f"Visual {skin.nome} equipado!", "sucesso")
            menu._som("equipar")
            menu.jogo._salvar_tudo()
        elif nome == "preview":
            menu.preview_skin, menu.preview_anim = skin, 0.0
            menu._som("navegar")
        elif nome == "voltar":
            menu._voltar_menu()

    def tratar_clique(self, pos: tuple[int, int]) -> None:
        """Trata clique em card, acao ou fechamento do preview."""
        menu = self.menu
        if menu.preview_skin:
            layout = menu.layout
            equipar = pygame.Rect(layout.x(0.5) - layout.px(170), layout.altura - layout.px(120),
                                  layout.px(160), layout.px(48))
            fechar = pygame.Rect(layout.x(0.5) + layout.px(10), layout.altura - layout.px(120),
                                 layout.px(160), layout.px(48))
            if equipar.collidepoint(pos):
                self.acao("equipar")
                menu.preview_skin = None
            elif fechar.collidepoint(pos):
                menu.preview_skin = None
                menu._som("navegar")
            return
        for indice, rect in enumerate(menu._rects_loja()):
            if rect.collidepoint(pos):
                menu.loja_selecao = indice
                return
        for nome, botao in menu._botoes_loja().items():
            if botao.rect.collidepoint(pos):
                self.acao(nome)
                return
