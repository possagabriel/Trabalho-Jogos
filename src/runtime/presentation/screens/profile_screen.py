"""Seleção e gerenciamento local de perfis em painéis cartoon."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from src.core.constants import CIANO, DOURADO, VERDE, VERMELHO, VOID_BLACK

if TYPE_CHECKING:
    from src.runtime.presentation.menu import MenuPrincipal


class ProfileScreen:
    """Oferece CRUD por teclado ou mouse antes de iniciar uma partida."""

    def __init__(self, menu: MenuPrincipal) -> None:
        self.menu = menu
        self.selection = 0
        self.mode: str | None = None
        self.text = ""
        self.message = ""
        self.buttons: list[pygame.Rect] = []
        self.cards: list[pygame.Rect] = []
        self.dialog_choice = 1
        self._return_selection = 0
        self._initial_create = False
        self._scroll_offset = 0
        self._visible_profile_indices: list[int] = []
        self._entries = None
        self.refresh()

    def _profiles(self):
        if self._entries is None:
            self._entries = self.menu.jogo.profile_service.list_profiles()
        return self._entries

    def refresh(self) -> None:
        """Atualiza os cartões e inicia a criação se ainda não houver perfil."""
        self._entries = self.menu.jogo.profile_service.list_profiles()
        if not self._entries:
            self.selection = 0
            if self.mode is None:
                self._begin_create()
                self._initial_create = True
            return
        if self._initial_create and self.mode == "create":
            self.mode, self.text = None, ""
        self._initial_create = False
        active = self.menu.jogo.profile_service.active
        last = self.menu.jogo.profile_service.index.get("last_used")
        preferred = active.id if active else last
        self.selection = next(
            (i for i, profile in enumerate(self._entries)
             if profile.id == preferred and not profile.damaged),
            min(self.selection, len(self._entries) - 1),
        )

    @property
    def new_profile_disabled(self) -> bool:
        """Indica se o limite configurado bloqueia a criação de outro perfil."""
        return len(self._profiles()) >= self.menu.jogo.profile_service.max_profiles

    def draw(self, surface: pygame.Surface) -> None:
        """Mostra cartões concisos e diálogos com texto legível."""
        layout = self.menu.layout
        scale = layout.escala
        w, h = layout.largura, layout.altura
        self._draw_text(surface, self.menu.fonte_cabecalho,
                        "PERFIS DE JOGADOR", (w // 2, int(48 * scale)), CIANO)
        profiles = self._profiles()
        self.cards = []
        top = int(88 * scale)
        footer_top = h - int(84 * scale)
        gap = max(3, int(7 * scale))
        available = footer_top - top
        min_card_h = max(43, int(52 * scale))
        max_rows = max(2, (available + gap) // (min_card_h + gap))
        visible_count = max(1, min(5, max_rows - 1))
        max_offset = max(0, len(profiles) - visible_count)
        if self.selection < self._scroll_offset:
            self._scroll_offset = self.selection
        elif (self.selection < len(profiles)
              and self.selection >= self._scroll_offset + visible_count):
            self._scroll_offset = self.selection - visible_count + 1
        self._scroll_offset = max(0, min(self._scroll_offset, max_offset))
        self._visible_profile_indices = list(range(
            self._scroll_offset,
            min(len(profiles), self._scroll_offset + visible_count),
        ))
        rows = len(self._visible_profile_indices) + 1
        card_h = max(43, min(int(78 * scale),
                             (available - gap * (rows - 1)) // rows))
        card_x = int(56 * scale)
        card_w = w - card_x * 2
        for row, index in enumerate(self._visible_profile_indices):
            profile = profiles[index]
            rect = pygame.Rect(card_x, top + row * (card_h + gap),
                               card_w, card_h)
            self.cards.append(rect)
            self._draw_profile_card(surface, rect, profile, index, scale)

        new_index = len(profiles)
        new_rect = pygame.Rect(card_x, top + len(self._visible_profile_indices)
                               * (card_h + gap),
                               card_w, card_h)
        self.cards.append(new_rect)
        self._draw_new_card(surface, new_rect, new_index, scale)

        self._draw_footer(surface, profiles, scale, footer_top)
        if self.mode:
            self._draw_dialog(surface, profiles, scale)
        elif self.message or self.menu.jogo.profile_service.migration_error:
            warning = self.message or "Há um save antigo danificado."
            color = (VERDE if warning.startswith(("Perfil ativo:",
                                                   "Perfil exportado:"))
                     else VERMELHO)
            self._draw_text(surface, self.menu.fonte_pequena, warning,
                            (w // 2, h - int(46 * scale)), color,
                            max_width=w - int(48 * scale))

    def _draw_profile_card(self, surface, rect, profile, index, scale) -> None:
        active = self.menu.jogo.profile_service.active
        is_active = bool(active and profile.id == active.id)
        focused = index == self.selection
        pygame.draw.rect(surface, (20, 31, 50), rect,
                         border_radius=max(4, int(9 * scale)))
        border = DOURADO if focused else CIANO
        pygame.draw.rect(surface, border, rect, max(2, int(2 * scale)),
                         border_radius=max(4, int(9 * scale)))
        if focused:
            focus_mark = self.menu.fonte_media.render(">", True, border)
            surface.blit(focus_mark, (rect.x + int(10 * scale),
                                      rect.centery - focus_mark.get_height() // 2))
        if profile.damaged:
            name_color = VERMELHO
        else:
            name_color = DOURADO if is_active else CIANO

        skin = None
        if not profile.damaged:
            skin_id = profile.progress.get("skin_atual", "padrao")
            skin = self.menu.jogo.loja.pegar_skin(skin_id)
        if skin is not None:
            self.menu._desenhar_preview_skin(
                surface, skin, rect.x + int(38 * scale), rect.centery)

        text_x = rect.x + int(76 * scale)
        max_text = rect.right - text_x - int(16 * scale)
        if is_active:
            badge_width = self.menu.fonte_pequena.size("ATIVO")[0]
            max_text -= badge_width + int(8 * scale)
        name = self._fit(self.menu.fonte_media, profile.name, max_text)
        self._draw_text(surface, self.menu.fonte_media, name,
                        (text_x, rect.y + int(20 * scale)), name_color,
                        anchor="topleft")
        if profile.damaged:
            details = "Perfil danificado — não pode ser ativado"
            detail_color = VERMELHO
        else:
            progress = profile.progress
            defeated = progress.get("bosses_por_tipo", {})
            bosses = min(6, sum(1 for value in defeated.values()
                                if type(value) is int and value > 0)
                         if isinstance(defeated, dict) else 0)
            coins = int(progress.get("moedas", 0))
            coins_text = f"{coins:,}".replace(",", ".")
            details = (f"{coins_text} moedas · Dimensão "
                       f"{progress.get('dimensao_maxima', 1)} · "
                       f"Bosses {bosses}/6 · {self._human_access(profile.last_access)}")
            detail_color = VERDE
        details = self._fit(self.menu.fonte_pequena, details, max_text)
        self._draw_text(surface, self.menu.fonte_pequena, details,
                        (text_x, rect.y + int(52 * scale)), detail_color,
                        anchor="topleft")
        if is_active:
            badge = self.menu.fonte_pequena.render("ATIVO", True, DOURADO)
            surface.blit(badge, (rect.right - badge.get_width() - int(14 * scale),
                                 rect.y + int(7 * scale)))

    def _draw_new_card(self, surface, rect, index, scale) -> None:
        limit = self.menu.jogo.profile_service.max_profiles
        disabled = self.new_profile_disabled
        focused = index == self.selection
        color = (150, 158, 172) if disabled else CIANO
        pygame.draw.rect(surface, (24, 35, 51), rect,
                         border_radius=max(4, int(9 * scale)))
        pygame.draw.rect(surface, color if focused else (82, 101, 122), rect,
                         max(2, int(2 * scale)),
                         border_radius=max(4, int(9 * scale)))
        label = f"+ NOVO PERFIL  —  Limite de {limit} perfis" if disabled \
            else "+ NOVO PERFIL"
        if focused:
            label = "> " + label
        self._draw_text(surface, self.menu.fonte_media, label,
                        (rect.centerx, rect.centery), color,
                        max_width=rect.width - int(24 * scale))

    def _draw_footer(self, surface, profiles, scale, footer_top) -> None:
        profile = profiles[self.selection] if self.selection < len(profiles) else None
        if profile is None:
            limit = self.menu.jogo.profile_service.max_profiles
            hint = (f"Limite de {limit} perfis" if len(profiles) >= limit
                    else "Enter criar · Esc voltar")
        elif profile.damaged:
            hint = "R renomear · Delete excluir · Esc voltar"
        else:
            hint = "Enter ativar · R renomear · Delete excluir · X exportar · Esc voltar"
        self._draw_text(surface, self.menu.fonte_pequena, hint,
                        (surface.get_width() // 2, footer_top + int(16 * scale)),
                        CIANO, max_width=surface.get_width() - int(40 * scale))

    def _draw_dialog(self, surface, profiles, scale) -> None:
        w, h = surface.get_size()
        cover = pygame.Surface((w, h), pygame.SRCALPHA)
        cover.fill((*VOID_BLACK, 228))
        surface.blit(cover, (0, 0))
        panel = pygame.Rect(int(w * 0.12), int(h * 0.24),
                            int(w * 0.76), int(h * 0.53))
        pygame.draw.rect(surface, (16, 28, 47), panel, border_radius=12)
        pygame.draw.rect(surface, CIANO, panel, 2, border_radius=12)
        if self.mode == "delete":
            profile = profiles[self.selection]
            title = "EXCLUIR PERFIL"
            self._draw_text(surface, self.menu.fonte_media,
                            f"Será perdido: {self._loss_summary(profile)}",
                            (w // 2, panel.y + int(76 * scale)), VERDE,
                            max_width=panel.width - int(42 * scale))
            if self._profile_in_game(profile):
                self._draw_text(
                    surface, self.menu.fonte_pequena,
                    "Este perfil está em uso numa partida e não pode ser excluído agora.",
                    (w // 2, panel.y + int(107 * scale)), VERMELHO,
                    max_width=panel.width - int(42 * scale),
                )
            self._draw_text(surface, self.menu.fonte_pequena,
                            "Digite o nome do perfil para confirmar:",
                            (w // 2, panel.y + int(136 * scale)), CIANO)
        else:
            title = ("Qual o seu nome, piloto?" if self.mode == "create"
                     and not profiles else
                     "NOVO PERFIL" if self.mode == "create" else "RENOMEAR PERFIL")
            self._draw_text(surface, self.menu.fonte_pequena,
                            "Use letras, números, espaço, apóstrofo e hífen.",
                            (w // 2, panel.y + int(89 * scale)), VERDE,
                            max_width=panel.width - int(42 * scale))

        self._draw_text(surface, self.menu.fonte_cabecalho, title,
                        (w // 2, panel.y + int(35 * scale)), CIANO,
                        max_width=panel.width - int(32 * scale))
        input_rect = pygame.Rect(panel.x + int(30 * scale),
                                 panel.y + int(153 * scale),
                                 panel.width - int(60 * scale),
                                 int(48 * scale))
        pygame.draw.rect(surface, (8, 16, 29), input_rect, border_radius=6)
        pygame.draw.rect(surface, DOURADO if self.mode == "delete" else CIANO,
                         input_rect, 2, border_radius=6)
        max_length = self.menu.jogo.profile_service.max_name_length
        shown_text = self.text + "_"
        counter = f"{len(self.text)}/{max_length}"
        text_width = input_rect.width - int(20 * scale)
        if self.mode in ("create", "rename"):
            counter_width = self.menu.fonte_pequena.size(counter)[0]
            text_width -= counter_width + int(18 * scale)
        self._draw_text(surface, self.menu.fonte_media, shown_text,
                        (input_rect.left + int(10 * scale), input_rect.centery),
                        CIANO, max_width=text_width, anchor="midleft")
        if self.mode in ("create", "rename"):
            self._draw_text(surface, self.menu.fonte_pequena, counter,
                            (input_rect.right - int(10 * scale), input_rect.centery),
                            VERDE, anchor="midright")
        if self.message:
            self._draw_text(surface, self.menu.fonte_pequena, self.message,
                            (w // 2, panel.y + int(224 * scale)), VERMELHO,
                            max_width=panel.width - int(30 * scale))
        elif self.mode == "delete":
            choices = ("CONFIRMAR", "CANCELAR")
            button_w = int(panel.width * 0.36)
            button_y = panel.bottom - int(54 * scale)
            self._draw_text(surface, self.menu.fonte_pequena,
                            "Enter escolhe · ←/→ muda ação · Esc cancela",
                            (w // 2, button_y - int(12 * scale)), CIANO)
            self.buttons = []
            for index, choice in enumerate(choices):
                rect = pygame.Rect(
                    panel.centerx - button_w - int(10 * scale)
                    + index * (button_w + int(20 * scale)),
                    button_y, button_w, int(42 * scale),
                )
                self.buttons.append(rect)
                color = DOURADO if index == self.dialog_choice else CIANO
                pygame.draw.rect(surface, (25, 44, 69), rect, border_radius=6)
                pygame.draw.rect(surface, color, rect, 2, border_radius=6)
                label = f"> {choice}" if index == self.dialog_choice else choice
                self._draw_text(surface, self.menu.fonte_pequena, label,
                                rect.center, color)
        else:
            self._draw_text(surface, self.menu.fonte_pequena,
                            "Enter confirma · Esc cancela",
                            (w // 2, panel.bottom - int(28 * scale)), CIANO)

    @staticmethod
    def _fit(font, text: str, max_width: int) -> str:
        if font.size(text)[0] <= max_width:
            return text
        result = text
        while result and font.size(result + "…")[0] > max_width:
            result = result[:-1]
        return result.rstrip() + "…"

    def _draw_text(self, surface, font, text, position, color,
                   max_width: int | None = None, anchor: str = "center") -> None:
        if max_width is not None:
            text = self._fit(font, text, max_width)
        image = font.render(text, True, color)
        rect = image.get_rect(**{anchor: position})
        surface.blit(image, rect)

    @staticmethod
    def _human_access(value: str) -> str:
        try:
            accessed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if accessed.tzinfo is None:
                accessed = accessed.replace(tzinfo=timezone.utc)
            days = max(0, (datetime.now(timezone.utc) - accessed).days)
        except (AttributeError, TypeError, ValueError):
            return "sem acesso registrado"
        if days == 0:
            return "acesso hoje"
        if days == 1:
            return "acesso ontem"
        return f"acesso há {days} dias"

    def _loss_summary(self, profile) -> str:
        progress = profile.progress
        coins = int(progress.get("moedas", 0))
        weapons = len(progress.get("armas_desbloqueadas", ()))
        skins = len(progress.get("skins_desbloqueadas", ()))
        seconds = progress.get("tempo_total")
        played = (f"{max(0, int(seconds)) // 3600}h de jogo"
                  if seconds is not None else "tempo sem registro")
        return f"{coins} moedas, {weapons} armas, {skins} skins e {played}"

    def _profile_in_game(self, profile) -> bool:
        active = self.menu.jogo.profile_service.active
        return bool(active and active.id == profile.id
                    and self.menu.jogo.estado.value != "MENU")

    def _begin_create(self) -> None:
        self._return_selection = self.selection
        self.mode = "create"
        count = len(self._profiles())
        self.text = "Piloto" if count == 0 else f"Piloto {count + 1}"
        self.message = ""

    def _begin_rename(self, profile) -> None:
        self._return_selection = self.selection
        self.mode = "rename"
        self.text = profile.name
        self.message = ""

    def _begin_delete(self) -> None:
        self._return_selection = self.selection
        self.mode = "delete"
        self.text = ""
        self.dialog_choice = 1
        self.message = ""

    def _action(self, action: str) -> None:
        profiles = self._profiles()
        if action == "new":
            if len(profiles) >= self.menu.jogo.profile_service.max_profiles:
                self.message = (f"Limite de "
                                f"{self.menu.jogo.profile_service.max_profiles} perfis")
                return
            self._begin_create()
            return
        if self.selection >= len(profiles):
            return
        profile = profiles[self.selection]
        if action == "activate":
            if profile.damaged:
                self.message = "Perfil danificado; não é possível ativá-lo."
                return
            try:
                self.menu.jogo.ativar_perfil(profile.id)
                self.menu._som("navegar")
                self.message = f"Perfil ativo: {profile.name}"
                self.refresh()
            except (ValueError, OSError) as exc:
                self.message = str(exc)
        elif action == "rename":
            self._begin_rename(profile)
        elif action == "delete":
            if self._profile_in_game(profile):
                self.message = "O perfil está em uso numa partida; encerre-a antes de excluir."
            else:
                self._begin_delete()
        elif action == "export":
            active = self.menu.jogo.profile_service.active
            if not active or active.id != profile.id:
                self.message = "Ative este perfil para exportá-lo."
                return
            path = Path.cwd() / "exports" / f"perfil-{profile.id}.json"
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                if self.menu.jogo.profile_service.export_active(path):
                    self.message = f"Perfil exportado: exports/{path.name}"
                else:
                    self.message = "Não foi possível exportar o perfil."
            except (OSError, ValueError) as exc:
                self.message = str(exc)

    def _confirm(self) -> None:
        service = self.menu.jogo.profile_service
        profiles = self._profiles()
        profile = profiles[self.selection] if self.selection < len(profiles) else None
        try:
            if self.mode == "create":
                created = service.create(self.text)
                self.menu.jogo.ativar_perfil(created.id)
                self.mode, self.text = None, ""
                self.message = f"Perfil ativo: {created.name}"
                self.menu._som("navegar")
                self.refresh()
            elif self.mode == "rename" and profile:
                renamed = service.rename(profile.id, self.text)
                if service.active and service.active.id == renamed.id:
                    self.menu.jogo.nome_jogador = renamed.name
                    self.menu.jogo.progresso.jogador["nome"] = renamed.name
                self.mode, self.text, self.message = None, "", ""
                self.refresh()
            elif self.mode == "delete" and profile:
                if self.dialog_choice == 1:
                    self._cancel_dialog()
                    return
                if self._profile_in_game(profile):
                    self.message = "O perfil está em uso numa partida; encerre-a antes de excluir."
                    return
                service.delete(profile.id, self.text, in_game=False)
                self.selection = min(self.selection, max(0, len(profiles) - 2))
                if service.active is None:
                    self.menu.jogo.progresso.carregar_ativo()
                    self.menu.jogo.loja = self.menu.jogo.loja.__class__()
                self.mode, self.text, self.message = None, "", ""
                self.refresh()
        except (ValueError, OSError) as exc:
            self.message = str(exc)

    def _cancel_dialog(self) -> None:
        self.selection = self._return_selection
        self.mode, self.text, self.message = None, "", ""

    def handle_event(self, event: pygame.event.Event) -> None:
        """Processa texto, foco por teclado e hover/cliques no cartão."""
        profiles = self._profiles()
        if event.type == pygame.KEYDOWN:
            if self.mode == "delete":
                if event.key == pygame.K_ESCAPE:
                    self._cancel_dialog()
                elif event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT,
                                   pygame.K_d):
                    self.dialog_choice = 1 - self.dialog_choice
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if self.dialog_choice == 1:
                        self._cancel_dialog()
                    else:
                        self._confirm()
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.unicode and event.unicode.isprintable():
                    if len(self.text) < self.menu.jogo.profile_service.max_name_length:
                        self.text += event.unicode
                return
            if self.mode:
                if event.key == pygame.K_ESCAPE:
                    self._cancel_dialog()
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._confirm()
                elif event.unicode and event.unicode.isprintable():
                    if len(self.text) < self.menu.jogo.profile_service.max_name_length:
                        self.text += event.unicode
                return
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selection = (self.selection - 1) % (len(profiles) + 1)
                self.message = ""
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selection = (self.selection + 1) % (len(profiles) + 1)
                self.message = ""
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._action("new" if self.selection == len(profiles) else "activate")
            elif event.key in (pygame.K_n, pygame.K_PLUS, pygame.K_KP_PLUS):
                self._action("new")
            elif event.key == pygame.K_r:
                self._action("rename")
            elif event.key == pygame.K_DELETE:
                self._action("delete")
            elif event.key == pygame.K_x:
                self._action("export")
            elif event.key == pygame.K_ESCAPE and self.menu.jogo.profile_service.active:
                self.menu._som("navegar")
                self.menu.subestado = "MENU"
        elif event.type == pygame.MOUSEMOTION and not self.mode:
            pos = self.menu._pos_logica(event.pos)
            for row, rect in enumerate(self.cards):
                if rect.collidepoint(pos):
                    self.selection = (self._visible_profile_indices[row]
                                      if row < len(self._visible_profile_indices)
                                      else len(profiles))
                    break
        elif event.type == pygame.MOUSEWHEEL and not self.mode:
            self.selection = max(0, min(len(profiles),
                                         self.selection - event.y))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.menu._pos_logica(event.pos)
            if self.mode == "delete":
                for index, rect in enumerate(self.buttons):
                    if rect.collidepoint(pos):
                        self.dialog_choice = index
                        if index == 0:
                            self._confirm()
                        else:
                            self._cancel_dialog()
                        return
            if self.mode:
                return
            for row, rect in enumerate(self.cards):
                if rect.collidepoint(pos):
                    index = (self._visible_profile_indices[row]
                             if row < len(self._visible_profile_indices)
                             else len(profiles))
                    self.selection = index
                    self._action("new" if index == len(profiles) else "activate")
                    return
