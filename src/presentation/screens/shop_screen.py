"""Shop screen — skin browsing, purchase, and equip.

Migrated from game/menu.py Loja section (_desenhar_loja, _desenhar_cartao_skin).
"""

from __future__ import annotations

from typing import Any

import pygame

from src.core.constants import BRANCO, CIANO, DOURADO, LARGURA, ALTURA, VERDE
from src.presentation.screens.menu_screen import SistemaNotificacao, formatar_pontos


class ShopScreen:
    """Skin shop with grid layout, buy/equip buttons, and preview."""

    def __init__(self, notificacoes: SistemaNotificacao) -> None:
        self.selecao: int = 0
        self.preview_skin: Any = None
        self.notificacoes = notificacoes
        self.mouse_pos: tuple[int, int] = (0, 0)

    def handle_event(self, evento: pygame.event.Event,
                     game: Any) -> str | None:
        """Handle shop events. Returns action string or None."""
        if self.preview_skin is not None:
            return self._handle_preview_event(evento, game)

        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                return "voltar"
            elif evento.key == pygame.K_LEFT:
                self.selecao = max(0, self.selecao - 1)
            elif evento.key == pygame.K_RIGHT:
                self.selecao = min(len(game.loja.skins) - 1,
                                   self.selecao + 1)
            elif evento.key == pygame.K_UP:
                self.selecao = max(0, self.selecao - 4)
            elif evento.key == pygame.K_DOWN:
                self.selecao = min(len(game.loja.skins) - 1,
                                   self.selecao + 4)
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return self._acao_principal(game)
            elif evento.key == pygame.K_p:
                return self._acao_preview(game)

        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            idx = self._colidir_grid(evento.pos, game)
            if idx is not None:
                self.selecao = idx
                return self._acao_principal(game)
            for nome, rect in self._rects_botoes().items():
                if rect.collidepoint(evento.pos):
                    return self._acao_botao(nome, game)
        return None

    def _handle_preview_event(self, evento: pygame.event.Event,
                              game: Any) -> str | None:
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_ESCAPE, pygame.K_p):
                self.preview_skin = None
            elif evento.key == pygame.K_e:
                self._equipar(game)
                self.preview_skin = None
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            btn_equipar = pygame.Rect(LARGURA // 2 - 170, ALTURA - 120,
                                      160, 48)
            btn_fechar = pygame.Rect(LARGURA // 2 + 10, ALTURA - 120,
                                     160, 48)
            if btn_equipar.collidepoint(evento.pos):
                self._equipar(game)
                self.preview_skin = None
            elif btn_fechar.collidepoint(evento.pos):
                self.preview_skin = None
        return None

    def _acao_principal(self, game: Any) -> str:
        skin = game.loja.skins[self.selecao]
        if not skin.desbloqueada:
            return self._acao_botao("comprar", game)
        if skin.id == game.loja.skin_atual:
            self.preview_skin = skin
        else:
            return self._acao_botao("equipar", game)
        return ""

    def _acao_preview(self, game: Any) -> str:
        self.preview_skin = game.loja.skins[self.selecao]
        return ""

    def _acao_botao(self, nome: str, game: Any) -> str:
        loja = game.loja
        skin = loja.skins[self.selecao]
        if nome == "comprar":
            if skin.desbloqueada:
                self.notificacoes.adicionar("Skin ja desbloqueada!", "info")
            else:
                sucesso, _ = loja.comprar_skin(self.selecao)
                if sucesso:
                    self.notificacoes.adicionar(
                        f"Skin {skin.nome} comprada!", "sucesso")
                else:
                    self.notificacoes.adicionar(
                        "Moedas insuficientes!", "erro")
                game._salvar_tudo()
        elif nome == "equipar":
            if skin.desbloqueada:
                loja.equipar_skin(self.selecao)
                self.notificacoes.adicionar(
                    f"Skin {skin.nome} equipada!", "sucesso")
                game._salvar_tudo()
            else:
                self.notificacoes.adicionar(
                    "Compre a skin antes de equipar!", "info")
        elif nome == "preview":
            self.preview_skin = skin
        elif nome == "voltar":
            return "voltar"
        return ""

    def _equipar(self, game: Any) -> None:
        skin = game.loja.skins[self.selecao]
        if skin.desbloqueada:
            game.loja.equipar_skin(self.selecao)
            self.notificacoes.adicionar(
                f"Skin {skin.nome} equipada!", "sucesso")
            game._salvar_tudo()

    def _colidir_grid(self, pos: tuple[int, int], game: Any) -> int | None:
        cols = 4
        cell = 205
        x0 = (LARGURA - cols * cell) // 2
        y0 = 122
        for i in range(len(game.loja.skins)):
            rx = x0 + (i % cols) * cell
            ry = y0 + (i // cols) * 150
            rect = pygame.Rect(rx, ry, cell - 10, 138)
            if rect.collidepoint(pos):
                return i
        return None

    def _rects_botoes(self) -> dict[str, pygame.Rect]:
        nomes = ["comprar", "equipar", "preview", "voltar"]
        labels = ["COMPRAR", "EQUIPAR", "PREVIEW", "VOLTAR"]
        largura, espaco = 140, 18
        total = largura * 4 + espaco * 3
        x = (LARGURA - total) // 2
        y = ALTURA - 94
        return {
            nome: pygame.Rect(x + i * (largura + espaco), y, largura, 46)
            for i, nome in enumerate(nomes)
        }

    def render(self, surface: pygame.Surface, game: Any,
               tema: dict, fonte_pequena: pygame.font.Font,
               fonte_media: pygame.font.Font) -> None:
        """Draw the shop screen."""
        fonte_titulo = pygame.font.SysFont("monospace", 38, bold=True)
        ts = fonte_titulo.render("LOJA DE SKINS", True, tema["primaria"])
        surface.blit(ts, ts.get_rect(center=(LARGURA // 2, 50)))

        moedas_s = fonte_media.render(
            f"Moedas: {formatar_pontos(game.loja.moedas)}", True, DOURADO)
        surface.blit(moedas_s, (20, 30))

        skin_atual = game.loja.pegar_skin(game.loja.skin_atual)
        sa_s = fonte_media.render(
            f"Skin atual: {skin_atual.nome}", True, tema["secundaria"])
        surface.blit(sa_s, sa_s.get_rect(topright=(LARGURA - 20, 30)))

        n_skin = len(game.loja.skins)
        desb = len(game.loja.lista_desbloqueadas())
        ds = fonte_pequena.render(
            f"{desb}/{n_skin} skins desbloqueadas", True, (150, 155, 200))
        surface.blit(ds, ds.get_rect(topright=(LARGURA - 20, 56)))

        # grid de cards
        cols = 4
        cell = 205
        x0 = (LARGURA - cols * cell) // 2
        y0 = 122
        for i, skin in enumerate(game.loja.skins):
            rx = x0 + (i % cols) * cell
            ry = y0 + (i // cols) * 150
            rect = pygame.Rect(rx, ry, cell - 10, 138)
            selecionada = (i == self.selecao)
            hover = rect.collidepoint(self.mouse_pos)
            fundo = (52, 46, 92) if selecionada else (36, 34, 62) if hover \
                else (28, 27, 50)
            borda = (255, 190, 90) if selecionada else tema["secundaria"] \
                if hover else tema["borda_fraco"]
            bg = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            pygame.draw.rect(bg, fundo + (255,),
                             (0, 0, rect.w, rect.h), border_radius=10)
            surface.blit(bg, rect.topleft)
            pygame.draw.rect(surface, borda, rect, 2, border_radius=10)
            ns = fonte_pequena.render(skin.nome, True, BRANCO)
            surface.blit(ns, ns.get_rect(center=(rect.centerx,
                                                  rect.y + 18)))
            if skin.desbloqueada:
                status = ("EQUIPADA" if skin.id == game.loja.skin_atual
                          else "DESBLOQ.")
                cor = CIANO if skin.id == game.loja.skin_atual else VERDE
            else:
                status = f"{formatar_pontos(skin.preco)} pts"
                cor = DOURADO
            ss = fonte_pequena.render(status, True, cor)
            surface.blit(ss, ss.get_rect(center=(rect.centerx,
                                                  rect.y + 122)))

        # botoes
        for nome, rect in self._rects_botoes().items():
            hover = rect.collidepoint(self.mouse_pos)
            bg = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            cor = tema["primaria"] if hover else (40, 40, 70)
            pygame.draw.rect(bg, cor + (200,),
                             (0, 0, rect.w, rect.h), border_radius=rect.h // 2)
            surface.blit(bg, rect.topleft)
            pygame.draw.rect(surface, (0, 0, 0), rect, 2,
                             border_radius=rect.h // 2)
            label = nome.upper()
            ls = fonte_media.render(label, True, BRANCO)
            surface.blit(ls, ls.get_rect(center=rect.center))

        # descricao da skin selecionada
        if game.loja.skins:
            skin = game.loja.skins[self.selecao]
            ds = fonte_pequena.render(skin.descricao, True, (170, 175, 220))
            surface.blit(ds, ds.get_rect(center=(LARGURA // 2,
                                                  ALTURA - 36)))

        # overlay de preview
        if self.preview_skin is not None:
            self._render_preview(surface, game, tema, fonte_media,
                                 fonte_pequena)

    def _render_preview(self, surface: pygame.Surface, game: Any,
                        tema: dict, fonte_media: pygame.font.Font,
                        fonte_pequena: pygame.font.Font) -> None:
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 195))
        surface.blit(overlay, (0, 0))

        skin = self.preview_skin
        ft = pygame.font.SysFont("monospace", 38, bold=True)
        ns = ft.render(skin.nome.upper(), True, (170, 120, 255))
        surface.blit(ns, ns.get_rect(center=(LARGURA // 2, 128)))

        ds = fonte_media.render(skin.descricao, True, (200, 205, 240))
        surface.blit(ds, ds.get_rect(center=(LARGURA // 2,
                                              ALTURA // 2 + 90)))
        if skin.id == game.loja.skin_atual:
            status, cor = "Equipada", tema["secundaria"]
        elif skin.desbloqueada:
            status, cor = "Desbloqueada", VERDE
        else:
            status, cor = f"Preco: {formatar_pontos(skin.preco)} pts", DOURADO
        ss = fonte_media.render(status, True, cor)
        surface.blit(ss, ss.get_rect(center=(LARGURA // 2,
                                              ALTURA // 2 + 130)))

        btn_eq = pygame.Rect(LARGURA // 2 - 170, ALTURA - 120, 160, 48)
        btn_fc = pygame.Rect(LARGURA // 2 + 10, ALTURA - 120, 160, 48)
        for label, rect in [("EQUIPAR", btn_eq), ("FECHAR", btn_fc)]:
            hover = rect.collidepoint(self.mouse_pos)
            bg = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            cor = tema["primaria"] if hover else (40, 40, 70)
            pygame.draw.rect(bg, cor + (200,),
                             (0, 0, rect.w, rect.h), border_radius=rect.h // 2)
            surface.blit(bg, rect.topleft)
            pygame.draw.rect(surface, (0, 0, 0), rect, 2,
                             border_radius=rect.h // 2)
            ls = fonte_media.render(label, True, BRANCO)
            surface.blit(ls, ls.get_rect(center=rect.center))
