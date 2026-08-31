"""Garante a organizacao do runtime canônico e suas fachadas publicas."""

from __future__ import annotations

import importlib

import pytest

FACHADAS_COMPATIVEIS = {
    "game.core": "src.runtime.application.core",
    "game.combat_controller": "src.runtime.controllers.combat",
    "game.loop_controller": "src.runtime.controllers.loop",
    "game.player": "src.runtime.domain.entities.player",
    "game.enemies": "src.runtime.domain.entities.enemies",
    "game.bosses": "src.runtime.domain.entities.bosses",
    "game.weapons": "src.runtime.domain.entities.weapons",
    "game.powerups": "src.runtime.domain.entities.powerups",
    "game.scenarios": "src.runtime.domain.world.scenarios",
    "game.particles": "src.runtime.domain.world.particles",
    "game.save_system": "src.runtime.infrastructure.persistence.save_system",
    "game.shop": "src.runtime.infrastructure.persistence.shop",
    "game.menu": "src.runtime.presentation.menu",
    "game.hud": "src.runtime.presentation.hud",
}


@pytest.mark.parametrize(("nome_legado", "nome_canonico"), FACHADAS_COMPATIVEIS.items())
def test_fachada_compativel_referencia_o_mesmo_modulo_canonico(
        nome_legado: str, nome_canonico: str) -> None:
    """Uma escrita no import histórico continua atingindo a fonte canônica."""
    assert importlib.import_module(nome_legado) is importlib.import_module(nome_canonico)
