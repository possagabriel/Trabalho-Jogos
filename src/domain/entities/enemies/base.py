"""Enemy base class with movement and attack patterns.

Migrated from game/enemies.py Inimigo class.
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
AMARELO = (255, 220, 60)
AZUL = (50, 100, 200)
BRANCO = (255, 255, 255)
CIANO = (0, 220, 255)
DOURADO = (255, 215, 0)
LARANJA = (255, 160, 40)
ROXO = (140, 60, 200)
VERDE = (80, 220, 100)
VERMELHO = (230, 50, 50)

# ---------------------------------------------------------------------------
# Enemy type definitions (one per dimension)
# ---------------------------------------------------------------------------
TIPOS: dict[str, dict] = {
    # Dimension 1 - Deep Space
    "scout": {"cor": VERDE, "raio": 12, "vida": 1, "pontos": 10,
              "vel": 2.5, "mov": "reta", "ataque": "nenhum"},
    "soldado": {"cor": AMARELO, "raio": 12, "vida": 2, "pontos": 20,
                "vel": 2.2, "mov": "zigzag", "ataque": "nenhum"},
    # Dimension 2 - Flame Nebula
    "flamifero": {"cor": VERMELHO, "raio": 12, "vida": 3, "pontos": 30,
                  "vel": 2.0, "mov": "espiral", "ataque": "baixo"},
    "forja": {"cor": LARANJA, "raio": 20, "vida": 5, "pontos": 50,
              "vel": 1.4, "mov": "zigzag_lento", "ataque": "leque"},
    # Dimension 3 - Cosmic Ocean
    "abissal": {"cor": AZUL, "raio": 16, "vida": 4, "pontos": 45,
                "vel": 1.8, "mov": "gira", "ataque": "4dir"},
    "estelar": {"cor": ROXO, "raio": 12, "vida": 3, "pontos": 40,
                "vel": 3.0, "mov": "persegue", "ataque": "nenhum"},
    "bomba": {"cor": VERMELHO, "raio": 10, "vida": 1, "pontos": 15,
              "vel": 3.0, "mov": "investida", "ataque": "nenhum"},
    # Dimension 4 - Crystal Forest
    "cristalino": {"cor": VERDE, "raio": 16, "vida": 5, "pontos": 50,
                   "vel": 1.7, "mov": "ondulacao", "ataque": "baixo"},
    "guardiao": {"cor": BRANCO, "raio": 15, "vida": 4, "pontos": 55,
                 "vel": 1.5, "mov": "reta", "ataque": "tudo"},
    "artilheiro": {"cor": CIANO, "raio": 14, "vida": 4, "pontos": 40,
                   "vel": 1.2, "mov": "flutua", "ataque": "rajada"},
    # Dimension 5 - Null Space
    "espectro": {"cor": (120, 60, 180), "raio": 12, "vida": 4, "pontos": 60,
                 "vel": 2.4, "mov": "erratico", "ataque": "nenhum"},
    "distorcao": {"cor": ROXO, "raio": 18, "vida": 6, "pontos": 70,
                  "vel": 1.1, "mov": "flutua", "ataque": "baixo"},
    "assombra": {"cor": (150, 150, 200), "raio": 12, "vida": 3, "pontos": 35,
                 "vel": 2.4, "mov": "fada", "ataque": "mira"},
    # Dimension 6 - Divine Plane
    "celestial": {"cor": DOURADO, "raio": 16, "vida": 6, "pontos": 80,
                  "vel": 2.0, "mov": "zigzag", "ataque": "leque"},
    "sentinela": {"cor": (240, 235, 200), "raio": 15, "vida": 8, "pontos": 100,
                  "vel": 1.3, "mov": "reta", "ataque": "feixe"},
}

# Drawing shape per enemy type
FORMAS: dict[str, str] = {
    "scout": "triangulo", "soldado": "quadrado", "flamifero": "circulo",
    "forja": "hexagono", "abissal": "losango", "estelar": "estrela",
    "bomba": "circulo", "cristalino": "hexagono", "guardiao": "pentagono",
    "artilheiro": "pentagono", "espectro": "aleatoria",
    "distorcao": "circulo_pulsante", "assombra": "circulo_pulsante",
    "celestial": "estrela", "sentinela": "olho",
}


class Enemy(Entity):
    """Normal enemy with movement and attack patterns.

    Migrated from game/enemies.py Inimigo.
    """

    def __init__(
        self,
        tipo: str,
        nivel: int,
        x: Optional[float] = None,
        y: float = -40.0,
        escala: float = 1.0,
    ) -> None:
        cfg = TIPOS[tipo]
        self.tipo: str = tipo
        self.nivel: int = nivel
        self.cor: tuple[int, int, int] = cfg["cor"]
        self.raio: float = cfg["raio"] * escala
        vida = cfg["vida"] * (1 + 0.03 * max(0, nivel - 1))
        vida = max(1, int(vida))
        self.pontos: int = cfg["pontos"]
        self.vel: float = cfg["vel"] * (1 + 0.04 * (nivel - 1)) * escala
        self.mov: str = cfg["mov"]
        self.ataque: str = cfg["ataque"]
        spawn_x = x if x is not None else random.randint(40, LARGURA - 40)
        super().__init__(x=spawn_x, y=y, health=vida)
        self.vida_max: int = self.health
        self.base_x: float = self.x
        self.fase: float = random.uniform(0, math.tau)
        self.angulo: float = random.uniform(0, math.tau)
        self.timer_ataque: int = random.randint(90, 140)
        self.flash: int = 0
        self.invisivel: int = 0
        self.vel_x: float = random.uniform(-1, 1)
        self.vel_y: float = 0.0
        self.timer_feixe: int = 0

    # ------------------------------------------------------------------
    # Entity interface
    # ------------------------------------------------------------------

    def on_update(self, dt: float = 1.0, **kwargs) -> list:
        jogador = kwargs.get("jogador")
        novos = []
        if self.flash > 0:
            self.flash -= 1
        novos = self._mover(jogador)
        if self.invisivel > 0:
            self.invisivel -= 1
        self.timer_ataque -= 1
        if self.timer_ataque <= 0:
            self.timer_ataque = random.randint(110, 170)
            novos.extend(self._atacar(jogador))
        return novos

    def render(self, surface, **kwargs) -> None:
        if self.invisivel > 0:
            if (self.invisivel // 4) % 2 == 0:
                return
        x, y = int(self.x), int(self.y)
        cor = BRANCO if self.flash > 0 else self.cor
        centro = (x, y)
        forma = FORMAS.get(self.tipo, "triangulo")
        self._desenhar_forma(surface, centro, cor, forma)

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x - self.raio),
            int(self.y - self.raio),
            self.raio * 2,
            self.raio * 2,
        )

    # ------------------------------------------------------------------
    # Movement patterns
    # ------------------------------------------------------------------

    def _mover(self, jogador) -> list:
        novos = []
        if self.mov == "reta":
            self.y += self.vel
            self.angulo += 0.04
        elif self.mov == "zigzag":
            self.y += self.vel
            self.fase += 0.05
            self.x = self.base_x + math.sin(self.fase) * 70
            self.angulo += 0.04
        elif self.mov == "zigzag_lento":
            self.y += self.vel
            self.fase += 0.03
            self.x = self.base_x + math.sin(self.fase) * 100
            self.angulo += 0.02
        elif self.mov == "espiral":
            self.y += self.vel * 0.9
            self.fase += 0.045
            self.x = self.base_x + math.sin(self.fase) * 60
            self.angulo += 0.08
        elif self.mov == "persegue":
            dx = jogador.x - self.x
            dy = jogador.y - self.y
            norma = math.hypot(dx, dy) or 1
            self.x += dx / norma * self.vel * 0.9
            self.y += dy / norma * self.vel * 0.9
            self.angulo += 0.06
        elif self.mov == "gira":
            self.y += self.vel
            self.angulo += 0.07
            self.fase += 0.03
            self.x = self.base_x + math.sin(self.fase) * 40
        elif self.mov == "ondulacao":
            self.y += self.vel
            self.angulo += 0.05
            self.x = self.base_x + math.sin(self.fase) * 90
            self.fase += 0.04
        elif self.mov == "erratico":
            if random.random() < 0.02:
                self.vel_x = random.uniform(-1.6, 1.6)
            if random.random() < 0.02:
                self.vel_y = random.uniform(1.0, 2.6)
            self.x += self.vel_x
            self.y += self.vel_y
            self.x = max(20, min(LARGURA - 20, self.x))
            self.angulo += 0.12
        elif self.mov == "flutua":
            self.y += self.vel * 0.5
            self.fase += 0.05
            self.x = self.base_x + math.sin(self.fase) * 30
            self.angulo += 0.03
        elif self.mov == "investida":
            self.y += self.vel * (1 + self.fase * 0.06)
            self.x += (jogador.x - self.x) * 0.03
            self.fase += 0.01
            self.angulo += 0.1
        elif self.mov == "fada":
            self.y += self.vel
            self.fase += 0.03
            self.x = self.base_x + math.sin(self.fase * 1.3) * 80
            self.angulo += 0.05
            if self.invisivel <= 0 and random.random() < 0.006:
                self.invisivel = 40
        return novos

    # ------------------------------------------------------------------
    # Attack patterns
    # ------------------------------------------------------------------

    def _atacar(self, jogador) -> list:
        from src.domain.entities.projectiles.factory import ProjectileFactory

        if self.ataque == "nenhum":
            return []
        x, y = self.x, self.y
        if self.ataque == "baixo":
            return [ProjectileFactory.criar_inimigo(x, y, 0, 4, 1, VERMELHO, 4)]
        if self.ataque == "leque":
            return [
                ProjectileFactory.criar_inimigo(x, y, dx, 4, 1, LARANJA, 4)
                for dx in (-1.5, 0, 1.5)
            ]
        if self.ataque == "4dir":
            return [
                ProjectileFactory.criar_inimigo(
                    x, y, math.cos(a) * 3.5, math.sin(a) * 3.5, 1, AZUL, 4
                )
                for a in (0, math.pi / 2, math.pi, -math.pi / 2)
            ]
        if self.ataque == "tudo":
            return [
                ProjectileFactory.criar_inimigo(
                    x, y, math.cos(a) * 3, math.sin(a) * 3, 1, BRANCO, 4
                )
                for a in [i * math.tau / 8 for i in range(8)]
            ]
        if self.ataque == "feixe":
            dx, dy = jogador.x - x, jogador.y - y
            norma = math.hypot(dx, dy) or 1
            return [
                ProjectileFactory.criar_inimigo(
                    x, y, dx / norma * 6, dy / norma * 6, 1,
                    (240, 235, 200), 3, tipo="feixe"
                )
            ]
        if self.ataque == "mira":
            dx, dy = jogador.x - x, jogador.y - y
            norma = math.hypot(dx, dy) or 1
            return [
                ProjectileFactory.criar_inimigo(
                    x, y, dx / norma * 5, dy / norma * 5, 1, self.cor, 4
                )
            ]
        if self.ataque == "rajada":
            dx, dy = jogador.x - x, jogador.y - y
            norma = math.hypot(dx, dy) or 1
            base_vx, base_vy = dx / norma, dy / norma
            return [
                ProjectileFactory.criar_inimigo(
                    x, y, base_vx * 5, base_vy * 5, 1, CIANO, 4
                )
                for _ in range(3)
            ]
        return []

    # ------------------------------------------------------------------
    # Damage
    # ------------------------------------------------------------------

    def sofrer_dano(self, dano: int) -> bool:
        self.health -= dano
        self.flash = 6
        return self.health <= 0

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _desenhar_forma(self, tela, centro, cor, forma: str) -> None:
        x, y = centro
        if forma == "circulo":
            pygame.draw.circle(tela, cor, (x, y), int(self.raio))
            pygame.draw.circle(tela, BRANCO, (x, y), int(self.raio), 3)
        elif forma == "circulo_pulsante":
            pulso = self.raio
            pygame.draw.circle(tela, cor, (x, y), int(pulso))
            pygame.draw.circle(tela, BRANCO, (x, y), int(pulso), 3)
        elif forma == "triangulo":
            pts = [
                (x, y - self.raio),
                (x - self.raio, y + self.raio),
                (x + self.raio, y + self.raio),
            ]
            pygame.draw.polygon(tela, cor, pts)
            pygame.draw.polygon(tela, BRANCO, pts, 3)
        elif forma == "quadrado":
            s = self.raio
            pts = [
                (x - s, y - s), (x + s, y - s),
                (x + s, y + s), (x - s, y + s),
            ]
            pygame.draw.polygon(tela, cor, pts)
            pygame.draw.polygon(tela, BRANCO, pts, 3)
        elif forma == "estrela":
            pts = self._pontos_estrela(centro, self.raio, self.angulo)
            pygame.draw.polygon(tela, cor, pts)
            pygame.draw.polygon(tela, BRANCO, pts, 3)
        elif forma == "hexagono":
            pts = self._pontos_poligono(centro, self.raio, 6, self.angulo)
            pygame.draw.polygon(tela, cor, pts)
            pygame.draw.polygon(tela, BRANCO, pts, 3)
        elif forma == "losango":
            pts = [
                (x, y - self.raio),
                (x + self.raio * 0.7, y),
                (x, y + self.raio),
                (x - self.raio * 0.7, y),
            ]
            pygame.draw.polygon(tela, cor, pts)
            pygame.draw.polygon(tela, BRANCO, pts, 3)
        elif forma == "pentagono":
            pts = self._pontos_poligono(centro, self.raio, 5, self.angulo)
            pygame.draw.polygon(tela, cor, pts)
            pygame.draw.polygon(tela, BRANCO, pts, 3)
        else:
            pygame.draw.circle(tela, cor, (x, y), int(self.raio))
            pygame.draw.circle(tela, BRANCO, (x, y), int(self.raio), 3)

    @staticmethod
    def _pontos_estrela(centro, raio: float, angulo: float) -> list:
        x, y = centro
        pts = []
        for i in range(10):
            a = angulo + i * math.pi / 5
            r = raio if i % 2 == 0 else raio * 0.45
            pts.append((x + r * math.cos(a), y + r * math.sin(a)))
        return pts

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


# ---------------------------------------------------------------------------
# Wave composition helpers
# ---------------------------------------------------------------------------

def composicao_onda(nivel: int, tipos: list[str]) -> tuple[list[str], int, list]:
    """Define enemy count and spawn positions for a wave.

    Returns ``(tipos, qtd, xs)`` where ``xs`` is a list of x-positions
    (or ``None`` for random) for each enemy in the wave.
    """
    qtd = min(5 + nivel // 2, 22)
    xs: list = [None] * qtd
    if qtd >= 5 and random.random() < 0.35:
        posicoes = [
            max(
                25,
                min(
                    LARGURA - 25,
                    LARGURA // 2 + (i - (qtd - 1) / 2) * 52,
                ),
            )
            for i in range(qtd)
        ]
        posicoes.sort(key=lambda v: abs(v - LARGURA // 2))
        xs = posicoes
    return tipos, qtd, xs


def sortear_inimigo_especial(nivel: int, especiais: list[str]) -> Optional[str]:
    """Roll for a special enemy spawn (10-15% chance)."""
    if not especiais:
        return None
    if random.random() > 0.12:
        return None
    return random.choice(especiais)
