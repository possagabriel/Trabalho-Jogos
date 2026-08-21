"""Animation utilities: tweens, keyframes, and time-based helpers.

Provides lightweight animation primitives that can be used across the game
without coupling to any specific rendering system.
"""

import math
from typing import Callable, Optional, Tuple


def tween_linear(inicio: float, fim: float, progresso: float) -> float:
    """Linear interpolation between two values."""
    progresso = max(0.0, min(1.0, progresso))
    return inicio + (fim - inicio) * progresso


def tween_ease_in(inicio: float, fim: float, progresso: float) -> float:
    """Quadratic ease-in."""
    progresso = max(0.0, min(1.0, progresso))
    t = progresso * progresso
    return inicio + (fim - inicio) * t


def tween_ease_out(inicio: float, fim: float, progresso: float) -> float:
    """Quadratic ease-out."""
    progresso = max(0.0, min(1.0, progresso))
    t = 1 - (1 - progresso) * (1 - progresso)
    return inicio + (fim - inicio) * t


def tween_ease_in_out(inicio: float, fim: float, progresso: float) -> float:
    """Smoothstep (ease-in-out)."""
    progresso = max(0.0, min(1.0, progresso))
    t = progresso * progresso * (3 - 2 * progresso)
    return inicio + (fim - inicio) * t


def tween_ease_out_back(inicio: float, fim: float,
                        progresso: float) -> float:
    """Overshoot ease-out (bouncy finish)."""
    progresso = max(0.0, min(1.0, progresso))
    c1 = 1.70158
    c3 = c1 + 1
    t = 1 + c3 * (progresso - 1) ** 3 + c1 * (progresso - 1) ** 2
    return inicio + (fim - inicio) * t


def cor_tween(cor1: Tuple[int, ...], cor2: Tuple[int, ...],
              progresso: float) -> Tuple[int, int, int]:
    """Interpolate two RGB colours with smoothstep."""
    progresso = max(0.0, min(1.0, progresso))
    t = progresso * progresso * (3 - 2 * progresso)
    return tuple(int(a + (b - a) * t) for a, b in zip(cor1[:3], cor2[:3]))


class Tween:
    """Time-based value interpolator.

    Usage::

        t = Tween(0.0, 100.0, duracao=1.0, easing=tween_ease_out)
        # each frame:
        t.atualizar(dt)
        valor = t.valor
        if t.terminado:
            ...
    """

    def __init__(self, inicio: float, fim: float, duracao: float = 1.0,
                 easing: Callable[[float, float, float], float] = tween_linear,
                 atraso: float = 0.0):
        self.inicio = inicio
        self.fim = fim
        self.duracao = max(0.001, duracao)
        self.easing = easing
        self.atraso = atraso
        self._tempo: float = 0.0
        self._atraso_restante: float = atraso
        self.terminado: bool = False
        self.valor: float = inicio

    def atualizar(self, dt: float) -> None:
        if self.terminado:
            return
        if self._atraso_restante > 0:
            self._atraso_restante = max(0.0, self._atraso_restante - dt)
            return
        self._tempo += dt
        progresso = min(1.0, self._tempo / self.duracao)
        self.valor = self.easing(self.inicio, self.fim, progresso)
        if progresso >= 1.0:
            self.terminado = True

    def reiniciar(self) -> None:
        self._tempo = 0.0
        self._atraso_restante = self.atraso
        self.terminado = False
        self.valor = self.inicio


class Oscilador:
    """Sinusoidal value oscillation for pulsing / breathing effects.

    Usage::

        osc = Oscilador(min_val=0.7, max_val=1.0, velocidade=2.5)
        # each frame:
        osc.atualizar(dt)
        valor = osc.valor
    """

    def __init__(self, min_val: float = 0.0, max_val: float = 1.0,
                 velocidade: float = 1.0, offset: float = 0.0):
        self.min_val = min_val
        self.max_val = max_val
        self.velocidade = velocidade
        self.offset = offset
        self._tempo: float = 0.0
        self.valor: float = min_val

    def atualizar(self, dt: float) -> None:
        self._tempo += dt
        t = 0.5 + 0.5 * math.sin(self._tempo * self.velocidade + self.offset)
        self.valor = self.min_val + (self.max_val - self.min_val) * t


class FlashController:
    """Manages a decaying flash overlay value (for damage / screen flash).

    Usage::

        flash = FlashController()
        # on hit:
        flash.ativar(intensidade=0.4)
        # each frame:
        flash.atualizar()
        if flash.intensidade > 0:
            # draw white overlay at flash.intensidade alpha
    """

    def __init__(self):
        self.intensidade: float = 0.0
        self._decaimento: float = 18.0

    def ativar(self, intensidade: float = 0.4) -> None:
        self.intensidade = intensidade

    def atualizar(self) -> None:
        if self.intensidade > 0:
            self.intensidade = max(0.0, self.intensidade - self._decaimento / 255.0)


class FadeController:
    """Fade-in / fade-out overlay controller.

    Usage::

        fade = FadeController()
        fade.iniciar_fade_in()
        # each frame:
        fade.atualizar()
        # draw black overlay at fade.alpha
    """

    def __init__(self):
        self.alpha: float = 255.0
        self._velocidade: float = 18.0
        self._alvo: float = 0.0

    def iniciar_fade_in(self) -> None:
        self.alpha = 255.0
        self._alvo = 0.0

    def iniciar_fade_out(self) -> None:
        self.alpha = 0.0
        self._alvo = 255.0

    def atualizar(self) -> None:
        if self.alpha < self._alvo:
            self.alpha = min(self._alvo, self.alpha + self._velocidade)
        elif self.alpha > self._alvo:
            self.alpha = max(self._alvo, self.alpha - self._velocidade)
