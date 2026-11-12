"""Bosses: um para cada cenario, com ataques e efeitos de morte proprios."""

from __future__ import annotations

import math
import random
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, Mapping

import pygame

from src.core.constants import (
    ALTURA,
    AZUL,
    BRANCO,
    CIANO,
    DOURADO,
    LARGURA,
    ROSA,
    ROXO,
    VERMELHO,
)
from src.runtime.domain.entities.weapons import Projetil
from src.runtime.infrastructure.graphics.cel_shading import (
    circulo_com_contorno,
    contorno_circulo,
    desenhar_highlight,
    desenhar_sombra_chapada,
    estrela_com_contorno,
    poligono_com_contorno,
)
from src.runtime.infrastructure.graphics.geometry import (
    estrela,
    losango,
    poligono,
)
from src.runtime.infrastructure.graphics.geometry import (
    pentagono as pent_pontos,
)
from src.runtime.infrastructure.graphics.smooth import (
    desenhar_glow,
    desenhar_poligono,
)

if TYPE_CHECKING:
    from src.runtime.domain.entities.player import Jogador
    from src.runtime.domain.world.scenarios import Cenario


class Boss:
    """Boss de um cenario. Aparece a cada 5 niveis."""

    VELOCIDADE_TELEGUIADO = 4.2

    def __init__(self, nivel: int, cenario: Cenario,
                 config: Mapping[str, Any] | None = None) -> None:
        self.nivel = nivel
        self.cenario_id = cenario.id
        cfg = config if config is not None else BOSSES_POR_CENARIO[cenario.id]
        self.nome = cfg["nome"]
        self.cor = cfg["cor"]
        self.raio = cfg["raio"]
        self.vida = cfg["vida"] * (
            1 + cfg.get("escala_vida", 0.15) * max(0, nivel - cfg["nivel"]))
        self.vida_max = self.vida
        self.pontos = cfg["pontos"]
        self.mov = cfg["mov"]
        self.ataques = list(cfg["ataques"])
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
        self.enraivecido = False
        self.teleportando = False
        self.teleport_timer = 130
        self.alvo = None
        self.fase_anterior = 1
        self.pulso_fase = 0
        self.aviso_ataques: tuple[str, ...] = ()
        self.alvo_ataque: tuple[float, float] | None = None
        self._angulo_aviso = 0.0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.raio), int(self.y - self.raio),
                           self.raio * 2, self.raio * 2)

    def _fracao_vida(self):
        return max(0.0, self.vida / self.vida_max)

    @property
    def fase_atual(self) -> int:
        """Fase comportamental atual, de um a três, baseada na vida."""
        fracao = self._fracao_vida()
        if fracao > 0.66:
            return 1
        if fracao > 0.33:
            return 2
        return 3

    def atualizar(self, jogador: Jogador) -> list[Projetil]:
        novos = []
        self.t += 1
        if self.flash > 0:
            self.flash -= 1
        if self.pulso_fase > 0:
            self.pulso_fase -= 1

        if self.entrando:
            self.y += 2
            if self.y >= self.alvo_y:
                self.y = self.alvo_y
                self.entrando = False
            return novos

        fase = self.fase_atual
        if fase != self.fase_anterior:
            self.fase_anterior = fase
            self.pulso_fase = 75
        velocidade = (1.0 + (fase - 1) * 0.2) * (1.5 if self.enraivecido else 1.0)
        if self.mov == "zigzag":
            amplitude = 220 + (fase - 1) * 55
            self.x = LARGURA // 2 + math.sin(self.t * 0.03 * velocidade) * amplitude
            self.angulo += 0.02 * velocidade
        elif self.mov == "gira":
            self.angulo += 0.03 * velocidade
            self.x += math.sin(self.t * 0.01) * 1.2 * velocidade
            self.x = max(self.raio, min(LARGURA - self.raio, self.x))
        elif self.mov == "infinito":
            self.x = LARGURA // 2 + math.sin(self.t * 0.02 * velocidade) * 320
            self.y = self.alvo_y + math.sin(self.t * 0.04 * velocidade) * 100
            self.angulo += 0.02 * velocidade
        elif self.mov == "teletransporte":
            self._atualizar_teletransporte()
        elif self.mov == "centro":
            self.angulo += 0.01 * velocidade
            if fase > 1:
                amplitude = 130 if fase == 2 else 250
                self.x = LARGURA // 2 + math.sin(self.t * 0.018 * velocidade) * amplitude
                self.y = self.alvo_y + math.sin(self.t * 0.031) * 45

        if not self.enraivecido and self._fracao_vida() <= 0.33:
            self.enraivecido = True

        self.timer_ataque -= 1
        if (self.nome in ("PRISMA", "ORACULO", "OBELISCO")
                and 0 < self.timer_ataque <= 30 and not self.aviso_ataques):
            disponiveis = self._ataques_por_fase()
            self.aviso_ataques = tuple(random.sample(
                disponiveis, min(self.fase_atual, 2, len(disponiveis))))
            self.alvo_ataque = (jogador.x, jogador.y)
            self._angulo_aviso = self.angulo
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
        fracao = self._fracao_vida()
        base = random.randint(75, 110)
        if fracao <= 0.33:
            base = int(base * 0.55)
        elif fracao <= 0.66:
            base = int(base * 0.8)
        if self.enraivecido:
            base = int(base * 0.85)
        return max(28, base)

    def _ataques_por_fase(self):
        """Seleciona os ataques ativos conforme a vida restante."""
        fracao = self._fracao_vida()
        if fracao > 0.66:
            return self.ataques[:1]
        if fracao > 0.33:
            return self.ataques[:2]
        return self.ataques

    def _atacar(self, jogador):
        x, y = self.x, self.y
        disponiveis = self._ataques_por_fase()
        if not disponiveis:
            return []
        if self.aviso_ataques:
            escolhidos = self.aviso_ataques
            if self.alvo_ataque is not None:
                jogador = SimpleNamespace(x=self.alvo_ataque[0], y=self.alvo_ataque[1])
        else:
            escolhidos = random.sample(
                disponiveis, min(self.fase_atual, 2, len(disponiveis)))
        projs = []
        for nome in escolhidos:
            projs += self._executar_ataque(nome, jogador, x, y)
        self.aviso_ataques = ()
        self.alvo_ataque = None
        return projs

    def _tiros_teleguiados(self, jogador, x, y):
        """Cria uma salva teleguiada visivel e desviavel.

        O vetor ate o jogador define somente a direcao. Usar a distancia como
        velocidade fazia o tiro cruzar a arena inteira em um unico quadro.
        """
        dx, dy = jogador.x - x, jogador.y - y
        angulo = math.atan2(dy, dx)
        return [
            Projetil(
                x,
                y,
                math.cos(angulo + desvio) * self.VELOCIDADE_TELEGUIADO,
                math.sin(angulo + desvio) * self.VELOCIDADE_TELEGUIADO,
                1,
                self.cor,
                5,
                origem="inimigo",
                teleguiado=True,
            )
            for desvio in (-0.18, 0.0, 0.18)
        ]

    def angulos_ataque_especial(self, nome: str, mira: float) -> tuple[float, ...]:
        """Retorna as mesmas direções para o aviso e a salva dos novos guardiões."""
        if nome == "tridente":
            return tuple(mira + lado * 0.26 for lado in (-1, 0, 1))
        if nome == "orbita":
            giro = self._angulo_aviso if self.aviso_ataques else self.angulo
            return tuple(mira + giro * 0.25 + i * math.tau / 10 for i in range(2, 9))
        if nome == "fratura":
            return tuple(mira + lado * (0.22 + passo * 0.18)
                         for lado in (-1, 1) for passo in range(3))
        return ()

    def _executar_ataque(self, nome, jogador, x, y):
        if nome in ("tridente", "orbita", "fratura"):
            mira = math.atan2(jogador.y - y, jogador.x - x)
            angulos = self.angulos_ataque_especial(nome, mira)
            return [Projetil(x, y, math.cos(a) * 3.6, math.sin(a) * 3.6,
                             1, self.cor, 5, origem="inimigo") for a in angulos]
        if nome == "leque":
            return [Projetil(x, y, dx, 4, 1, self.cor, 5, origem="inimigo")
                    for dx in (-2, 0, 2)]
        if nome == "8dir":
            return [Projetil(x, y, math.cos(a) * 3.5, math.sin(a) * 3.5, 1,
                             self.cor, 5, origem="inimigo")
                    for a in [i * math.tau / 8 for i in range(8)]]
        if nome == "teleguiado":
            return self._tiros_teleguiados(jogador, x, y)
        if nome == "tudo":
            return [Projetil(x, y, math.cos(a) * 3.2, math.sin(a) * 3.2, 1,
                             self.cor, 5, origem="inimigo")
                    for a in [i * math.tau / 12 for i in range(12)]]
        if nome == "mira":
            dx, dy = jogador.x - x, jogador.y - y
            norma = math.hypot(dx, dy) or 1
            return [Projetil(x, y, dx / norma * 7, dy / norma * 7, 1,
                             ROSA, 5, origem="inimigo") for _ in range(3)]
        if nome == "espiral":
            return [Projetil(x, y, math.cos(a) * 3.4, math.sin(a) * 3.4, 1,
                             CIANO, 5, origem="inimigo")
                    for a in [i * math.tau / 16 for i in range(16)]]
        if nome == "combinado":
            fracao = self._fracao_vida()
            projs = []
            if fracao <= 0.66:
                projs += [Projetil(x, y, math.cos(a) * 3.2,
                                   math.sin(a) * 3.2, 1, ROSA, 5,
                                   origem="inimigo")
                          for a in [i * math.tau / 8 for i in range(8)]]
            if fracao <= 0.33:
                teleguiados = self._tiros_teleguiados(jogador, x, y)
                for projetil in teleguiados:
                    projetil.cor = CIANO
                projs += teleguiados
            projs += [Projetil(x, y, dx, 4.5, 1, self.cor, 5,
                               origem="inimigo") for dx in (-2, 0, 2)]
            return projs
        return []

    def sofrer_dano(self, dano: int) -> bool:
        self.vida -= dano
        self.flash = 6
        return self.vida <= 0

    def desenhar(self, tela: pygame.Surface, *, efeitos_reduzidos: bool = False) -> None:
        if self.nome in ("PRISMA", "ORACULO", "OBELISCO"):
            from src.runtime.infrastructure.graphics.boss_art import desenhar_guardiao
            if desenhar_guardiao(tela, self, efeitos_reduzidos):
                return
        x, y = int(self.x), int(self.y)
        cor = BRANCO if self.flash > 0 else self.cor
        centro = (x, y)
        if self.pulso_fase > 0:
            raio_fase = self.raio + (75 - self.pulso_fase) * 3
            intensidade = self.pulso_fase / 75
            contorno_circulo(
                tela, centro, raio_fase, 3,
                cor_contorno=tuple(int(c * intensidade) for c in DOURADO),
            )
        if self.enraivecido:
            desenhar_glow(tela, VERMELHO, centro, self.raio + 12, 0.5)
            contorno_circulo(tela, centro, self.raio + 8, 2,
                            cor_contorno=VERMELHO)
        if self.entrando:
            desenhar_glow(tela, cor, centro, self.raio * 1.3, 0.6)
            circulo_com_contorno(tela, cor, centro, self.raio,
                                espessura_contorno=4)
            return
        if self.nome == "HEXAGONO":
            desenhar_glow(tela, cor, centro, self.raio * 1.6, 0.6)
            pts = poligono(centro, self.raio, 6, self.angulo)
            desenhar_sombra_chapada(tela, pts, deslocamento=(5, 7))
            poligono_com_contorno(tela, cor, pts, espessura_contorno=4)
            desenhar_poligono(tela, (120, 0, 0), pts, 3)
            desenhar_highlight(tela, centro, self.raio * 0.5, intensidade=0.4)
        elif self.nome == "LOSANGO":
            desenhar_glow(tela, cor, centro, self.raio * 1.6, 0.6)
            pts = losango(centro, self.raio * 0.7, self.raio, self.angulo)
            desenhar_sombra_chapada(tela, pts, deslocamento=(5, 7))
            poligono_com_contorno(tela, cor, pts, espessura_contorno=4)
            pts_int = losango(centro, self.raio * 0.4, self.raio * 0.6,
                             -self.angulo)
            desenhar_poligono(tela, (0, 60, 130), pts_int, 2)
            desenhar_poligono(tela, (0, 120, 200), pts_int, 1)
            desenhar_highlight(tela, centro, self.raio * 0.4, intensidade=0.4)
        elif self.nome == "ESTRELA":
            desenhar_glow(tela, cor, centro, self.raio * 1.7, 0.7)
            pts = estrela(centro, self.raio, angulo=self.angulo)
            desenhar_sombra_chapada(tela, pts, deslocamento=(5, 7))
            estrela_com_contorno(tela, cor, pts, espessura_contorno=4)
            pts_int = estrela(centro, self.raio * 0.6, angulo=-self.angulo)
            desenhar_poligono(tela, (120, 90, 0), pts_int, 2)
            desenhar_highlight(tela, centro, self.raio * 0.4, intensidade=0.4)
        elif self.nome == "PENTAGONO":
            desenhar_glow(tela, cor, centro, self.raio * 1.6, 0.6)
            pts = pent_pontos(centro, self.raio, self.angulo)
            desenhar_sombra_chapada(tela, pts, deslocamento=(5, 7))
            poligono_com_contorno(tela, cor, pts, espessura_contorno=4)
            desenhar_poligono(tela, (70, 20, 100), pts, 3)
            desenhar_highlight(tela, centro, self.raio * 0.4, intensidade=0.4)
            if self.teleportando:
                desenhar_glow(tela, ROSA, self.alvo, 20, 0.8)
                circulo_com_contorno(tela, ROSA, self.alvo, 12,
                                    espessura_contorno=2)
        elif self.nome in ("PRISMA", "ORACULO", "OBELISCO"):
            lados = {"PRISMA": 3, "ORACULO": 8, "OBELISCO": 4}[self.nome]
            pts = poligono(centro, self.raio, lados, self.angulo)
            desenhar_glow(tela, cor, centro, self.raio * 1.3, 0.35)
            desenhar_sombra_chapada(tela, pts, deslocamento=(5, 7))
            poligono_com_contorno(tela, cor, pts, espessura_contorno=4)
            contra = poligono(centro, self.raio * 0.62, lados, -self.angulo)
            desenhar_poligono(tela, BRANCO, contra, espessura=2)
            circulo_com_contorno(tela, cor, centro, self.raio * 0.22,
                                espessura_contorno=3)
            for lado in (-1, 1):
                ponto = (x + lado * self.raio * 0.7, y)
                circulo_com_contorno(tela, BRANCO, ponto, 5, espessura_contorno=2)
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
            contorno_circulo(tela, centro, raio, 2, cor_contorno=(0, 0, 0))
            circulo_com_contorno(tela, cor_anel, centro, raio,
                                espessura_contorno=2,
                                desenhar_borda_interna=False)
            ang = self.t * velocidade
            for i in range(3):
                a = ang + i * math.tau / 3
                px = x + math.cos(a) * raio
                py = y + math.sin(a) * raio
                circulo_com_contorno(tela, cor_anel, (px, py), 4,
                                    espessura_contorno=2)
                desenhar_highlight(tela, (px, py), 4, intensidade=0.6)
        circulo_com_contorno(tela, BRANCO, centro, 12, espessura_contorno=2)
        desenhar_highlight(tela, centro, 12, intensidade=0.7)


BOSSES_POR_CENARIO = {
    1: {"nome": "HEXAGONO", "cor": VERMELHO, "raio": 40, "vida": 30,
        "pontos": 200, "mov": "zigzag", "ataques": ["leque", "8dir"],
        "alvo_y": 150, "efeito": "explosao", "part_qtd": 10, "nivel": 5},
    2: {"nome": "LOSANGO", "cor": AZUL, "raio": 45, "vida": 50,
        "pontos": 350, "mov": "gira", "ataques": ["8dir", "espiral"],
        "alvo_y": 150, "efeito": "espiral", "part_qtd": 20, "nivel": 10},
    3: {"nome": "ESTRELA", "cor": DOURADO, "raio": 50, "vida": 70,
        "pontos": 500, "mov": "infinito", "ataques": ["teleguiado", "tudo"],
        "alvo_y": 180, "efeito": "estrela", "part_qtd": 30, "nivel": 15},
    4: {"nome": "PENTAGONO", "cor": ROXO, "raio": 55, "vida": 100,
        "pontos": 750, "mov": "teletransporte",
        "ataques": ["tudo", "leque", "mira"],
        "alvo_y": 150, "efeito": "pulsacao", "part_qtd": 40, "nivel": 20},
    5: {"nome": "ANEIS", "cor": BRANCO, "raio": 75, "vida": 150,
        "pontos": 1000, "mov": "centro",
        "ataques": ["combinado", "espiral"],
        "alvo_y": ALTURA // 2, "efeito": "mega", "part_qtd": 100,
        "nivel": 25},
    6: {"nome": "ANEIS DOURADO", "cor": DOURADO, "raio": 85, "vida": 220,
        "pontos": 1500, "mov": "centro",
        "ataques": ["combinado", "espiral", "teleguiado"],
        "alvo_y": ALTURA // 2, "efeito": "mega", "part_qtd": 140,
        "nivel": 30},
    7: {"nome": "PRISMA", "cor": CIANO, "raio": 58, "vida": 240,
        "pontos": 1700, "mov": "zigzag", "ataques": ["tridente", "leque", "espiral"],
        "alvo_y": 160, "efeito": "espiral", "part_qtd": 48, "nivel": 35},
    8: {"nome": "ORACULO", "cor": AZUL, "raio": 64, "vida": 270,
        "pontos": 1900, "mov": "infinito", "ataques": ["orbita", "8dir", "teleguiado"],
        "alvo_y": 180, "efeito": "estrela", "part_qtd": 56, "nivel": 40},
    9: {"nome": "OBELISCO", "cor": ROSA, "raio": 68, "vida": 300,
        "pontos": 2200, "mov": "gira", "ataques": ["fratura", "tridente", "orbita"],
        "alvo_y": 170, "efeito": "pulsacao", "part_qtd": 64, "nivel": 45},
}
