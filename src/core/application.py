"""Aplicacao principal — loop do jogo, janela pygame e integracao.

A classe ``Application`` e o entry-point que:
1. Inicializa o pygame e cria a janela/janela fullscreen.
2. Gerencia o relogio (delta_time).
3. Integra a ``GameContext`` (maquina de estados) e o ``EventBus``.
4. Executa o loop principal: eventos → update → render → flip.

Variante interna ``_Jogo`` adapta o jogo existente para rodar dentro
dessa estrutura ate que os estados concretos sejam totalmente
implementados.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pygame

from .constants import ALTURA, FPS, LARGURA, TITULO, VOID_BLACK
from .event_bus import EventBus, GameEvent, GameEventType
from .settings import Configuracoes, parse_resolucao
from .state_machine import GameContext

if TYPE_CHECKING:
    pass


class Application:
    """Ponto de entrada principal do VOID//SHIFT.

    Responsabilidades:
    - Inicializar pygame e criar a janela.
    - Manter o relogio e calcular ``delta_time``.
    - Alimentar a maquina de estados e o event bus.
    - Encerrar limpo ao receber ``QUIT``.
    """

    def __init__(self) -> None:
        # --- pygame core ---
        pygame.init()

        self.config = Configuracoes()
        self.event_bus = EventBus()
        self.state_machine = GameContext()

        # --- janela ---
        self.window = self._create_window()
        pygame.display.set_caption(TITULO)
        pygame.display.set_icon(self._create_icon())

        # superficie logica (tamanho constante 900x700)
        self.surface = pygame.Surface((LARGURA, ALTURA))

        self.clock = pygame.time.Clock()
        self.running = True

        # compat: legado Jogo pode ser injetado aqui
        self._legacy_game: Any = None

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------

    def _create_window(self) -> pygame.Surface:
        """Cria a janela do jogo conforme configuracoes salvas."""
        if self.config["tela_cheia"]:
            try:
                w, h = pygame.display.get_desktop_sizes()[0]
            except (IndexError, pygame.error):
                w, h = parse_resolucao(self.config["resolucao"])
            return pygame.display.set_mode((w, h), pygame.FULLSCREEN)
        w, h = parse_resolucao(self.config["resolucao"])
        return pygame.display.set_mode((w, h))

    def _create_icon(self) -> pygame.Surface:
        """Gera o icone 32x32 da janela."""
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        from .constants import RIFT_MAGENTA, QUANTUM_CYAN
        # glow basico
        for r in range(14, 0, -1):
            alpha = int(90 * (r / 14))
            pygame.draw.circle(surf, RIFT_MAGENTA + (alpha,), (16, 16), r)
        # seta/rift
        pygame.draw.polygon(
            surf, RIFT_MAGENTA,
            [(8, 4), (12, 4), (16, 20), (20, 4), (24, 4), (16, 26)])
        pygame.draw.line(surf, QUANTUM_CYAN, (26, 6), (22, 24), 2)
        pygame.draw.line(surf, QUANTUM_CYAN, (30, 6), (26, 24), 2)
        return surf

    # ------------------------------------------------------------------
    # Apresentacao (escala-to-fit)
    # ------------------------------------------------------------------

    def _present(self) -> None:
        """Redimensiona ``self.surface`` para a janela com letterbox."""
        w, h = self.window.get_size()
        if (w, h) == (LARGURA, ALTURA):
            self.window.blit(self.surface, (0, 0))
        else:
            scale = min(w / LARGURA, h / ALTURA)
            ox = (w - LARGURA * scale) / 2
            oy = (h - ALTURA * scale) / 2
            scaled = pygame.transform.smoothscale(
                self.surface,
                (max(1, int(LARGURA * scale)), max(1, int(ALTURA * scale))))
            self.window.fill(VOID_BLACK)
            self.window.blit(scaled, (int(ox), int(oy)))
        pygame.display.flip()

    # ------------------------------------------------------------------
    # Loop principal
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Loop principal do jogo.

        Calcula ``delta_time`` a cada frame e delega para a maquina de
        estados. Encerra quando ``self.running`` se torna ``False`` ou
        quando o usuario fecha a janela.
        """
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                    break
                self.state_machine.handle_event(event)
                # legado: repassa ao jogo antigo enquanto nao migrado
                if self._legacy_game is not None:
                    # o Jogo original controla seus proprios eventos
                    pass

            if not self.running:
                break

            self.state_machine.update(dt)
            self.state_machine.render(self.surface)
            self._present()

            # legado
            if self._legacy_game is not None:
                self._legacy_game.relogio.tick(FPS)

        pygame.quit()
        sys.exit(0)

    # ------------------------------------------------------------------
    # Controle externo
    # ------------------------------------------------------------------

    def quit(self) -> None:
        """Solicita o encerramento da aplicacao."""
        self.running = False
        self.event_bus.publish(GameEvent(GameEventType.GAME_OVER))

    def set_legacy_game(self, jogo: Any) -> None:
        """Conecta o jogo legado ``Jogo`` ao loop da Application.

        Removido quando todos os estados migrarem para a nova
        arquitetura.
        """
        self._legacy_game = jogo
