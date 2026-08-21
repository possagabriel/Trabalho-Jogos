"""ParticleSystem and related classes.

Migrated from game/particles.py SistemaParticulas, Particula, MensagemFlutuante.
"""

from __future__ import annotations

import math
import random
from typing import Optional

import pygame

BRANCO = (255, 255, 255)
CIANO = (0, 220, 255)
DOURADO = (255, 215, 0)
LARANJA = (255, 160, 40)
ROXO = (140, 60, 200)
VERMELHO = (230, 50, 50)


class Particula:
    """Single particle with velocity, lifetime, gravity, and drag.

    Migrated from game/particles.py Particula.
    """

    def __init__(
        self,
        x: float,
        y: float,
        cor: tuple[int, int, int],
        vel: tuple[float, float],
        tamanho: int,
        vida: int,
        gravidade: float = 0.0,
        arrasto: float = 0.98,
    ) -> None:
        self.x: float = x
        self.y: float = y
        self.vx: float = vel[0]
        self.vy: float = vel[1]
        self.cor: tuple[int, int, int] = cor
        self.tamanho: int = tamanho
        self.vida: int = vida
        self.vida_max: int = vida
        self.gravidade: float = gravidade
        self.arrasto: float = arrasto

    def atualizar(self) -> None:
        self.vx *= self.arrasto
        self.vy *= self.arrasto
        self.vy += self.gravidade
        self.x += self.vx
        self.y += self.vy
        self.vida -= 1

    def desenhar(self, tela) -> None:
        if self.vida <= 0:
            return
        alfa = int(255 * self.vida / self.vida_max)
        tam = max(1, int(self.tamanho))
        x, y = int(self.x), int(self.y)
        # Glow
        glow_r = max(2, tam * 2)
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, self.cor + (int(alfa * 0.7),), (glow_r, glow_r), glow_r)
        tela.blit(glow_surf, (x - glow_r, y - glow_r))
        # Core
        surf = pygame.Surface((tam * 2, tam * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, self.cor + (alfa,), (tam, tam), tam)
        tela.blit(surf, (x - tam, y - tam))


class ParticleSystem:
    """Collection of particle effects used by the game.

    Migrated from game/particles.py SistemaParticulas.
    """

    def __init__(self) -> None:
        self.particulas: list[Particula] = []

    def explosao(self, x: float, y: float, cor: tuple, qtd: int = 20, forca: float = 6.0, gravidade: float = 0.0) -> None:
        for _ in range(qtd):
            ang = random.uniform(0, math.tau)
            v = random.uniform(1, forca)
            self.particulas.append(
                Particula(x, y, cor, (math.cos(ang) * v, math.sin(ang) * v),
                          random.randint(2, 5), random.randint(15, 35), gravidade)
            )

    def espiral(self, x: float, y: float, cor: tuple, qtd: int) -> None:
        for i in range(qtd):
            frac = i / qtd
            ang = frac * math.tau * 2
            raio = frac * 45
            px = x + math.cos(ang) * raio
            py = y + math.sin(ang) * raio
            vx = math.cos(ang) * 3
            vy = math.sin(ang) * 3
            self.particulas.append(
                Particula(px, py, cor, (vx, vy), random.randint(2, 4), 40)
            )

    def estrela(self, x: float, y: float, cor: tuple, qtd: int) -> None:
        for i in range(qtd):
            ponta = i % 5
            ang = ponta * math.tau / 5 - math.pi / 2
            raio = random.uniform(5, 60)
            px = x + math.cos(ang) * raio
            py = y + math.sin(ang) * raio
            self.particulas.append(
                Particula(px, py, cor, (math.cos(ang) * 2, math.sin(ang) * 2),
                          random.randint(2, 5), random.randint(25, 45))
            )

    def pulsacao(self, x: float, y: float, cor: tuple, qtd: int) -> None:
        for _ in range(qtd):
            ang = random.uniform(0, math.tau)
            v = random.uniform(4, 8)
            self.particulas.append(
                Particula(x, y, cor, (math.cos(ang) * v, math.sin(ang) * v),
                          random.randint(3, 6), random.randint(10, 22))
            )

    def mega(self, x: float, y: float) -> None:
        cores = [BRANCO, CIANO, VERMELHO, LARANJA, ROXO, DOURADO]
        for _ in range(100):
            ang = random.uniform(0, math.tau)
            v = random.uniform(2, 10)
            cor = random.choice(cores)
            self.particulas.append(
                Particula(x, y, cor, (math.cos(ang) * v, math.sin(ang) * v),
                          random.randint(2, 6), random.randint(25, 55))
            )

    def explosao_dupla(self, x: float, y: float) -> None:
        self.explosao(x, y, LARANJA, 35, 7)
        self.explosao(x, y, VERMELHO, 25, 5)

    def faiscas(self, x: float, y: float, cor: tuple, qtd: int = 6, forca: float = 4.0) -> None:
        for _ in range(qtd):
            ang = random.uniform(0, math.tau)
            v = random.uniform(1.5, forca)
            self.particulas.append(
                Particula(x, y, cor, (math.cos(ang) * v, math.sin(ang) * v),
                          random.randint(1, 2), random.randint(5, 13))
            )

    def rastro(self, x: float, y: float, cor: tuple, forca: float = 1.5) -> None:
        self.particulas.append(
            Particula(x + random.uniform(-2, 2), y + random.uniform(-2, 2),
                      cor, (random.uniform(-forca, forca), random.uniform(-forca, forca)),
                      random.randint(1, 3), random.randint(8, 18))
        )

    def chamas(self, x: float, y: float, cor: tuple, qtd: int = 2) -> None:
        for _ in range(qtd):
            self.particulas.append(
                Particula(x + random.uniform(-3, 3), y,
                          random.choice([cor, LARANJA, DOURADO]),
                          (random.uniform(-0.5, 0.5), random.uniform(-2.5, -1.0)),
                          random.randint(2, 5), random.randint(15, 30))
            )

    def bolhas(self, x: float, y: float, cor: tuple, qtd: int = 1) -> None:
        for _ in range(qtd):
            self.particulas.append(
                Particula(x + random.uniform(-2, 2), y, cor,
                          (random.uniform(-0.3, 0.3), random.uniform(-1.2, -0.5)),
                          random.randint(2, 5), random.randint(40, 90), arrasto=0.99)
            )

    def cristais(self, x: float, y: float, cor: tuple, qtd: int = 1) -> None:
        for _ in range(qtd):
            self.particulas.append(
                Particula(x + random.uniform(-2, 2), y, cor,
                          (random.uniform(-0.4, 0.4), random.uniform(0.8, 1.5)),
                          random.randint(1, 3), random.randint(40, 90), arrasto=0.99)
            )

    def relampago(self, x: float, y: float, cor: tuple) -> None:
        pontos = [(x, y)]
        px, py = x, y
        for _ in range(random.randint(4, 7)):
            px += random.uniform(-25, 25)
            py += random.randint(20, 40)
            pontos.append((px, py))
        for i in range(len(pontos) - 1):
            a, b = pontos[i], pontos[i + 1]
            qtd = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 6))
            for _ in range(qtd):
                t = random.random()
                ex = a[0] + (b[0] - a[0]) * t
                ey = a[1] + (b[1] - a[1]) * t
                self.particulas.append(
                    Particula(ex, ey, cor, (random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4)),
                              random.randint(1, 2), random.randint(8, 16))
                )

    def buraco_negro(self, x: float, y: float) -> None:
        for i in range(14):
            ang = random.uniform(0, math.tau)
            self.particulas.append(
                Particula(x + math.cos(ang) * 16, y + math.sin(ang) * 16,
                          (150, 80, 220), (-math.sin(ang) * 1.5, math.cos(ang) * 1.5),
                          random.randint(1, 3), random.randint(12, 30))
            )

    def salto_dimensional(self, x: float, y: float, cor: tuple) -> None:
        for i in range(30):
            frac = i / 30
            ang = frac * math.tau * 3
            raio = frac * 260
            px = x + math.cos(ang) * raio
            py = y + math.sin(ang) * raio
            self.particulas.append(
                Particula(px, py, cor, (math.cos(ang) * 2.2, math.sin(ang) * 2.2),
                          random.randint(2, 5), random.randint(30, 60))
            )

    def espiral_revelacao(self, x: float, y: float, cor: tuple) -> None:
        for i in range(50):
            px = random.uniform(0, 900)
            py = random.uniform(0, 700)
            self.particulas.append(
                Particula(px, py, cor, (random.uniform(-1, 1), random.uniform(-1, 1)),
                          random.randint(3, 8), random.randint(20, 50))
            )

    def atualizar(self) -> None:
        for p in self.particulas:
            p.atualizar()
        self.particulas = [p for p in self.particulas if p.vida > 0]

    def desenhar(self, tela) -> None:
        for p in self.particulas:
            p.desenhar(tela)

    def limpar(self) -> None:
        self.particulas.clear()


class MensagemFlutuante:
    """Floating text message that rises and fades.

    Migrated from game/particles.py MensagemFlutuante.
    """

    def __init__(
        self,
        texto: str,
        x: float,
        y: float,
        cor: tuple[int, int, int] = BRANCO,
        tempo: int = 70,
    ) -> None:
        self.texto: str = texto
        self.x: float = x
        self.y: float = y
        self.cor: tuple[int, int, int] = cor
        self.tempo: int = tempo
        self.tempo_max: int = tempo

    def atualizar(self) -> None:
        self.y -= 1.0
        self.tempo -= 1

    @property
    def viva(self) -> bool:
        return self.tempo > 0

    def desenhar(self, tela) -> None:
        if self.tempo <= 0:
            return
        try:
            fonte = pygame.font.Font(None, 26)
            superficie = fonte.render(self.texto, True, self.cor)
            superficie.set_alpha(int(255 * self.tempo / self.tempo_max))
            tela.blit(superficie, superficie.get_rect(center=(int(self.x), int(self.y))))
        except Exception:
            pass
