"""Regras puras para progresso do nível e transições do percurso visual."""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum


class EstadoMundoVisual(Enum):
    """Fases do avanço visual que influenciam os marcos e o destino."""

    AVANCANDO = "AVANCANDO"
    FREANDO = "FREANDO"
    PARADO = "PARADO"
    ACELERANDO = "ACELERANDO"


class EstadoDestino(Enum):
    """Ciclo de vida do destino criado apenas para bosses principais."""

    INATIVO = "INATIVO"
    APROXIMANDO = "APROXIMANDO"
    ESTAVEL = "ESTAVEL"
    AGUARDANDO_CUTSCENE = "AGUARDANDO_CUTSCENE"
    SAINDO = "SAINDO"


_ESTADOS_CONGELADOS = {"PAUSA", "CUTSCENE", "MELHORIA", "GAME_OVER"}


def _simulacao_ativa(estado_jogo: str | Enum) -> bool:
    valor = estado_jogo.value if isinstance(estado_jogo, Enum) else str(estado_jogo)
    return valor.upper() not in _ESTADOS_CONGELADOS


@dataclass(frozen=True, slots=True)
class MarcoAgendado:
    """Resultado determinístico de um sorteio de marco."""

    marco: str
    intervalo: float


class SorteadorMarcos:
    """Sorteia marcos sem repetição adjacente e com intervalo limitado."""

    def __init__(
        self,
        marcos: tuple[str, ...],
        semente: int,
        intervalo_minimo: float,
        intervalo_maximo: float,
    ) -> None:
        if not marcos:
            raise ValueError("O catálogo precisa ter ao menos um marco")
        if intervalo_minimo < 0 or intervalo_maximo < intervalo_minimo:
            raise ValueError("Intervalos de marco inválidos")
        self._marcos = tuple(dict.fromkeys(marcos))
        self._aleatorio = random.Random(semente)
        self._minimo = float(intervalo_minimo)
        self._maximo = float(intervalo_maximo)
        self._anterior: str | None = None

    def proximo(self) -> MarcoAgendado:
        """Retorna o próximo tipo e seu intervalo, com semente reproduzível."""
        opcoes = [marco for marco in self._marcos if marco != self._anterior]
        if not opcoes:
            opcoes = list(self._marcos)
        escolhido = self._aleatorio.choice(opcoes)
        intervalo = self._aleatorio.uniform(self._minimo, self._maximo)
        self._anterior = escolhido
        return MarcoAgendado(escolhido, intervalo)


def curva_evolucao(progresso: float, curva: str = "suave") -> float:
    """Normaliza o progresso e aplica uma das curvas visuais configuráveis."""
    valor = min(1.0, max(0.0, float(progresso)))
    if curva == "linear":
        return valor
    if curva == "tardia":
        return valor * valor
    if curva == "inicial":
        return 1.0 - (1.0 - valor) ** 2
    return valor * valor * (3.0 - 2.0 * valor)


class RitmoVariavel:
    """Varia a velocidade visual e dispara passagens em intervalos definidos."""

    def __init__(
        self,
        semente: int,
        duracao_variacao: float = 8.0,
        variacao_maxima: float = 0.08,
        duracao_passagem: float = 2.5,
    ) -> None:
        self._aleatorio = random.Random(semente)
        self.duracao_variacao = max(0.1, float(duracao_variacao))
        self.variacao_maxima = min(0.25, max(0.0, float(variacao_maxima)))
        self.duracao_passagem = max(0.0, float(duracao_passagem))
        self.fator = 1.0
        self._alvo = 1.0
        self._tempo_variacao = 0.0
        self._tempo_passagem = 0.0

    @property
    def em_passagem(self) -> bool:
        """Indica o período curto de travessia acelerada."""
        return self._tempo_passagem > 0.0

    def atualizar(self, dt: float) -> float:
        """Interpola o fator atual e agenda uma passagem ocasional."""
        passo = max(0.0, float(dt))
        self._tempo_variacao -= passo
        self._tempo_passagem = max(0.0, self._tempo_passagem - passo)
        if self._tempo_variacao <= 0.0:
            self._tempo_variacao = self.duracao_variacao
            faixa = self.variacao_maxima
            self._alvo = self._aleatorio.uniform(1.0 - faixa, 1.0 + faixa)
            if self.duracao_passagem and self._aleatorio.random() < 0.25:
                self._tempo_passagem = self.duracao_passagem
        fracao = min(1.0, passo / self.duracao_variacao)
        self.fator += (self._alvo - self.fator) * fracao
        if self.em_passagem:
            self.fator = min(1.0 + self.variacao_maxima, self.fator + passo * 0.02)
        return min(1.0 + self.variacao_maxima, max(1.0 - self.variacao_maxima, self.fator))


class ProgressTracker:
    """Progresso suavizado, monotônico e independente da lógica de combate."""

    def __init__(self, suavizacao: float = 3.0) -> None:
        self.suavizacao = max(0.0, float(suavizacao))
        self.total_unidades = 0
        self.nivel_de_boss = False
        self.valor = 0.0

    def reiniciar(self, unidades: int, nivel_de_boss: bool = False) -> None:
        """Começa o progresso de um nível sem herdar o valor anterior."""
        self.total_unidades = max(0, int(unidades))
        self.nivel_de_boss = bool(nivel_de_boss)
        self.valor = 0.0

    def atualizar(
        self, fila: int, ativos: int, dt: float, chefe_ativo: bool = False, concluido: bool = False
    ) -> float:
        """Interpola até um alvo que nunca fica abaixo do progresso já exibido."""
        if self.nivel_de_boss:
            alvo = 1.0 if concluido and not chefe_ativo else 0.0
        elif concluido or self.total_unidades == 0:
            alvo = 1.0
        else:
            restantes = max(0, int(fila)) + max(0, int(ativos))
            alvo = min(1.0, max(0.0, 1.0 - restantes / self.total_unidades))
        alvo = max(self.valor, alvo)
        passo = min(1.0, max(0.0, float(dt)) * self.suavizacao)
        self.valor += (alvo - self.valor) * passo
        if passo >= 1.0:
            self.valor = alvo
        return self.valor


class TransicaoDestino:
    """Aproxima, estabiliza e retira o destino de um boss sem saltos visuais."""

    def __init__(self, duracao_entrada: float = 1.5, duracao_saida: float = 1.0) -> None:
        self.duracao_entrada = max(0.01, float(duracao_entrada))
        self.duracao_saida = max(0.01, float(duracao_saida))
        self.estado = EstadoDestino.INATIVO
        self.escala = 0.0
        self.opacidade = 0.0
        self._tempo = 0.0
        self._escala_saida = 0.0
        self._opacidade_saida = 0.0

    def iniciar_boss(self) -> None:
        """Ativa o destino quando surge um boss principal."""
        self.estado = EstadoDestino.APROXIMANDO
        self.escala = 0.15
        self.opacidade = 0.25
        self._tempo = 0.0
        self._escala_saida = self.escala
        self._opacidade_saida = self.opacidade

    def derrotar_boss(self, cutscene_pendente: bool = False) -> None:
        """Para a aproximação e aguarda a cutscene ou inicia a saída."""
        if self.estado is EstadoDestino.INATIVO:
            return
        self._escala_saida = self.escala
        self._opacidade_saida = self.opacidade
        self._tempo = 0.0
        if cutscene_pendente:
            self.estado = EstadoDestino.AGUARDANDO_CUTSCENE
        else:
            self.estado = EstadoDestino.SAINDO

    def liberar_cutscene(self) -> None:
        """Inicia a saída quando a narrativa pós-boss termina."""
        if self.estado is EstadoDestino.AGUARDANDO_CUTSCENE:
            self.estado = EstadoDestino.SAINDO
            self._escala_saida = self.escala
            self._opacidade_saida = self.opacidade
            self._tempo = 0.0

    def atualizar(
        self, dt: float, estado_avanco: EstadoMundoVisual, estado_jogo: str | Enum = "JOGANDO"
    ) -> bool:
        """Atualiza o destino; retorna False enquanto estiver totalmente inativo."""
        if self.estado is EstadoDestino.INATIVO:
            return False
        if not _simulacao_ativa(estado_jogo):
            return True
        dt = max(0.0, float(dt))
        if self.estado is EstadoDestino.APROXIMANDO:
            if estado_avanco is EstadoMundoVisual.FREANDO:
                self._tempo = min(self.duracao_entrada, self._tempo + dt)
                fracao = self._tempo / self.duracao_entrada
                self.escala = 0.15 + 0.85 * fracao
                self.opacidade = 0.25 + 0.75 * fracao
            elif estado_avanco is EstadoMundoVisual.PARADO:
                self.estado = EstadoDestino.ESTAVEL
            elif estado_avanco is EstadoMundoVisual.ACELERANDO:
                self.derrotar_boss()
        elif self.estado is EstadoDestino.SAINDO:
            self._tempo = min(self.duracao_saida, self._tempo + dt)
            fracao = self._tempo / self.duracao_saida
            self.escala = self._escala_saida + (1.15 - self._escala_saida) * fracao
            self.opacidade = self._opacidade_saida * (1.0 - fracao)
            if fracao >= 1.0:
                self.estado = EstadoDestino.INATIVO
                self.escala = 0.0
                self.opacidade = 0.0
                return False
        return True


class FadeDimensao:
    """Cross-fade contínuo entre o cenário antigo e o novo."""

    def __init__(self, duracao: float = 0.8) -> None:
        self.duracao = max(0.01, float(duracao))
        self.tempo = 0.0

    @property
    def antiga(self) -> float:
        """Opacidade restante do cenário anterior."""
        return 1.0 - min(1.0, self.tempo / self.duracao)

    @property
    def nova(self) -> float:
        """Opacidade alcançada pelo cenário novo."""
        return min(1.0, self.tempo / self.duracao)

    @property
    def ativo(self) -> bool:
        """Indica se o cross-fade ainda está em andamento."""
        return self.tempo < self.duracao

    def iniciar(self) -> None:
        """Reinicia o cross-fade a partir de uma troca de dimensão."""
        self.tempo = 0.0

    def atualizar(
        self, dt: float, estado_avanco: EstadoMundoVisual, estado_jogo: str | Enum = "JOGANDO"
    ) -> None:
        """Avança o cross-fade sem alterar sua continuidade durante pausa."""
        if self.ativo and _simulacao_ativa(estado_jogo):
            self.tempo = min(self.duracao, self.tempo + max(0.0, float(dt)))
