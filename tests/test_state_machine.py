"""Testes da maquina de estados e dos adaptadores de callbacks."""

from __future__ import annotations

from src.core.state_machine import GameContext, MenuState


def test_estado_de_callbacks_delega_ciclo_de_vida() -> None:
    chamadas: list[object] = []
    contexto = GameContext()
    estado = MenuState(
        contexto,
        on_enter=lambda: chamadas.append("enter"),
        on_exit=lambda: chamadas.append("exit"),
        on_update=lambda dt: chamadas.append(dt),
        on_render=lambda superficie: chamadas.append(superficie),
    )
    contexto.change_state(estado)
    contexto.update(0.25)
    marcador = object()
    contexto.render(marcador)
    contexto.change_state(MenuState(contexto))
    assert chamadas == ["enter", 0.25, marcador, "exit"]
