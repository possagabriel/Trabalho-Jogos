"""Tela de recordes e resumo persistido do jogador."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.core.constants import DOURADO
from src.infrastructure.ui.layout import CENTRO, LARGURA_BASE, ALTURA_BASE
from src.infrastructure.graphics.theme import tema_atual
from src.runtime.presentation.ui import BotaoNeon

if TYPE_CHECKING:
    from src.runtime.presentation.menu import MenuPrincipal


class TelaRecordesJogo:
    """Implementa a apresentacao dos recordes e estatisticas."""

    def __init__(self, menu: MenuPrincipal) -> None:
        self.menu = menu

    def botao_voltar(self) -> BotaoNeon:
        """Cria o botao de retorno ao menu principal."""
        layout = self.menu.layout
        return BotaoNeon("VOLTAR", (layout.x(0.5) - layout.px(90),
                                    layout.altura - layout.px(64), layout.px(180), layout.px(46)))

    def desenhar(self, tela: pygame.Surface) -> None:
        """Renderiza recordes, estatisticas e retorno."""
        menu = self.menu
        layout = menu.layout
        tema = tema_atual(menu.jogo.config["tema"])
        menu._cabecalho_sub_animado(tela, "RECORDES", tema["secundaria"])
        lista = menu.jogo.recordes
        painel = layout.rect(CENTRO, 520 / LARGURA_BASE, 330 / ALTURA_BASE, dy=-35)
        menu._painel_sub(tela, painel, tema)
        menu._detalhe_painel(tela, painel, tema, DOURADO)
        dx, dy, alfa = menu._entrada_anim(menu._frac_sub(0.12, 0.3), dy_design=-10)
        superficie = menu.fonte_media.render("TOP 5", True, tema["secundaria"])
        menu._blit_alfa(tela, superficie, superficie.get_rect(
            center=(painel.centerx + dx, painel.y + layout.px(28) + dy)), int(255 * alfa))
        if not lista:
            dx, dy, alfa = menu._entrada_anim(menu._frac_sub(0.2, 0.35), dx_design=-18)
            superficie = menu.fonte_media.render("Nenhum recorde ainda.", True, (200, 205, 240))
            menu._blit_alfa(tela, superficie, superficie.get_rect(
                center=(painel.centerx + dx, painel.centery + dy)), int(255 * alfa))
        else:
            y = painel.y + layout.px(70)
            for indice, registro in enumerate(lista[:5]):
                dx, dy, alfa = menu._entrada_anim(menu._frac_sub(0.2 + indice * 0.06, 0.35), dx_design=-40)
                cor = DOURADO if indice == 0 else (205, 210, 235) if indice < 3 else (150, 155, 190)
                texto = (f"TOP {indice + 1}. {registro['nome']}  "
                         f"{registro['pontos']:,}".replace(",", ".") + f" pts  (Nivel {registro['nivel']})")
                superficie = menu.fonte_media.render(texto, True, cor)
                menu._blit_alfa(tela, superficie, superficie.get_rect(
                    center=(painel.centerx + dx, y + dy)), int(255 * alfa))
                y += layout.px(52)
        jogador = menu.jogo.progresso.jogador
        estatisticas = menu.jogo.progresso.dados["estatisticas"]
        melhor = f"{lista[0]['pontos']:,}".replace(",", ".") if lista else "0"
        linha = (f"Seu melhor: {melhor} pts  |  Skins: {len(menu.jogo.loja.lista_desbloqueadas())}/10  |  "
                 f"Inimigos: {estatisticas['inimigos_derrotados']}  |  Bosses: {jogador['bosses_derrotados']}")
        dx, dy, alfa = menu._entrada_anim(menu._frac_sub(0.55, 0.3), dy_design=16)
        superficie = menu.fonte_media.render(linha, True, (170, 175, 220))
        menu._blit_alfa(tela, superficie, superficie.get_rect(
            center=(layout.x(0.5) + dx, layout.y(0.72) + dy)), int(255 * alfa))
        botao = self.botao_voltar()
        botao.atualizar(menu.mouse)
        menu._desenhar_botao_entrada(tela, botao, menu.fonte_media, menu._frac_sub(0.6, 0.25))
