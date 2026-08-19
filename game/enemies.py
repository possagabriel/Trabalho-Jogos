"""Inimigos normais (por cenario) e inimigos especiais com sistema de carga."""

import math
import random

import pygame

from .config import AMARELO, AZUL, BRANCO, DOURADO, LARGURA, \
    LARANJA, ROXO, VERDE, VERMELHO
from .geometry import estrela, losango, pentagono, poligono, quadrado, triangulo
from .smooth import desenhar_circulo, desenhar_glow, desenhar_poligono
from .weapons import Projetil

# ---------------------------------------------------------------------------
# Inimigos normais
# ---------------------------------------------------------------------------

TIPOS = {
    # Dimensao 1 - Deep Space
    "scout": {"cor": VERDE, "raio": 12, "vida": 1, "pontos": 10,
              "vel": 2.5, "mov": "reta", "ataque": "nenhum"},
    "soldado": {"cor": AMARELO, "raio": 12, "vida": 2, "pontos": 20,
                "vel": 2.2, "mov": "zigzag", "ataque": "nenhum"},
    # Dimensao 2 - Flame Nebula
    "flamifero": {"cor": VERMELHO, "raio": 12, "vida": 3, "pontos": 30,
                  "vel": 2.0, "mov": "espiral", "ataque": "baixo"},
    "forja": {"cor": LARANJA, "raio": 20, "vida": 5, "pontos": 50,
              "vel": 1.4, "mov": "zigzag_lento", "ataque": "leque"},
    # Dimensao 3 - Cosmic Ocean
    "abissal": {"cor": AZUL, "raio": 16, "vida": 4, "pontos": 45,
                "vel": 1.8, "mov": "gira", "ataque": "4dir"},
    "estelar": {"cor": ROXO, "raio": 12, "vida": 3, "pontos": 40,
                "vel": 3.0, "mov": "persegue", "ataque": "nenhum"},
    # Dimensao 4 - Crystal Forest
    "cristalino": {"cor": VERDE, "raio": 16, "vida": 5, "pontos": 50,
                   "vel": 1.7, "mov": "ondulacao", "ataque": "baixo"},
    "guardiao": {"cor": BRANCO, "raio": 15, "vida": 4, "pontos": 55,
                 "vel": 1.5, "mov": "reta", "ataque": "tudo"},
    # Dimensao 5 - Null Space
    "espectro": {"cor": (120, 60, 180), "raio": 12, "vida": 4, "pontos": 60,
                 "vel": 2.4, "mov": "erratico", "ataque": "nenhum"},
    "distorcao": {"cor": ROXO, "raio": 18, "vida": 6, "pontos": 70,
                  "vel": 1.1, "mov": "flutua", "ataque": "baixo"},
    # Dimensao 6 - Divine Plane
    "celestial": {"cor": DOURADO, "raio": 16, "vida": 6, "pontos": 80,
                  "vel": 2.0, "mov": "zigzag", "ataque": "leque"},
    "sentinela": {"cor": (240, 235, 200), "raio": 15, "vida": 8, "pontos": 100,
                  "vel": 1.3, "mov": "reta", "ataque": "feixe"},
}

# Forma de desenho de cada tipo de inimigo
FORMAS = {
    "scout": "triangulo", "soldado": "quadrado", "flamifero": "circulo",
    "forja": "hexagono", "abissal": "losango", "estelar": "estrela",
    "cristalino": "hexagono", "guardiao": "pentagono", "espectro": "aleatoria",
    "distorcao": "circulo_pulsante", "celestial": "estrela",
    "sentinela": "olho",
}


class Inimigo:
    """Inimigo normal com movimento e ataque proprios."""

    def __init__(self, tipo, nivel, x=None, y=-40, escala=1.0):
        cfg = TIPOS[tipo]
        self.tipo = tipo
        self.cor = cfg["cor"]
        self.raio = cfg["raio"] * escala
        self.vida = cfg["vida"]
        self.vida_max = self.vida
        self.pontos = cfg["pontos"]
        self.vel = cfg["vel"] * (1 + 0.04 * (nivel - 1)) * escala
        self.mov = cfg["mov"]
        self.ataque = cfg["ataque"]
        self.x = x if x is not None else random.randint(40, LARGURA - 40)
        self.y = y
        self.base_x = self.x
        self.fase = random.uniform(0, math.tau)
        self.angulo = random.uniform(0, math.tau)
        self.timer_ataque = random.randint(90, 140)
        self.flash = 0
        self.vel_x = random.uniform(-1, 1)
        self.vel_y = 0
        self.timer_feixe = 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.raio), int(self.y - self.raio),
                           self.raio * 2, self.raio * 2)

    def atualizar(self, jogador):
        novos = []
        if self.flash > 0:
            self.flash -= 1
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

        self.timer_ataque -= 1
        if self.timer_ataque <= 0:
            self.timer_ataque = random.randint(110, 170)
            novos = self._atacar(jogador)
        return novos

    def _atacar(self, jogador):
        if self.ataque == "nenhum":
            return []
        x, y = self.x, self.y
        if self.ataque == "baixo":
            return [Projetil(x, y, 0, 4, 1, VERMELHO, 4, origem="inimigo")]
        if self.ataque == "leque":
            return [Projetil(x, y, dx, 4, 1, LARANJA, 4, origem="inimigo")
                    for dx in (-1.5, 0, 1.5)]
        if self.ataque == "4dir":
            return [Projetil(x, y, math.cos(a) * 3.5, math.sin(a) * 3.5, 1,
                             AZUL, 4, origem="inimigo")
                    for a in (0, math.pi / 2, math.pi, -math.pi / 2)]
        if self.ataque == "tudo":
            return [Projetil(x, y, math.cos(a) * 3, math.sin(a) * 3, 1,
                             BRANCO, 4, origem="inimigo")
                    for a in [i * math.tau / 8 for i in range(8)]]
        if self.ataque == "feixe":
            # mira um laser na direcao do jogador
            dx, dy = jogador.x - x, jogador.y - y
            norma = math.hypot(dx, dy) or 1
            return [Projetil(x, y, dx / norma * 6, dy / norma * 6, 1,
                             (240, 235, 200), 3, tipo="feixe",
                             origem="inimigo")]
        return []

    def sofrer_dano(self, dano):
        self.vida -= dano
        self.flash = 6
        return self.vida <= 0

    def _pontos_forma(self, centro, forma):
        x, y = centro
        raio = self.raio
        if forma == "triangulo":
            return triangulo(centro, raio, self.angulo)
        if forma == "quadrado":
            return quadrado(centro, raio, self.angulo)
        if forma == "estrela":
            return estrela(centro, raio, angulo=self.angulo)
        if forma == "hexagono":
            return poligono(centro, raio, 6, self.angulo)
        if forma == "losango":
            return losango(centro, raio * 0.7, raio, self.angulo)
        if forma == "pentagono":
            return pentagono(centro, raio, self.angulo)
        if forma == "olho":
            return losango(centro, raio * 0.9, raio * 0.6, self.angulo)
        if forma == "cruz":
            from .geometry import cruz as _cruz
            return _cruz(centro, raio)
        return poligono(centro, raio, 3, self.angulo)

    def desenhar(self, tela):
        x, y = int(self.x), int(self.y)
        cor = BRANCO if self.flash > 0 else self.cor
        centro = (x, y)
        if self.tipo == "espectro":
            # forma aleatoria (versao escura de todas as formas)
            formas = ["triangulo", "quadrado", "circulo", "estrela",
                      "hexagono", "losango", "pentagono"]
            forma = formas[int(self.fase) % len(formas)]
            self._desenhar_forma(tela, centro, cor, forma)
            return
        if self.tipo == "distorcao":
            # circulo pulsante com aneis
            pulso = 1 + 0.15 * math.sin(self.tempo_global())
            raio = self.raio * pulso
            desenhar_glow(tela, cor, centro, raio * 1.4, 0.6)
            desenhar_circulo(tela, cor, centro, raio)
            desenhar_circulo(tela, BRANCO, centro, raio, 2, brilho=1.2)
            desenhar_circulo(tela, (40, 10, 60), centro, raio / 2)
            desenhar_circulo(tela, (180, 100, 255), centro, raio * 1.35, 1,
                             brilho=0.9)
            return
        if self.tipo == "sentinela":
            desenhar_poligono(tela, cor, self._pontos_forma(centro, "olho"),
                              glow_cor=cor, glow_raio=self.raio)
            desenhar_circulo(tela, DOURADO, centro, self.raio // 3, brilho=1.2)
            desenhar_circulo(tela, BRANCO, centro, self.raio // 6, brilho=1.5)
            return
        forma = FORMAS[self.tipo]
        self._desenhar_forma(tela, centro, cor, forma)

    def _desenhar_forma(self, tela, centro, cor, forma):
        x, y = centro
        if forma == "circulo":
            desenhar_glow(tela, cor, (x, y), self.raio * 1.5, 0.5)
            desenhar_circulo(tela, cor, (x, y), self.raio)
            desenhar_circulo(tela, (90, 0, 0), (x, y), self.raio - 4, 2)
            desenhar_circulo(tela, BRANCO, (x, y), 3, brilho=1.5)
        elif forma == "circulo_pulsante":
            desenhar_glow(tela, cor, (x, y), self.raio * 1.5, 0.5)
            desenhar_circulo(tela, cor, (x, y), self.raio)
            desenhar_circulo(tela, BRANCO, (x, y), self.raio, 2, brilho=1.2)
        else:
            desenhar_glow(tela, cor, centro, self.raio * 1.4, 0.4)
            desenhar_poligono(tela, cor, self._pontos_forma(centro, forma),
                              glow_cor=cor, glow_raio=self.raio)
            if forma == "quadrado":
                desenhar_poligono(tela, (90, 80, 0),
                                  quadrado(centro, self.raio, self.angulo), 2)
            elif forma == "hexagono":
                desenhar_poligono(tela, (120, 70, 0),
                                  poligono(centro, self.raio, 6,
                                           self.angulo), 2)
            elif forma == "pentagono":
                desenhar_poligono(tela, (150, 150, 160),
                                  pentagono(centro, self.raio, self.angulo), 2)

    def tempo_global(self):
        return pygame.time.get_ticks() * 0.001


# ---------------------------------------------------------------------------
# Inimigos especiais (sistema de carga)
# ---------------------------------------------------------------------------

class InimigoEspecial(Inimigo):
    """Inimigo especial que carrega energia a cada tiro recebido.

    Ao atingir 100% de carga, ativa um efeito unico dependendo do tipo:
      - acumulador: explode em 8 direcoes (dano em area)
      - esponja: nao toma dano, so carrega; aos 100% se divide em 4 menores
      - condutor: libera um raio que atinge o jogador
      - mutante: se transforma em um mini-boss
      - cristalino: cria um campo de forca que reflete tiros
    """

    CARGA_POR_TIRO = {
        "acumulador": 5, "esponja": 3, "condutor": 8, "mutante": 10,
        "cristalino": 15,
    }
    CORES = {
        "acumulador": (255, 200, 40), "esponja": (150, 60, 200),
        "condutor": (80, 160, 255), "mutante": (200, 40, 255),
        "cristalino": (210, 235, 245),
    }

    def __init__(self, tipo_especial, nivel, cenario_id=1):
        # tipo base (forma) com base nos TIPOS atuais
        base = {"acumulador": "flamifero", "esponja": "soldado",
                "condutor": "estelar", "mutante": "forja",
                "cristalino": "guardiao"}[tipo_especial]
        super().__init__(base, nivel)
        self.tipo = base
        self.tipo_especial = tipo_especial
        self.cor = self.CORES[tipo_especial]
        self.carga = 0
        self.carga_maxima = 100
        self.carga_por_tiro = self.CARGA_POR_TIRO[tipo_especial]
        self.carregado = False
        self.efeito_ja_atirado = False
        self.vida = max(10, 6 + nivel)
        self.vida_max = self.vida
        self.pontos = 50 + nivel * 5
        self.raio = 22
        self.mini_boss = False
        self.campo_forca = False
        self.invisivel = 0
        # comportamento proprio de cada tipo
        self.mov = {"acumulador": "flutua", "esponja": "zigzag",
                    "condutor": "gira", "mutante": "reta",
                    "cristalino": "flutua"}[tipo_especial]
        self.ataque = "nenhum"
        self.vel = 1.2

    def receber_tiro(self, dano):
        """Processa o tiro: acumula carga. Retorna True se deve ser removido."""
        self.flash = 6
        if self.tipo_especial == "esponja":
            # esponja absorve tiros: nao toma dano, so carrega
            self.carga += self.carga_por_tiro * dano
            if self.carga >= self.carga_maxima:
                self.carregado = True
            return False
        if self.tipo_especial == "mutante" and not self.carregado:
            self._teleportar()
        self.carga += self.carga_por_tiro * dano
        if self.carga >= self.carga_maxima and not self.carregado:
            self.carregado = True
        self.vida -= dano
        return self.vida <= 0

    def _teleportar(self):
        self.x = random.randint(60, LARGURA - 60)
        self.y = random.randint(30, 400)
        self.base_x = self.x
        self.invisivel = 40

    def acoes_carregado(self):
        """Retorna acoes geradas quando a carga chega a 100%.

        Retorna um dict com listas de projeteis/inimigos a adicionar,
        poder de queda e se o proprio inimigo morre.
        """
        if self.e_feito_ja_atirado():
            return {}
        self.efeito_ja_atirado = True
        x, y = int(self.x), int(self.y)
        acoes = {"projeteis": [], "inimigos": [], "morrer": False,
                 "mensagem": ""}
        if self.tipo_especial == "acumulador":
            acoes["projeteis"] = [
                Projetil(x, y, math.cos(a) * 4, math.sin(a) * 4, 1,
                         (255, 200, 40), 4, origem="inimigo")
                for a in [i * math.tau / 8 for i in range(8)]]
            acoes["morrer"] = True
            acoes["mensagem"] = "EXPLOSAO EM AREA!"
        elif self.tipo_especial == "esponja":
            for _ in range(4):
                acoes["inimigos"].append(Inimigo("soldado", 1,
                                                 x + random.randint(-30, 30),
                                                 y, escala=0.7))
            acoes["morrer"] = True
            acoes["mensagem"] = "SE DIVIDIU!"
        elif self.tipo_especial == "condutor":
            acoes["projeteis"].append(
                Projetil(x, y, 0, 6, 2, (150, 200, 255), 5, tipo="feixe",
                         origem="inimigo", teleguiado=True))
            acoes["mensagem"] = "RAIO LIBERADO!"
            self.efeito_ja_atirado = False
            self.carga = 0
            self.carregado = False
        elif self.tipo_especial == "mutante":
            self.mini_boss = True
            self.raio = 36
            self.vida += 60
            self.vida_max = self.vida
            self.ataque = "leque"
            self.timer_ataque = 60
            acoes["mensagem"] = "MINI-BOSS!"
        elif self.tipo_especial == "cristalino":
            self.campo_forca = True
            acoes["mensagem"] = "CAMPO DE FORCA!"
        return acoes

    def e_feito_ja_atirado(self):
        return self.efeito_ja_atirado

    def _caminho_ordem(self):
        return 0

    def desenhar_barra_carga(self, tela):
        """Barra de carga acima do inimigo."""
        largura_barra = int(self.raio * 2)
        altura_barra = 5
        x = int(self.x) - largura_barra // 2
        y = int(self.y) - self.raio - 15
        progresso = self.carga / self.carga_maxima
        from .smooth import barra_suave
        barra_suave(tela, x, y, largura_barra, altura_barra, progresso,
                    (0, 255, 0), fundo=(50, 50, 50), glow=False)
        if progresso > 0.8:
            pulso = int(128 + 127 * math.sin(pygame.time.get_ticks() * 0.01))
            brilho = pygame.Surface((int(largura_barra * progresso),
                                     altura_barra))
            brilho.fill((255, 255, 255))
            brilho.set_alpha(pulso)
            tela.blit(brilho, (x, y))

    def desenhar(self, tela):
        if self.invisivel > 0:
            self.invisivel -= 1
            if (self.invisivel // 4) % 2 == 0:
                return
        x, y = int(self.x), int(self.y)
        centro = (x, y)
        cor = BRANCO if self.flash > 0 else self.cor
        t = pygame.time.get_ticks() * 0.001

        if self.mini_boss:
            # versao maior e ameacadora
            desenhar_glow(tela, (60, 0, 80), centro, self.raio + 10, 0.7)
            desenhar_circulo(tela, (60, 0, 80), centro, self.raio + 8)
            desenhar_poligono(tela, cor, poligono(centro, self.raio, 6,
                                                  t * 2),
                              glow_cor=cor, glow_raio=self.raio)
            desenhar_circulo(tela, (255, 0, 255), centro, 8, brilho=1.5)
            self.desenhar_barra_carga(tela)
            return

        if self.tipo_especial == "acumulador":
            # circulo com borda pontilhada (progresso da carga)
            desenhar_glow(tela, cor, centro, self.raio * 1.5, 0.6)
            desenhar_circulo(tela, cor, centro, self.raio)
            desenhar_circulo(tela, (120, 100, 0), centro, self.raio - 4, 2)
            progresso = self.carga / self.carga_maxima
            pontos_borda = []
            for i in range(0, 360, 20):
                if i < 360 * progresso:
                    a = math.radians(i)
                    px = self.x + (self.raio + 5) * math.cos(a)
                    py = self.y + (self.raio + 5) * math.sin(a)
                    pontos_borda.append((px, py))
            for ponto in pontos_borda:
                desenhar_circulo(tela, (255, 200, 50), ponto, 3, brilho=1.2)
        elif self.tipo_especial == "esponja":
            # quadrado com listras
            desenhar_glow(tela, cor, centro, self.raio * 1.5, 0.5)
            desenhar_poligono(tela, cor, quadrado(centro, self.raio,
                                                  self.angulo),
                              glow_cor=cor, glow_raio=self.raio)
            for i in range(3):
                a = t * 2 + i * math.tau / 3
                px = self.x + math.cos(a) * self.raio * 0.7
                py = self.y + math.sin(a) * self.raio * 0.7
                desenhar_circulo(tela, (100, 255, 120), (px, py), 3,
                                 brilho=1.3)
        elif self.tipo_especial == "condutor":
            # estrela com raios eletricos girando
            desenhar_glow(tela, cor, centro, self.raio * 1.5, 0.5)
            desenhar_poligono(tela, cor, estrela(centro, self.raio,
                                                 angulo=self.angulo),
                              glow_cor=cor, glow_raio=self.raio)
            for i in range(5):
                a = -t * 3 + i * math.tau / 5
                px = self.x + math.cos(a) * (self.raio + 7)
                py = self.y + math.sin(a) * (self.raio + 7)
                desenhar_glow(tela, (160, 200, 255), ((self.x + px) / 2,
                                                      (self.y + py) / 2), 6, 0.6)
                pygame.draw.aaline(tela, (160, 200, 255),
                                   (self.x, self.y), (px, py), 2)
        elif self.tipo_especial == "mutante":
            # hexagono neon com olhos
            desenhar_glow(tela, cor, centro, self.raio * 1.5, 0.6)
            desenhar_poligono(tela, cor, poligono(centro, self.raio, 6,
                                                  self.angulo),
                              glow_cor=cor, glow_raio=self.raio)
            desenhar_circulo(tela, (255, 0, 255), centro, 5, brilho=1.5)
            desenhar_circulo(tela, BRANCO, centro, 2, brilho=1.8)
        elif self.tipo_especial == "cristalino":
            # pentagono translucido com halo suave
            desenhar_glow(tela, self.cor, centro, self.raio * 1.6, 0.7)
            surf = pygame.Surface((self.raio * 2 + 8, self.raio * 2 + 8),
                                  pygame.SRCALPHA)
            pts = pentagono((self.raio + 4, self.raio + 4), self.raio,
                            self.angulo)
            pygame.draw.polygon(surf, self.cor + (150,), pts)
            pygame.draw.polygon(surf, (255, 255, 255, 230), pts, 2)
            tela.blit(surf, (x - self.raio - 4, y - self.raio - 4))

        # campo de forca refletor
        if self.campo_forca:
            pulso = 4 + 2 * math.sin(t * 6)
            desenhar_glow(tela, (200, 240, 255), centro, self.raio + 12, 0.5)
            desenhar_circulo(tela, (200, 240, 255), centro, self.raio + 12,
                             pulso)
            desenhar_circulo(tela, BRANCO, centro, self.raio + 12, 1,
                             brilho=1.2)

        self.desenhar_barra_carga(tela)


# ---------------------------------------------------------------------------
# Composicao de ondas
# ---------------------------------------------------------------------------

def composicao_onda(nivel, tipos):
    """Define a quantidade de inimigos da onda de acordo com o nivel."""
    qtd = min(5 + nivel // 2, 22)
    return tipos, qtd


def sortear_inimigo_especial(nivel, especiais):
    """Sorteia um inimigo especial com chance de 10-15%."""
    if not especiais:
        return None
    if random.random() > 0.12:
        return None
    return random.choice(especiais)