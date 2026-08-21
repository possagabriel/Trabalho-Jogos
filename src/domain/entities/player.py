"""Player entity with movement, shooting, combo system, and skin system."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Optional

import pygame

from src.domain.entities.base import Entity

if TYPE_CHECKING:
    from src.domain.entities.projectiles.factory import ProjectileFactory

# ---------------------------------------------------------------------------
# Screen constants (matching original game config)
# ---------------------------------------------------------------------------
LARGURA = 900
ALTURA = 700

# ---------------------------------------------------------------------------
# Color constants (matching original game config)
# ---------------------------------------------------------------------------
AZUL_CLARO = (100, 180, 255)
BRANCO = (255, 255, 255)
CIANO = (0, 220, 255)
DOURADO = (255, 215, 0)
INDIGO = (75, 0, 130)
LARANJA = (255, 160, 40)
ROXO = (140, 60, 200)
VERDE = (80, 220, 100)
VERMELHO = (230, 50, 50)
AZUL = (50, 100, 200)

# ---------------------------------------------------------------------------
# Skin catalog
# ---------------------------------------------------------------------------

SKINS = [
    {"id": "padrao", "nome": "Padrao", "preco": 0, "cor": CIANO,
     "cor2": (30, 90, 110), "efeito": "nenhum",
     "descricao": "Nave classica"},
    {"id": "fenix", "nome": "Fenix", "preco": 500, "cor": LARANJA,
     "cor2": VERMELHO, "efeito": "chamas",
     "descricao": "Nave com chamas laranjas"},
    {"id": "tempestade", "nome": "Tempestade", "preco": 800, "cor": AZUL,
     "cor2": (255, 240, 60), "efeito": "relampago",
     "descricao": "Nave eletrica"},
    {"id": "sombra", "nome": "Sombra", "preco": 1000, "cor": (60, 40, 90),
     "cor2": ROXO, "efeito": "transparencia",
     "descricao": "Nave stealth"},
    {"id": "cristal", "nome": "Cristal", "preco": 1500, "cor": VERDE,
     "cor2": (200, 255, 220), "efeito": "diamante",
     "descricao": "Nave de cristal"},
    {"id": "dourada", "nome": "Dourada", "preco": 2000, "cor": DOURADO,
     "cor2": BRANCO, "efeito": "brilho",
     "descricao": "Nave de ouro"},
    {"id": "galactica", "nome": "Galactica", "preco": 3000, "cor": (120, 90, 255),
     "cor2": CIANO, "efeito": "estrelas",
     "descricao": "Nave cosmica"},
    {"id": "demoniaca", "nome": "Demoniaca", "preco": 4000, "cor": VERMELHO,
     "cor2": (20, 0, 0), "efeito": "chamas_escuras",
     "descricao": "Nave infernal"},
    {"id": "anjo", "nome": "Anjo", "preco": 5000, "cor": BRANCO,
     "cor2": DOURADO, "efeito": "asas",
     "descricao": "Nave celestial"},
    {"id": "void", "nome": "Void", "preco": 10000, "cor": (20, 0, 40),
     "cor2": INDIGO, "efeito": "buraco_negro",
     "descricao": "Nave do vazio"},
]


class Skin:
    """Ship skin with its own visual effect."""

    def __init__(self, config: dict) -> None:
        self.id: str = config["id"]
        self.nome: str = config["nome"]
        self.preco: int = config["preco"]
        self.cor: tuple[int, int, int] = tuple(config["cor"])
        self.cor2: tuple[int, int, int] = tuple(config["cor2"])
        self.efeito: str = config["efeito"]
        self.descricao: str = config["descricao"]
        self.desbloqueada: bool = config["preco"] == 0

    def __repr__(self) -> str:
        return f"Skin({self.nome!r})"


class ComboSystem:
    """Controls the score multiplier based on consecutive shots."""

    def __init__(self) -> None:
        self.combo_atual: int = 0
        self.combo_maximo: int = 0
        self.ultimo_tiro: int = -99999
        self.tempo_maximo_entre_tiros: int = 500

    def adicionar_tiro(self) -> None:
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro < self.tempo_maximo_entre_tiros:
            self.combo_atual += 1
        else:
            self.combo_atual = 1
        self.ultimo_tiro = agora
        if self.combo_atual > self.combo_maximo:
            self.combo_maximo = self.combo_atual

    def get_bonus(self) -> float:
        if self.combo_atual > 20:
            return 2.0
        if self.combo_atual > 10:
            return 1.5
        return 1.0

    def zerar(self) -> None:
        self.combo_atual = 0


class Player(Entity):
    """The player ship entity with full movement, shooting, and skin system.

    Migrated from game/player.py Jogador class.
    """

    def __init__(
        self,
        nome: str = "Jogador",
        skin: Optional[Skin] = None,
        projectile_factory: Optional["ProjectileFactory"] = None,
    ) -> None:
        super().__init__(
            x=LARGURA // 2,
            y=ALTURA - 100,
            health=5,
            max_health=8,
        )
        self.nome: str = nome
        self.raio: int = 16
        self.velocidade: float = 5.0
        self.pontuacao: int = 0
        self.moedas_jogo: int = 0
        self.nivel: int = 1
        self.arma_atual: int = 0
        self.armas_desbloqueadas: list[int] = [0]
        self.escudo: bool = False
        self.cooldown_tiro: int = 0
        self.burst_left: int = 0
        self.angulo_arma: float = 0.0
        self.invencivel: int = 0
        self.tilt: float = 0.0
        self.vivo: bool = True
        self.skin: Skin = skin or Skin(SKINS[0])
        self.combo: ComboSystem = ComboSystem()
        self._projectile_factory: Optional["ProjectileFactory"] = (
            projectile_factory
        )

    # ------------------------------------------------------------------
    # Entity interface
    # ------------------------------------------------------------------

    def on_update(self, dt: float = 1.0, **kwargs) -> list:
        teclas = kwargs.get("teclas")
        controles = kwargs.get("controles") or {}
        if teclas is None:
            return []
        self._mover(teclas, controles)
        if self.cooldown_tiro > 0:
            self.cooldown_tiro -= 1
        if self.invencivel > 0:
            self.invencivel -= 1
        return []

    def render(self, surface, **kwargs) -> None:
        particulas = kwargs.get("particulas")
        if self.invencivel > 0 and (self.invencivel // 4) % 2 == 0:
            return
        self._desenhar_skin(surface, particulas)
        if self.escudo:
            self._desenhar_escudo(surface)

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

    def _mover(self, teclas, controles: dict) -> None:
        dx = dy = 0
        esquerda = controles.get("esquerda")
        direita = controles.get("direita")
        cima = controles.get("cima")
        baixo = controles.get("baixo")
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a] or (
            esquerda and teclas[esquerda]
        ):
            dx -= 1
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d] or (
            direita and teclas[direita]
        ):
            dx += 1
        if teclas[pygame.K_UP] or teclas[pygame.K_w] or (
            cima and teclas[cima]
        ):
            dy -= 1
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s] or (
            baixo and teclas[baixo]
        ):
            dy += 1
        if dx and dy:
            dx *= 0.7071
            dy *= 0.7071
        self.x += dx * self.velocidade
        self.y += dy * self.velocidade
        self.x = max(20, min(LARGURA - 20, self.x))
        self.y = max(40, min(ALTURA - 30, self.y))
        self.tilt += (dx * 5 - self.tilt) * 0.15

    # ------------------------------------------------------------------
    # Shooting
    # ------------------------------------------------------------------

    def atirar(self) -> list:
        """Fire the current weapon. Returns a list of Projectile instances."""
        from src.domain.entities.projectiles.factory import (
            ProjectileFactory,
            ARMARIA,
        )

        arma = ARMARIA[self.arma_atual]
        if self.cooldown_tiro > 0 or not self.vivo:
            return []
        self.combo.adicionar_tiro()
        x, y = self.x, self.y - 20
        tipo = arma["tipo"]

        if tipo == "metralhadora":
            if self.burst_left <= 0:
                self.burst_left = arma["qtd"]
            self.burst_left -= 1
            self.cooldown_tiro = 4 if self.burst_left > 0 else arma["cooldown"]
            return [
                ProjectileFactory.criar(
                    x, y, 0, -arma["vel"], arma["dano"], arma["cor"],
                    arma["raio"], tipo=tipo
                )
            ]

        self.cooldown_tiro = arma["cooldown"]

        if tipo == "duplo":
            return [
                ProjectileFactory.criar(
                    x - 9, y, 0, -arma["vel"], arma["dano"], arma["cor"],
                    arma["raio"], tipo=tipo
                ),
                ProjectileFactory.criar(
                    x + 9, y, 0, -arma["vel"], arma["dano"], arma["cor"],
                    arma["raio"], tipo=tipo
                ),
            ]
        if tipo == "espiral":
            self.angulo_arma += 0.45
            projs = []
            for i in range(arma["qtd"]):
                a = self.angulo_arma + (i - 1) * 0.7
                projs.append(
                    ProjectileFactory.criar(
                        x, y, math.sin(a) * 2.2, -arma["vel"],
                        arma["dano"], arma["cor"], arma["raio"], tipo=tipo
                    )
                )
            return projs
        if tipo == "ion":
            return [
                ProjectileFactory.criar(
                    x, y, 0, 0, arma["dano"], arma["cor"],
                    arma["raio"], tipo=tipo
                )
            ]
        if tipo == "gauss":
            return [
                ProjectileFactory.criar(
                    x, y, 0, -arma["vel"], arma["dano"], arma["cor"],
                    arma["raio"], tipo=tipo
                )
            ]
        if tipo == "nova":
            return [
                ProjectileFactory.criar(
                    x, y, 0, -arma["vel"], arma["dano"], arma["cor"],
                    arma["raio"], tipo=tipo
                )
            ]

        return [
            ProjectileFactory.criar(
                x, y, 0, -arma["vel"], arma["dano"], arma["cor"],
                arma["raio"], tipo=tipo
            )
        ]

    def selecionar_arma(self, indice: int) -> None:
        if indice in self.armas_desbloqueadas:
            self.arma_atual = indice

    # ------------------------------------------------------------------
    # Damage
    # ------------------------------------------------------------------

    def sofrer_dano(self) -> bool:
        """Apply damage to the player. Returns True if damage was applied."""
        if self.invencivel > 0 or not self.vivo:
            return False
        self.combo.zerar()
        if self.escudo:
            self.escudo = False
            self.invencivel = 90
            return True
        self.health -= 1
        self.invencivel = 120
        if self.health <= 0:
            self.health = 0
            self.vivo = False
        return True

    # ------------------------------------------------------------------
    # Skin rendering (migrated from Skin.desenhar)
    # ------------------------------------------------------------------

    def _desenhar_skin(self, tela, particulas=None) -> None:
        x, y = int(self.x), int(self.y)
        t = pygame.time.get_ticks() * 0.001
        if self.skin.id == "padrao":
            self._desenhar_nave_base(tela, x, y, self.tilt, t)
        elif self.skin.efeito == "transparencia":
            self._desenhar_transparente(tela, x, y, self.tilt, t)
        elif self.skin.efeito == "diamante":
            self._desenhar_diamante(tela, x, y, self.tilt, t)
        elif self.skin.efeito == "asas":
            self._desenhar_asas(tela, x, y, self.tilt, t)
        else:
            self._desenhar_nave_base(tela, x, y, self.tilt, t)

        if self.skin.efeito == "chamas" and particulas:
            particulas.chamas(x, y + 14, LARANJA, 2)
        elif self.skin.efeito == "chamas_escuras" and particulas:
            particulas.chamas(x, y + 14, VERMELHO, 2)
        elif self.skin.efeito == "relampago":
            self._desenhar_relampago(tela, x, y, t)
        elif self.skin.efeito == "brilho":
            self._desenhar_brilho(tela, x, y, t)
        elif self.skin.efeito == "estrelas" and particulas:
            if t % 0.15 < 0.02:
                particulas.rastro(
                    x + random.uniform(-4, 4), y, (200, 220, 255), 1.0
                )
        elif self.skin.efeito == "buraco_negro" and particulas:
            particulas.buraco_negro(x, y)

    def _pontos_nave(self, x: float, y: float, tilt: float) -> list:
        return [(x, y - 20), (x - 15, y + 16), (x, y + 7), (x + 15, y + 16)]

    def _desenhar_nave_base(self, tela, x, y, tilt, t) -> None:
        cor = self.skin.cor
        cor2 = self.skin.cor2
        from src.domain.systems.particle_system import ParticleSystem
        pts = self._pontos_nave(x, y, tilt)
        # Simplified rendering - full visual requires cel_shading/smooth modules
        pygame.draw.polygon(tela, cor, pts)
        pygame.draw.polygon(tela, cor2, pts, 2)
        pygame.draw.circle(tela, AZUL_CLARO, (int(x), int(y) - 2), 6)

    def _desenhar_transparente(self, tela, x, y, tilt, t) -> None:
        alfa = int(120 + 60 * math.sin(t * 3))
        surf = pygame.Surface((44, 44), pygame.SRCALPHA)
        pts = [(22, 2), (7, 38), (22, 29), (37, 38)]
        pygame.draw.polygon(surf, self.skin.cor + (alfa,), pts)
        pygame.draw.polygon(surf, (150, 60, 200, alfa), pts, 2)
        tela.blit(surf, (x - 22, y - 22))

    def _desenhar_diamante(self, tela, x, y, tilt, t) -> None:
        # Diamond shape - simplified losango
        r = 14
        angle = tilt + math.sin(t * 2) * 0.1
        pts = [
            (x + r * math.sin(angle), y - r * math.cos(angle)),
            (x + r * 0.7 * math.cos(angle), y + r * 0.7 * math.sin(angle)),
            (x - r * math.sin(angle), y + r * math.cos(angle)),
            (x - r * 0.7 * math.cos(angle), y - r * 0.7 * math.sin(angle)),
        ]
        pygame.draw.polygon(tela, self.skin.cor, pts)
        pygame.draw.polygon(tela, self.skin.cor2, pts, 2)

    def _desenhar_asas(self, tela, x, y, tilt, t) -> None:
        self._desenhar_nave_base(tela, x, y, tilt, t)
        for sinal in (-1, 1):
            base_y = y + 8
            ponta_y = y + 24
            pts = [
                (x + sinal * 10, base_y),
                (x + sinal * 34, ponta_y + math.sin(t * 5) * 6),
                (x + sinal * 26, ponta_y),
                (x + sinal * 8, base_y + 6),
            ]
            pygame.draw.polygon(tela, (255, 250, 220), pts)
            pygame.draw.polygon(tela, (200, 180, 160), pts, 2)

    def _desenhar_relampago(self, tela, x, y, t) -> None:
        if int(t * 4) % 2 == 0:
            for sinal in (-1, 1):
                pts = [
                    (x + sinal * 18, y - 8),
                    (x + sinal * 8, y),
                    (x + sinal * 20, y + 12),
                    (x + sinal * 6, y + 22),
                ]
                pygame.draw.polygon(tela, (255, 240, 60), pts)

    def _desenhar_brilho(self, tela, x, y, t) -> None:
        pulso = 14 + 5 * math.sin(t * 4)
        # Simplified glow
        pygame.draw.circle(
            tela, (255, 215, 0), (int(x), int(y)), int(pulso), 2
        )

    def _desenhar_escudo(self, tela) -> None:
        pulso = 1 + 0.15 * math.sin(pygame.time.get_ticks() * 0.008)
        raio = int((self.raio + 8) * pulso)
        pygame.draw.circle(
            tela, (50, 150, 255), (int(self.x), int(self.y)), raio, 2
        )
