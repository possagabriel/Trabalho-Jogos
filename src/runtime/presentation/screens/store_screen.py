"""Interacoes exclusivas da tela de loja de skins."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

from src.core.constants import DOURADO, NEGRO
from src.infrastructure.graphics.theme import tema_atual
from src.runtime.infrastructure.graphics.map_art import miniatura_nave
from src.runtime.infrastructure.graphics.menu_panels import (
    ACENTO_ORIGINAL,
    BORDA_ORIGINAL,
    FUNDO_ORIGINAL,
    TEXTO_ATIVO_ORIGINAL,
    TEXTO_ORIGINAL,
    icone_menu_original,
    painel_original,
    plataforma_hangar,
    texto_painel,
)

if TYPE_CHECKING:
    from src.infrastructure.ui.layout import Layout
    from src.runtime.domain.entities.player import Skin
    from src.runtime.presentation.menu import MenuPrincipal


def geometria_hangar_original(layout: Layout, painel: pygame.Rect,
                              total: int) -> tuple[list[pygame.Rect], pygame.Rect]:
    """Divide o hangar entre catálogo de quatro colunas e expositor lateral."""
    margem, gap = layout.px(16), layout.px(8)
    topo = painel.top + layout.px(54)
    altura = painel.bottom - topo - margem
    catalogo = pygame.Rect(painel.x + margem, topo, round(painel.width * .63), altura)
    expositor = pygame.Rect(catalogo.right + margem, topo,
                            painel.right - catalogo.right - margem * 2, altura)
    linhas = max(1, (total + 3) // 4)
    largura_card = (catalogo.width - gap * 3) // 4
    altura_card = (catalogo.height - gap * (linhas - 1)) // linhas
    cards = [pygame.Rect(catalogo.x + indice % 4 * (largura_card + gap),
                          catalogo.y + indice // 4 * (altura_card + gap),
                          largura_card, altura_card) for indice in range(total)]
    return cards, expositor


class TelaLojaJogo:
    """Controla selecao, compra, equipagem e preview de skins."""

    def __init__(self, menu: MenuPrincipal) -> None:
        self.menu = menu
        self._overlay_original: pygame.Surface | None = None

    def tratar_tecla(self, evento: pygame.event.Event) -> bool:
        """Trata navegacao da grade e acoes sobre a skin selecionada."""
        menu = self.menu
        if menu.preview_skin:
            if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if (menu.preview_skin.desbloqueada or
                        menu.jogo.config["estilo_visual"] != "ORIGINAL"):
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
        if menu.jogo.config["estilo_visual"] == "ORIGINAL":
            self._desenhar_original(tela)
            return
        layout = menu.layout
        tema = tema_atual(menu.jogo.config["tema"])
        menu._cabecalho_sub_animado(tela, "HANGAR DE VISUAIS", tema["primaria"])
        painel = menu._painel_loja()
        menu._painel_sub(tela, painel, tema)
        menu._detalhe_painel(tela, painel, tema, tema["secundaria"])
        dx, dy, alfa = menu._entrada_anim(
            menu._frac_sub(0.06, 0.3), dx_design=-16)
        moedas = f"Moedas: {menu.jogo.loja.moedas:,}".replace(",", ".")
        moeda = menu.fonte_media.render(moedas, True, DOURADO)
        menu._blit_alfa(
            tela,
            moeda,
            (painel.x + layout.px(20) + dx, painel.y + layout.px(17) + dy),
            int(255 * alfa),
        )
        atual = menu.jogo.loja.pegar_skin(menu.jogo.loja.skin_atual)
        total = len(menu.jogo.loja.skins)
        desbloqueadas = len(menu.jogo.loja.lista_desbloqueadas())
        resumo_visual = (
            f"Visual atual: {atual.nome}  //  "
            f"{desbloqueadas}/{total} desbloqueados"
        )
        skin_atual = menu.fonte_media.render(
            resumo_visual, True, tema["secundaria"])
        menu._blit_alfa(tela, skin_atual, skin_atual.get_rect(
            topright=(painel.right - layout.px(20) - dx,
                      painel.y + layout.px(17) + dy)), int(255 * alfa))
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
            center=(layout.x(0.5) + dx,
                    layout.altura - layout.px(91) + dy)), int(255 * alfa))
        if menu.preview_skin:
            menu._desenhar_preview_overlay(tela)

    def estado_selecao(self) -> tuple[str, str, str]:
        """Informa estado, orientação e ação principal sem alterar a loja."""
        loja = self.menu.jogo.loja
        skin = loja.skins[self.menu.loja_selecao]
        if skin.id == loja.skin_atual:
            return "EM USO", "VISUAL EQUIPADO", "prévia"
        if skin.desbloqueada:
            return "LIBERADA", "PRONTO PARA EQUIPAR", "equipar"
        falta = max(0, skin.preco - loja.moedas)
        detalhe = (f"FALTAM {falta:,} MOEDAS".replace(",", ".") if falta else
                    "PRONTO PARA COMPRAR")
        return "BLOQUEADA", detalhe, "comprar"

    def _texto(self, tela: pygame.Surface, texto: str, rect: pygame.Rect,
                tamanho: int = 18, cor: tuple = TEXTO_ORIGINAL) -> None:
        arte = texto_painel(self.menu.layout.fonte_texto(tamanho), texto, cor, rect.w, rect.h)
        tela.blit(arte, arte.get_rect(center=rect.center))

    def _desenhar_original(self, tela: pygame.Surface) -> None:
        menu, layout, loja = self.menu, self.menu.layout, self.menu.jogo.loja
        menu._cabecalho_sub_animado(tela, "HANGAR // CASCOS", ACENTO_ORIGINAL)
        painel = menu._painel_loja()
        tela.blit(painel_original(painel.size, FUNDO_ORIGINAL, BORDA_ORIGINAL), painel)
        resumo = (f"{loja.moedas:,} MOEDAS  ·  "
                   f"{len(loja.lista_desbloqueadas())}/{len(loja.skins)} VISUAIS LIBERADOS")
        self._texto(tela, resumo.replace(",", "."),
                     pygame.Rect(painel.x + layout.px(16), painel.y + layout.px(12),
                                 painel.w - layout.px(32), layout.px(26)), 22, ACENTO_ORIGINAL)
        cards, expositor = geometria_hangar_original(layout, painel, len(loja.skins))
        for indice, (skin, rect) in enumerate(zip(loja.skins, cards)):
            self._desenhar_card_original(tela, rect, skin, indice == menu.loja_selecao)
        self._desenhar_expositor(tela, expositor)
        self._desenhar_acoes(tela)
        self._texto(tela, "SETAS: SELECIONAR  ·  ENTER: AÇÃO PRINCIPAL  ·  ESC: VOLTAR",
                     pygame.Rect(0, layout.altura - layout.px(96), layout.largura, layout.px(22)))
        if menu.preview_skin:
            self._desenhar_preview_original(tela)

    def _desenhar_card_original(self, tela: pygame.Surface, rect: pygame.Rect,
                                 skin: Skin, selecionada: bool) -> None:
        menu, layout = self.menu, self.menu.layout
        tela.blit(painel_original(rect.size, FUNDO_ORIGINAL, BORDA_ORIGINAL,
                                   selecionado=selecionada, raio=layout.px(8)), rect)
        self._texto(tela, skin.nome.upper(),
                     pygame.Rect(rect.x + layout.px(6), rect.y + layout.px(6),
                                 rect.w - layout.px(12), layout.px(23)))
        tamanho = max(8, min(layout.px(56), rect.h - layout.px(64)))
        arte = miniatura_nave(skin, 0, False, tamanho)
        tela.blit(arte, arte.get_rect(center=rect.center))
        estado = ("EM USO" if skin.id == menu.jogo.loja.skin_atual else
                   "LIBERADA" if skin.desbloqueada else f"{skin.preco:,} MOEDAS")
        self._texto(tela, estado.replace(",", "."),
                     pygame.Rect(rect.x + layout.px(6), rect.bottom - layout.px(26),
                                 rect.w - layout.px(12), layout.px(20)),
                     16, TEXTO_ORIGINAL if skin.desbloqueada else ACENTO_ORIGINAL)

    def _desenhar_expositor(self, tela: pygame.Surface, rect: pygame.Rect) -> None:
        menu, layout = self.menu, self.menu.layout
        skin = menu.jogo.loja.skins[menu.loja_selecao]
        tela.blit(painel_original(rect.size, FUNDO_ORIGINAL, BORDA_ORIGINAL,
                                   selecionado=True), rect)

        def linha(texto: str, y: int, tamanho: int = 18,
                  cor: tuple = TEXTO_ORIGINAL) -> None:
            area = pygame.Rect(rect.x + layout.px(12), rect.y + layout.px(y),
                                rect.w - layout.px(24), layout.px(28))
            self._texto(tela, texto, area, tamanho, cor)

        linha("VISUAL EM FOCO", 8, 16, ACENTO_ORIGINAL)
        linha(skin.nome.upper(), 34, 28)
        piso = plataforma_hangar((rect.w - layout.px(20), layout.px(160)))
        tela.blit(piso, piso.get_rect(center=(rect.centerx, rect.y + layout.px(149))))
        arte = miniatura_nave(skin, 0, False, min(layout.px(130), rect.w - layout.px(44)))
        flutuar = (layout.px(math.sin(menu.animacao_original.tempo * 1.8) * 4)
                   if menu.jogo.config["intensidade_flash"] == "NORMAL" else 0)
        tela.blit(arte, arte.get_rect(center=(rect.centerx, rect.y + layout.px(143) + flutuar)))
        estado, detalhe, _acao = self.estado_selecao()
        linha(estado, 230, 20, ACENTO_ORIGINAL)
        linha(f"{skin.preco:,} MOEDAS".replace(",", ".") if not skin.desbloqueada else
               "CASCO NO SEU HANGAR", 258, 22)
        linha(skin.descricao, 296, 18)
        linha(detalhe, 358, 17, ACENTO_ORIGINAL)

    def _desenhar_acoes(self, tela: pygame.Surface) -> None:
        menu, layout = self.menu, self.menu.layout
        _estado, _detalhe, principal = self.estado_selecao()
        for nome, botao in menu._botoes_loja().items():
            ativo = botao.rect.collidepoint(menu.mouse) or nome == principal
            tela.blit(painel_original(botao.rect.size, FUNDO_ORIGINAL, BORDA_ORIGINAL,
                                       selecionado=ativo, botao=True), botao.rect)
            icone = icone_menu_original(nome, ativo, layout.px(22))
            tela.blit(icone, icone.get_rect(center=(botao.rect.x + layout.px(19),
                                                    botao.rect.centery)))
            texto = botao.rect.inflate(-layout.px(14), -layout.px(8))
            texto.x += layout.px(32)
            texto.w -= layout.px(48)
            self._texto(tela, botao.texto, texto,
                         20, TEXTO_ATIVO_ORIGINAL if ativo else TEXTO_ORIGINAL)

    def _desenhar_preview_original(self, tela: pygame.Surface) -> None:
        menu, layout, skin = self.menu, self.menu.layout, self.menu.preview_skin
        if self._overlay_original is None or self._overlay_original.get_size() != tela.get_size():
            self._overlay_original = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
            self._overlay_original.fill((*NEGRO, 220))
        tela.blit(self._overlay_original, (0, 0))
        rect = pygame.Rect(0, 0, layout.px(620), layout.px(420))
        rect.center = (layout.x(.5), layout.y(.47))
        tela.blit(painel_original(rect.size, FUNDO_ORIGINAL, BORDA_ORIGINAL), rect)
        self._texto(tela, skin.nome.upper(), pygame.Rect(rect.x, rect.y + layout.px(20),
                                                        rect.w, layout.px(34)), 30, ACENTO_ORIGINAL)
        arte = miniatura_nave(skin, 0, False, layout.px(200))
        tela.blit(arte, arte.get_rect(center=rect.center))
        self._texto(tela, skin.descricao, pygame.Rect(rect.x + layout.px(20),
                     rect.bottom - layout.px(84), rect.w - layout.px(40), layout.px(28)), 22)
        dica = ("ENTER: EQUIPAR  ·  ESC: FECHAR" if skin.desbloqueada else
                "VISUAL BLOQUEADO  ·  ESC: VOLTAR AO HANGAR")
        self._texto(tela, dica, pygame.Rect(rect.x + layout.px(20),
                     rect.bottom - layout.px(46), rect.w - layout.px(40), layout.px(24)),
                     18, ACENTO_ORIGINAL)
        for indice, nome in enumerate(("equipar", "voltar")):
            botao = pygame.Rect(layout.x(.5) - layout.px(170) + indice * layout.px(180),
                                layout.altura - layout.px(120), layout.px(160), layout.px(48))
            bloqueado = indice == 0 and not skin.desbloqueada
            ativo = botao.collidepoint(menu.mouse) and not bloqueado
            rotulo = "BLOQUEADA" if bloqueado else "EQUIPAR" if indice == 0 else "FECHAR"
            tela.blit(painel_original(botao.size, FUNDO_ORIGINAL, BORDA_ORIGINAL,
                                       selecionado=ativo, botao=True), botao)
            icone = icone_menu_original(nome, ativo, layout.px(22), desabilitado=bloqueado)
            tela.blit(icone, icone.get_rect(center=(botao.x + layout.px(20), botao.centery)))
            texto = botao.inflate(-layout.px(16), -layout.px(8))
            texto.x += layout.px(32)
            texto.w -= layout.px(42)
            self._texto(tela, rotulo, texto, 18,
                         TEXTO_ATIVO_ORIGINAL if ativo else TEXTO_ORIGINAL)

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
        if nome == "prévia":
            nome = "preview"
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
                if (menu.preview_skin.desbloqueada or
                        menu.jogo.config["estilo_visual"] != "ORIGINAL"):
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
