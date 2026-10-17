"""Modelo puro de avanço visual; não move entidades nem altera colisões."""

from __future__ import annotations

import math
from enum import Enum


class EstadoAvanco(Enum):
    """Fases da velocidade do cenário."""

    AVANCANDO = "AVANCANDO"
    FREANDO = "FREANDO"
    PARADO = "PARADO"
    ACELERANDO = "ACELERANDO"


def deslocamento_camada(
    direcao: tuple[float, float], velocidade: float, fator: float, dt: float,
) -> tuple[float, float]:
    """Calcula o deslocamento plano de uma camada em um passo de simulação."""
    dx, dy = direcao
    modulo = math.hypot(dx, dy)
    if modulo == 0:
        return 0.0, 0.0
    distancia = max(0.0, velocidade) * max(0.0, fator) * max(0.0, dt)
    return dx / modulo * distancia, dy / modulo * distancia


def faixas_repetidas(tamanho: int, deslocamento: float) -> list[tuple[int, int, int]]:
    """Retorna fatias de origem e destino que cobrem um eixo sem lacunas."""
    if tamanho <= 0:
        raise ValueError("tamanho deve ser positivo")
    offset = int(deslocamento) % tamanho
    if offset == 0:
        return [(0, 0, tamanho)]
    return [(tamanho - offset, 0, offset), (0, offset, tamanho - offset)]


def _suave(progresso: float) -> float:
    t = max(0.0, min(1.0, progresso))
    return t * t * (3.0 - 2.0 * t)


class ModeloAvanco:
    """Controla frenagem, repouso, aceleração e impulsos do cenário."""

    def __init__(
        self, velocidade_base: float, freada: float = 1.5,
        aceleracao: float = 1.2, pico: float = 0.3,
        intensidade_pico: float = 0.25,
    ) -> None:
        self.velocidade_base = max(0.0, velocidade_base)
        self.freada = max(0.001, freada)
        self.aceleracao = max(0.001, aceleracao)
        self.pico = max(0.0, pico)
        self.intensidade_pico = max(0.0, intensidade_pico)
        self.estado = EstadoAvanco.AVANCANDO
        self._velocidade = self.velocidade_base
        self._inicio = self._velocidade
        self._alvo = self._velocidade
        self._tempo = 0.0
        self._duracao = 0.0
        self._pico_restante = 0.0
        self._salto_restante = 0.0
        self._salto_duracao = 0.0
        self._salto_intensidade = 0.0
        self._boss_ativo = False
        self._miniboss_ativo = False
        self._miniboss_percentual = 1.0

    @property
    def velocidade(self) -> float:
        """Velocidade instantânea, incluindo impulsos visuais temporários."""
        fator = 1.0
        if self._pico_restante > 0 and self.pico > 0:
            fator += self.intensidade_pico * self._pico_restante / self.pico
        if self._salto_restante > 0 and self._salto_duracao > 0:
            progresso = 1.0 - self._salto_restante / self._salto_duracao
            fator += self._salto_intensidade * math.sin(math.pi * progresso)
        return self._velocidade * fator

    def _transicionar(self, alvo: float, duracao: float, estado: EstadoAvanco) -> None:
        self._inicio = self._velocidade
        self._alvo = max(0.0, alvo)
        self._tempo = 0.0
        self._duracao = max(0.001, duracao)
        self._pico_restante = 0.0
        self.estado = estado

    def boss_entrou(self) -> None:
        """Inicia a frenagem do boss principal."""
        self._boss_ativo = True
        self._miniboss_ativo = False
        self._transicionar(0.0, self.freada, EstadoAvanco.FREANDO)

    def boss_derrotado(self) -> None:
        """Retoma o avanço mesmo quando a frenagem ainda está em curso."""
        if not self._boss_ativo:
            return
        self._boss_ativo = False
        self._transicionar(self.velocidade_base, self.aceleracao, EstadoAvanco.ACELERANDO)

    def miniboss_entrou(self, percentual: float = 0.5) -> None:
        """Reduz o avanço até a fração configurada enquanto houver miniboss."""
        if self._boss_ativo:
            return
        self._miniboss_percentual = max(0.0, min(1.0, percentual))
        if self._miniboss_percentual == 1.0:
            self._miniboss_ativo = False
            return
        self._miniboss_ativo = True
        self._transicionar(
            self.velocidade_base * self._miniboss_percentual,
            self.freada, EstadoAvanco.FREANDO,
        )

    def miniboss_derrotado(self) -> None:
        """Restaura a velocidade após o miniboss sair do campo."""
        if not self._miniboss_ativo:
            return
        self._miniboss_ativo = False
        self._transicionar(self.velocidade_base, self.aceleracao, EstadoAvanco.ACELERANDO)

    def trocar_dimensao(
        self, velocidade_base: float, duracao_salto: float = 1.0,
        pico_salto: float = 0.5,
    ) -> None:
        """Atualiza a velocidade alvo sem descartar a transição em andamento."""
        antiga = self.velocidade_base
        self.velocidade_base = max(0.0, velocidade_base)
        proporcao = self.velocidade_base / antiga if antiga > 0 else 1.0
        self._velocidade *= proporcao
        self._inicio *= proporcao
        self._alvo *= proporcao
        self._salto_duracao = max(0.0, duracao_salto)
        self._salto_restante = self._salto_duracao
        self._salto_intensidade = max(0.0, pico_salto)

    def atualizar(self, dt: float, pausado: bool = False) -> None:
        """Avança as curvas apenas quando a simulação está ativa."""
        if pausado or dt <= 0:
            return
        if self.estado in (EstadoAvanco.FREANDO, EstadoAvanco.ACELERANDO):
            self._tempo = min(self._duracao, self._tempo + dt)
            t = _suave(self._tempo / self._duracao)
            self._velocidade = self._inicio + (self._alvo - self._inicio) * t
            if self._tempo >= self._duracao:
                if self.estado is EstadoAvanco.FREANDO:
                    self.estado = (EstadoAvanco.PARADO if self._boss_ativo
                                   or self._miniboss_percentual == 0
                                   else EstadoAvanco.AVANCANDO)
                else:
                    self.estado = EstadoAvanco.AVANCANDO
                    self._pico_restante = self.pico
        elif self._pico_restante > 0:
            self._pico_restante = max(0.0, self._pico_restante - dt)
        if self._salto_restante > 0:
            self._salto_restante = max(0.0, self._salto_restante - dt)
