"""Armas do jogador e classe de projeteis."""

import math

import pygame

from .config import ALTURA, AZUL_CLARO, BRANCO, CIANO, LARANJA, LARGURA, ROXO, \
    VERDE
from .smooth import desenhar_circulo, desenhar_glow, retangulo_suave

CORES_ARCO_IRIS = [(255, 60, 60), (255, 220, 60), (90, 255, 90),
                   (60, 220, 255), (90, 120, 255), (230, 90, 255)]

ARMARIA = [
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
]


class Projetil:
    """Projetil disparado pelo jogador ou por inimigos."""

    def __init__(self, x, y, vel_x, vel_y, dano, cor, raio, tipo="padrao",
                 origem="jogador", teleguiado=False, refletor=False):
        self.x, self.y = x, y
        self.vel_x, self.vel_y = vel_x, vel_y
        self.dano = dano
        self.cor = cor
        self.raio = raio
        self.tipo = tipo
        self.origem = origem
        self.teleguiado = teleguiado
        self.refletor = refletor
        self.tempo = 0
        self.speed = math.hypot(vel_x, vel_y) or 1

    @property
    def rect(self):
        if self.tipo == "ion":
            return pygame.Rect(int(self.x - 7), 0, 14, ALTURA)
        return pygame.Rect(int(self.x - self.raio), int(self.y - self.raio),
                           self.raio * 2, self.raio * 2)

    def atualizar(self):
        if self.tipo == "ion":
            self.tempo += 1
            return
        self.x += self.vel_x
        self.y += self.vel_y
        self.tempo += 1

    def atualizar_teleguiado(self, alvo_x, alvo_y):
        dx, dy = alvo_x - self.x, alvo_y - self.y
        norma = math.hypot(dx, dy) or 1
        self.vel_x += (dx / norma * self.speed - self.vel_x) * 0.1
        self.vel_y += (dy / norma * self.speed - self.vel_y) * 0.1
        self.x += self.vel_x
        self.y += self.vel_y
        self.tempo += 1

    def refletir(self):
        """Inverte a direcao do projetil (usado pelo campo de forca)."""
        self.vel_x *= -1
        self.vel_y *= -1
        self.origem = "inimigo"
        self.refletor = True

    def saiu_da_tela(self):
        if self.tipo == "ion":
            return self.tempo > 14
        return not (-30 <= self.x <= LARGURA + 30 and
                    -30 <= self.y <= ALTURA + 30)

    def _cor_atual(self):
        if self.tipo == "espiral":
            return CORES_ARCO_IRIS[(self.tempo // 6) % len(CORES_ARCO_IRIS)]
        return self.cor

    def desenhar(self, tela):
        x, y = int(self.x), int(self.y)
        cor = self._cor_atual()
        if self.tipo == "plasma":
            r = self.raio * (1 + 0.3 * math.sin(self.tempo * 0.4))
            desenhar_glow(tela, ROXO, (x, y), r + 8, 0.7)
            desenhar_circulo(tela, ROXO, (x, y), r + 3)
            desenhar_circulo(tela, cor, (x, y), r)
            desenhar_circulo(tela, BRANCO, (x, y), max(2, r // 2), brilho=1.5)
        elif self.tipo == "laser":
            desenhar_glow(tela, (0, 120, 50), (x, y), 14, 0.6)
            retangulo_suave(tela, (0, 120, 50),
                            pygame.Rect(x - 3, y - 10, 6, 20), 3)
            retangulo_suave(tela, cor, pygame.Rect(x - 1, y - 8, 2, 16), 2,
                            glow_cor=cor, glow_raio=8)
        elif self.tipo == "ion":
            desenhar_glow(tela, (80, 110, 180), (x, ALTURA // 2),
                          max(ALTURA, LARGURA) // 2, 0.5)
            retangulo_suave(tela, (80, 110, 180),
                            pygame.Rect(x - 9, 0, 18, ALTURA), 6)
            retangulo_suave(tela, cor, pygame.Rect(x - 3, 0, 6, ALTURA), 3,
                            glow_cor=cor, glow_raio=20)
            retangulo_suave(tela, BRANCO, pygame.Rect(x - 1, 0, 2, ALTURA), 2,
                            glow_cor=BRANCO, glow_raio=12)
        elif self.tipo == "feixe":
            desenhar_glow(tela, cor, (x, y + 30), 20, 0.6)
            pygame.draw.aaline(tela, cor + (255,), (x, y), (x, y + 60), 3)
            pygame.draw.aaline(tela, BRANCO + (255,), (x, y), (x, y + 60), 1)
        else:
            desenhar_glow(tela, cor, (x, y), self.raio * 3, 0.6)
            desenhar_circulo(tela, cor, (x, y), self.raio)
            desenhar_circulo(tela, BRANCO, (x, y), max(1, self.raio // 2),
                             brilho=1.6)