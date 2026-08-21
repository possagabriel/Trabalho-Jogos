"""Boss entity for each scenario.

Migrated from game/bosses.py Boss class.
"""

from __future__ import annotations

import math
import random
from typing import Optional

import pygame

from src.domain.entities.base import Entity

# ---------------------------------------------------------------------------
# Screen constants
# ---------------------------------------------------------------------------
LARGURA = 900
ALTURA = 700

# ---------------------------------------------------------------------------
# Color constants
# ---------------------------------------------------------------------------
AZUL = (50, 100, 200)
BRANCO = (255, 255, 255)
CIANO = (0, 220, 255)
DOURADO = (255, 215, 0)
ROSA = (255, 100, 150)
ROXO = (140, 60, 200)
VERMELHO = (230, 50, 50)

# ---------------------------------------------------------------------------
# Boss configuration per scenario
# ---------------------------------------------------------------------------

BOSSES_POR_CENARIO: dict[int, dict] = {
    1: {
        "nome": "HEXAGONO", "cor": VERMELHO, "raio": 40, "vida": 30,
        "pontos": 200, "mov": "zigzag", "ataques": ["leque", "8dir"],
        "alvo_y": 150, "efeito": "explosao", "part_qtd": 10, "nivel": 5,
    },
    2: {
        "nome": "LOSANGO", "cor": AZUL, "raio": 45, "vida": 50,
        "pontos": 350, "mov": "gira", "ataques": ["8dir", "espiral"],
        "alvo_y": 150, "efeito": "espiral", "part_qtd": 20, "nivel": 10,
    },
    3: {
        "nome": "ESTRELA", "cor": DOURADO, "raio": 50, "vida": 70,
        "pontos": 500, "mov": "infinito", "ataques": ["teleguiado", "tudo"],
        "alvo_y": 180, "efeito": "estrela", "part_qtd": 30, "nivel": 15,
    },
    4: {
        "nome": "PENTAGONO", "cor": ROXO, "raio": 55, "vida": 100,
        "pontos": 750, "mov": "teletransporte",
        "ataques": ["tudo", "leque", "mira"],
        "alvo_y": 150, "efeito": "pulsacao", "part_qtd": 40, "nivel": 20,
    },
    5: {
        "nome": "ANEIS", "cor": BRANCO, "raio": 75, "vida": 150,
        "pontos": 1000, "mov": "centro",
        "ataques": ["combinado", "espiral"],
        "alvo_y": ALTURA // 2, "efeito": "mega", "part_qtd": 100,
        "nivel": 25,
    },
    6: {
        "nome": "ANEIS DOURADO", "cor": DOURADO, "raio": 85, "vida": 220,
        "pontos": 1500, "mov": "centro",
        "ataques": ["combinado", "espiral", "teleguiado"],
        "alvo_y": ALTURA // 2, "efeito": "mega", "part_qtd": 140,
        "nivel": 30,
    },
}


class Boss(Entity):
    """Boss entity for each scenario. Appears every 5 levels.

    Migrated from game/bosses.py Boss.
    """

    def __init__(self, nivel: int, cenario_id: int) -> None:
        cfg = BOSSES_POR_CENARIO[cenario_id]
        self.nome: str = cfg["nome"]
        self.cor: tuple[int, int, int] = cfg["cor"]
        raio = cfg["raio"]
        vida = cfg["vida"] * (1 + 0.15 * max(0, (nivel - cfg["nivel"])))
        super().__init__(
            x=LARGURA // 2,
            y=-raio - 20,
            health=int(vida),
        )
        self.nivel: int = nivel
        self.cenario_id: int = cenario_id
        self.raio: int = raio
        self.vida_max: int = self.health
        self.pontos: int = cfg["pontos"]
        self.mov: str = cfg["mov"]
        self.ataques: list[str] = list(cfg["ataques"])
        self.alvo_y: int = cfg["alvo_y"]
        self.efeito: str = cfg["efeito"]
        self.part_qtd: int = cfg["part_qtd"]
        self.angulo: float = 0.0
        self.t: int = 0
        self.entrando: bool = True
        self.timer_ataque: int = 90
        self.flash: int = 0
        self.enraivecido: bool = False
        self.teleportando: bool = False
        self.teleport_timer: int = 130
        self.alvo: Optional[tuple[int, int]] = None

    # ------------------------------------------------------------------
    # Entity interface
    # ------------------------------------------------------------------

    def on_update(self, dt: float = 1.0, **kwargs) -> list:
        jogador = kwargs.get("jogador")
        novos = []
        self.t += 1
        if self.flash > 0:
            self.flash -= 1

        if self.entrando:
            self.y += 2
            if self.y >= self.alvo_y:
                self.y = self.alvo_y
                self.entrando = False
            return novos

        velocidade = 1.5 if self.enraivecido else 1.0
        if self.mov == "zigzag":
            self.x = LARGURA // 2 + math.sin(self.t * 0.03) * 220
            self.angulo += 0.02 * velocidade
        elif self.mov == "gira":
            self.angulo += 0.03 * velocidade
            self.x += math.sin(self.t * 0.01) * 1.2 * velocidade
            self.x = max(self.raio, min(LARGURA - self.raio, self.x))
        elif self.mov == "infinito":
            self.x = LARGURA // 2 + math.sin(self.t * 0.02) * 320
            self.y = self.alvo_y + math.sin(self.t * 0.04) * 100
            self.angulo += 0.02 * velocidade
        elif self.mov == "teletransporte":
            self._atualizar_teletransporte()
        elif self.mov == "centro":
            self.angulo += 0.01 * velocidade

        if not self.enraivecido and self._fracao_vida() <= 0.33:
            self.enraivecido = True

        self.timer_ataque -= 1
        if self.timer_ataque <= 0:
            self.timer_ataque = self._intervalo_ataque()
            novos = self._atacar(jogador)
        return novos

    def render(self, surface, **kwargs) -> None:
        x, y = int(self.x), int(self.y)
        cor = (255, 255, 255) if self.flash > 0 else self.cor
        centro = (x, y)

        if self.enraivecido:
            pygame.draw.circle(surface, VERMELHO, centro, self.raio + 8, 2)

        if self.entrando:
            pygame.draw.circle(surface, cor, centro, self.raio)
            pygame.draw.circle(surface, BRANCO, centro, self.raio, 4)
            return

        # Draw shape based on boss name
        if self.nome == "HEXAGONO":
            pts = self._pontos_poligono(centro, self.raio, 6, self.angulo)
            pygame.draw.polygon(surface, cor, pts)
            pygame.draw.polygon(surface, BRANCO, pts, 4)
        elif self.nome == "LOSANGO":
            pts = [
                (x, y - self.raio),
                (x + self.raio * 0.7, y),
                (x, y + self.raio),
                (x - self.raio * 0.7, y),
            ]
            pygame.draw.polygon(surface, cor, pts)
            pygame.draw.polygon(surface, BRANCO, pts, 4)
            # Inner diamond
            pts_int = [
                (x, y - self.raio * 0.6),
                (x + self.raio * 0.4, y),
                (x, y + self.raio * 0.6),
                (x - self.raio * 0.4, y),
            ]
            pygame.draw.polygon(surface, (0, 60, 130), pts_int, 2)
        elif self.nome == "ESTRELA":
            pts = self._pontos_estrela(centro, self.raio, self.angulo)
            pygame.draw.polygon(surface, cor, pts)
            pygame.draw.polygon(surface, BRANCO, pts, 4)
        elif self.nome == "PENTAGONO":
            pts = self._pontos_poligono(centro, self.raio, 5, self.angulo)
            pygame.draw.polygon(surface, cor, pts)
            pygame.draw.polygon(surface, BRANCO, pts, 4)
            if self.teleportando and self.alvo:
                pygame.draw.circle(surface, ROSA, self.alvo, 12, 2)
        elif self.nome in ("ANEIS", "ANEIS DOURADO"):
            self._desenhar_aneis(surface, centro, x, y, cor)
        else:
            pygame.draw.circle(surface, cor, centro, self.raio)
            pygame.draw.circle(surface, BRANCO, centro, self.raio, 4)

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x - self.raio),
            int(self.y - self.raio),
            self.raio * 2,
            self.raio * 2,
        )

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------

    def _atualizar_teletransporte(self) -> None:
        if not self.teleportando:
            self.teleport_timer -= 1
            if self.teleport_timer <= 0:
                self.teleportando = True
                self.alvo = (
                    random.randint(100, LARGURA - 100),
                    random.randint(100, 450),
                )
        else:
            assert self.alvo is not None
            dx = self.alvo[0] - self.x
            dy = self.alvo[1] - self.y
            distancia = math.hypot(dx, dy)
            if distancia < 8:
                self.x, self.y = self.alvo
                self.teleportando = False
                self.teleport_timer = 160
                self.timer_ataque = 0
            else:
                self.x += dx / distancia * 5
                self.y += dy / distancia * 5
            self.angulo += 0.05

    # ------------------------------------------------------------------
    # Attacks
    # ------------------------------------------------------------------

    def _fracao_vida(self) -> float:
        return max(0.0, self.health / self.vida_max)

    def _intervalo_ataque(self) -> int:
        fracao = self._fracao_vida()
        base = random.randint(75, 110)
        if fracao <= 0.33:
            base = int(base * 0.55)
        elif fracao <= 0.66:
            base = int(base * 0.8)
        if self.enraivecido:
            base = int(base * 0.85)
        return max(28, base)

    def _ataques_por_fase(self) -> list[str]:
        fracao = self._fracao_vida()
        if fracao > 0.66:
            return self.ataques[:1]
        if fracao > 0.33:
            return self.ataques[:2]
        return self.ataques

    def _atacar(self, jogador) -> list:
        from src.domain.entities.projectiles.factory import ProjectileFactory

        x, y = self.x, self.y
        disponiveis = self._ataques_por_fase()
        if not disponiveis:
            return []
        escolhidos = random.sample(
            disponiveis, min(1 + (len(disponiveis) > 1), 3)
        )
        projs = []
        for nome in escolhidos:
            projs.extend(self._executar_ataque(nome, jogador, x, y))
        return projs

    def _executar_ataque(self, nome: str, jogador, x: float, y: float) -> list:
        from src.domain.entities.projectiles.factory import ProjectileFactory

        if nome == "leque":
            return [
                ProjectileFactory.criar_inimigo(x, y, dx, 4, 1, self.cor, 5)
                for dx in (-2, 0, 2)
            ]
        if nome == "8dir":
            return [
                ProjectileFactory.criar_inimigo(
                    x, y, math.cos(a) * 3.5, math.sin(a) * 3.5, 1, self.cor, 5
                )
                for a in [i * math.tau / 8 for i in range(8)]
            ]
        if nome == "teleguiado":
            return [
                ProjectileFactory.criar_inimigo(
                    x, y, jogador.x - x, jogador.y - y, 1, self.cor, 5,
                    teleguiado=True,
                )
                for _ in range(3)
            ]
        if nome == "tudo":
            return [
                ProjectileFactory.criar_inimigo(
                    x, y, math.cos(a) * 3.2, math.sin(a) * 3.2, 1, self.cor, 5
                )
                for a in [i * math.tau / 12 for i in range(12)]
            ]
        if nome == "mira":
            dx, dy = jogador.x - x, jogador.y - y
            norma = math.hypot(dx, dy) or 1
            return [
                ProjectileFactory.criar_inimigo(
                    x, y, dx / norma * 7, dy / norma * 7, 1, ROSA, 5
                )
                for _ in range(3)
            ]
        if nome == "espiral":
            return [
                ProjectileFactory.criar_inimigo(
                    x, y, math.cos(a) * 3.4, math.sin(a) * 3.4, 1, CIANO, 5
                )
                for a in [i * math.tau / 16 for i in range(16)]
            ]
        if nome == "combinado":
            fracao = self._fracao_vida()
            projs = []
            if fracao <= 0.66:
                projs.extend([
                    ProjectileFactory.criar_inimigo(
                        x, y, math.cos(a) * 3.2, math.sin(a) * 3.2, 1, ROSA, 5
                    )
                    for a in [i * math.tau / 8 for i in range(8)]
                ])
            if fracao <= 0.33:
                projs.extend([
                    ProjectileFactory.criar_inimigo(
                        x, y, jogador.x - x, jogador.y - y, 1, CIANO, 5,
                        teleguiado=True,
                    )
                    for _ in range(3)
                ])
            projs.extend([
                ProjectileFactory.criar_inimigo(x, y, dx, 4.5, 1, self.cor, 5)
                for dx in (-2, 0, 2)
            ])
            return projs
        return []

    # ------------------------------------------------------------------
    # Damage
    # ------------------------------------------------------------------

    def sofrer_dano(self, dano: int) -> bool:
        self.health -= dano
        self.flash = 6
        return self.health <= 0

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _desenhar_aneis(self, tela, centro, x, y, cor, dourado=False) -> None:
        aneis = [
            (cor, self.raio, 0.10),
            (ROSA, self.raio * 0.72, 0.16),
            (VERMELHO, self.raio * 0.44, 0.24),
        ]
        if dourado:
            aneis = [
                (DOURADO, self.raio, 0.10),
                (BRANCO, self.raio * 0.72, 0.16),
                (cor, self.raio * 0.44, 0.24),
            ]
        for cor_anel, raio, velocidade in aneis:
            pygame.draw.circle(tela, (0, 0, 0), centro, int(raio), 2)
            pygame.draw.circle(tela, cor_anel, centro, int(raio), 2)
            ang = self.t * velocidade
            for i in range(3):
                a = ang + i * math.tau / 3
                px = x + math.cos(a) * raio
                py = y + math.sin(a) * raio
                pygame.draw.circle(tela, cor_anel, (int(px), int(py)), 4, 2)
        pygame.draw.circle(tela, BRANCO, centro, 12, 2)

    @staticmethod
    def _pontos_poligono(centro, raio: float, lados: int, angulo: float) -> list:
        x, y = centro
        return [
            (
                x + raio * math.cos(angulo + 2 * math.pi * i / lados),
                y + raio * math.sin(angulo + 2 * math.pi * i / lados),
            )
            for i in range(lados)
        ]

    @staticmethod
    def _pontos_estrela(centro, raio: float, angulo: float) -> list:
        x, y = centro
        pts = []
        for i in range(10):
            a = angulo + i * math.pi / 5
            r = raio if i % 2 == 0 else raio * 0.45
            pts.append((x + r * math.cos(a), y + r * math.sin(a)))
        return pts
