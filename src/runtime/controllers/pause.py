"""Interacao e transicoes da pausa durante a partida."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.core.constants import ALTURA, LARGURA
from src.runtime.presentation.menu import Dialogo
from src.core.settings import TEMAS

if TYPE_CHECKING:
    from src.runtime.application.core import Jogo


class ControladorPausa:
    """Mantem a navegacao da pausa fora do controlador central ``Jogo``."""

    def __init__(self, jogo: Jogo) -> None:
        self.jogo = jogo

    def tratar_evento(self, evento: pygame.event.Event) -> None:
        """Encaminha a entrada para a pausa, seu dialogo ou configuracoes."""
        jogo = self.jogo
        if jogo._pausa_dialogo and jogo._pausa_dialogo.ativo:
            jogo._pausa_dialogo.tratar_evento(evento, mouse_pos=jogo._pausa_mouse)
            if not jogo._pausa_dialogo.ativo:
                jogo._pausa_dialogo = None
            return
        if jogo._pausa_mostrando_config:
            self.tratar_evento_config(evento)
            return
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_p, pygame.K_ESCAPE):
                jogo.estado = "JOGANDO"
            elif evento.key == pygame.K_m:
                self.sair_para_menu()
            elif evento.key == pygame.K_UP:
                jogo._pausa_selecao = (jogo._pausa_selecao - 1) % 3
            elif evento.key == pygame.K_DOWN:
                jogo._pausa_selecao = (jogo._pausa_selecao + 1) % 3
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.executar_acao(jogo._pausa_selecao)
        elif evento.type == pygame.MOUSEMOTION:
            jogo._pausa_mouse = evento.pos
            self.atualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.colidir_opcao(evento.pos) is not None:
                self.executar_acao(jogo._pausa_selecao)

    def tratar_evento_config(self, evento: pygame.event.Event) -> None:
        """Trata a navegacao do subpainel de configuracoes da pausa."""
        jogo = self.jogo
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                jogo._pausa_mostrando_config = False
            elif evento.key == pygame.K_UP:
                jogo._pausa_config_selecao = (jogo._pausa_config_selecao - 1) % 4
            elif evento.key == pygame.K_DOWN:
                jogo._pausa_config_selecao = (jogo._pausa_config_selecao + 1) % 4
            elif evento.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.ajustar_config(jogo._pausa_config_selecao,
                                    1 if evento.key == pygame.K_RIGHT else -1)
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self.clique_config(evento.pos)

    def ajustar_config(self, indice: int, delta: int) -> None:
        """Altera uma configuracao disponivel na pausa e a persiste."""
        jogo = self.jogo
        if indice == 0:
            valor = max(0.0, min(1.0, jogo.config["musica_volume"] + delta * 0.05))
            jogo.config["musica_volume"] = round(valor, 2)
            jogo.sons.set_volume_musica(valor)
        elif indice == 1:
            valor = max(0.0, min(1.0, jogo.config["efeitos_volume"] + delta * 0.05))
            jogo.config["efeitos_volume"] = round(valor, 2)
            jogo.sons.set_volume_efeitos(valor)
        elif indice == 2:
            atual = jogo.config["tema"]
            indice_tema = TEMAS.index(atual) if atual in TEMAS else 0
            jogo.config["tema"] = TEMAS[(indice_tema + delta) % len(TEMAS)]
        elif indice == 3 and delta > 0:
            jogo.config["tela_cheia"] = not jogo.config["tela_cheia"]
            jogo._aplicar_modo_video()
        jogo.config.salvar()

    def clique_config(self, pos: tuple[int, int]) -> None:
        """Aplica a configuracao ou acao selecionada pelo mouse."""
        jogo = self.jogo
        painel = pygame.Rect(LARGURA // 2 - 270, ALTURA // 2 - 215, 540, 430)
        for indice in range(4):
            linha = pygame.Rect(painel.x + 24, painel.y + 70 + indice * 70, 492, 44)
            if linha.collidepoint(pos):
                jogo._pausa_config_selecao = indice
                self.ajustar_config(indice, 1)
                return
        if pygame.Rect(painel.x + 30, painel.bottom - 56, 150, 42).collidepoint(pos):
            jogo._pausa_mostrando_config = False
        elif pygame.Rect(painel.right - 180, painel.bottom - 56, 150, 42).collidepoint(pos):
            jogo.config["musica_volume"] = 0.8
            jogo.config["efeitos_volume"] = 0.8
            jogo.config["tema"] = "NEON"
            jogo.config["tela_cheia"] = False
            jogo.config.salvar()
            jogo.sons.set_volume_musica(0.8)
            jogo.sons.set_volume_efeitos(0.8)
            jogo._aplicar_modo_video()

    def colidir_opcao(self, pos: tuple[int, int]) -> int | None:
        """Retorna a opcao da pausa posicionada sob o cursor."""
        painel = pygame.Rect(LARGURA // 2 - 220, ALTURA // 2 - 210, 440, 420)
        for indice in range(3):
            botao = pygame.Rect(LARGURA // 2 - 160, painel.y + 118 + indice * 74, 320, 54)
            if botao.collidepoint(pos):
                return indice
        return None

    def atualizar_hover(self, pos: tuple[int, int]) -> None:
        """Sincroniza a selecao visual da pausa com o cursor."""
        indice = self.colidir_opcao(pos)
        if indice is not None:
            self.jogo._pausa_selecao = indice

    def executar_acao(self, indice: int) -> None:
        """Executa a opcao selecionada no menu de pausa."""
        jogo = self.jogo
        if indice == 0:
            jogo.estado = "JOGANDO"
        elif indice == 1:
            jogo._pausa_mostrando_config = True
            jogo._pausa_config_selecao = 0
        elif indice == 2:
            self.sair_para_menu()

    def sair_para_menu(self) -> None:
        """Pede confirmacao antes de abandonar a missao ativa."""
        jogo = self.jogo
        jogo._pausa_dialogo = Dialogo(
            "Sair da Missao",
            "Tem certeza que deseja voltar ao menu? O progresso desta sessao sera salvo.",
            self.confirmar_saida, lambda: None)

    def confirmar_saida(self) -> None:
        """Salva a sessao e retorna ao menu principal."""
        jogo = self.jogo
        jogo.estado = "MENU"
        jogo.fade = 255
        jogo._salvar_tudo()
