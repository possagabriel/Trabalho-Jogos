"""Tela de continuar partida e reinicializacao de progresso."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import pygame

from src.core.constants import BRANCO
from src.infrastructure.ui.layout import CENTRO, LARGURA_BASE, ALTURA_BASE
from src.legacy.presentation.menu_scene import texto_espacado
from src.legacy.infrastructure.persistence.save_system import ARQUIVO_RECORDES
from src.legacy.infrastructure.persistence.shop import LojaSkins
from src.legacy.infrastructure.graphics.smooth import ease_out
from src.infrastructure.graphics.theme import tema_atual
from src.legacy.presentation.ui import BotaoNeon

if TYPE_CHECKING:
    from src.legacy.presentation.menu import MenuPrincipal

LOGGER = logging.getLogger(__name__)


class TelaContinuarJogo:
    """Implementa desenho e interacoes exclusivas da tela Continuar."""

    def __init__(self, menu: MenuPrincipal) -> None:
        self.menu = menu

    def tem_save(self) -> bool:
        """Informa se existe um save valido para carregar."""
        return self.menu.jogo.progresso.existe_save()

    def botoes(self) -> list[BotaoNeon]:
        """Cria os botoes posicionados para a resolucao atual."""
        layout = self.menu.layout
        largura = layout.px(205)
        centro_x = layout.x(0.5)
        return [
            BotaoNeon("CONTINUAR", (centro_x - largura - layout.px(15),
                                     layout.altura - layout.px(118), largura, layout.px(48))),
            BotaoNeon("NOVO JOGO", (centro_x + layout.px(15),
                                     layout.altura - layout.px(118), largura, layout.px(48))),
            BotaoNeon("VOLTAR", (centro_x - layout.px(90),
                                  layout.altura - layout.px(60), layout.px(180), layout.px(42))),
        ]

    def acao(self, indice: int) -> None:
        """Executa a acao selecionada pelo jogador."""
        menu = self.menu
        if indice == 0:
            if self.tem_save():
                menu._iniciar_missao(menu.jogo._preparar_jogo)
            else:
                menu._som("erro")
                menu.notificacoes.adicionar("Nenhum save encontrado!", "erro")
        elif indice == 1:
            menu._mostrar_dialogo(
                "Novo Jogo",
                "Isso apagara seu progresso (moedas, skins e recordes). Continuar?",
                self.resetar_e_jogar,
                lambda: None,
            )
        else:
            menu._voltar_menu()

    def resetar_e_jogar(self) -> None:
        """Remove o progresso existente e inicia uma nova missao."""
        menu = self.menu
        menu.jogo.progresso.resetar_progresso()
        try:
            if os.path.exists(ARQUIVO_RECORDES):
                os.remove(ARQUIVO_RECORDES)
        except OSError as erro:
            LOGGER.warning("Nao foi possivel apagar os recordes: %s", erro)
        menu.jogo.loja = LojaSkins()
        menu.jogo.progresso.sincronizar_loja(menu.jogo.loja)
        menu.jogo.progresso.salvar_arquivo()
        menu.jogo.recordes = []
        menu.jogo.nome_jogador = "Jogador"
        menu.notificacoes.adicionar("Progresso reiniciado!", "sucesso")
        menu._som("comprar")
        menu._iniciar_missao(menu.jogo._preparar_jogo)

    def desenhar(self, tela: pygame.Surface) -> None:
        """Renderiza a tela e o resumo do save existente."""
        menu = self.menu
        layout = menu.layout
        tema = tema_atual(menu.jogo.config["tema"])
        menu._cabecalho_sub_animado(tela, "CARREGANDO JOGO", tema["secundaria"])
        tem = self.tem_save()
        painel = layout.rect(CENTRO, 520 / LARGURA_BASE, 330 / ALTURA_BASE, dy=-35)
        menu._painel_sub(tela, painel, tema)
        menu._detalhe_painel(tela, painel, tema, tema["secundaria"])
        jogador = menu.jogo.progresso.jogador
        cor_titulo = (150, 230, 120) if tem else (230, 120, 120)
        dx, dy, alfa = menu._entrada_anim(menu._frac_sub(0.14, 0.3), dy_design=-14)
        titulo = "SAVE ENCONTRADO" if tem else "NENHUM SAVE"
        superficie = menu.fonte_media.render(titulo, True, cor_titulo)
        menu._blit_alfa(tela, superficie, superficie.get_rect(
            center=(painel.centerx + dx, painel.y + layout.px(28) + dy)), int(255 * alfa))
        if tem:
            skin = menu.jogo.loja.pegar_skin(jogador["skin_atual"])
            linhas = [
                ("Jogador", jogador["nome"]), ("Nivel", str(jogador["nivel_maximo"])),
                ("Pontos totais", f"{jogador['total_pontos']:,}".replace(",", ".")),
                ("Bosses", str(jogador["bosses_derrotados"])),
                ("Moedas", f"{jogador['moedas']:,}".replace(",", ".")),
                ("Skin", skin.nome), ("Cenarios", f"{len(jogador['cenarios_desbloqueados'])}/6"),
            ]
            y = painel.y + layout.px(62)
            for indice, (rotulo, valor) in enumerate(linhas):
                dx, dy, alfa = menu._entrada_anim(menu._frac_sub(0.20 + indice * 0.05, 0.35), dx_design=-30)
                rotulo_surf = menu.fonte_media.render(f"{rotulo}:", True, (170, 175, 225))
                menu._blit_alfa(tela, rotulo_surf, (painel.x + layout.px(70) + dx, y + dy), int(255 * alfa))
                valor_surf = menu.fonte_media.render(valor, True, BRANCO)
                menu._blit_alfa(tela, valor_surf, valor_surf.get_rect(
                    midleft=(painel.x + layout.px(250) + dx, y + layout.px(9) + dy)), int(255 * alfa))
                y += layout.px(36)
        else:
            dx, dy, alfa = menu._entrada_anim(menu._frac_sub(0.2, 0.35), dx_design=-20)
            superficie = menu.fonte_media.render("Nenhum progresso salvo ainda.", True, (200, 200, 240))
            menu._blit_alfa(tela, superficie, superficie.get_rect(
                center=(painel.centerx + dx, painel.centery + dy)), int(255 * alfa))
        for indice, botao in enumerate(self.botoes()):
            botao.atualizar(menu.mouse)
            menu._desenhar_botao_entrada(tela, botao, menu.fonte_media,
                                         menu._frac_sub(0.55 + indice * 0.06, 0.3))
        if menu.continuar_selecao < 2:
            pygame.draw.rect(tela, (255, 200, 100), self.botoes()[menu.continuar_selecao].rect, 3,
                             border_radius=10)
