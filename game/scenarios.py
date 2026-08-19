"""Cenarios dinamicos: fundo, estrelas, nebulosas e efeitos especiais."""

import math
import random

import pygame

from .config import ALTURA, LARGURA
from .geometry import cruz, losango
from .smooth import desenhar_circulo, desenhar_glow


def _superficie_alpha(raio, cor):
    """Superficie com brilho radial suave (cacheada).

    Retorna a superficie compartilhada do cache; quem precisar alterar o
    alpha individualmente deve chamar ``.copy()`` antes de ``set_alpha``.
    """
    from .smooth import luz_radial
    return luz_radial(cor, raio, 1.0)


# Raios de luz do Plano Divino, cacheados por largura (evita alocar
# superficies e smoothscale a cada frame).
_CACHE_RAIOS = {}


class Estrela:
    """Estrela de fundo com forma especifica do cenario."""

    def __init__(self, x, y, tamanho, velocidade, cor, forma):
        self.x, self.y = x, y
        self.tamanho = tamanho
        self.velocidade = velocidade
        self.cor = cor
        self.forma = forma
        self.fase = random.uniform(0, math.tau)

    def atualizar(self):
        self.y += self.velocidade
        self.fase += 0.02
        if self.y > ALTURA + 10:
            self.y = -10
            self.x = random.randint(0, LARGURA)

    def desenhar(self, tela):
        x, y = int(self.x), int(self.y)
        t = self.tamanho
        if self.forma == "circulo":
            if t <= 1:
                pygame.draw.circle(tela, self.cor, (x, y), t)
            else:
                desenhar_glow(tela, self.cor, (x, y), t * 2, 0.5)
                desenhar_circulo(tela, self.cor, (x, y), t)
        elif self.forma == "chama":
            # formato de chama: triangulo fino apontando para baixo
            desenhar_glow(tela, self.cor, (x, y), t * 2.5, 0.4)
            pygame.draw.polygon(tela, self.cor, [(x, y - t), (x + t, y + t),
                                                 (x - t, y + t)])
        elif self.forma == "bolha":
            desenhar_glow(tela, self.cor, (x, y), t * 2.5, 0.5)
            desenhar_circulo(tela, self.cor, (x, y), t)
            desenhar_circulo(tela, (255, 255, 255),
                             (x - t // 2, y - t // 2), max(1, t // 3),
                             brilho=1.4)
        elif self.forma == "diamante":
            desenhar_glow(tela, self.cor, (x, y), t * 2.5, 0.4)
            pygame.draw.polygon(tela, self.cor,
                                losango((x, y), t, t, 0.0))
        elif self.forma == "espiral":
            desenhar_glow(tela, self.cor, (x, y), t * 2.5, 0.5)
            desenhar_circulo(tela, self.cor, (x, y), t)
            desenhar_circulo(tela, (10, 0, 30), (x, y), t // 2)
        elif self.forma == "cruz":
            desenhar_glow(tela, self.cor, (x, y), t * 2, 0.4)
            pygame.draw.polygon(tela, self.cor, cruz((x, y), t))


class Cenario:
    """Um dos seis cenarios do jogo, com visual e efeitos proprios."""

    def __init__(self, cenario_id):
        cfg = CENARIOS[cenario_id - 1]
        self.id = cfg["id"]
        self.nome = cfg["nome"]
        self.cor_estrela = cfg["cor_estrela"]
        self.forma_estrela = cfg["forma_estrela"]
        self.efeito = cfg["efeito"]
        self.cor_transicao = cfg["cor_transicao"]
        self.cores_principais = cfg["cores_principais"]
        self.inimigos = cfg["inimigos"]
        self.especiais = cfg["especiais"]
        self.tempo = 0
        self.gradiente = self._criar_gradiente(cfg["topo"], cfg["base"])
        self.nebulosas = self._criar_nebulosas(cfg["cores_nebulosa"])
        self.estrelas = self._criar_estrelas(cfg["camadas_estrelas"])
        self.efeitos = []

    # ----- construcao -----

    def _criar_gradiente(self, topo, base):
        from .smooth import gradiente_vertical
        return gradiente_vertical(topo, base)

    def _criar_nebulosas(self, cores):
        nebulosas = []
        for _ in range(6):
            surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            x = random.randint(0, LARGURA)
            y = random.randint(0, ALTURA)
            raio = random.randint(80, 180)
            cor = random.choice(cores)
            pygame.draw.circle(surf, cor + (random.randint(14, 22),),
                               (x, y), raio)
            nebulosas.append(surf)
        return nebulosas

    def _criar_estrelas(self, camadas):
        estrelas = []
        for (qtd, velocidade, tamanho) in camadas:
            for _ in range(qtd):
                estrelas.append(Estrela(
                    random.randint(0, LARGURA), random.randint(0, ALTURA),
                    tamanho, velocidade, self.cor_estrela, self.forma_estrela))
        return estrelas

    # ----- atualizacao -----

    def atualizar(self):
        self.tempo += 1
        for estrela in self.estrelas:
            estrela.atualizar()
        self._atualizar_efeito()

    def _atualizar_efeito(self):
        if self.efeito == "fogo":
            # particulas de fogo subindo pelo fundo
            if random.random() < 0.3:
                self.efeitos.append({
                    "x": random.uniform(0, LARGURA), "y": ALTURA + 10,
                    "vy": random.uniform(-2.5, -1.5),
                    "t": 0, "max": random.randint(80, 140),
                    "cor": random.choice([(255, 120, 40), (255, 80, 30),
                                          (200, 60, 10)]), "r": random.randint(2, 5)})
        elif self.efeito == "bolhas":
            if random.random() < 0.15:
                self.efeitos.append({
                    "x": random.uniform(0, LARGURA), "y": ALTURA + 10,
                    "vy": random.uniform(-1.6, -0.9),
                    "t": 0, "max": random.randint(90, 150),
                    "cor": (170, 230, 255), "r": random.randint(2, 5)})
        elif self.efeito == "cristais":
            if random.random() < 0.15:
                self.efeitos.append({
                    "x": random.uniform(0, LARGURA), "y": -10,
                    "vy": random.uniform(1.0, 1.8),
                    "t": 0, "max": random.randint(90, 160),
                    "cor": random.choice([(120, 255, 160), (150, 255, 200),
                                          (200, 160, 255)]), "r": random.randint(2, 4)})
        for ef in self.efeitos[:]:
            ef["y"] += ef["vy"]
            ef["x"] += math.sin((ef["t"] + 1) * 0.08) * 0.3
            ef["t"] += 1
            if ef["t"] >= ef["max"]:
                self.efeitos.remove(ef)

    # ----- desenho -----

    def desenhar(self, tela):
        tela.blit(self.gradiente, (0, 0))
        for nebulosa in self.nebulosas:
            tela.blit(nebulosa, (0, 0))
        for estrela in self.estrelas:
            estrela.desenhar(tela)
        self._desenhar_efeito(tela)

    def _desenhar_efeito(self, tela):
        for ef in self.efeitos:
            alfa = min(1.0, 1 - ef["t"] / ef["max"]) * 0.8
            x, y, r = int(ef["x"]), int(ef["y"]), ef["r"]
            if self.efeito == "cristais":
                pygame.draw.polygon(tela, ef["cor"],
                                    losango((x, y), r * 2, r, 0.0))
            elif self.efeito == "fogo":
                # copia para nao mutar a superficie cacheada do glow
                surf = _superficie_alpha(r * 4, ef["cor"]).copy()
                surf.set_alpha(int(255 * alfa))
                tela.blit(surf, (x - r * 2, y - r * 2))
            else:
                surf = _superficie_alpha(r * 4, ef["cor"]).copy()
                surf.set_alpha(int(255 * alfa))
                tela.blit(surf, (x - r * 2, y - r * 2))
        if self.efeito == "distorcao":
            self._desenhar_distorcao(tela)
        elif self.efeito == "raios":
            self._desenhar_raios(tela)

    def _desenhar_distorcao(self, tela):
        """Ondas de distorcao atravessando a tela (Vazio Dimensional)."""
        t = self.tempo
        for k in range(3):
            y_base = (t * 1.5 + k * 240) % (ALTURA + 200) - 100
            for i in range(0, LARGURA, 8):
                desloc = math.sin(i * 0.02 + t * 0.05) * 18
                y = y_base + desloc
                alfa = max(0, 140 - int(abs(y_base - ALTURA // 2) * 0.3))
                cor = (160, 100, 255, min(140, alfa))
                pygame.draw.aaline(tela, cor, (i, y), (i + 8, y), 2)

    def _desenhar_raios(self, tela):
        """Raios de luz descendo (Plano Divino)."""
        t = self.tempo
        for k in range(4):
            x_base = (t * 2 + k * 260) % (LARGURA + 300) - 150
            largura = 60 + 30 * math.sin(t * 0.02 + k)
            larg = int(largura)
            if larg not in _CACHE_RAIOS:
                surf = pygame.Surface((larg, ALTURA), pygame.SRCALPHA)
                meio = larg / 2
                for i in range(larg):
                    alfa = int(90 * (1 - abs(i - meio) / meio))
                    pygame.draw.line(surf, (255, 240, 180, alfa), (i, 0),
                                     (i, ALTURA))
                surf = pygame.transform.smoothscale(
                    surf, (max(1, int(larg * 0.7)), ALTURA))
                _CACHE_RAIOS[larg] = (surf, int(larg * 0.15))
            surf, offset = _CACHE_RAIOS[larg]
            tela.blit(surf, (int(x_base) + offset, 0))


# ----- definicao dos cenarios -----

CENARIOS = [
    {
        "id": 1, "nome": "ESPACO PROFUNDO",
        "topo": (10, 16, 60), "base": (4, 4, 26),
        "cor_estrela": (120, 160, 255), "forma_estrela": "circulo",
        "cores_nebulosa": [(60, 40, 130), (20, 80, 150), (90, 30, 110)],
        "camadas_estrelas": [(50, 0.4, 1), (35, 1.0, 2), (20, 2.0, 3)],
        "efeito": "nenhum", "cor_transicao": (120, 160, 255),
        "cores_principais": [(120, 160, 255), (90, 120, 255), (255, 255, 255)],
        "inimigos": ["scout", "soldado"],
        "especiais": ["acumulador", "esponja", "condutor"],
    },
    {
        "id": 2, "nome": "NEBULOSA FLAMEJANTE",
        "topo": (70, 20, 16), "base": (30, 6, 8),
        "cor_estrela": (255, 210, 120), "forma_estrela": "chama",
        "cores_nebulosa": [(200, 70, 20), (140, 40, 20), (220, 120, 30)],
        "camadas_estrelas": [(50, 0.5, 2), (30, 1.1, 3), (15, 2.2, 4)],
        "efeito": "fogo", "cor_transicao": (255, 140, 50),
        "cores_principais": [(255, 150, 50), (255, 90, 30), (255, 220, 90)],
        "inimigos": ["flamifero", "forja"],
        "especiais": ["acumulador", "esponja", "condutor", "mutante"],
    },
    {
        "id": 3, "nome": "OCEANO COSMICO",
        "topo": (8, 50, 90), "base": (4, 16, 50),
        "cor_estrela": (200, 220, 235), "forma_estrela": "bolha",
        "cores_nebulosa": [(20, 90, 120), (10, 120, 110), (50, 70, 130)],
        "camadas_estrelas": [(50, 0.5, 2), (30, 1.2, 3), (15, 2.4, 4)],
        "efeito": "bolhas", "cor_transicao": (100, 200, 220),
        "cores_principais": [(100, 200, 220), (80, 160, 255), (160, 220, 235)],
        "inimigos": ["abissal", "estelar"],
        "especiais": ["acumulador", "condutor", "mutante"],
    },
    {
        "id": 4, "nome": "FLORESTA DE CRISTAIS",
        "topo": (12, 60, 30), "base": (8, 22, 12),
        "cor_estrela": (150, 255, 180), "forma_estrela": "diamante",
        "cores_nebulosa": [(30, 110, 60), (80, 40, 130), (40, 90, 70)],
        "camadas_estrelas": [(50, 0.5, 2), (30, 1.2, 3), (15, 2.4, 4)],
        "efeito": "cristais", "cor_transicao": (150, 255, 180),
        "cores_principais": [(120, 255, 160), (200, 160, 255), (150, 255, 180)],
        "inimigos": ["cristalino", "guardiao"],
        "especiais": ["cristalino", "acumulador", "esponja"],
    },
    {
        "id": 5, "nome": "VAZIO DIMENSIONAL",
        "topo": (16, 8, 30), "base": (4, 2, 12),
        "cor_estrela": (200, 190, 255), "forma_estrela": "espiral",
        "cores_nebulosa": [(90, 40, 130), (120, 30, 110), (60, 20, 90)],
        "camadas_estrelas": [(50, 0.6, 2), (30, 1.4, 3), (15, 2.6, 4)],
        "efeito": "distorcao", "cor_transicao": (170, 90, 255),
        "cores_principais": [(170, 90, 255), (120, 40, 200), (220, 160, 255)],
        "inimigos": ["espectro", "distorcao"],
        "especiais": ["mutante", "condutor", "esponja"],
    },
    {
        "id": 6, "nome": "PLANO DIVINO",
        "topo": (120, 90, 40), "base": (40, 30, 12),
        "cor_estrela": (255, 235, 160), "forma_estrela": "cruz",
        "cores_nebulosa": [(180, 140, 60), (160, 160, 200), (200, 170, 90)],
        "camadas_estrelas": [(50, 0.5, 2), (30, 1.2, 3), (15, 2.4, 4)],
        "efeito": "raios", "cor_transicao": (255, 235, 160),
        "cores_principais": [(255, 235, 160), (240, 220, 190), (255, 255, 255)],
        "inimigos": ["celestial", "sentinela"],
        "especiais": ["cristalino", "mutante", "acumulador", "condutor"],
    },
]


def cenario_do_nivel(nivel):
    """Retorna o id do cenario correspondente ao nivel."""
    return min((nivel - 1) // 5 + 1, 6)