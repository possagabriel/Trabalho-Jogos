"""Hubs de navegação para as ações Jogar e Perfil."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.infrastructure.graphics.theme import MENU_RESUMO_CONTINUAR_FONT_SIZE, tema_atual

if TYPE_CHECKING:
    from src.runtime.presentation.menu import MenuPrincipal


class MenuHubScreen:
    """Oferece destinos de segundo nível sem alterar as telas de destino."""

    def __init__(self, menu: MenuPrincipal, kind: str) -> None:
        self.menu = menu
        self.kind = kind
        self.selection = 0
        self._text_cache: dict[tuple, pygame.Surface] = {}

    @property
    def entries(self) -> tuple[tuple[str, str], ...]:
        if self.kind == "JOGAR":
            return (("CONTINUAR", "continuar"), ("LOBBY", "lobby"))
        return (("PILOTOS", "pilotos"), ("RECORDES", "recordes"),
                ("MEMÓRIAS", "memorias"))

    def abrir(self) -> None:
        """Define seleção inicial de acordo com o estado do perfil."""
        self.selection = (0 if self.menu._tem_save() else 1) \
            if self.kind == "JOGAR" else 0

    def _panel(self) -> pygame.Rect:
        layout = self.menu.layout
        narrow = self.menu._layout_4_3()
        width = layout.px(620 if narrow else 700)
        height = layout.px((350 if self.kind == "PERFIL" else 280)
                           if narrow else
                           (385 if self.kind == "PERFIL" else 310))
        return pygame.Rect(
            layout.x(0.5) - width // 2,
            layout.y(0.5) - height // 2,
            width,
            height,
        )

    def _rects(self) -> list[pygame.Rect]:
        panel = self._panel()
        layout = self.menu.layout
        narrow = self.menu._layout_4_3()
        row_height = layout.px(58 if narrow else 62)
        margin = layout.px(28 if narrow else 32)
        gap = layout.px(10 if narrow else 14)
        top = panel.y + layout.px(96 if narrow else 104)
        return [pygame.Rect(
            panel.x + margin,
            top + index * (row_height + gap),
            panel.width - margin * 2,
            row_height,
        ) for index in range(len(self.entries))]

    def _back_rect(self) -> pygame.Rect:
        panel = self._panel()
        layout = self.menu.layout
        return pygame.Rect(
            panel.centerx - layout.px(70), panel.bottom - layout.px(48),
            layout.px(140), layout.px(32),
        )

    def desenhar(self, surface: pygame.Surface) -> None:
        """Desenha as opções do hub sobre o fundo atual do menu."""
        menu = self.menu
        theme = tema_atual(menu.jogo.config["tema"])
        panel = self._panel()
        pygame.draw.rect(surface, (4, 7, 23), panel, border_radius=16)
        pygame.draw.rect(surface, theme["primaria"], panel, 2, border_radius=16)
        title = "JOGAR" if self.kind == "JOGAR" else "PERFIL"
        title_surface = menu.fonte_cabecalho.render(title, True, theme["primaria"])
        surface.blit(title_surface, title_surface.get_rect(
            midtop=(panel.centerx, panel.y + menu.layout.px(26))))
        for index, ((label, action), rect) in enumerate(zip(self.entries, self._rects())):
            selected = index == self.selection
            disabled = action == "continuar" and not menu._tem_save()
            color = (105, 111, 135) if disabled else (
                theme["primaria"] if selected else theme["secundaria"])
            pygame.draw.rect(surface, (8, 13, 32), rect, border_radius=10)
            pygame.draw.rect(surface, color, rect, 3 if selected else 1,
                             border_radius=10)
            text = menu.fonte_opcao.render(label, True, color)
            summary = (menu.jogo.profile_service.continue_summary()
                       if action == "continuar" and not disabled and selected else None)
            if summary:
                surface.blit(text, text.get_rect(
                    center=(rect.centerx, rect.centery - menu.layout.px(10))))
                total = summary["total_play_time"]
                hours, remainder = divmod(total, 3600)
                minutes = remainder // 60
                short = (f"Dimensão {summary['dimension']} · Nível {summary['level']}"
                         f" · tempo total {hours:02d}h{minutes:02d}")
                font = menu.layout.fonte_texto(MENU_RESUMO_CONTINUAR_FONT_SIZE)
                key = (id(font), short, (210, 220, 240))
                detail = self._text_cache.get(key)
                if detail is None:
                    detail = font.render(short, True, (210, 220, 240))
                    self._text_cache[key] = detail
                surface.blit(detail, detail.get_rect(
                    center=(rect.centerx, rect.centery + menu.layout.px(15))))
            else:
                surface.blit(text, text.get_rect(center=rect.center))
            if self.kind == "PERFIL" and action == "memorias" \
                    and menu._novidades("memorias"):
                self._badge(surface, rect, theme["terciaria"])
            elif action == "continuar" and disabled:
                hint = menu.fonte_pequena.render("SEM SAVE", True, color)
                surface.blit(hint, hint.get_rect(
                    midright=(rect.right - menu.layout.px(14), rect.centery)))
        hint_rect = self._back_rect()
        pygame.draw.rect(surface, (8, 13, 32), hint_rect, border_radius=6)
        pygame.draw.rect(surface, theme["secundaria"], hint_rect, 1,
                         border_radius=6)
        hint = menu.fonte_pequena.render("ESC  VOLTAR", True, (210, 220, 240))
        surface.blit(hint, hint.get_rect(center=hint_rect.center))

    def _badge(self, surface: pygame.Surface, rect: pygame.Rect,
               color: tuple[int, int, int]) -> None:
        menu = self.menu
        badge = pygame.Rect(0, 0, menu.layout.px(78), menu.layout.px(27))
        badge.midright = (rect.right - menu.layout.px(12), rect.centery)
        pygame.draw.rect(surface, color, badge, border_radius=7)
        text = menu.fonte_pequena.render("NOVO", True, (255, 255, 255))
        surface.blit(text, text.get_rect(center=badge.center))

    def tratar_tecla(self, event: pygame.event.Event) -> bool:
        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.menu._voltar_menu()
        elif event.key in (pygame.K_UP, pygame.K_w):
            self.selection = (self.selection - 1) % len(self.entries)
            self.menu._som("navegar")
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selection = (self.selection + 1) % len(self.entries)
            self.menu._som("navegar")
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.ativar(self.selection)
        return True

    def tratar_clique(self, pos: tuple[int, int]) -> None:
        if self._back_rect().collidepoint(pos):
            self.menu._voltar_menu()
            return
        for index, rect in enumerate(self._rects()):
            if rect.collidepoint(pos):
                self.selection = index
                self.ativar(index)
                return

    def ativar(self, index: int) -> None:
        """Encaminha o destino para os callbacks já usados pelo jogo."""
        menu = self.menu
        action = self.entries[index][1]
        if action == "continuar":
            if not menu._tem_save():
                menu._som("erro")
                menu.notificacoes.adicionar("Nenhum save encontrado!", "erro")
                return
            menu._abrir_continuar()
        elif action == "lobby":
            menu._abrir_lobby()
        elif action == "pilotos":
            menu._abrir_perfis()
        elif action == "recordes":
            menu._abrir_recordes()
        elif action == "memorias":
            menu._abrir_arquivo()
