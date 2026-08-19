"""Jogador, sistema de combos e catalogo de skins."""

import math
import random

import pygame

from .config import ALTURA, AZUL, AZUL_CLARO, BRANCO, CIANO, DOURADO, INDIGO, \
    LARGURA, LARANJA, ROXO, VERDE, VERMELHO
from .geometry import losango
from .smooth import desenhar_circulo, desenhar_glow, desenhar_poligono
from .weapons import ARMARIA, Projetil


# ---------------------------------------------------------------------------
# Catalogo de skins
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
    """Representa uma skin de nave com efeito visual proprio."""

    def __init__(self, config):
        self.id = config["id"]
        self.nome = config["nome"]
        self.preco = config["preco"]
        self.cor = tuple(config["cor"])
        self.cor2 = tuple(config["cor2"])
        self.efeito = config["efeito"]
        self.descricao = config["descricao"]
        self.desbloqueada = config["preco"] == 0

    def desenhar(self, tela, jogador, particulas=None):
        """Desenha a nave do jogador com a skin aplicada."""
        x, y = int(jogador.x), int(jogador.y)
        t = pygame.time.get_ticks() * 0.001
        if self.efeito == "transparencia":
            self._desenhar_transparente(tela, x, y, jogador.tilt, t)
        elif self.efeito == "diamante":
            self._desenhar_diamante(tela, x, y, jogador.tilt, t)
        elif self.efeito == "asas":
            self._desenhar_asas(tela, x, y, jogador.tilt, t)
        else:
            self._desenhar_nave_base(tela, x, y, jogador.tilt)

        if self.efeito == "chamas" and particulas:
            particulas.chamas(x, y + 14, LARANJA, 2)
        elif self.efeito == "chamas_escuras" and particulas:
            particulas.chamas(x, y + 14, VERMELHO, 2)
        elif self.efeito == "relampago":
            self._desenhar_relampago(tela, x, y, t)
        elif self.efeito == "brilho":
            self._desenhar_brilho(tela, x, y, t)
        elif self.efeito == "estrelas" and particulas:
            if t % 0.15 < 0.02:
                particulas.rastro(x + random.uniform(-4, 4), y,
                                  (200, 220, 255), 1.0)
        elif self.efeito == "buraco_negro" and particulas:
            particulas.buraco_negro(x, y)

    def _pontos_nave(self, x, y, tilt):
        return [(x, y - 20), (x - 15, y + 16), (x, y + 7), (x + 15, y + 16)]

    def _desenhar_nave_base(self, tela, x, y, tilt):
        pts = self._pontos_nave(x, y, tilt)
        desenhar_glow(tela, self.cor, (x, y), 22, 0.5)
        desenhar_poligono(tela, self.cor, pts, glow_cor=self.cor2, glow_raio=14)
        desenhar_poligono(tela, self.cor2, pts, 2)
        desenhar_circulo(tela, AZUL_CLARO, (x, y - 2), 6, brilho=1.0)
        desenhar_circulo(tela, BRANCO, (x, y - 2), 3, brilho=1.2)

    def _desenhar_transparente(self, tela, x, y, tilt, t):
        alfa = int(120 + 60 * math.sin(t * 3))
        surf = pygame.Surface((44, 44), pygame.SRCALPHA)
        pts = [(22, 2), (7, 38), (22, 29), (37, 38)]
        pygame.draw.polygon(surf, self.cor + (alfa,), pts)
        pygame.draw.polygon(surf, (150, 60, 200, alfa), pts, 2)
        tela.blit(surf, (x - 22, y - 22))

    def _desenhar_diamante(self, tela, x, y, tilt, t):
        pts = losango((x, y), 14, 22, tilt + math.sin(t * 2) * 0.1)
        desenhar_glow(tela, self.cor, (x, y), 20, 0.5)
        desenhar_poligono(tela, self.cor, pts, glow_cor=(220, 255, 230),
                          glow_raio=12)
        desenhar_poligono(tela, self.cor2, pts, 2)
        desenhar_circulo(tela, (220, 255, 230), (x, y - 2), 5, brilho=1.2)

    def _desenhar_asas(self, tela, x, y, tilt, t):
        self._desenhar_nave_base(tela, x, y, tilt)
        for sinal in (-1, 1):
            base_y = y + 8
            ponta_y = y + 24
            pts = [(x + sinal * 10, base_y),
                   (x + sinal * 34, ponta_y + math.sin(t * 5) * 6),
                   (x + sinal * 26, ponta_y),
                   (x + sinal * 8, base_y + 6)]
            desenhar_poligono(tela, (255, 250, 220), pts,
                              glow_cor=(255, 250, 220), glow_raio=8)

    def _desenhar_relampago(self, tela, x, y, t):
        if int(t * 4) % 2 == 0:
            for sinal in (-1, 1):
                desenhar_poligono(tela, (255, 240, 60),
                                  [(x + sinal * 18, y - 8), (x + sinal * 8, y),
                                   (x + sinal * 20, y + 12),
                                   (x + sinal * 6, y + 22)],
                                  glow_cor=(255, 240, 60), glow_raio=10)

    def _desenhar_brilho(self, tela, x, y, t):
        pulso = 14 + 5 * math.sin(t * 4)
        desenhar_glow(tela, (255, 215, 0), (x, y), pulso, 0.9)


# ---------------------------------------------------------------------------
# Sistema de combos
# ---------------------------------------------------------------------------

class SistemaCombo:
    """Controla o multiplicador de pontos baseado em tiros consecutivos."""

    def __init__(self):
        self.combo_atual = 0
        self.combo_maximo = 0
        self.ultimo_tiro = -99999
        self.tempo_maximo_entre_tiros = 500

    def adicionar_tiro(self):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro < self.tempo_maximo_entre_tiros:
            self.combo_atual += 1
        else:
            self.combo_atual = 1
        self.ultimo_tiro = agora
        if self.combo_atual > self.combo_maximo:
            self.combo_maximo = self.combo_atual

    def get_bonus(self):
        if self.combo_atual > 20:
            return 2.0
        if self.combo_atual > 10:
            return 1.5
        return 1.0

    def zerar(self):
        self.combo_atual = 0


# ---------------------------------------------------------------------------
# Jogador
# ---------------------------------------------------------------------------

class Jogador:
    def __init__(self, nome="Jogador", skin=None):
        self.nome = nome
        self.x = LARGURA // 2
        self.y = ALTURA - 100
        self.raio = 16
        self.velocidade = 5
        self.vida = 5
        self.max_vida = 8
        self.pontuacao = 0
        self.moedas_jogo = 0
        self.nivel = 1
        self.arma_atual = 0
        self.armas_desbloqueadas = [0]
        self.escudo = False
        self.cooldown_tiro = 0
        self.burst_left = 0
        self.angulo_arma = 0.0
        self.invencivel = 0
        self.tilt = 0.0
        self.vivo = True
        self.skin = skin or Skin(SKINS[0])
        self.combo = SistemaCombo()

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.raio), int(self.y - self.raio),
                           self.raio * 2, self.raio * 2)

    def equipar_skin(self, skin):
        self.skin = skin

    def atualizar(self, teclas, controles=None):
        controles = controles or {}
        dx = dy = 0
        esquerda = controles.get("esquerda")
        direita = controles.get("direita")
        cima = controles.get("cima")
        baixo = controles.get("baixo")
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a] or \
                (esquerda and teclas[esquerda]):
            dx -= 1
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d] or \
                (direita and teclas[direita]):
            dx += 1
        if teclas[pygame.K_UP] or teclas[pygame.K_w] or \
                (cima and teclas[cima]):
            dy -= 1
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s] or \
                (baixo and teclas[baixo]):
            dy += 1
        if dx and dy:
            dx *= 0.7071
            dy *= 0.7071
        self.x += dx * self.velocidade
        self.y += dy * self.velocidade
        self.x = max(20, min(LARGURA - 20, self.x))
        self.y = max(40, min(ALTURA - 30, self.y))
        self.tilt += (dx * 5 - self.tilt) * 0.15
        if self.cooldown_tiro > 0:
            self.cooldown_tiro -= 1
        if self.invencivel > 0:
            self.invencivel -= 1

    def atirar(self):
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
            return [Projetil(x, y, 0, -arma["vel"], arma["dano"], arma["cor"],
                             arma["raio"], tipo=tipo)]

        self.cooldown_tiro = arma["cooldown"]

        if tipo == "duplo":
            return [
                Projetil(x - 9, y, 0, -arma["vel"], arma["dano"], arma["cor"],
                         arma["raio"], tipo=tipo),
                Projetil(x + 9, y, 0, -arma["vel"], arma["dano"], arma["cor"],
                         arma["raio"], tipo=tipo),
            ]
        if tipo == "espiral":
            self.angulo_arma += 0.45
            projs = []
            for i in range(arma["qtd"]):
                a = self.angulo_arma + (i - 1) * 0.7
                projs.append(Projetil(x, y, math.sin(a) * 2.2, -arma["vel"],
                                      arma["dano"], arma["cor"], arma["raio"],
                                      tipo=tipo))
            return projs
        if tipo == "ion":
            return [Projetil(x, y, 0, 0, arma["dano"], arma["cor"],
                             arma["raio"], tipo=tipo)]

        return [Projetil(x, y, 0, -arma["vel"], arma["dano"], arma["cor"],
                         arma["raio"], tipo=tipo)]

    def selecionar_arma(self, indice):
        if indice in self.armas_desbloqueadas:
            self.arma_atual = indice

    def sofrer_dano(self):
        if self.invencivel > 0 or not self.vivo:
            return False
        self.combo.zerar()
        if self.escudo:
            self.escudo = False
            self.invencivel = 90
            return True
        self.vida -= 1
        self.invencivel = 120
        if self.vida <= 0:
            self.vida = 0
            self.vivo = False
        return True

    def desenhar(self, tela, particulas=None):
        if self.invencivel > 0 and (self.invencivel // 4) % 2 == 0:
            return
        self.skin.desenhar(tela, self, particulas)
        if self.escudo:
            pulso = 1 + 0.15 * math.sin(pygame.time.get_ticks() * 0.008)
            desenhar_glow(tela, (50, 150, 255), (self.x, self.y),
                          (self.raio + 8) * pulso, 0.5)
            desenhar_circulo(tela, (50, 150, 255), (self.x, self.y),
                             (self.raio + 8) * pulso, 2, brilho=1.0)