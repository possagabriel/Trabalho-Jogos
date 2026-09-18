"""Cadência determinística da simulação, independente da renderização."""

from __future__ import annotations

from src.core.constants import FPS

PASSO_FIXO = 1.0 / FPS
MAXIMO_PASSOS_POR_QUADRO = 5


class RelogioSimulacao:
    """Converte tempo real em uma quantidade limitada de passos fixos."""

    def __init__(
            self,
            passo: float = PASSO_FIXO,
            maximo_passos: int = MAXIMO_PASSOS_POR_QUADRO) -> None:
        self.passo = passo
        self.maximo_passos = maximo_passos
        self._acumulado = 0.0

    @property
    def fracao(self) -> float:
        """Retorna a fração restante para futura interpolação visual."""
        return self._acumulado / self.passo if self.passo else 0.0

    def consumir(self, tempo_ms: float) -> int:
        """Acumula tempo e retorna quantos passos de simulação executar.

        Atrasos extremos são limitados para impedir a espiral de atualizações
        que deixaria o jogo ainda mais lento depois de uma pausa do sistema.
        """
        limite = self.passo * self.maximo_passos
        decorrido = max(0.0, min(float(tempo_ms) / 1000.0, limite))
        self._acumulado = min(limite, self._acumulado + decorrido)
        passos = min(self.maximo_passos, int((self._acumulado + 1e-12) / self.passo))
        self._acumulado -= passos * self.passo
        return passos
