"""Inimigos normais (por cenario) e inimigos especiais com sistema de carga."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

import pygame

from src.legacy.infrastructure.graphics.cel_shading import (barra_vida_cartoon, circulo_com_contorno,
                          contorno_circulo, contorno_poligono,
                          desenhar_brilho_contorno, desenhar_highlight,
                          desenhar_sombra_chapada, escurecer_cor,
                          estrela_com_contorno, poligono_com_contorno)
from src.core.constants import AMARELO, AZUL, BRANCO, CIANO, \
    COOLDOWN_ATAQUE_INIMIGO_MAXIMO, COOLDOWN_ATAQUE_INIMIGO_MINIMO, \
    DOURADO, INVISIBILIDADE_QUADROS, LARGURA, LARANJA, \
    PISCAR_INVISIBILIDADE_QUADROS, ROXO, VERDE, VERMELHO
from src.legacy.infrastructure.graphics.geometry import estrela, losango, pentagono, poligono, quadrado, triangulo
from src.legacy.infrastructure.graphics.smooth import desenhar_circulo, desenhar_glow, desenhar_poligono, \
    linha_suave
from src.legacy.domain.entities.weapons import Projetil

if TYPE_CHECKING:
    from src.legacy.domain.entities.player import Jogador

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
    "bomba": {"cor": VERMELHO, "raio": 10, "vida": 1, "pontos": 15,
              "vel": 3.0, "mov": "investida", "ataque": "nenhum"},
    # Dimensao 4 - Crystal Forest
    "cristalino": {"cor": VERDE, "raio": 16, "vida": 5, "pontos": 50,
                   "vel": 1.7, "mov": "ondulacao", "ataque": "baixo"},
    "guardiao": {"cor": BRANCO, "raio": 15, "vida": 4, "pontos": 55,
                 "vel": 1.5, "mov": "reta", "ataque": "tudo"},
    "artilheiro": {"cor": CIANO, "raio": 14, "vida": 4, "pontos": 40,
                   "vel": 1.2, "mov": "flutua", "ataque": "rajada"},
    # Dimensao 5 - Null Space
    "espectro": {"cor": (120, 60, 180), "raio": 12, "vida": 4, "pontos": 60,
                 "vel": 2.4, "mov": "erratico", "ataque": "nenhum"},
    "distorcao": {"cor": ROXO, "raio": 18, "vida": 6, "pontos": 70,
                  "vel": 1.1, "mov": "flutua", "ataque": "baixo"},
    "assombra": {"cor": (150, 150, 200), "raio": 12, "vida": 3, "pontos": 35,
                 "vel": 2.4, "mov": "fada", "ataque": "mira"},
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
    "bomba": "circulo", "cristalino": "hexagono", "guardiao": "pentagono",
    "artilheiro": "pentagono", "espectro": "aleatoria",
    "distorcao": "circulo_pulsante", "assombra": "circulo_pulsante",
    "celestial": "estrela", "sentinela": "olho",
}


class Inimigo:
    """Inimigo normal com movimento e ataque proprios."""

    def __init__(self, tipo: str, nivel: int, x: float | None = None,
                 y: float = -40, escala: float = 1.0) -> None:
        cfg = TIPOS[tipo]
        self.tipo = tipo
        self.nivel = nivel
        self.cor = cfg["cor"]
        self.raio = cfg["raio"] * escala
        self.vida = cfg["vida"] * (1 + 0.03 * max(0, nivel - 1))
        self.vida = max(1, int(self.vida))
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
        self.invisivel = 0
        self.vel_x = random.uniform(-1, 1)
        self.vel_y = 0
        self.timer_feixe = 0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.raio), int(self.y - self.raio),
                           self.raio * 2, self.raio * 2)

    def atualizar(self, jogador: Jogador) -> list[Projetil]:
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
                self.invisivel = INVISIBILIDADE_QUADROS

        if self.invisivel > 0:
            self.invisivel -= 1
        self.timer_ataque -= 1
        if self.timer_ataque <= 0:
            self.timer_ataque = random.randint(
                COOLDOWN_ATAQUE_INIMIGO_MINIMO, COOLDOWN_ATAQUE_INIMIGO_MAXIMO)
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
        if self.ataque == "mira":
            dx, dy = jogador.x - x, jogador.y - y
            norma = math.hypot(dx, dy) or 1
            return [Projetil(x, y, dx / norma * 5, dy / norma * 5, 1,
                             self.cor, 4, origem="inimigo")]
        if self.ataque == "rajada":
            dx, dy = jogador.x - x, jogador.y - y
            norma = math.hypot(dx, dy) or 1
            base = (dx / norma, dy / norma)
            return [Projetil(x, y, base[0] * 5, base[1] * 5, 1, CIANO, 4,
                             origem="inimigo")
                    for _ in range(3)]
        return []

    def sofrer_dano(self, dano: int) -> bool:
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
            from src.legacy.infrastructure.graphics.geometry import cruz as _cruz
            return _cruz(centro, raio)
        return poligono(centro, raio, 3, self.angulo)

    def desenhar(self, tela: pygame.Surface) -> None:
        if self.invisivel > 0:
            if (self.invisivel // PISCAR_INVISIBILIDADE_QUADROS) % 2 == 0:
                return
        x, y = int(self.x), int(self.y)
        cor = BRANCO if self.flash > 0 else self.cor
        centro = (x, y)
        if self.tipo == "bomba":
            pulso = 1 + 0.2 * math.sin(self.tempo_global() * 6)
            desenhar_glow(tela, cor, centro, self.raio * 1.8, 0.7)
            circulo_com_contorno(tela, cor, centro, int(self.raio * pulso),
                                espessura_contorno=3)
            circulo_com_contorno(tela, (80, 0, 0), centro,
                                int(self.raio * 0.55), espessura_contorno=2)
            desenhar_circulo(tela, AMARELO, centro, self.raio * 0.28,
                             brilho=1.5)
            desenhar_highlight(tela, centro, self.raio * 0.55, intensidade=0.5)
            return
        if self.tipo == "espectro":
            # forma aleatoria (versao escura de todas as formas)
            formas = ["triangulo", "quadrado", "circulo", "estrela",
                      "hexagono", "losango", "pentagono"]
            forma = formas[int(self.fase) % len(formas)]
            self._desenhar_forma(tela, centro, cor, forma)
            return
        if self.tipo == "distorcao":
            pulso = 1 + 0.15 * math.sin(self.tempo_global())
            raio = self.raio * pulso
            desenhar_glow(tela, cor, centro, raio * 1.4, 0.6)
            circulo_com_contorno(tela, cor, centro, int(raio),
                                espessura_contorno=3)
            circulo_com_contorno(tela, BRANCO, centro, int(raio),
                                espessura_contorno=1,
                                desenhar_borda_interna=False)
            circulo_com_contorno(tela, (40, 10, 60), centro, int(raio / 2),
                                espessura_contorno=2)
            circulo_com_contorno(tela, (180, 100, 255), centro,
                                int(raio * 1.35), espessura_contorno=1,
                                desenhar_borda_interna=False)
            return
        if self.tipo == "sentinela":
            desenhar_sombra_chapada(tela, self._pontos_forma(centro, "olho"),
                                    deslocamento=(3, 5))
            contorno_poligono(tela, self._pontos_forma(centro, "olho"), 3)
            desenhar_poligono(tela, cor, self._pontos_forma(centro, "olho"))
            desenhar_poligono(tela, escurecer_cor(cor, 0.7),
                              self._pontos_forma(centro, "olho"), 2)
            circulo_com_contorno(tela, DOURADO, centro, self.raio // 3,
                                espessura_contorno=2)
            desenhar_highlight(tela, centro, self.raio // 3, intensidade=0.6)
            return
        forma = FORMAS[self.tipo]
        self._desenhar_forma(tela, centro, cor, forma)

    def _desenhar_forma(self, tela, centro, cor, forma):
        x, y = centro
        if forma == "circulo":
            desenhar_glow(tela, cor, (x, y), self.raio * 1.5, 0.5)
            circulo_com_contorno(tela, cor, (x, y), self.raio,
                                espessura_contorno=3)
            desenhar_highlight(tela, (x, y), self.raio, intensidade=0.5)
        elif forma == "circulo_pulsante":
            desenhar_glow(tela, cor, (x, y), self.raio * 1.5, 0.5)
            circulo_com_contorno(tela, cor, (x, y), self.raio,
                                espessura_contorno=3)
            contorno_circulo(tela, (x, y), self.raio, 2, BRANCO)
        else:
            pts = self._pontos_forma(centro, forma)
            desenhar_glow(tela, cor, centro, self.raio * 1.4, 0.4)
            desenhar_sombra_chapada(tela, pts, deslocamento=(3, 5))
            poligono_com_contorno(tela, cor, pts, espessura_contorno=3)
            desenhar_highlight(tela, centro, self.raio * 0.6, intensidade=0.4)

    def tempo_global(self) -> float:
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
        "cristalino": 15, "evocador": 12,
    }
    CORES = {
        "acumulador": (255, 200, 40), "esponja": (150, 60, 200),
        "condutor": (80, 160, 255), "mutante": (200, 40, 255),
        "cristalino": (210, 235, 245), "evocador": (200, 120, 255),
    }

    def __init__(self, tipo_especial: str, nivel: int,
                 cenario_id: int = 1) -> None:
        # tipo base (forma) com base nos TIPOS atuais
        base = {"acumulador": "flamifero", "esponja": "soldado",
                "condutor": "estelar", "mutante": "forja",
                "cristalino": "guardiao", "evocador": "celestial"}[tipo_especial]
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
                    "cristalino": "flutua", "evocador": "flutua"}[tipo_especial]
        self.ataque = "nenhum"
        self.vel = 1.2

    def receber_tiro(self, dano: int) -> bool:
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
        self.invisivel = INVISIBILIDADE_QUADROS

    def acoes_carregado(self) -> dict[str, object]:
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
        elif self.tipo_especial == "evocador":
            for _ in range(3):
                acoes["inimigos"].append(Inimigo(
                    self.tipo, self.nivel,
                    x + random.randint(-40, 40), y))
            self.efeito_ja_atirado = False
            self.carga = 0
            self.carregado = False
            self._teleportar()
            acoes["mensagem"] = "EVOCACAO!"
        return acoes

    def e_feito_ja_atirado(self) -> bool:
        return self.efeito_ja_atirado

    def _caminho_ordem(self):
        return 0

    def desenhar_barra_carga(self, tela: pygame.Surface) -> None:
        """Barra de carga acima do inimigo estilo cartoon."""
        largura_barra = int(self.raio * 2)
        altura_barra = 5
        x = int(self.x) - largura_barra // 2
        y = int(self.y) - self.raio - 15
        progresso = self.carga / self.carga_maxima
        barra_vida_cartoon(tela, x, y, largura_barra,
                          int(progresso * 100), 100, altura=altura_barra)
        if progresso > 0.8:
            pulso = int(128 + 127 * math.sin(pygame.time.get_ticks() * 0.01))
            brilho = pygame.Surface((int(largura_barra * progresso),
                                     altura_barra))
            brilho.fill((255, 255, 255))
            brilho.set_alpha(pulso)
            tela.blit(brilho, (x, y))

    def desenhar(self, tela: pygame.Surface) -> None:
        if self.invisivel > 0:
            if (self.invisivel // PISCAR_INVISIBILIDADE_QUADROS) % 2 == 0:
                return
        x, y = int(self.x), int(self.y)
        centro = (x, y)
        cor = BRANCO if self.flash > 0 else self.cor
        t = pygame.time.get_ticks() * 0.001

        if self.mini_boss:
            desenhar_glow(tela, (60, 0, 80), centro, self.raio + 10, 0.7)
            circulo_com_contorno(tela, (60, 0, 80), centro, self.raio + 8,
                                espessura_contorno=4)
            pts_hex = poligono(centro, self.raio, 6, t * 2)
            desenhar_sombra_chapada(tela, pts_hex, deslocamento=(4, 6))
            poligono_com_contorno(tela, cor, pts_hex, espessura_contorno=3)
            circulo_com_contorno(tela, (255, 0, 255), centro, 8,
                                espessura_contorno=2)
            desenhar_highlight(tela, centro, 8, intensidade=0.7)
            self.desenhar_barra_carga(tela)
            return

        if self.tipo_especial == "acumulador":
            desenhar_glow(tela, cor, centro, self.raio * 1.5, 0.6)
            circulo_com_contorno(tela, cor, centro, self.raio,
                                espessura_contorno=3)
            circulo_com_contorno(tela, (120, 100, 0), centro,
                                self.raio - 4, espessura_contorno=2)
            desenhar_highlight(tela, centro, self.raio, intensidade=0.5)
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
            desenhar_glow(tela, cor, centro, self.raio * 1.5, 0.5)
            pts_quad = quadrado(centro, self.raio, self.angulo)
            desenhar_sombra_chapada(tela, pts_quad, deslocamento=(3, 5))
            poligono_com_contorno(tela, cor, pts_quad, espessura_contorno=3)
            desenhar_highlight(tela, centro, self.raio * 0.6, intensidade=0.4)
            for i in range(3):
                a = t * 2 + i * math.tau / 3
                px = self.x + math.cos(a) * self.raio * 0.7
                py = self.y + math.sin(a) * self.raio * 0.7
                desenhar_circulo(tela, (100, 255, 120), (px, py), 3,
                                 brilho=1.3)
        elif self.tipo_especial == "condutor":
            desenhar_glow(tela, cor, centro, self.raio * 1.5, 0.5)
            pts_est = estrela(centro, self.raio, angulo=self.angulo)
            desenhar_sombra_chapada(tela, pts_est, deslocamento=(3, 5))
            estrela_com_contorno(tela, cor, pts_est, espessura_contorno=3)
            desenhar_highlight(tela, centro, self.raio * 0.5, intensidade=0.4)
            for i in range(5):
                a = -t * 3 + i * math.tau / 5
                px = self.x + math.cos(a) * (self.raio + 7)
                py = self.y + math.sin(a) * (self.raio + 7)
                desenhar_glow(tela, (160, 200, 255), ((self.x + px) / 2,
                                                      (self.y + py) / 2), 6, 0.6)
                linha_suave(tela, (160, 200, 255),
                            (self.x, self.y), (px, py), 2)
        elif self.tipo_especial == "mutante":
            desenhar_glow(tela, cor, centro, self.raio * 1.5, 0.6)
            pts_hex = poligono(centro, self.raio, 6, self.angulo)
            desenhar_sombra_chapada(tela, pts_hex, deslocamento=(3, 5))
            poligono_com_contorno(tela, cor, pts_hex, espessura_contorno=3)
            circulo_com_contorno(tela, (255, 0, 255), centro, 5,
                                espessura_contorno=2)
            desenhar_highlight(tela, centro, 5, intensidade=0.7)
        elif self.tipo_especial == "cristalino":
            desenhar_glow(tela, self.cor, centro, self.raio * 1.6, 0.7)
            surf = pygame.Surface((self.raio * 2 + 8, self.raio * 2 + 8),
                                  pygame.SRCALPHA)
            pts = pentagono((self.raio + 4, self.raio + 4), self.raio,
                            self.angulo)
            desenhar_poligono(surf, self.cor + (150,), pts)
            desenhar_poligono(surf, (255, 255, 255, 230), pts, 2)
            tela.blit(surf, (x - self.raio - 4, y - self.raio - 4))
            contorno_pents = [(p[0] + x - self.raio - 4,
                              p[1] + y - self.raio - 4) for p in pts]
            contorno_poligono(tela, contorno_pents, 3)
        elif self.tipo_especial == "evocador":
            desenhar_glow(tela, cor, centro, self.raio * 1.5, 0.6)
            pts_est = estrela(centro, self.raio, angulo=self.angulo)
            desenhar_sombra_chapada(tela, pts_est, deslocamento=(3, 5))
            estrela_com_contorno(tela, cor, pts_est, espessura_contorno=3)
            desenhar_highlight(tela, centro, self.raio * 0.5, intensidade=0.4)
            for i in range(4):
                a = t * 1.5 + i * math.tau / 4
                px = self.x + math.cos(a) * (self.raio + 9)
                py = self.y + math.sin(a) * (self.raio + 9)
                circulo_com_contorno(tela, (255, 200, 255), (px, py), 3,
                                    espessura_contorno=1,
                                    desenhar_borda_interna=False)
            circulo_com_contorno(tela, (80, 20, 120), centro, 6,
                                espessura_contorno=2)

        # campo de forca refletor
        if self.campo_forca:
            pulso = 4 + 2 * math.sin(t * 6)
            desenhar_glow(tela, (200, 240, 255), centro, self.raio + 12, 0.5)
            contorno_circulo(tela, centro, self.raio + 12, int(pulso),
                            cor_contorno=(200, 240, 255))
            circulo_com_contorno(tela, (200, 240, 255), centro,
                                self.raio + 12, espessura_contorno=1,
                                desenhar_borda_interna=False)

        self.desenhar_barra_carga(tela)


# ---------------------------------------------------------------------------
# Composicao de ondas
# ---------------------------------------------------------------------------

def composicao_onda(nivel, tipos):
    """Define a quantidade de inimigos e as posicoes de spawn da onda.

    Retorna ``(tipos, qtd, xs)`` onde ``xs`` e uma lista do mesmo tamanho
    de ``qtd`` com a posicao x de cada inimigo da onda (ou ``None`` para
    posicao aleatoria), permitindo formacoes em "V" em ondas maiores.
    """
    qtd = min(5 + nivel // 2, 22)
    xs = [None] * qtd
    if qtd >= 5 and random.random() < 0.35:
        posicoes = [max(25, min(LARGURA - 25,
                                LARGURA // 2 + (i - (qtd - 1) / 2) * 52))
                    for i in range(qtd)]
        posicoes.sort(key=lambda v: abs(v - LARGURA // 2))
        xs = posicoes
    return tipos, qtd, xs


def sortear_inimigo_especial(nivel, especiais):
    """Sorteia um inimigo especial com chance de 10-15%."""
    if not especiais:
        return None
    if random.random() > 0.12:
        return None
    return random.choice(especiais)
