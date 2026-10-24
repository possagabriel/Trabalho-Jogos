"""Adaptadores de Strategy para os fluxos LINEAR e MUNDO ABERTO."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

import pygame

from src.core.constants import EstadoJogo
from src.infrastructure.graphics.comic_theme import usar_visual

if TYPE_CHECKING:
    from src.runtime.application.core import Jogo
    from src.runtime.domain.world.open_world import OpenWorldRuntime


class ModeStrategy(Protocol):
    """Contrato mínimo para conectar um modo ao loop e à persistência comuns."""

    mode_id: str
    handles_gameplay: bool

    def start_new(self, game: Jogo) -> bool: ...

    def continue_game(self, game: Jogo) -> bool: ...

    def update(self, game: Jogo, dt: float) -> None: ...

    def handle_event(self, game: Jogo, event: pygame.event.Event) -> bool: ...

    def render(self, game: Jogo, surface: pygame.Surface) -> bool: ...

    def save(self, game: Jogo) -> None: ...


class LinearModeStrategy:
    """Encaminha o modo LINEAR aos controladores que já governam a campanha."""

    mode_id = "linear"
    handles_gameplay = False

    def start_new(self, game: Jogo) -> bool:
        game.modo_atual = self.mode_id
        game.profile_service.set_last_mode(self.mode_id)
        game.menu._abrir_fases(nova_campanha=True)
        return True

    def continue_game(self, game: Jogo) -> bool:
        if not game.progresso.existe_save():
            return False
        game.modo_atual = self.mode_id
        game.profile_service.set_last_mode(self.mode_id)
        game.menu.phase_screen.cancelar_nova_campanha()
        game.menu.phase_screen.refresh()
        game.menu._iniciar_missao(game.menu.phase_screen.confirm)
        return True

    def update(self, game: Jogo, dt: float) -> None:
        del game, dt  # O loop e os controladores LINEAR mantêm a atualização atual.

    def handle_event(self, game: Jogo, event: pygame.event.Event) -> bool:
        del game, event
        return False

    def render(self, game: Jogo, surface: pygame.Surface) -> bool:
        del game, surface
        return False

    def save(self, game: Jogo) -> None:
        game.progressao_controller.salvar_tudo()


class OpenWorldModeStrategy:
    """Conecta o primeiro mundo contínuo ao loop e ao balde próprio do modo."""

    mode_id = "mundo_aberto"
    handles_gameplay = True

    def __init__(self) -> None:
        self.world: OpenWorldRuntime | None = None

    def start_new(self, game: Jogo) -> bool:
        from src.runtime.domain.world.open_world import OpenWorldRuntime

        if game.profile_service.active is None:
            return False
        self.world = OpenWorldRuntime(visual_config=game.config)
        game.modo_atual = self.mode_id
        game.profile_service.set_last_mode(self.mode_id)
        modes = game.profile_service.active.progress.get("modos", {})
        state = modes.get(self.mode_id, {}) if isinstance(modes, dict) else {}
        sessions = state.get("partidas_jogadas", 0) if isinstance(state, dict) else 0
        game.profile_service.update_mode_progress(
            self.mode_id,
            partidas_jogadas=(sessions + 1 if type(sessions) is int else 1),
            regioes_libertas=0,
            ecos=0,
            bosses=0,
            moedas=0,
        )
        game.tempo_partida = 0
        game.estado = EstadoJogo.JOGANDO
        self.save(game)
        return True

    def continue_game(self, game: Jogo) -> bool:
        from src.runtime.domain.world.open_world import OpenWorldRuntime

        profile = game.profile_service.active
        if profile is None:
            return False
        modes = profile.progress.get("modos", {})
        state = modes.get(self.mode_id, {}) if isinstance(modes, dict) else {}
        position = state.get("posicao") if isinstance(state, dict) else None
        if (not isinstance(state, dict)
                or not state.get("partidas_jogadas")
                or not isinstance(position, (list, tuple))
                or len(position) != 2):
            return False
        try:
            point = (float(position[0]), float(position[1]))
            elapsed = max(0.0, float(state.get("tempo", 0)))
        except (TypeError, ValueError):
            return False
        self.world = OpenWorldRuntime(point, elapsed, game.config)
        game.modo_atual = self.mode_id
        game.profile_service.set_last_mode(self.mode_id)
        game.tempo_partida = elapsed
        game.estado = EstadoJogo.JOGANDO
        return True

    def update(self, game: Jogo, dt: float) -> None:
        if self.world is None or game.estado is not EstadoJogo.JOGANDO:
            return
        self.world.update(dt, pygame.key.get_pressed(), game.controles, game)
        game.tempo_partida = self.world.elapsed

    def handle_event(self, game: Jogo, event: pygame.event.Event) -> bool:
        if (game.estado is EstadoJogo.JOGANDO
                and event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE, pygame.K_p,
                game.controles.get("pausar", pygame.K_p))):
            game.estado = EstadoJogo.PAUSA
            return True
        return False

    def render(self, game: Jogo, surface: pygame.Surface) -> bool:
        if self.world is None:
            return False
        if game.estado not in (EstadoJogo.JOGANDO, EstadoJogo.PAUSA,
                               EstadoJogo.GAME_OVER):
            return False
        with usar_visual(
                game.config, acabamento_gpu=game.shader_comic_ativo()):
            self.world.render(surface, game.jogador)
        return True

    def save(self, game: Jogo) -> None:
        if self.world is not None:
            game.profile_service.update_mode_progress(
                self.mode_id, **self.world.save_state())
