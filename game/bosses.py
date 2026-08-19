"""Bosses: um para cada cenario, com ataques e efeitos de morte proprios."""

import math
import random

import pygame

from .config import ALTURA, AZUL, BRANCO, CIANO, DOURADO, LARGURA, ROSA, ROXO, \
    VERMELHO
from .geometry import estrela, losango, pentagono as pent_pontos, poligono
from .smooth import desenhar_circulo, desenhar_glow, desenhar_poligono
from .weapons import Projetil


class Boss:
    """Boss de um cenario. Aparece a cada 5 niveis."""

    def __init__(self, nivel, cenario):
        self.nivel = nivel
        self.cenario_id = cenario.id
        cfg = BOSSES_POR_CENARIO[cenario.id]
        self.nome = cfg["nome"]
        self.cor = cfg["cor"]
        self.raio = cfg["raio"]
        self.vida = cfg["vida"] * (1 + 0.15 * max(0, (nivel - cfg["nivel"])))
        self.vida_max = self.vida
        self.pontos = cfg["pontos"]
        self.mov = cfg["mov"]
        self.ataque = cfg["ataque"]
        self.alvo_y = cfg["alvo_y"]
        self.efeito = cfg["efeito"]
        self.part_qtd = cfg["part_qtd"]
        self.x = LARGURA // 2
        self.y = -self.raio - 20
        self.angulo = 0.0
        self.t = 0
        self.entrando = True
        self.timer_ataque = 90
        self.flash = 0
        self.teleportando = False
        self.teleport_timer = 130
        self.alvo = None

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.raio), int(self.y - self.raio),
                           self.raio * 2, self.raio * 2)

    def atualizar(self, jogador):
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

        if self.mov == "zigzag":
            self.x = LARGURA // 2 + math.sin(self.t * 0.03) * 220
            self.angulo += 0.02
        elif self.mov == "gira":
            self.angulo += 0.03
            self.x += math.sin(self.t * 0.01) * 1.2
            self.x = max(self.raio, min(LARGURA - self.raio, self.x))
        elif self.mov == "infinito":
            self.x = LARGURA // 2 + math.sin(self.t * 0.02) * 320
            self.y = self.alvo_y + math.sin(self.t * 0.04) * 100
            self.angulo += 0.02
        elif self.mov == "teletransporte":
            self._atualizar_teletransporte()
        elif self.mov == "centro":
            self.angulo += 0.01

        self.timer_ataque -= 1
        if self.timer_ataque <= 0:
            self.timer_ataque = self._intervalo_ataque()
            novos = self._atacar(jogador)
        return novos

    def _atualizar_teletransporte(self):
        if not self.teleportando:
            self.teleport_timer -= 1
            if self.teleport_timer <= 0:
                self.teleportando = True
                self.alvo = (random.randint(100, LARGURA - 100),
                             random.randint(100, 450))
        else:
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

    def _intervalo_ataque(self):
        if self.ataque == "combinado":
            return 60
        return random.randint(75, 110)

    def _atacar(self, jogador):
        x, y = self.x, self.y
        if self.ataque == "leque":
            return [Projetil(x, y, dx, 4, 1, self.cor, 5, origem="inimigo")
                    for dx in (-2, 0, 2)]
        if self.ataque == "8dir":
            return [Projetil(x, y, math.cos(a) * 3.5, math.sin(a) * 3.5, 1,
                             self.cor, 5, origem="inimigo")
                    for a in [i * math.tau / 8 for i in range(8)]]
        if self.ataque == "teleguiado":
            return [Projetil(x, y, jogador.x - x, jogador.y - y, 1,
                             self.cor, 5, origem="inimigo", teleguiado=True)
                    for _ in range(3)]
        if self.ataque == "tudo":
            return [Projetil(x, y, math.cos(a) * 3.2, math.sin(a) * 3.2, 1,
                             self.cor, 5, origem="inimigo")
                    for a in [i * math.tau / 12 for i in range(12)]]
        if self.ataque == "combinado":
            fracao = self.vida / self.vida_max
            projs = []
            if fracao <= 0.66:
                projs += [Projetil(x, y, math.cos(a) * 3.2,
                                   math.sin(a) * 3.2, 1, ROSA, 5,
                                   origem="inimigo")
                          for a in [i * math.tau / 8 for i in range(8)]]
            if fracao <= 0.33:
                projs += [Projetil(x, y, jogador.x - x, jogador.y - y, 1,
                                   CIANO, 5, origem="inimigo",
                                   teleguiado=True) for _ in range(3)]
            projs += [Projetil(x, y, dx, 4.5, 1, self.cor, 5,
                               origem="inimigo") for dx in (-2, 0, 2)]
            return projs
        return []

    def sofrer_dano(self, dano):
        self.vida -= dano
        self.flash = 6
        return self.vida <= 0

    def desenhar(self, tela):
        x, y = int(self.x), int(self.y)
        cor = BRANCO if self.flash > 0 else self.cor
        centro = (x, y)
        if self.entrando:
            desenhar_glow(tela, cor, centro, self.raio * 1.3, 0.6)
            desenhar_circulo(tela, cor, centro, self.raio, 3)
            return
        if self.nome == "HEXAGONO":
            desenhar_glow(tela, cor, centro, self.raio * 1.6, 0.6)
            desenhar_poligono(tela, cor, poligono(centro, self.raio, 6,
                                                  self.angulo),
                              glow_cor=cor, glow_raio=self.raio)
            desenhar_poligono(tela, (120, 0, 0), poligono(centro,
                                                          self.raio, 6,
                                                          self.angulo), 3)
        elif self.nome == "LOSANGO":
            desenhar_glow(tela, cor, centro, self.raio * 1.6, 0.6)
            desenhar_poligono(tela, cor, losango(centro, self.raio * 0.7,
                                                 self.raio, self.angulo),
                              glow_cor=cor, glow_raio=self.raio)
            desenhar_poligono(tela, (0, 60, 130),
                              losango(centro, self.raio * 0.4,
                                      self.raio * 0.6, -self.angulo),
                              glow_cor=(0, 120, 200), glow_raio=14)
        elif self.nome == "ESTRELA":
            desenhar_glow(tela, cor, centro, self.raio * 1.7, 0.7)
            desenhar_poligono(tela, cor, estrela(centro, self.raio,
                                                 angulo=self.angulo),
                              glow_cor=cor, glow_raio=self.raio)
            desenhar_poligono(tela, (120, 90, 0),
                              estrela(centro, self.raio * 0.6,
                                      angulo=-self.angulo), 2)
        elif self.nome == "PENTAGONO":
            desenhar_glow(tela, cor, centro, self.raio * 1.6, 0.6)
            desenhar_poligono(tela, cor, pent_pontos(centro, self.raio,
                                                     self.angulo),
                              glow_cor=cor, glow_raio=self.raio)
            desenhar_poligono(tela, (70, 20, 100),
                              pent_pontos(centro, self.raio, self.angulo), 3)
            if self.teleportando:
                desenhar_glow(tela, ROSA, self.alvo, 20, 0.8)
                desenhar_circulo(tela, ROSA, self.alvo, 12, 2, brilho=1.2)
        elif self.nome == "ANEIS":
            self._desenhar_aneis(tela, centro, x, y, cor)
        elif self.nome == "ANEIS DOURADO":
            self._desenhar_aneis(tela, centro, x, y, cor, dourado=True)

    def _desenhar_aneis(self, tela, centro, x, y, cor, dourado=False):
        aneis = [(cor, self.raio, 0.10), (ROSA, self.raio * 0.72, 0.16),
                 (VERMELHO, self.raio * 0.44, 0.24)]
        if dourado:
            aneis = [(DOURADO, self.raio, 0.10), (BRANCO, self.raio * 0.72,
                                                  0.16),
                     (cor, self.raio * 0.44, 0.24)]
        desenhar_glow(tela, cor, centro, self.raio * 1.4, 0.6)
        for cor_anel, raio, velocidade in aneis:
            desenhar_circulo(tela, cor_anel, centro, raio, 2, brilho=1.1)
            ang = self.t * velocidade
            for i in range(3):
                a = ang + i * math.tau / 3
                px = x + math.cos(a) * raio
                py = y + math.sin(a) * raio
                desenhar_circulo(tela, cor_anel, (px, py), 4, brilho=1.4)
        desenhar_circulo(tela, BRANCO, centro, 12, brilho=1.4)


BOSSES_POR_CENARIO = {
    1: {"nome": "HEXAGONO", "cor": VERMELHO, "raio": 40, "vida": 30,
        "pontos": 200, "mov": "zigzag", "ataque": "leque",
        "alvo_y": 150, "efeito": "explosao", "part_qtd": 10, "nivel": 5},
    2: {"nome": "LOSANGO", "cor": AZUL, "raio": 45, "vida": 50,
        "pontos": 350, "mov": "gira", "ataque": "8dir",
        "alvo_y": 150, "efeito": "espiral", "part_qtd": 20, "nivel": 10},
    3: {"nome": "ESTRELA", "cor": DOURADO, "raio": 50, "vida": 70,
        "pontos": 500, "mov": "infinito", "ataque": "teleguiado",
        "alvo_y": 180, "efeito": "estrela", "part_qtd": 30, "nivel": 15},
    4: {"nome": "PENTAGONO", "cor": ROXO, "raio": 55, "vida": 100,
        "pontos": 750, "mov": "teletransporte", "ataque": "tudo",
        "alvo_y": 150, "efeito": "pulsacao", "part_qtd": 40, "nivel": 20},
    5: {"nome": "ANEIS", "cor": BRANCO, "raio": 75, "vida": 150,
        "pontos": 1000, "mov": "centro", "ataque": "combinado",
        "alvo_y": ALTURA // 2, "efeito": "mega", "part_qtd": 100,
        "nivel": 25},
    6: {"nome": "ANEIS DOURADO", "cor": DOURADO, "raio": 85, "vida": 220,
        "pontos": 1500, "mov": "centro", "ataque": "combinado",
        "alvo_y": ALTURA // 2, "efeito": "mega", "part_qtd": 140,
        "nivel": 30},
}