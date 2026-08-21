"""ProjectileFactory and Projetil class.

Migrated from game/weapons.py Projetil class and ARMARIA list.
"""

from __future__ import annotations

import math

import pygame

# ---------------------------------------------------------------------------
# Screen constants
# ---------------------------------------------------------------------------
LARGURA = 900
ALTURA = 700

# ---------------------------------------------------------------------------
# Color constants
# ---------------------------------------------------------------------------
AZUL_CLARO = (100, 180, 255)
BRANCO = (255, 255, 255)
CIANO = (0, 220, 255)
LARANJA = (255, 160, 40)
ROXO = (140, 60, 200)
VERDE = (80, 220, 100)

# Rainbow colors for spiral projectiles
CORES_ARCO_IRIS = [
    (255, 60, 60), (255, 220, 60), (90, 255, 90),
    (60, 220, 255), (90, 120, 255), (230, 90, 255),
]

# ---------------------------------------------------------------------------
# Weapon catalog
# ---------------------------------------------------------------------------

ARMARIA: list[dict] = [
    {"nome": "Tiro Padrao", "nivel": 1, "cor": BRANCO, "raio": 4, "vel": 8,
     "dano": 1, "cooldown": 12, "tipo": "padrao"},
    {"nome": "Laser", "nivel": 3, "cor": VERDE, "raio": 3, "vel": 12,
     "dano": 2, "cooldown": 9, "tipo": "laser"},
    {"nome": "Tiro Duplo", "nivel": 6, "cor": CIANO, "raio": 6, "vel": 9,
     "dano": 1, "cooldown": 15, "tipo": "duplo"},
    {"nome": "Plasma", "nivel": 9, "cor": ROXO, "raio": 8, "vel": 7,
     "dano": 3, "cooldown": 18, "tipo": "plasma"},
    {"nome": "Metralhadora", "nivel": 12, "cor": LARANJA, "raio": 3, "vel": 10,
     "dano": 1, "cooldown": 30, "tipo": "metralhadora", "qtd": 5},
    {"nome": "Espiral", "nivel": 16, "cor": BRANCO, "raio": 5, "vel": 8,
     "dano": 2, "cooldown": 24, "tipo": "espiral", "qtd": 3},
    {"nome": "Canhao de Ions", "nivel": 20, "cor": AZUL_CLARO, "raio": 6,
     "vel": 0, "dano": 5, "cooldown": 48, "tipo": "ion"},
    {"nome": "Rifle Gauss", "nivel": 22, "cor": (180, 220, 255), "raio": 3,
     "vel": 14, "dano": 3, "cooldown": 16, "tipo": "gauss"},
    {"nome": "Nova", "nivel": 24, "cor": LARANJA, "raio": 9, "vel": 6,
     "dano": 6, "cooldown": 40, "tipo": "nova"},
]


class Projetil:
    """Projectile fired by the player or enemies.

    Migrated from game/weapons.py Projetil.
    """

    def __init__(
        self,
        x: float,
        y: float,
        vel_x: float,
        vel_y: float,
        dano: int,
        cor: tuple[int, int, int],
        raio: int,
        tipo: str = "padrao",
        origem: str = "jogador",
        teleguiado: bool = False,
        refletor: bool = False,
    ) -> None:
        self.x: float = x
        self.y: float = y
        self.vel_x: float = vel_x
        self.vel_y: float = vel_y
        self.dano: int = dano
        self.cor: tuple[int, int, int] = cor
        self.raio: int = raio
        self.tipo: str = tipo
        self.origem: str = origem
        self.teleguiado: bool = teleguiado
        self.refletor: bool = refletor
        self.tempo: int = 0
        self.speed: float = math.hypot(vel_x, vel_y) or 1

    @property
    def rect(self) -> pygame.Rect:
        if self.tipo == "ion":
            return pygame.Rect(int(self.x - 7), 0, 14, ALTURA)
        return pygame.Rect(
            int(self.x - self.raio),
            int(self.y - self.raio),
            self.raio * 2,
            self.raio * 2,
        )

    def atualizar(self) -> None:
        """Update projectile position."""
        if self.tipo == "ion":
            self.tempo += 1
            return
        self.x += self.vel_x
        self.y += self.vel_y
        self.tempo += 1

    def atualizar_teleguiado(self, alvo_x: float, alvo_y: float) -> None:
        """Update homing projectile toward target."""
        dx, dy = alvo_x - self.x, alvo_y - self.y
        norma = math.hypot(dx, dy) or 1
        self.vel_x += (dx / norma * self.speed - self.vel_x) * 0.1
        self.vel_y += (dy / norma * self.speed - self.vel_y) * 0.1
        self.x += self.vel_x
        self.y += self.vel_y
        self.tempo += 1

    def refletir(self) -> None:
        """Reflect projectile direction (used by force field)."""
        self.vel_x *= -1
        self.vel_y *= -1
        self.origem = "inimigo"
        self.refletor = True

    def saiu_da_tela(self) -> bool:
        """Check if projectile left the screen bounds."""
        if self.tipo == "ion":
            return self.tempo > 14
        return not (-30 <= self.x <= LARGURA + 30 and -30 <= self.y <= ALTURA + 30)

    def _cor_atual(self) -> tuple[int, int, int]:
        if self.tipo == "espiral":
            return CORES_ARCO_IRIS[(self.tempo // 6) % len(CORES_ARCO_IRIS)]
        return self.cor

    def desenhar(self, tela) -> None:
        """Draw the projectile on the given surface."""
        x, y = int(self.x), int(self.y)
        cor = self._cor_atual()
        if self.tipo == "plasma":
            r = self.raio * (1 + 0.3 * math.sin(self.tempo * 0.4))
            pygame.draw.circle(tela, ROXO, (x, y), int(r + 3), 2)
            pygame.draw.circle(tela, cor, (x, y), int(r), 2)
            pygame.draw.circle(tela, BRANCO, (x, y), max(2, int(r // 2)))
        elif self.tipo == "laser":
            rect_laser = pygame.Rect(x - 2, y - 12, 4, 24)
            pygame.draw.rect(tela, cor, rect_laser)
            pygame.draw.rect(tela, BRANCO, rect_laser, 1)
            pygame.draw.line(tela, BRANCO, (x, y - 12), (x, y + 12), 2)
        elif self.tipo == "ion":
            rect_ion = pygame.Rect(x - 9, 0, 18, ALTURA)
            pygame.draw.rect(tela, (80, 110, 180), rect_ion)
            pygame.draw.rect(tela, cor, pygame.Rect(x - 3, 0, 6, ALTURA))
            pygame.draw.line(tela, BRANCO, (x - 1, 0), (x - 1, ALTURA), 2)
        elif self.tipo == "feixe":
            pygame.draw.line(tela, cor, (x, y), (x, y + 60), 3)
            pygame.draw.line(tela, BRANCO, (x, y), (x, y + 60), 1)
        elif self.tipo == "gauss":
            rect_gauss = pygame.Rect(x - 2, y - 14, 4, 28)
            pygame.draw.rect(tela, cor, rect_gauss)
            pygame.draw.rect(tela, BRANCO, rect_gauss, 1)
            pygame.draw.line(tela, BRANCO, (x, y - 14), (x, y + 14), 2)
        elif self.tipo == "nova":
            pulso = 1 + 0.25 * math.sin(self.tempo * 0.5)
            r = int(self.raio * pulso)
            pygame.draw.circle(tela, cor, (x, y), r, 3)
            pygame.draw.circle(tela, BRANCO, (x, y), max(2, r // 2))
        elif self.tipo == "bomba":
            pulso = 1 + 0.15 * math.sin(self.tempo * 0.4)
            r = int(self.raio * pulso)
            pygame.draw.circle(tela, (60, 40, 24), (x, y), r, 3)
            pygame.draw.circle(tela, cor, (x, y), int(r * 0.72), 2)
            pygame.draw.circle(tela, BRANCO, (x, y), max(2, int(r * 0.3)))
            # Fuse line
            pygame.draw.line(
                tela, (255, 240, 180),
                (x, y - int(self.raio * 0.9)),
                (x, y - int(self.raio * 1.25)), 3,
            )
        else:
            comp = max(self.raio * 2 + 4, self.speed + 4)
            ang = math.atan2(self.vel_y, self.vel_x)
            dx = math.cos(ang) * comp
            dy = math.sin(ang) * comp
            larg = max(3, self.raio * 2)
            pygame.draw.line(tela, cor, (x - dx, y - dy), (x + dx, y + dy), larg)
            pygame.draw.line(
                tela, BRANCO,
                (x - dx * 0.5, y - dy * 0.5),
                (x + dx * 0.85, y + dy * 0.85),
                max(1, larg // 2 - 1),
            )


class ProjectileFactory:
    """Factory for creating Projectile instances.

    Provides static methods for both player and enemy projectiles.
    """

    @staticmethod
    def criar(
        x: float,
        y: float,
        vel_x: float,
        vel_y: float,
        dano: int,
        cor: tuple[int, int, int],
        raio: int,
        tipo: str = "padrao",
        origem: str = "jogador",
        teleguiado: bool = False,
    ) -> Projetil:
        """Create a player projectile."""
        return Projetil(
            x, y, vel_x, vel_y, dano, cor, raio,
            tipo=tipo, origem=origem, teleguiado=teleguiado,
        )

    @staticmethod
    def criar_inimigo(
        x: float,
        y: float,
        vel_x: float,
        vel_y: float,
        dano: int,
        cor: tuple[int, int, int],
        raio: int,
        tipo: str = "padrao",
        teleguiado: bool = False,
    ) -> Projetil:
        """Create an enemy projectile."""
        return Projetil(
            x, y, vel_x, vel_y, dano, cor, raio,
            tipo=tipo, origem="inimigo", teleguiado=teleguiado,
        )

    @staticmethod
    def criar_especial(
        x: float,
        y: float,
        vel_x: float,
        vel_y: float,
        dano: int,
        cor: tuple[int, int, int],
        raio: int,
        tipo: str = "bomba",
    ) -> Projetil:
        """Create a special weapon projectile (e.g. vortex bomb)."""
        return Projetil(
            x, y, vel_x, vel_y, dano, cor, raio,
            tipo=tipo, origem="jogador",
        )
