"""EnemyFactory using Factory Method pattern.

Handles creation of regular enemies, special enemies, and wave compositions.
"""

from __future__ import annotations

import math
import random
from typing import Optional

from src.domain.entities.enemies.base import (
    Enemy,
    TIPOS,
    composicao_onda,
    sortear_inimigo_especial,
)
from src.domain.entities.enemies.types.soldier import SoldierEnemy
from src.domain.entities.enemies.types.shooter import ShooterEnemy
from src.domain.entities.enemies.types.tank import TankEnemy

LARGURA = 900

# Map enemy type to its specialized class
_TYPE_CLASSES: dict[str, type[Enemy]] = {
    "scout": SoldierEnemy,
    "soldado": SoldierEnemy,
    "flamifero": Enemy,
    "forja": TankEnemy,
    "abissal": Enemy,
    "estelar": Enemy,
    "bomba": Enemy,
    "cristalino": TankEnemy,
    "guardiao": ShooterEnemy,
    "artilheiro": ShooterEnemy,
    "espectro": Enemy,
    "distorcao": TankEnemy,
    "assombra": Enemy,
    "celestial": Enemy,
    "sentinela": ShooterEnemy,
}

# Special enemy types with their charge mechanics
SPECIAL_TIPOS = {
    "acumulador": {"cor": (255, 200, 40), "carga_por_tiro": 5},
    "esponja": {"cor": (150, 60, 200), "carga_por_tiro": 3},
    "condutor": {"cor": (80, 160, 255), "carga_por_tiro": 8},
    "mutante": {"cor": (200, 40, 255), "carga_por_tiro": 10},
    "cristalino": {"cor": (210, 235, 245), "carga_por_tiro": 15},
    "evocador": {"cor": (200, 120, 255), "carga_por_tiro": 12},
}

# Base type for each special enemy
_SPECIAL_BASE = {
    "acumulador": "flamifero",
    "esponja": "soldado",
    "condutor": "estelar",
    "mutante": "forja",
    "cristalino": "guardiao",
    "evocador": "celestial",
}


class SpecialEnemy(Enemy):
    """Special enemy with charge mechanic.

    Accumulates energy from player shots; triggers unique effect at 100%.
    """

    CARGA_POR_TIRO: dict[str, int] = {k: v["carga_por_tiro"] for k, v in SPECIAL_TIPOS.items()}
    CORES: dict[str, tuple[int, int, int]] = {k: v["cor"] for k, v in SPECIAL_TIPOS.items()}

    def __init__(
        self,
        tipo_especial: str,
        nivel: int,
        cenario_id: int = 1,
    ) -> None:
        base = _SPECIAL_BASE[tipo_especial]
        super().__init__(base, nivel)
        self.tipo = base
        self.tipo_especial: str = tipo_especial
        self.cor = self.CORES[tipo_especial]
        self.carga: int = 0
        self.carga_maxima: int = 100
        self.carga_por_tiro: int = self.CARGA_POR_TIRO[tipo_especial]
        self.carregado: bool = False
        self.efeito_ja_atirado: bool = False
        self.vida = max(10, 6 + nivel)
        self.vida_max = self.vida
        self.pontos = 50 + nivel * 5
        self.raio = 22
        self.mini_boss: bool = False
        self.campo_forca: bool = False
        self.invisivel: int = 0
        self.mov = {
            "acumulador": "flutua", "esponja": "zigzag",
            "condutor": "gira", "mutante": "reta",
            "cristalino": "flutua", "evocador": "flutua",
        }[tipo_especial]
        self.ataque = "nenhum"
        self.vel = 1.2

    def receber_tiro(self, dano: int) -> bool:
        """Process a hit: accumulate charge. Returns True if should be removed."""
        self.flash = 6
        if self.tipo_especial == "esponja":
            self.carga += self.carga_por_tiro * dano
            if self.carga >= self.carga_maxima:
                self.carregado = True
            return False
        if self.tipo_especial == "mutante" and not self.carregado:
            self._teleportar()
        self.carga += self.carga_por_tiro * dano
        if self.carga >= self.carga_maxima and not self.carregado:
            self.carregado = True
        self.health -= dano
        return self.health <= 0

    def _teleportar(self) -> None:
        self.x = random.randint(60, LARGURA - 60)
        self.y = random.randint(30, 400)
        self.base_x = self.x
        self.invisivel = 40

    def acoes_carregado(self) -> dict:
        """Execute the charged effect. Returns dict of spawned entities."""
        if self.efeito_ja_atirado:
            return {}
        self.efeito_ja_atirado = True
        x, y = int(self.x), int(self.y)
        from src.domain.entities.projectiles.factory import ProjectileFactory

        acoes: dict = {"projeteis": [], "inimigos": [], "morrer": False, "mensagem": ""}
        if self.tipo_especial == "acumulador":
            acoes["projeteis"] = [
                ProjectileFactory.criar_inimigo(
                    x, y, math.cos(a) * 4, math.sin(a) * 4, 1,
                    (255, 200, 40), 4
                )
                for a in [i * math.tau / 8 for i in range(8)]
            ]
            acoes["morrer"] = True
            acoes["mensagem"] = "EXPLOSAO EM AREA!"
        elif self.tipo_especial == "esponja":
            for _ in range(4):
                acoes["inimigos"].append(
                    Enemy("soldado", 1, x + random.randint(-30, 30), y, escala=0.7)
                )
            acoes["morrer"] = True
            acoes["mensagem"] = "SE DIVIDIU!"
        elif self.tipo_especial == "condutor":
            acoes["projeteis"].append(
                ProjectileFactory.criar_inimigo(
                    x, y, 0, 6, 2, (150, 200, 255), 5, tipo="feixe", teleguiado=True
                )
            )
            acoes["mensagem"] = "RAIO LIBERADO!"
            self.efeito_ja_atirado = False
            self.carga = 0
            self.carregado = False
        elif self.tipo_especial == "mutante":
            self.mini_boss = True
            self.raio = 36
            self.health += 60
            self.vida_max = self.health
            self.ataque = "leque"
            self.timer_ataque = 60
            acoes["mensagem"] = "MINI-BOSS!"
        elif self.tipo_especial == "cristalino":
            self.campo_forca = True
            acoes["mensagem"] = "CAMPO DE FORCA!"
        elif self.tipo_especial == "evocador":
            for _ in range(3):
                acoes["inimigos"].append(
                    Enemy(self.tipo, self.nivel, x + random.randint(-40, 40), y)
                )
            self.efeito_ja_atirado = False
            self.carga = 0
            self.carregado = False
            self._teleportar()
            acoes["mensagem"] = "EVOCACAO!"
        return acoes

    def e_feito_ja_atirado(self) -> bool:
        return self.efeito_ja_atirado


class EnemyFactory:
    """Factory for creating enemies using the Factory Method pattern.

    Supports creation of individual enemies, random enemies, and full waves.
    """

    _registry: dict[str, type[Enemy]] = dict(_TYPE_CLASSES)

    @classmethod
    def register(cls, tipo: str, klass: type[Enemy]) -> None:
        """Register a custom enemy class for a type name."""
        cls._registry[tipo] = klass

    @classmethod
    def create(cls, tipo: str, nivel: int, **kwargs) -> Enemy:
        """Create a single enemy of the given type."""
        klass = cls._registry.get(tipo, Enemy)
        return klass(tipo, nivel, **kwargs)

    @classmethod
    def create_random(cls, nivel: int, tipos: list[str], **kwargs) -> Enemy:
        """Create a random enemy from the allowed type list."""
        tipo = random.choice(tipos)
        return cls.create(tipo, nivel, **kwargs)

    @classmethod
    def create_special(cls, tipo_especial: str, nivel: int, cenario_id: int = 1) -> SpecialEnemy:
        """Create a special enemy with charge mechanics."""
        return SpecialEnemy(tipo_especial, nivel, cenario_id)

    @classmethod
    def create_wave(
        cls,
        nivel: int,
        tipos: list[str],
    ) -> list[Enemy]:
        """Create a full wave of enemies based on the level.

        Returns a list of Enemy instances with pre-computed spawn positions.
        """
        wave_tipos, qtd, xs = composicao_onda(nivel, tipos)
        inimigos: list[Enemy] = []
        for i in range(qtd):
            tipo = random.choice(wave_tipos)
            x = xs[i] if i < len(xs) else None
            inimigos.append(cls.create(tipo, nivel, x=x))
        return inimigos

    @classmethod
    def maybe_create_special(
        cls,
        nivel: int,
        especiais: list[str],
        cenario_id: int = 1,
    ) -> Optional[SpecialEnemy]:
        """Roll for a special enemy spawn. Returns None if the roll fails."""
        tipo = sortear_inimigo_especial(nivel, especiais)
        if tipo is None:
            return None
        return cls.create_special(tipo, nivel, cenario_id)
