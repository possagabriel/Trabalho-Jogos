"""Métricas de frame com custo pequeno e janela limitada."""

from __future__ import annotations

import math
from collections import deque


class MetricasQuadro:
    """Calcula média, p95 e 1% low de uma janela de tempos de quadro."""

    def __init__(self, tamanho_janela: int = 300) -> None:
        self._tempos: deque[float] = deque(maxlen=max(10, tamanho_janela))

    def registrar(self, tempo_ms: float) -> None:
        """Registra um tempo de quadro positivo em milissegundos."""
        if tempo_ms > 0:
            self._tempos.append(float(tempo_ms))

    def percentil(self, percentual: float) -> float:
        """Retorna o percentil pelo método nearest-rank."""
        if not self._tempos:
            return 0.0
        ordenados = sorted(self._tempos)
        indice = max(0, math.ceil(len(ordenados) * percentual) - 1)
        return ordenados[min(indice, len(ordenados) - 1)]

    @property
    def media_ms(self) -> float:
        """Tempo médio de quadro da janela."""
        return sum(self._tempos) / len(self._tempos) if self._tempos else 0.0

    @property
    def p95_ms(self) -> float:
        """Tempo abaixo do qual ficam 95% dos quadros."""
        return self.percentil(0.95)

    @property
    def fps_1_baixo(self) -> float:
        """Converte o p99 de frame time no indicador de 1% low FPS."""
        p99 = self.percentil(0.99)
        return 1000.0 / p99 if p99 > 0 else 0.0
