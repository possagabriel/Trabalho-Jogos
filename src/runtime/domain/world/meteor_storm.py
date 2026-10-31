"""Tempestades locais de meteoros com aviso, trajetórias fixas e corredor livre."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass(slots=True)
class Meteoro:
    """Obstáculo móvel; o segmento percorrido evita atravessar a nave sem colisão."""

    origem_x: float
    origem_y: float
    vx: float
    vy: float
    raio: int
    atraso: float
    x: float = 0.0
    y: float = 0.0
    anterior_x: float = 0.0
    anterior_y: float = 0.0
    idade: float = -1.0

    def mover(self, tempo: float) -> None:
        """Posiciona pelo tempo da onda, conservando o início do segmento."""
        self.anterior_x, self.anterior_y = self.x, self.y
        self.idade = tempo - self.atraso
        self.x = self.origem_x + self.vx * max(0.0, self.idade)
        self.y = self.origem_y + self.vy * max(0.0, self.idade)

    def atinge(self, posicao: tuple[float, float], raio: float) -> bool:
        """Testa a distância da nave ao segmento varrido pelo corpo da rocha."""
        if not 0 <= self.idade <= 6:
            return False
        dx, dy = self.x - self.anterior_x, self.y - self.anterior_y
        comprimento = dx * dx + dy * dy
        t = (((posicao[0] - self.anterior_x) * dx
              + (posicao[1] - self.anterior_y) * dy) / comprimento if comprimento else 0.0)
        t = max(0.0, min(1.0, t))
        return math.dist(posicao, (self.anterior_x + dx * t,
                                   self.anterior_y + dy * t)) <= raio + self.raio


class TempestadeMeteoros:
    """Agenda grupos aleatórios sem seguir a nave depois do aviso."""

    DURACAO_AVISO = 2.0
    DURACAO_CHUVA = 10.0
    LARGURA_CORREDOR = 200.0

    def __init__(self, rng: random.Random) -> None:
        self._rng = rng
        self.proxima_chuva = rng.uniform(14, 28)
        self.estado = "calma"
        self.tempo = 0.0
        self.meteoros: list[Meteoro] = []
        self.vertical = True
        self.sentido = 1
        self.corredor = 0.0
        self.centro = (0.0, 0.0)
        self.tamanho = (1280, 720)

    def _iniciar(self, centro: tuple[float, float], tamanho: tuple[int, int]) -> None:
        self.estado, self.tempo = "aviso", 0.0
        self.centro, self.tamanho = centro, tamanho
        self.vertical = self._rng.choice((True, False))
        self.sentido = self._rng.choice((-1, 1))
        transversal = centro[0 if self.vertical else 1]
        extensao = tamanho[0 if self.vertical else 1]
        self.corredor = transversal + self._rng.uniform(-extensao * 0.15, extensao * 0.15)
        longitudinal = centro[1 if self.vertical else 0]
        distancia = tamanho[1 if self.vertical else 0] / 2 + 180
        self.meteoros.clear()
        for indice in range(36):
            raio = self._rng.randint(12, 20)
            posicao = transversal
            while abs(posicao - self.corredor) < self.LARGURA_CORREDOR / 2 + raio:
                posicao = transversal + self._rng.uniform(-extensao / 2 - 80, extensao / 2 + 80)
            inicio = longitudinal - self.sentido * (distancia + self._rng.uniform(0, 90))
            velocidade = self.sentido * self._rng.uniform(420, 540)
            atraso = indice // 6 * 0.8
            x, y = (posicao, inicio) if self.vertical else (inicio, posicao)
            vx, vy = (0.0, velocidade) if self.vertical else (velocidade, 0.0)
            meteoro = Meteoro(x, y, vx, vy, raio, atraso, x, y, x, y)
            self.meteoros.append(meteoro)
        self.proxima_chuva = self._rng.uniform(14, 28)

    def atualizar(self, dt: float, centro: tuple[float, float],
                  tamanho: tuple[int, int]) -> None:
        """Avança somente em simulação; pausa e mapa deixam o grupo imóvel."""
        if dt <= 0 or not math.isfinite(dt):
            return
        if self.estado == "calma":
            if dt < self.proxima_chuva:
                self.proxima_chuva -= dt
                return
            dt -= self.proxima_chuva
            self._iniciar(centro, tamanho)
        self.tempo += dt
        if self.tempo >= self.DURACAO_AVISO + self.DURACAO_CHUVA:
            self.estado = "calma"
            self.meteoros.clear()
            return
        if self.tempo >= self.DURACAO_AVISO:
            self.estado = "ativa"
            for meteoro in self.meteoros:
                meteoro.mover(self.tempo - self.DURACAO_AVISO)

    def atinge(self, posicao: tuple[float, float], raio: float) -> bool:
        """Consome os impactos do quadro para usar o dano já existente no jogo."""
        if self.estado != "ativa":
            return False
        atingidos = [m for m in self.meteoros if m.atinge(posicao, raio)]
        self.meteoros = [m for m in self.meteoros if m not in atingidos]
        return bool(atingidos)
