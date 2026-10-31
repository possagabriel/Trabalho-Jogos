"""Tela principal do menu e suas interacoes diretas."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

from src.infrastructure.graphics.comic_theme import opcoes_atuais
from src.infrastructure.graphics.theme import (
    MENU_CARTAO_PERFIL_ALPHA,
    MENU_CARTAO_PERFIL_COR,
    MENU_CARTAO_PERFIL_ESPESSURA,
    MENU_CARTAO_PERFIL_FONT_SIZE,
    MENU_CARTAO_PERFIL_FONT_SIZE_PEQUENA,
    MENU_CARTAO_PERFIL_RECT,
    MENU_CARTAO_PERFIL_RECT_4_3,
    MENU_CARTAO_PERFIL_TEXTO,
    MENU_CARTAO_PERFIL_TEXTO_SECUNDARIO,
    tema_atual,
)
from src.runtime.domain.entities.player import SKINS
from src.runtime.infrastructure.graphics.menu_panels import (
    ACENTO_ORIGINAL,
    TEXTO_ORIGINAL,
    painel_original,
    texto_painel,
)
from src.runtime.infrastructure.graphics.smooth import ease_out

if TYPE_CHECKING:
    from src.runtime.presentation.menu import MenuPrincipal


class TelaPrincipalJogo:
    """Renderiza e controla exclusivamente a tela inicial do menu."""

    def __init__(self, menu: MenuPrincipal) -> None:
        self.menu = menu
        self._card_cache: dict[tuple, pygame.Surface] = {}
        self._text_cache: dict[tuple, pygame.Surface] = {}

    def desenhar(self, tela: pygame.Surface) -> None:
        """Desenha titulo, opcoes e rodape da tela inicial."""
        menu = self.menu
        tema = tema_atual(menu.jogo.config["tema"])
        menu._desenhar_linhas_diagonais(tela, tema)
        menu._desenhar_bloco_titulo(tela, tema)
        for indice, opcao in enumerate(menu.opcoes):
            progresso = menu._frac(0.34 + indice * 0.07, 0.42)
            original = not opcoes_atuais().ativo
            if original and menu.jogo.config["intensidade_flash"] != "NORMAL":
                progresso = 1.0
            deslocamento = int((1 - ease_out(progresso))
                               * menu.layout.px(-12 if original else 18))
            opcao.desabilitado = False
            if indice == 1:
                opcao.novo = bool(menu._novidades("hangar"))
            elif indice == 2:
                opcao.novo = bool(menu._novidades("memorias"))
            else:
                opcao.novo = False
            fonte = (menu.fonte_principal if opcao.principal
                     else menu.fonte_secundaria)
            fonte_sel = (menu.fonte_principal_sel if opcao.principal
                         else menu.fonte_secundaria_sel)
            opcao.desenhar(tela, fonte, fonte_sel, tema,
                           menu.x_opcoes, indice == menu.opcao_selecionada,
                           deslocamento, int(255 * ease_out(progresso)), menu.layout)
        menu._desenhar_seta(tela, tema)
        self._desenhar_cartao_perfil(tela, menu, tema)
        menu._desenhar_rodape(tela, tema)

    def cartao_rect(self) -> tuple[int, int, int, int]:
        """Retorna o retângulo lógico do cartão conforme a proporção da janela."""
        menu = self.menu
        tokens = (MENU_CARTAO_PERFIL_RECT_4_3 if menu._layout_4_3()
                  else MENU_CARTAO_PERFIL_RECT)
        return tuple(menu.layout.px(value) for value in tokens)

    def desenhar_fundo_cartao(self, tela: pygame.Surface, resumo) -> None:
        """Desenha o painel do perfil antes da nave de prévia."""
        rect = pygame.Rect(*self.cartao_rect())
        tema = tema_atual(self.menu.jogo.config["tema"])
        border = tema["secundaria"] if resumo else tema["borda_fraco"]
        if self.menu.jogo.config["estilo_visual"] == "ORIGINAL":
            panel = painel_original(rect.size, MENU_CARTAO_PERFIL_COR,
                                     tuple(border[:3]), alpha=MENU_CARTAO_PERFIL_ALPHA,
                                     raio=self.menu.layout.px(12))
            tela.blit(panel, rect)
            return
        key = (rect.size, tuple(border), tuple(tema["primaria"]))
        panel = self._card_cache.get(key)
        if panel is None:
            panel = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(
                panel, MENU_CARTAO_PERFIL_COR + (MENU_CARTAO_PERFIL_ALPHA,),
                panel.get_rect(), border_radius=self.menu.layout.px(12),
            )
            pygame.draw.rect(
                panel, border, panel.get_rect(), MENU_CARTAO_PERFIL_ESPESSURA,
                border_radius=self.menu.layout.px(12),
            )
            pygame.draw.line(
                panel, tema["primaria"],
                (self.menu.layout.px(16), self.menu.layout.px(35)),
                (rect.width - self.menu.layout.px(16), self.menu.layout.px(35)),
                max(1, self.menu.layout.px(1)),
            )
            self._card_cache[key] = panel
        tela.blit(panel, rect)

    def _text(self, font, text: str, color: tuple[int, int, int]) -> pygame.Surface:
        key = (id(font), text, tuple(color))
        surface = self._text_cache.get(key)
        if surface is None:
            surface = font.render(text, True, color)
            self._text_cache[key] = surface
        return surface

    def _desenhar_cartao_perfil(self, tela, menu, tema) -> None:
        summary = menu.jogo.profile_service.menu_profile_summary()
        rect = pygame.Rect(*self.cartao_rect())
        margin = menu.layout.px(18)
        font = menu.layout.fonte_titulo(MENU_CARTAO_PERFIL_FONT_SIZE)
        font_small = menu.layout.fonte_texto(MENU_CARTAO_PERFIL_FONT_SIZE_PEQUENA)
        if summary is None:
            label = "PERFIL // NENHUM PERFIL ATIVO"
            text = self._text(font, label, MENU_CARTAO_PERFIL_TEXTO_SECUNDARIO)
            tela.blit(text, (rect.x + margin, rect.y + menu.layout.px(36)))
            return

        name = self._truncar_nome(font, summary["name"],
                                  rect.width - menu.layout.px(150))
        cor_titulo = (TEXTO_ORIGINAL if menu.jogo.config["estilo_visual"] == "ORIGINAL"
                      else tema["primaria"])
        title = self._text(font, f"PILOTO // {name}", cor_titulo)
        tela.blit(title, (rect.x + margin, rect.y + menu.layout.px(8)))
        hours, remainder = divmod(summary["play_time"], 3600)
        minutes = remainder // 60
        skin = next((row["nome"] for row in SKINS if row["id"] == summary["skin_id"]),
                    "Padrão")
        lines = (
            f"DIM. MÁXIMA {summary['dimension']} · BOSSES {summary['bosses_defeated']}",
            f"MOEDAS {summary['coins']:,}".replace(",", ".")
            + f" · TEMPO {hours:02d}h{minutes:02d}",
            f"SKIN {skin}",
        )
        for index, line in enumerate(lines):
            color = MENU_CARTAO_PERFIL_TEXTO if index == 0 else MENU_CARTAO_PERFIL_TEXTO_SECUNDARIO
            text = self._text(font_small, line, color)
            tela.blit(text, (rect.x + margin, rect.y + menu.layout.px(42 + index * 22)))

    def desenhar_titulo_original(self, tela: pygame.Surface, superficies: dict) -> None:
        """Compõe a marca à esquerda com tipografia de console e selo orbital."""
        menu, layout = self.menu, self.menu.layout
        reduzido = menu.jogo.config["intensidade_flash"] != "NORMAL"
        p = 1.0 if reduzido else ease_out(menu._frac(0.08, 0.45))
        deslocamento = 0 if reduzido else layout.px((1 - p) * -12)
        flutuar = layout.px(math.sin(menu.animacao_original.tempo * 0.9) * 2)
        selo = pygame.Rect(layout.px(56), layout.px(126), layout.px(330), layout.px(30))
        base = painel_original(selo.size, (0, 0, 0), ACENTO_ORIGINAL)
        menu._blit_alfa(tela, base, selo.topleft, round(p * 255))
        rotulo = texto_painel(layout.fonte_texto(16), "CONSOLE ORBITAL // NAVEGAÇÃO",
                              ACENTO_ORIGINAL, selo.width - layout.px(24), selo.height)
        menu._blit_alfa(tela, rotulo, rotulo.get_rect(center=selo.center).topleft, round(p * 255))
        titulo = self._text(layout.fonte_texto(76), "INCARNATE", TEXTO_ORIGINAL)
        rect = titulo.get_rect(topleft=(layout.px(56), layout.px(165) + deslocamento + flutuar))
        menu._blit_alfa(tela, titulo, rect.topleft, round(p * 255))
        sub = superficies["sub"]
        rect = sub.get_rect(topleft=(layout.px(60), layout.px(292)))
        menu._blit_alfa(tela, sub, rect.topleft, round(p * 255))


    @staticmethod
    def _truncar_nome(font, name: str, max_width: int) -> str:
        """Trunca nome pelo tamanho renderizado e preserva reticências."""
        if font.size(name)[0] <= max_width:
            return name
        prefix = name
        while prefix and font.size(prefix + "…")[0] > max_width:
            prefix = prefix[:-1]
        return prefix.rstrip() + "…"

    def tratar_tecla(self, evento: pygame.event.Event) -> bool:
        """Trata navegacao e digitacao do nome do jogador."""
        menu = self.menu
        if evento.key == pygame.K_TAB:
            passo = -1 if getattr(evento, "mod", 0) & pygame.KMOD_SHIFT else 1
            menu._selecionar((menu.opcao_selecionada + passo) % len(menu.opcoes))
        elif evento.key in (pygame.K_UP, pygame.K_w, pygame.K_LEFT):
            menu._selecionar((menu.opcao_selecionada - 1) % len(menu.opcoes))
        elif evento.key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT):
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
