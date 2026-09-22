"""Miniboss abstrato: reutiliza vida, colisão e ataques básicos de Boss."""

from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Mapping

import pygame

from src.core.constants import FPS
from src.runtime.domain.entities.bosses import Boss
from src.runtime.domain.entities.minibosses.states import Ataque, Aviso
from src.runtime.domain.entities.weapons import Projetil

if TYPE_CHECKING:
    from src.runtime.domain.entities.enemies import Inimigo
    from src.runtime.domain.entities.minibosses.strategies import Estrategia
    from src.runtime.domain.entities.player import Jogador
    from src.runtime.domain.world.scenarios import Cenario


class Miniboss(Boss, ABC):
    """Entidade do runtime; efeitos ficam locais ao encontro, nunca no save de input."""

    chave: str

    def __init__(self, nivel: int, cenario: Cenario, cfg: Mapping[str, Any],
                 rng: random.Random) -> None:
        super().__init__(nivel, cenario, config=cfg)
        self.cfg = dict(cfg)
        self.rng = rng
        self.estrategia = self.criar_estrategia()
        self.estado = Aviso(cfg["aviso"])
        self._iniciou = False
        self._projeteis: list[Projetil] = []
        self.lacaios: list[Inimigo] = []
        self.novos_lacaios: list[Inimigo] = []
        self.zonas: list[pygame.Rect] = []
        self.ultimo_disparo: list[tuple[float, float, float, int, tuple, str]] = []

    @abstractmethod
    def criar_estrategia(self) -> Estrategia:
        """Fornece o comportamento do protocolo registrado."""

    @property
    def inverte_controles(self) -> bool:
        """Efeito consultado apenas enquanto a entidade está viva."""
        return self.vida > 0 and self.estrategia.inverte and isinstance(self.estado, Ataque)

    def atualizar(self, jogador: Jogador, dt: float = 1 / FPS) -> list[Projetil]:
        """Avança o relógio e retorna os novos projéteis, como ``Boss.atualizar``.

        Args:
            jogador: Alvo atual dos ataques.
            dt: Segundos de simulação, sem incluir pausas ou hitstop.
        """
        if not math.isfinite(dt) or dt < 0:
            raise ValueError("dt deve ser finito e não negativo")
        if self.vida <= 0:
            return []
        self.flash = max(0, self.flash - dt * FPS)
        self.angulo += dt * 0.4
        if self.entrando:
            tempo = max(0.0, (self.alvo_y - self.y) / self.cfg["velocidade_entrada"])
            passo = min(tempo, dt)
            self.y += self.cfg["velocidade_entrada"] * passo
            self.t += passo * FPS
            dt -= passo
            if passo < tempo:
                return []
            self.y, self.entrando = self.alvo_y, False
        if not self._iniciou:
            self.estado.entrar(self, jogador)
            self._iniciou = True
        while dt > 1e-9:
            passo = min(dt, self.estado.restante)
            self.t += passo * FPS
            self.estrategia.mover(self, jogador, passo)
            self.estado.restante -= passo
            dt -= passo
            if self.estado.restante <= 1e-9:
                self.estado = self.estado.proximo(self)
                self.estado.entrar(self, jogador)
        return self.drenar_projeteis()

    def emitir(self, projeteis: list[Projetil]) -> None:
        """Enfileira projéteis pertencentes ao encontro."""
        self._projeteis.extend(projeteis)

    def drenar_projeteis(self) -> list[Projetil]:
        """Transfere cada disparo uma única vez para o controlador."""
        resultado, self._projeteis = self._projeteis, []
        return resultado

    def observar_tiros(self, projeteis: list[Projetil]) -> None:
        """Fotografa o último disparo real, sem manter referências mutáveis."""
        tiros = [p for p in projeteis if p.origem == "jogador"]
        if tiros:
            self.ultimo_disparo = [
                (p.vel_x, p.vel_y, p.raio, p.dano, tuple(p.cor), p.tipo)
                for p in tiros[:self.cfg.get("limite_copia", 5)]
            ]

    def sofrer_dano(self, dano: int) -> bool:
        """Aplica a proteção da estratégia antes do dano comum de Boss."""
        if self.vida <= 0:
            return True
        if self.entrando:
            return False
        efetivo = self.estrategia.dano(self, max(0, dano))
        return super().sofrer_dano(efetivo) if efetivo else False

    def receber_tiro(self, proj: Projetil) -> bool:
        """Resolve hitboxes especiais antes do casco; retorna colisão."""
        if self.estrategia.interceptar(self, proj):
            return True
        if self.rect.colliderect(proj.rect):
            self.sofrer_dano(proj.dano)
            return True
        return False

    def receber_area(self, dano: int, x: float, y: float, raio: float) -> None:
        """Dano em área respeita o escudo; núcleos exigem acerto direto."""
        if math.hypot(self.x - x, self.y - y) < raio:
            self.sofrer_dano(dano)

    def perigo(self, rect: pygame.Rect) -> bool:
        """Retorna se uma zona ativa atinge o jogador."""
        return (self.vida > 0 and isinstance(self.estado, Ataque)
                and any(z.colliderect(rect) for z in self.zonas))

    def desenhar(self, tela: pygame.Surface) -> None:
        """Delega o visual cel-shaded ao adaptador de apresentação."""
        from src.runtime.presentation.miniboss_view import desenhar_miniboss

        desenhar_miniboss(tela, self)
