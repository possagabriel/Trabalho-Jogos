"""Hubs de navegação para as ações Jogar e Perfil."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.infrastructure.graphics.theme import MENU_RESUMO_CONTINUAR_FONT_SIZE
from src.runtime.infrastructure.graphics.menu_animation import FocoAnimado, desenhar_trilha_foco
from src.runtime.infrastructure.graphics.menu_panels import (
    ACENTO_ORIGINAL,
    TEXTO_ATIVO_ORIGINAL,
    TEXTO_ORIGINAL,
    icone_menu_original,
    painel_menu,
    texto_painel,
)

if TYPE_CHECKING:
    from src.runtime.presentation.menu import MenuPrincipal


class MenuHubScreen:
    """Oferece destinos de segundo nível sem alterar as telas de destino."""

    def __init__(self, menu: MenuPrincipal, kind: str) -> None:
        self.menu = menu
        self.kind = kind
        self.selection = 0
        self._text_cache: dict[tuple, pygame.Surface] = {}
        self.focos = [FocoAnimado() for _ in self.entries]
        self.efeitos_reduzidos = False

    def atualizar_animacao(self, dt: float, *, reduzido: bool = False) -> None:
        """Move o foco das opções sem deslocar suas áreas clicáveis."""
        self.efeitos_reduzidos = reduzido
        for indice, foco in enumerate(self.focos):
            foco.atualizar(indice == self.selection, dt, reduzido=reduzido)

    @property
    def entries(self) -> tuple[tuple[str, str], ...]:
        if self.kind == "JOGAR":
            return (("CONTINUAR", "continuar"), ("LINEAR", "linear"),
                    ("MUNDO ABERTO", "mundo_aberto"))
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
        height = layout.px(450)
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
        row_height = layout.px(82)
        margin = layout.px(28 if narrow else 32)
        gap = layout.px(12)
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
        """Compartilha hierarquia, ícones e resumos nos dois acabamentos."""
        menu, layout = self.menu, self.menu.layout
        panel = self._panel()
        surface.blit(painel_menu(panel.size, (0, 0, 0), ACENTO_ORIGINAL,
                                  raio=layout.px(16)), panel)
        title = texto_painel(menu.fonte_cabecalho, self.kind, TEXTO_ORIGINAL,
                             panel.w - layout.px(48), layout.px(42))
        surface.blit(title, title.get_rect(midtop=(panel.centerx, panel.y + layout.px(26))))
        for index, ((label, action), rect) in enumerate(zip(self.entries, self._rects())):
            disabled = action == "continuar" and not menu._tem_save()
            selected = index == self.selection and not disabled
            color = TEXTO_ATIVO_ORIGINAL if selected else TEXTO_ORIGINAL
            conteudo = self._desenhar_opcao_original(surface, rect, action, index, disabled)
            recuo = round(layout.px(8) * self.focos[index].valor)
            self._desenhar_cartao(surface, conteudo.move(recuo, 0), label, action, color)
            if self.kind == "PERFIL" and action == "memorias" and menu._novidades("memorias"):
                self._badge(surface, rect, ACENTO_ORIGINAL)
        self._desenhar_voltar(surface)

    def _desenhar_opcao_original(self, surface: pygame.Surface, rect: pygame.Rect,
                                  action: str, index: int, disabled: bool) -> pygame.Rect:
        menu, layout = self.menu, self.menu.layout
        selected = index == self.selection and not disabled
        surface.blit(painel_menu(rect.size, (0, 0, 0), ACENTO_ORIGINAL,
                                     selecionado=selected, raio=layout.px(10), botao=True), rect)
        icone = icone_menu_original(action, selected, layout.px(30), desabilitado=disabled)
        surface.blit(icone, icone.get_rect(center=(rect.x + layout.px(29), rect.centery)))
        if not disabled:
            desenhar_trilha_foco(surface, rect, layout,
                                 menu.animacao_original.tempo, self.focos[index].valor,
                                 reduzido=self.efeitos_reduzidos)
        return pygame.Rect(rect.x + layout.px(56), rect.y,
                           rect.width - layout.px(72), rect.height)

    def _desenhar_voltar(self, surface: pygame.Surface) -> None:
        menu = self.menu
        rect = self._back_rect()
        hover = rect.collidepoint(menu.mouse)
        surface.blit(painel_menu(rect.size, (0, 0, 0), ACENTO_ORIGINAL,
                                  selecionado=hover, botao=True, segmentado=False), rect)
        cor = TEXTO_ATIVO_ORIGINAL if hover else TEXTO_ORIGINAL
        hint = texto_painel(menu.fonte_pequena, "ESC  VOLTAR", cor,
                            rect.width - menu.layout.px(12), rect.height)
        surface.blit(hint, hint.get_rect(center=rect.center))

    def _badge(self, surface: pygame.Surface, rect: pygame.Rect,
               color: tuple[int, int, int]) -> None:
        menu = self.menu
        badge = pygame.Rect(0, 0, menu.layout.px(78), menu.layout.px(27))
        badge.midright = (rect.right - menu.layout.px(12), rect.centery)
        surface.blit(painel_menu(badge.size, (0, 0, 0), ACENTO_ORIGINAL,
                                  selecionado=True, botao=True, segmentado=False), badge)
        text = texto_painel(menu.fonte_pequena, "NOVO", TEXTO_ATIVO_ORIGINAL,
                            badge.width - menu.layout.px(10), badge.height - menu.layout.px(4))
        surface.blit(text, text.get_rect(center=badge.center))

    def _desenhar_cartao(self, surface: pygame.Surface, rect: pygame.Rect,
                         label: str, action: str,
                         color: tuple[int, int, int]) -> None:
        menu = self.menu
        heading = texto_painel(menu.fonte_opcao, label, tuple(color[:3]),
                               rect.width - menu.layout.px(32), menu.layout.px(26))
        if self.kind != "JOGAR":
            surface.blit(heading, heading.get_rect(center=rect.center))
            return
        details = self._detalhes_cartao(action)
        font = menu.layout.fonte_texto(
            max(14, MENU_RESUMO_CONTINUAR_FONT_SIZE - 4))
        surface.blit(heading, heading.get_rect(
            midtop=(rect.centerx, rect.y + menu.layout.px(8))))
        for index, detail in enumerate(details):
            cor_detalhe = (TEXTO_ATIVO_ORIGINAL if color == TEXTO_ATIVO_ORIGINAL
                           else (210, 220, 240))
            detail_surface = texto_painel(
                font, detail, cor_detalhe, rect.width - menu.layout.px(32),
                menu.layout.px(19))
            surface.blit(detail_surface, detail_surface.get_rect(
                midtop=(rect.centerx, rect.y + menu.layout.px(39 + index * 21))))

    def _detalhes_cartao(self, action: str) -> tuple[str, str]:
        service = self.menu.jogo.profile_service
        if action == "continuar":
            summary = service.continue_summary() or {}
            if not self.menu._tem_save():
                return ("SEM PARTIDA SALVA", "ESCOLHA UM MODO PARA COMEÇAR")
            mode = summary.get("mode", "linear").replace("_", " ").upper()
            if summary.get("mode") == "mundo_aberto":
                return (f"MODO {mode}",
                        f"CHECKPOINT {summary.get('level', 'início')}")
            return (f"MODO {mode} · DIM. {summary.get('dimension', 1)}",
                    f"NÍVEL {summary.get('level', 1)}")
        mode = "linear" if action == "linear" else "mundo_aberto"
        summary = service.mode_progress_summary(mode) or {}
        hours, remainder = divmod(summary.get("play_time", 0), 3600)
        minutes = remainder // 60
        coins = f"{summary.get('coins', 0):,}".replace(",", ".")
        if action == "linear":
            status = "CONTINUAR" if summary.get("started") else "NOVO"
            return (f"{status} · DIM. {summary.get('dimension', 1)} · NÍVEL "
                    f"{summary.get('level', 1)} · BOSSES {summary.get('bosses', 0)}/6",
                    f"MOEDAS {coins} · TEMPO {hours:02d}h{minutes:02d}")
        status = "CONTINUAR" if summary.get("started") else "NOVO"
        return (f"{status} · REGIÕES {summary.get('regions', 0)}/6 · ECOS "
                f"{summary.get('echoes', 0)} · BOSSES {summary.get('bosses', 0)}/6",
                f"MOEDAS {coins} · TEMPO {hours:02d}h{minutes:02d}")

    def tratar_tecla(self, event: pygame.event.Event) -> bool:
        if event.key == pygame.K_TAB:
            passo = -1 if getattr(event, "mod", 0) & pygame.KMOD_SHIFT else 1
            self.selection = (self.selection + passo) % len(self.entries)
            self.menu._som("navegar")
        elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
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
            summary = menu.jogo.profile_service.continue_summary() or {}
            strategy = menu.mode_strategies.get(summary.get("mode", "linear"))
            if strategy is None or not strategy.continue_game(menu.jogo):
                menu._som("erro")
                menu.notificacoes.adicionar("Modo salvo indisponível", "erro")
        elif action in {"linear", "mundo_aberto"}:
            strategy = menu.mode_strategies[action]
            if not strategy.start_new(menu.jogo):
                menu._som("erro")
                menu.notificacoes.adicionar(
                    "Mundo Aberto estará disponível na próxima etapa.", "info")
        elif action == "pilotos":
            menu._abrir_perfis()
        elif action == "recordes":
            menu._abrir_recordes()
        elif action == "memorias":
            menu._abrir_arquivo()
