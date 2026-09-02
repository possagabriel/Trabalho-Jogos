"""Armas do jogador e classe de projeteis."""

import math

import pygame

from .config import ALTURA, AZUL_CLARO, BRANCO, CIANO, LARANJA, LARGURA, ROXO, \
    VERDE
from .smooth import desenhar_circulo, desenhar_glow, desenhar_poligono, \
    retangulo_suave

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
    {"nome": "Rifle Gauss", "nivel": 22, "cor": (180, 220, 255), "raio": 3,
     "vel": 14, "dano": 3, "cooldown": 16, "tipo": "gauss"},
    {"nome": "Nova", "nivel": 24, "cor": LARANJA, "raio": 9, "vel": 6,
     "dano": 6, "cooldown": 40, "tipo": "nova"},
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
        # Teleguiados não podem orbitar o jogador indefinidamente. Além de
        # poluir a tela, isso fazia alguns ataques de boss parecerem dano por
        # tempo, vários segundos depois de terem sido disparados.
        if self.origem == "inimigo" and self.tempo > 8 * 60:
            return True
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
            desenhar_glow(tela, (0, 120, 50), (x, y), 12, 0.4)
            retangulo_suave(tela, cor,
                            pygame.Rect(x - 2, y - 12, 4, 24), 2,
                            glow_cor=cor, glow_raio=6)
            pygame.draw.line(tela, BRANCO, (x, y - 12), (x, y + 12), 2)
            desenhar_circulo(tela, BRANCO, (x, y - 12), 2, brilho=1.8)
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
        elif self.tipo == "gauss":
            desenhar_glow(tela, (90, 130, 200), (x, y), 14, 0.4)
            retangulo_suave(tela, cor,
                            pygame.Rect(x - 2, y - 14, 4, 28), 2,
                            glow_cor=cor, glow_raio=6)
            pygame.draw.line(tela, BRANCO, (x, y - 14), (x, y + 14), 2)
            desenhar_circulo(tela, BRANCO, (x, y - 14), 2, brilho=1.8)
        elif self.tipo == "nova":
            pulso = 1 + 0.25 * math.sin(self.tempo * 0.5)
            desenhar_glow(tela, LARANJA, (x, y), (self.raio + 10) * pulso,
                          0.8)
            desenhar_glow(tela, (255, 220, 120), (x, y),
                          (self.raio + 4) * pulso, 0.9)
            desenhar_circulo(tela, cor, (x, y), self.raio * pulso)
            desenhar_circulo(tela, BRANCO, (x, y), max(2, self.raio // 2),
                             brilho=1.6)
        elif self.tipo == "bomba":
            # bomba pesada do especial: esfera grande com nucleo ardente,
            # aletas e uma ponta de ignicao acesa no topo
            pulso = 1 + 0.15 * math.sin(self.tempo * 0.4)
            desenhar_glow(tela, (255, 60, 20), (x, y),
                          (self.raio + 16) * pulso, 0.9)
            desenhar_glow(tela, (255, 220, 120), (x, y),
                          (self.raio + 8) * pulso, 0.8)
            desenhar_circulo(tela, (60, 40, 24), (x, y), self.raio * pulso)
            desenhar_circulo(tela, cor, (x, y), self.raio * 0.72 * pulso)
            desenhar_circulo(tela, BRANCO, (x, y),
                             max(2, int(self.raio * 0.3)), brilho=1.8)
            for sinal in (-1, 1):
                desenhar_poligono(tela, (90, 70, 40),
                                  [(x + sinal * self.raio * 0.85,
                                    y + self.raio * 0.1),
                                   (x + sinal * self.raio * 1.15,
                                    y + self.raio * 0.55),
                                   (x + sinal * self.raio * 0.95,
                                    y + self.raio * 0.55)],
                                  glow_cor=(255, 140, 60), glow_raio=4)
            pygame.draw.line(tela, (255, 240, 180),
                             (x, y - self.raio * 0.9),
                             (x, y - self.raio * 1.25), 3)
            desenhar_glow(tela, (255, 240, 120), (x, y - self.raio * 1.3),
                          6, 0.9)
        else:
            # projetil nitido: capsula alongada no sentido do movimento,
            # nucleo branco quente e ponta brilhante (facil de ler)
            comp = max(self.raio * 2 + 4, self.speed + 4)
            ang = math.atan2(self.vel_y, self.vel_x)
            dx = math.cos(ang) * comp
            dy = math.sin(ang) * comp
            larg = max(3, self.raio * 2)
            desenhar_glow(tela, cor, (x, y), max(10, self.raio * 3), 0.45)
            pygame.draw.line(tela, cor, (x - dx, y - dy), (x + dx, y + dy),
                             larg)
            pygame.draw.line(tela, BRANCO,
                             (x - dx * 0.5, y - dy * 0.5),
                             (x + dx * 0.85, y + dy * 0.85),
                             max(1, larg // 2 - 1))
            desenhar_circulo(tela, BRANCO, (x, y), max(1, larg // 2 - 1),
                             brilho=1.6)
