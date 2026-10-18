"""Seleção e gerenciamento local de perfis em painéis cartoon."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.core.constants import CIANO, DOURADO, VERDE, VERMELHO, VOID_BLACK

if TYPE_CHECKING:
    from src.runtime.presentation.menu import MenuPrincipal


class ProfileScreen:
    """Oferece CRUD por teclado ou mouse antes de iniciar uma partida."""

    ACTIONS = ("SELECIONAR", "CRIAR", "RENOMEAR", "EXCLUIR", "VOLTAR")

    def __init__(self, menu: MenuPrincipal) -> None:
        self.menu = menu
        self.selection = 0
        self.mode: str | None = None
        self.text = ""
        self.message = ""
        self.buttons: list[pygame.Rect] = []
        self.cards: list[pygame.Rect] = []
        self._entries = None
        last = menu.jogo.profile_service.index.get("last_used")
        for index, profile in enumerate(self._profiles()):
            if profile.id == last and not profile.damaged:
                self.selection = index
                break

    def _profiles(self):
        if self._entries is None:
            self._entries = self.menu.jogo.profile_service.list_profiles()
        return self._entries

    def refresh(self) -> None:
        """Atualiza o resumo após uma operação ou ao abrir a tela."""
        self._entries = self.menu.jogo.profile_service.list_profiles()

    def draw(self, surface: pygame.Surface) -> None:
        """Mostra progresso resumido, último acesso e entradas danificadas."""
        layout = self.menu.layout
        scale = layout.escala
        w, h = layout.largura, layout.altura
        title = self.menu.fonte_cabecalho.render("PERFIS DE JOGADOR", True, CIANO)
        surface.blit(title, title.get_rect(center=(w // 2, int(52 * scale))))
        profiles = self._profiles()
        self.cards = []
        for i, profile in enumerate(profiles):
            rect = pygame.Rect(int(90 * scale), int((95 + 87 * i) * scale),
                               w - int(180 * scale), int(76 * scale))
            self.cards.append(rect)
            pygame.draw.rect(surface, (20, 31, 50), rect, border_radius=int(10 * scale))
            border = DOURADO if i == self.selection else CIANO
            pygame.draw.rect(surface, border, rect, max(2, int(2 * scale)),
                             border_radius=int(10 * scale))
            name = self.menu.fonte_media.render(profile.name, True, border)
            surface.blit(name, (rect.x + int(16 * scale), rect.y + int(8 * scale)))
            if profile.damaged:
                detail = "DANIFICADO — arquivo e backup ilegíveis"
            else:
                p = profile.progress
                detail = (f"{p['moedas']} moedas  •  {len(p['armas_desbloqueadas'])} armas  •  "
                          f"{len(p['skins_desbloqueadas'])} skins  •  "
                          f"Dimensão {p['dimensao_maxima']}  •  "
                          f"{len(p['bosses_por_tipo'])} bosses  •  "
                          f"Acesso {profile.last_access[:16]}")
            line = self.menu.fonte_pequena.render(detail, True,
                                                   VERMELHO if profile.damaged else VERDE)
            surface.blit(line, (rect.x + int(17 * scale), rect.y + int(43 * scale)))
        if not profiles:
            line = self.menu.fonte_media.render("Crie seu primeiro perfil para jogar.",
                                                 True, CIANO)
            surface.blit(line, line.get_rect(center=(w // 2, h // 2)))
        self.buttons = []
        button_w = (w - int(100 * scale)) // len(self.ACTIONS)
        for i, label in enumerate(self.ACTIONS):
            rect = pygame.Rect(int(50 * scale) + i * button_w,
                               h - int(80 * scale), button_w - int(7 * scale),
                               int(48 * scale))
            self.buttons.append(rect)
            pygame.draw.rect(surface, (25, 44, 69), rect,
                             border_radius=int(9 * scale))
            pygame.draw.rect(surface, CIANO, rect, 2, border_radius=int(9 * scale))
            line = self.menu.fonte_pequena.render(label, True, CIANO)
            surface.blit(line, line.get_rect(center=rect.center))
        if self.mode:
            cover = pygame.Surface((w, h), pygame.SRCALPHA)
            cover.fill((*VOID_BLACK, 225))
            surface.blit(cover, (0, 0))
            instruction = ("DIGITE O NOME DO PERFIL PARA EXCLUIR" if self.mode == "delete"
                           else "NOVO NOME" if self.mode == "rename" else "NOME DO PERFIL")
            for line, y in ((instruction, h // 2 - int(70 * scale)),
                            (self.text + "_", h // 2),
                            ("ENTER confirma • ESC cancela", h // 2 + int(65 * scale))):
                image = self.menu.fonte_media.render(line, True, CIANO)
                surface.blit(image, image.get_rect(center=(w // 2, y)))
        if self.message or self.menu.jogo.profile_service.migration_error:
            warning = self.message or "Save antigo danificado; crie um perfil novo."
            line = self.menu.fonte_pequena.render(warning, True, VERMELHO)
            surface.blit(line, line.get_rect(center=(w // 2, h - int(103 * scale))))

    def _action(self, index: int) -> None:
        service = self.menu.jogo.profile_service
        profiles = self._profiles()
        profile = profiles[self.selection] if self.selection < len(profiles) else None
        if index == 0 and profile:
            try:
                self.menu.jogo.ativar_perfil(profile.id)
                self.message = ""
            except (ValueError, OSError) as exc:
                self.message = str(exc)
        elif index == 1:
            if len(profiles) >= service.max_profiles:
                self.message = "Limite de perfis atingido"
            else:
                self.mode, self.text = "create", ""
        elif index in (2, 3) and profile:
            self.mode = "rename" if index == 2 else "delete"
            self.text = profile.name if index == 2 else ""
        elif index == 4 and service.active:
            self.menu.subestado = "MENU"

    def _confirm(self) -> None:
        service = self.menu.jogo.profile_service
        profiles = self._profiles()
        profile = profiles[self.selection] if self.selection < len(profiles) else None
        try:
            if self.mode == "create":
                created = service.create(self.text)
                self.selection = len(profiles)
                self.menu.jogo.ativar_perfil(created.id)
            elif self.mode == "rename" and profile:
                renamed = service.rename(profile.id, self.text)
                if service.active and service.active.id == renamed.id:
                    self.menu.jogo.nome_jogador = renamed.name
                    self.menu.jogo.progresso.jogador["nome"] = renamed.name
            elif self.mode == "delete" and profile:
                service.delete(profile.id, self.text,
                               in_game=self.menu.jogo.estado.value != "MENU")
                self.selection = min(self.selection, max(0, len(profiles) - 2))
                if service.active is None:
                    self.menu.jogo.progresso.carregar_ativo()
                    self.menu.jogo.loja = self.menu.jogo.loja.__class__()
            self.mode, self.text, self.message = None, "", ""
            self.refresh()
        except (ValueError, OSError) as exc:
            self.message = str(exc)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Processa texto Unicode, navegação padrão e cliques."""
        profiles = self._profiles()
        if event.type == pygame.KEYDOWN:
            if self.mode:
                if event.key == pygame.K_ESCAPE:
                    self.mode, self.text = None, ""
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._confirm()
                elif event.unicode and event.unicode.isprintable():
                    if len(self.text) < self.menu.jogo.profile_service.max_name_length:
                        self.text += event.unicode
                return
            if event.key in (pygame.K_UP, pygame.K_w) and profiles:
                self.selection = (self.selection - 1) % len(profiles)
            elif event.key in (pygame.K_DOWN, pygame.K_s) and profiles:
                self.selection = (self.selection + 1) % len(profiles)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._action(0 if profiles else 1)
            elif event.key == pygame.K_n:
                self._action(1)
            elif event.key == pygame.K_r:
                self._action(2)
            elif event.key == pygame.K_DELETE:
                self._action(3)
            elif event.key == pygame.K_ESCAPE:
                self._action(4)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.menu._pos_logica(event.pos)
            if self.mode:
                return
            for i, rect in enumerate(self.cards):
                if rect.collidepoint(pos):
                    self.selection = i
                    return
            for i, rect in enumerate(self.buttons):
                if rect.collidepoint(pos):
                    self._action(i)
                    return
