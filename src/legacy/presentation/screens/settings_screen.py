"""Renderizacao e entrada da tela de configuracoes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.core.constants import BRANCO, QUANTUM_CYAN, VERDE
from src.infrastructure.graphics.theme import tema_atual
from src.legacy.presentation.ui import BotaoNeon
from src.core.settings import ACOES_CONTROLE, RESOLUCOES

if TYPE_CHECKING:
    from src.legacy.presentation.menu import MenuPrincipal


class TelaConfiguracoesJogo:
    """Coordena a apresentacao dos submodos de configuracao."""

    def __init__(self, menu: MenuPrincipal) -> None:
        self.menu = menu

    def desenhar(self, tela: pygame.Surface) -> None:
        """Renderiza configuracoes gerais ou encaminha para o submodo ativo."""
        menu = self.menu
        layout = menu.layout
        tema = tema_atual(menu.jogo.config["tema"])
        menu._cabecalho_sub_animado(tela, "CONFIGURACOES", tema["primaria"])
        if menu.remapando:
            menu._desenhar_remapando(tela)
            return
        if menu.config_submodo == "controles":
            menu._desenhar_controles(tela)
            return
        if menu.config_submodo == "resolucao":
            menu._desenhar_resolucoes(tela)
            return
        if menu.config_submodo == "ajuste":
            menu._desenhar_ajuste(tela)
            return
        painel = menu._painel_config()
        menu._painel_sub(tela, painel, tema)
        menu._detalhe_painel(tela, painel, tema, tema["secundaria"])
        linhas = menu._linhas_config()
        inicio, fim = menu._config_visiveis()
        for deslocamento in range(fim - inicio):
            indice = inicio + deslocamento
            rotulo, tipo = linhas[indice]
            progresso = menu._frac_sub(0.12 + deslocamento * 0.05, 0.35)
            dx, dy, alfa = menu._entrada_anim(progresso, dx_design=30, dy_design=18)
            y = menu._y_linha_config(deslocamento) + dy
            selecionada = indice == menu.config_selecao
            texto = menu.fonte_media.render(rotulo, True, BRANCO if selecionada else (190, 195, 235))
            menu._blit_alfa(tela, texto, (layout.px(190) + dx, y - layout.px(12)), int(255 * alfa))
            if selecionada:
                pygame.draw.rect(tela, (255, 200, 100),
                                 (layout.px(175) + dx, y - layout.px(24), layout.px(6), layout.px(30)),
                                 border_radius=3)
            self._desenhar_valor(tela, indice, tipo, y, dx, alfa, tema)
        if len(linhas) > menu._CONFIG_VISIVEIS:
            menu._desenhar_indicador_config(tela, painel, inicio, fim)
        for indice, botao in enumerate((
            BotaoNeon("SALVAR", (layout.x(0.5) - layout.px(190), layout.altura - layout.px(80), layout.px(180), layout.px(44))),
            BotaoNeon("VOLTAR", (layout.x(0.5) + layout.px(10), layout.altura - layout.px(80), layout.px(180), layout.px(44))),
        )):
            botao.atualizar(menu.mouse)
            menu._desenhar_botao_entrada(tela, botao, menu.fonte_media, menu._frac_sub(0.62 + indice * 0.06, 0.25))

    def tratar_tecla(self, evento: pygame.event.Event) -> bool:
        """Trata navegacao e abertura dos submodos de configuracao."""
        menu = self.menu
        if menu.config_submodo == "controles":
            if evento.key == pygame.K_ESCAPE:
                menu.config_submodo, menu.sub_anim = None, 0.0
            elif evento.key in (pygame.K_UP, pygame.K_DOWN):
                passo = 1 if evento.key == pygame.K_DOWN else -1
                menu.controle_selecao = (menu.controle_selecao + passo) % len(ACOES_CONTROLE)
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                menu.remapando = ACOES_CONTROLE[menu.controle_selecao]
            else:
                return True
            menu._som("navegar")
            return True
        if menu.config_submodo == "resolucao":
            if evento.key == pygame.K_ESCAPE:
                menu.config_submodo, menu.sub_anim = None, 0.0
            elif evento.key in (pygame.K_UP, pygame.K_DOWN):
                passo = 1 if evento.key == pygame.K_DOWN else -1
                menu.resolucao_selecao = (menu.resolucao_selecao + passo) % len(RESOLUCOES)
                menu._rolar_resolucao(menu.resolucao_selecao)
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                menu._aplicar_resolucao(menu.resolucao_selecao)
            else:
                return True
            menu._som("navegar")
            return True
        if menu.config_submodo == "ajuste":
            return menu._tecla_ajuste(evento)
        quantidade = len(menu._linhas_config())
        if evento.key in (pygame.K_UP, pygame.K_w):
            menu.config_selecao = (menu.config_selecao - 1) % quantidade
            menu._rolar_config(menu.config_selecao)
        elif evento.key in (pygame.K_DOWN, pygame.K_s):
            menu.config_selecao = (menu.config_selecao + 1) % quantidade
            menu._rolar_config(menu.config_selecao)
        elif evento.key == pygame.K_LEFT:
            menu._ajustar_config(-1)
            return True
        elif evento.key == pygame.K_RIGHT:
            menu._ajustar_config(1)
            return True
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._abrir_selecao()
            return True
        elif evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            menu._voltar_menu()
            return True
        else:
            return True
        menu._som("navegar")
        return True

    def _abrir_selecao(self) -> None:
        """Abre ou ajusta o controle atualmente selecionado."""
        menu = self.menu
        if menu.config_selecao == 2:
            menu.config_submodo, menu.resolucao_selecao, menu.sub_anim = "resolucao", menu._indice_resolucao_atual(), 0.0
        elif menu.config_selecao == 5:
            menu.config_submodo, menu.controle_selecao, menu.sub_anim = "controles", 0, 0.0
        elif menu.config_selecao == 8:
            menu._abrir_ajuste_tela()
        else:
            menu._ajustar_config(1)

    def tratar_clique(self, pos: tuple[int, int]) -> None:
        """Trata cliques nos controles e acoes da tela."""
        menu, layout = self.menu, self.menu.layout
        if menu.remapando:
            return
        if menu.config_submodo == "resolucao":
            menu._clique_resolucao(pos)
            return
        if menu.config_submodo == "controles":
            painel = menu._painel_controles()
            for indice, acao in enumerate(ACOES_CONTROLE):
                rect = pygame.Rect(painel.x + layout.px(30), painel.y + layout.px(64) + indice * layout.px(48),
                                   painel.width - layout.px(60), layout.px(40))
                if rect.collidepoint(pos):
                    menu.controle_selecao, menu.remapando = indice, acao
                    menu._som("navegar")
                    return
            return
        inicio, fim = menu._config_visiveis()
        linhas = menu._linhas_config()
        for deslocamento in range(fim - inicio):
            indice = inicio + deslocamento
            if abs(pos[1] - menu._y_linha_config(deslocamento)) >= 24:
                continue
            menu.config_selecao = indice
            if linhas[indice][1] == "slider":
                menu._aplicar_slider(indice, menu._slider_fracao(pos[0]))
            else:
                self._abrir_selecao()
            return
        salvar = pygame.Rect(layout.x(0.5) - layout.px(190), layout.altura - layout.px(80), layout.px(180), layout.px(44))
        if salvar.collidepoint(pos):
            menu.jogo.config.salvar()
            menu.notificacoes.adicionar("Configuracoes salvas!", "sucesso")
            menu._som("equipar")

    def _desenhar_valor(self, tela, indice, tipo, y, dx, alfa, tema) -> None:
        """Desenha o controle correspondente a uma linha de configuracao."""
        menu, layout = self.menu, self.menu.layout
        if tipo == "slider":
            chave = "sensibilidade" if indice == 4 else ("musica_volume" if indice == 0 else "efeitos_volume")
            fracao = max(0.0, min(1.0, menu.jogo.config[chave] - 0.5 if indice == 4 else menu.jogo.config[chave]))
            menu._desenhar_slider(tela, y, fracao)
            percentual = int((0.5 + fracao) * 100) if indice == 4 else int(fracao * 100)
            texto = menu.fonte_media.render(f"{percentual}%", True, (170, 175, 220))
            menu._blit_alfa(tela, texto, (layout.px(720) + dx, y - layout.px(12)), int(255 * alfa))
        elif tipo == "toggle":
            estado = menu.jogo.config["tela_cheia"]
            menu._desenhar_toggle(tela, layout.px(420) + dx, y, estado)
            texto = menu.fonte_media.render("LIGADO" if estado else "DESLIGADO", True, VERDE if estado else (160, 160, 190))
            menu._blit_alfa(tela, texto, texto.get_rect(midleft=(layout.px(510) + dx, y)), int(255 * alfa))
        else:
            valores = {"resolucao": menu.jogo.config["resolucao"], "tema": menu.jogo.config["tema"],
                       "aspecto": menu.jogo.config["aspecto"], "controles": "PERSONALIZAR >", "ajuste": "CALIBRAR >"}
            valor = valores.get(tipo, "")
            cor = tema["secundaria"] if tipo == "resolucao" else QUANTUM_CYAN if tipo == "aspecto" else (200, 150, 255)
            texto = menu.fonte_media.render(valor, True, cor)
            menu._blit_alfa(tela, texto, texto.get_rect(midleft=(layout.px(420) + dx, y)), int(255 * alfa))
