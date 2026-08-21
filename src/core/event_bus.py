"""Event bus com padrao Observer — desacoplamento entre subsystemas.

Singleton que permite que qualquer parte do jogo publique ``GameEvent`` e
que qualquer interessado registre callbacks para tipos especificos de evento.
Evita o acoplamento direto entre classes (ex.: player nao precisa conhecer
o HUD para avisar que houve combo change).

Uso::

    bus = EventBus()
    bus.subscribe(GameEventType.SCBORE_CHANGED, meu_callback)
    bus.publish(GameEvent(GameEventType.SCORE_CHANGED, score=100))
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tipos de evento
# ---------------------------------------------------------------------------

class GameEventType(Enum):
    """Enumeracao de todos os eventos possiveis no jogo."""

    # Lifecycle
    GAME_START = auto()
    GAME_OVER = auto()
    LEVEL_UP = auto()
    PAUSE_TOGGLE = auto()

    # Player
    PLAYER_HIT = auto()
    PLAYER_DIED = auto()
    PLAYER_SHOOT = auto()

    # Enemies
    ENEMY_SPAWNED = auto()
    ENEMY_DEFEATED = auto()
    BOSS_SPAWNED = auto()
    BOSS_DEFEATED = auto()

    # Score / progression
    SCORE_CHANGED = auto()
    COMBO_CHANGED = auto()
    POWERUP_COLLECTED = auto()


# ---------------------------------------------------------------------------
# Evento
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class GameEvent:
    """Evento imutavel transmitido pelo bus.

    Attributes:
        type: Tipo do evento (enum).
        data: Dicionario generico com metadados arbitrarios.
    """

    type: GameEventType
    data: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Callback type
# ---------------------------------------------------------------------------

EventListener = Callable[[GameEvent], None]
"""Signature: ``(event: GameEvent) -> None``."""


# ---------------------------------------------------------------------------
# EventBus (Singleton)
# ---------------------------------------------------------------------------

class EventBus:
    """Central de publicacao/inscricao de eventos (Observer pattern).

    Implementado como Singleton para que todos os subsystemas compartilhem
    a mesma instancia.
    """

    _instancia: EventBus | None = None

    def __new__(cls) -> EventBus:
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._initialized = False
        return cls._instancia

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._listeners: dict[GameEventType, list[EventListener]] = {}

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def subscribe(self, event_type: GameEventType,
                  listener: EventListener) -> None:
        """Registra um callback para um tipo de evento.

        Se o callback ja estiver registrado, a chamada e ignorada.
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        if listener not in self._listeners[event_type]:
            self._listeners[event_type].append(listener)

    def unsubscribe(self, event_type: GameEventType,
                    listener: EventListener) -> None:
        """Remove um callback previamente registrado."""
        try:
            self._listeners[event_type].remove(listener)
        except (KeyError, ValueError):
            pass

    def publish(self, event: GameEvent) -> None:
        """Dispara um evento, notificando todos os listeners inscritos.

        Erros individuais sao logados mas nao interrompem a execucao
        dos listeners seguintes.
        """
        listeners = self._listeners.get(event.type, [])
        for listener in listeners:
            try:
                listener(event)
            except Exception:
                logger.exception(
                    "Erro ao executar listener %s para evento %s",
                    listener, event.type.name)

    def clear(self) -> None:
        """Remove todos os listeners (util em testes ou reset)."""
        self._listeners.clear()
