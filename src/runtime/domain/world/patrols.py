"""Encontros locais reutilizam o catálogo e mantêm trajetória no mundo."""

from __future__ import annotations

import math
from dataclasses import dataclass

from src.runtime.domain.entities.minibosses.base import Miniboss


@dataclass
class Patrulha:
    """Arena, identidade persistente e entidade de uma patrulha independente."""

    ident: str
    boss: Miniboss
    centro: tuple[float, float]
    indice: int
    derrotada: bool = False

    def posicao(self, tempo: float) -> tuple[float, float]:
        """Varia órbita e fase sem perseguir o jogador nem depender da câmera."""
        fase = self.indice * 1.7
        return (self.centro[0] + math.sin(tempo * (0.42 + self.indice * 0.03) + fase) * 95,
                self.centro[1] + math.cos(tempo * 0.58 + fase) * 48)
