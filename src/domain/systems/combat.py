"""CombatSystem - handles damage, scoring, and combat events.

Extracted from game/core.py collision/combat logic.
"""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.domain.entities.bosses.types import Boss
    from src.domain.entities.enemies.base import Enemy
    from src.domain.entities.enemies.factory import SpecialEnemy
    from src.domain.entities.player import Player
    from src.domain.entities.projectiles.factory import Projetil


class CombatEvent:
    """Represents a combat event generated during resolution."""

    def __init__(self, kind: str, data: Optional[dict] = None) -> None:
        self.kind: str = kind
        self.data: dict = data or {}


class CombatSystem:
    """Resolves combat interactions between entities.

    Handles projectile-enemy hits, enemy-player collisions, scoring,
    and generates combat events for the game loop to consume.
    """

    def __init__(self) -> None:
        self.inimigos_abates: int = 0
        self.bosses_abates: int = 0
        self.tiros_disparados: int = 0

    def resolver_projetil_jogador(
        self,
        proj: "Projetil",
        inimigos: list["Enemy"],
        boss: Optional["Boss"],
        jogador: "Player",
    ) -> list[CombatEvent]:
        """Resolve a player projectile hitting enemies/boss."""
        events: list[CombatEvent] = []

        if proj.tipo == "nova":
            return self._explodir_nova(proj, inimigos, boss, jogador)
        if proj.tipo == "bomba":
            return self._explodir_bomba(proj, inimigos, boss, jogador)

        penetrante = proj.tipo in ("ion", "gauss")

        for inimigo in inimigos[:]:
            if not proj.rect.colliderect(inimigo.rect):
                continue
            if isinstance(inimigo, SpecialEnemy) and inimigo.campo_forca:
                if proj.tipo != "ion":
                    proj.refletir()
                    events.append(CombatEvent("reflect", {"projectile": proj}))
                return events
            if isinstance(inimigo, SpecialEnemy):
                morreu = inimigo.receber_tiro(proj.dano)
                events.append(CombatEvent("hit", {
                    "projectile": proj, "enemy": inimigo,
                }))
                if morreu:
                    events.extend(self._matar_inimigo(inimigo, jogador))
            else:
                if inimigo.sofrer_dano(proj.dano):
                    events.extend(self._matar_inimigo(inimigo, jogador))
                else:
                    events.append(CombatEvent("hit", {
                        "projectile": proj, "enemy": inimigo,
                    }))
            if not penetrante:
                return events

        if boss and proj.rect.colliderect(boss.rect):
            if boss.sofrer_dano(proj.dano):
                events.extend(self._matar_boss(boss, jogador))
            else:
                events.append(CombatEvent("hit", {
                    "projectile": proj, "boss": boss,
                }))
        return events

    def _explodir_nova(self, proj, inimigos, boss, jogador) -> list[CombatEvent]:
        events: list[CombatEvent] = []
        raio = 90
        tem_alvo = any(math.hypot(i.x - proj.x, i.y - proj.y) < raio for i in inimigos)
        if not tem_alvo and boss and math.hypot(boss.x - proj.x, boss.y - proj.y) < raio:
            tem_alvo = True
        if not tem_alvo and proj.y > 40:
            return events
        events.append(CombatEvent("nova_explosion", {"projectile": proj, "radius": raio}))
        for inimigo in inimigos[:]:
            if math.hypot(inimigo.x - proj.x, inimigo.y - proj.y) < raio:
                if inimigo.sofrer_dano(proj.dano):
                    events.extend(self._matar_inimigo(inimigo, jogador))
                else:
                    inimigo.flash = 8
        if boss and math.hypot(boss.x - proj.x, boss.y - proj.y) < raio:
            if boss.sofrer_dano(proj.dano):
                events.extend(self._matar_boss(boss, jogador))
            else:
                events.append(CombatEvent("boss_hit", {"boss": boss}))
        return events

    def _explodir_bomba(self, proj, inimigos, boss, jogador) -> list[CombatEvent]:
        events: list[CombatEvent] = []
        raio = 150
        tem_alvo = any(math.hypot(i.x - proj.x, i.y - proj.y) < raio for i in inimigos)
        if not tem_alvo and boss and math.hypot(boss.x - proj.x, boss.y - proj.y) < raio:
            tem_alvo = True
        if not tem_alvo and proj.y > 60:
            return events
        events.append(CombatEvent("bomb_explosion", {"projectile": proj, "radius": raio}))
        for inimigo in inimigos[:]:
            if math.hypot(inimigo.x - proj.x, inimigo.y - proj.y) < raio:
                if inimigo.sofrer_dano(proj.dano):
                    events.extend(self._matar_inimigo(inimigo, jogador))
                else:
                    inimigo.flash = 10
        if boss and math.hypot(boss.x - proj.x, boss.y - proj.y) < raio:
            if boss.sofrer_dano(proj.dano):
                events.extend(self._matar_boss(boss, jogador))
            else:
                events.append(CombatEvent("boss_hit", {"boss": boss}))
        return events

    def _matar_inimigo(self, inimigo: "Enemy", jogador: "Player") -> list[CombatEvent]:
        bonus = jogador.combo.combo_atual * 5
        multiplicador = jogador.combo.get_bonus()
        total = int((inimigo.pontos + bonus) * multiplicador)
        jogador.pontuacao += total
        self.inimigos_abates += 1
        events = [CombatEvent("enemy_killed", {
            "enemy": inimigo, "score": total, "x": inimigo.x, "y": inimigo.y,
        })]
        if inimigo.tipo == "bomba":
            events.append(CombatEvent("bomb_chain", {
                "x": inimigo.x, "y": inimigo.y,
            }))
        if isinstance(inimigo, SpecialEnemy):
            drop = self._drop_especial(inimigo)
            if drop:
                events.append(CombatEvent("powerup_drop", {
                    "tipo": drop, "x": inimigo.x, "y": inimigo.y,
                }))
        else:
            chance = 0.08 + min(0.12, jogador.combo.combo_atual * 0.004)
            if random.random() < chance:
                from src.domain.systems.progression import ProgressionSystem
                events.append(CombatEvent("powerup_drop", {
                    "tipo": ProgressionSystem.sortear_tipo_powerup(),
                    "x": inimigo.x, "y": inimigo.y,
                }))
        return events

    def _drop_especial(self, inimigo: "SpecialEnemy") -> Optional[str]:
        tipo = inimigo.tipo_especial
        chance = {
            "acumulador": 0.50, "esponja": 0.30, "condutor": 0.40,
            "mutante": 0.80, "cristalino": 0.05, "evocador": 0.30,
        }.get(tipo, 0.0)
        if random.random() > chance:
            return None
        drops = {
            "acumulador": "arma", "esponja": "vida", "condutor": "escudo",
            "mutante": "moedas", "evocador": "arma", "cristalino": "skin",
        }
        return drops.get(tipo)

    def _matar_boss(self, boss: "Boss", jogador: "Player") -> list[CombatEvent]:
        multiplicador = jogador.combo.get_bonus()
        total = int(boss.pontos * multiplicador)
        jogador.pontuacao += total
        self.bosses_abates += 1
        return [CombatEvent("boss_killed", {
            "boss": boss, "score": total, "x": boss.x, "y": boss.y,
            "efeito": boss.efeito, "part_qtd": boss.part_qtd,
        })]

    def verificar_colisao_inimigo_jogador(
        self,
        inimigos: list["Enemy"],
        boss: Optional["Boss"],
        jogador: "Player",
    ) -> list[CombatEvent]:
        events: list[CombatEvent] = []
        for inimigo in inimigos[:]:
            if inimigo.rect.colliderect(jogador.rect):
                if jogador.sofrer_dano():
                    events.append(CombatEvent("player_hit", {"source": "enemy"}))
                if not isinstance(inimigo, SpecialEnemy):
                    events.extend(self._matar_inimigo(inimigo, jogador))
        if boss and boss.rect.colliderect(jogador.rect):
            if jogador.sofrer_dano():
                events.append(CombatEvent("player_hit", {"source": "boss"}))
        return events
