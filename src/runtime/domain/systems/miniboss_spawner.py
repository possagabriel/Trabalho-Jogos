"""Agendamento e seleção ponderada, isolados do relógio e RNG globais."""

from __future__ import annotations

import math
import random
from collections.abc import Mapping
from typing import TYPE_CHECKING

from src.runtime.domain.entities.minibosses import REGISTRO, Miniboss, criar_miniboss
from src.runtime.domain.entities.minibosses.config import CATALOGO

if TYPE_CHECKING:
    from src.runtime.domain.world.scenarios import Cenario


class MinibossSpawner:
    """Mantém no máximo um encontro e nunca repete o último tipo.

    Args:
        modo: ``ondas`` iniciadas (exceto bosses) ou ``segundos`` de simulação.
        intervalo: Ondas inteiras ou segundos entre encontros.
        seed: Semente privada; não altera o RNG global do jogo.
        pesos: Sobrescritas de peso por identificador; zero desabilita o tipo.
    """

    def __init__(self, modo: str = "ondas", intervalo: float = 3,
                 seed: int | None = None, pesos: Mapping[str, float] | None = None) -> None:
        if (modo not in ("ondas", "segundos") or not math.isfinite(intervalo)
                or intervalo <= 0 or (modo == "ondas" and int(intervalo) != intervalo)):
            raise ValueError("Modo ou intervalo de miniboss inválido")
        self.modo, self.intervalo = modo, intervalo
        self.pesos = {chave: float(CATALOGO[chave]["peso"]) for chave in REGISTRO}
        for chave, peso in (pesos or {}).items():
            if chave not in self.pesos or not math.isfinite(peso) or peso < 0:
                raise ValueError(f"Peso de miniboss inválido: {chave}")
            self.pesos[chave] = peso
        self._rng = random.Random(seed)
        self._rng_mecanicas = random.Random(self._rng.getrandbits(64))
        self.ultimo: str | None = None
        self.ativo: Miniboss | None = None
        self.tempo = 0.0
        self._onda = self._onda_ultimo = 0

    def sortear(self, dimensao: int) -> str | None:
        """Sorteia entre elegíveis; lista vazia adia em vez de repetir."""
        elegiveis = [chave for chave in REGISTRO
                     if chave != self.ultimo and self.pesos[chave] > 0
                     and dimensao in CATALOGO[chave]["dimensoes"]]
        if not elegiveis:
            return None
        self.ultimo = self._rng.choices(
            elegiveis, weights=[self.pesos[chave] for chave in elegiveis], k=1)[0]
        return self.ultimo

    def atualizar(self, dt: float, nivel: int, cenario: Cenario,
                  onda: int = 0, bloqueado: bool = False) -> Miniboss | None:
        """Retorna apenas encontros novos; pausa/boss não acumulam tempo."""
        if not math.isfinite(dt) or dt < 0:
            raise ValueError("dt deve ser finito e não negativo")
        self._onda = max(self._onda, onda)
        if self.ativo is not None or bloqueado:
            return None
        self.tempo += dt
        pronto = (self.tempo >= self.intervalo if self.modo == "segundos"
                  else self._onda - self._onda_ultimo >= self.intervalo)
        if not pronto:
            return None
        chave = self.sortear(cenario.id)
        if chave is None:
            return None
        self.ativo = criar_miniboss(chave, nivel, cenario, self._rng_mecanicas)
        self.tempo = 0.0
        self._onda_ultimo = self._onda
        return self.ativo

    def liberar(self) -> None:
        """Encerra o encontro e reinicia o intervalo sem fila de spawns atrasados."""
        self.ativo = None
        self.tempo = 0.0
        self._onda_ultimo = self._onda
