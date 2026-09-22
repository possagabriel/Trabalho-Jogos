"""Strategy: regras de ataque, movimento e defesa de cada protocolo."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

from src.core.constants import ALTURA, LARGURA
from src.runtime.domain.entities.enemies import Inimigo
from src.runtime.domain.entities.minibosses.states import Ataque, Recuperacao
from src.runtime.domain.entities.weapons import Projetil

if TYPE_CHECKING:
    from src.runtime.domain.entities.minibosses.base import Miniboss
    from src.runtime.domain.entities.player import Jogador


class Estrategia:
    """Hooks extensíveis; o caso comum é um leque e movimento lento lateral."""

    inverte = False
    destino: tuple[float, float] | None = None

    def preparar(self, boss: Miniboss, jogador: Jogador) -> None:
        """Prepara os indicadores de aviso."""

    def ativar(self, boss: Miniboss, jogador: Jogador) -> None:
        """Reutiliza o leque já implementado pelo boss do jogo."""
        boss.emitir(boss._executar_ataque("leque", jogador, boss.x, boss.y))

    def recuperar(self, boss: Miniboss, jogador: Jogador) -> None:
        """Finaliza efeitos do ataque anterior."""
        boss.zonas.clear()

    def mover(self, boss: Miniboss, jogador: Jogador, dt: float) -> None:
        """Orbita horizontalmente sem sair da arena."""
        boss.x = LARGURA / 2 + math.sin(boss.t / 90) * LARGURA * 0.12

    def dano(self, boss: Miniboss, quantidade: int) -> int:
        """Transforma dano segundo a defesa do protocolo."""
        return quantidade

    def interceptar(self, boss: Miniboss, proj: Projetil) -> bool:
        """Resolve partes destacadas, quando existem."""
        return False

    def pontos_fracos(self, boss: Miniboss) -> list[pygame.Rect]:
        """Expõe núcleos para colisão e desenho usando a mesma geometria."""
        return []


class EscudoNuclear(Estrategia):
    """Dois núcleos independentes bloqueiam todo dano no casco."""

    def __init__(self, vida: int) -> None:
        self.vidas = [vida, vida]

    def pontos_fracos(self, boss: Miniboss) -> list[pygame.Rect]:
        """Retorna somente núcleos ainda vivos, laterais e abaixo do casco."""
        return [self._rect(boss, i) for i, vida in enumerate(self.vidas) if vida > 0]

    @staticmethod
    def _rect(boss: Miniboss, indice: int) -> pygame.Rect:
        return pygame.Rect(round(boss.x + (-1, 1)[indice] * 48 - 12),
                           round(boss.y + 20), 24, 24)

    def dano(self, boss: Miniboss, quantidade: int) -> int:
        """O escudo não é removido por explosões nem por tiros no centro."""
        return 0 if self.pontos_fracos(boss) else quantidade

    def interceptar(self, boss: Miniboss, proj: Projetil) -> bool:
        """Aplica dano apenas ao núcleo atingido pelo projétil."""
        acertou = False
        for i, vida in enumerate(self.vidas):
            if vida > 0 and self._rect(boss, i).colliderect(proj.rect):
                if not boss.entrando:
                    self.vidas[i] = max(0, vida - proj.dano)
                acertou = True
        return acertou


class Emboscada(Estrategia):
    """Anuncia uma posição atrás do jogador e volta ao topo após atirar."""

    def preparar(self, boss: Miniboss, jogador: Jogador) -> None:
        """Fixa o destino antes do salto, dando tempo de esquiva."""
        lado = -1 if jogador.x > LARGURA / 2 else 1
        self.destino = (
            max(boss.raio, min(LARGURA - boss.raio, jogador.x + lado * 130)),
            min(ALTURA - boss.raio, jogador.y + 90),
        )

    def ativar(self, boss: Miniboss, jogador: Jogador) -> None:
        """Salta para o destino e dispara uma bala mirando a posição atual."""
        if self.destino is not None:
            boss.x, boss.y = self.destino
        dx, dy = jogador.x - boss.x, jogador.y - boss.y
        norma = math.hypot(dx, dy) or 1
        vel = boss.cfg["velocidade_tiro"]
        boss.emitir([Projetil(boss.x, boss.y, dx / norma * vel, dy / norma * vel,
                              1, boss.cor, 6, origem="inimigo")])

    def mover(self, boss: Miniboss, jogador: Jogador, dt: float) -> None:
        """Mantém a posição da emboscada enquanto ela estiver ativa."""
        if not isinstance(boss.estado, Ataque):
            super().mover(boss, jogador, dt)

    def recuperar(self, boss: Miniboss, jogador: Jogador) -> None:
        """Retorna ao campo de tiro frontal para continuar derrotável."""
        boss.y = boss.alvo_y
        boss.x = LARGURA / 2
        self.destino = None


class Invocacao(Estrategia):
    """Cria cópias descartáveis limitadas por encontro."""

    def ativar(self, boss: Miniboss, jogador: Jogador) -> None:
        """Preenche somente vagas livres; o controlador remove referências mortas."""
        vagas = boss.cfg["limite_lacaios"] - len(boss.lacaios)
        for _ in range(vagas):
            x = max(30, min(LARGURA - 30, boss.x + boss.rng.uniform(-100, 100)))
            lacaio = Inimigo("scout", boss.nivel, x=x, y=boss.y + boss.raio + 20)
            boss.lacaios.append(lacaio)
            boss.novos_lacaios.append(lacaio)
        super().ativar(boss, jogador)

    def dano(self, boss: Miniboss, quantidade: int) -> int:
        """O núcleo sem cópias recebe dano dobrado."""
        return quantidade if boss.lacaios else quantidade * 2


class Inversao(Estrategia):
    """O pulso inverte somente o vetor de movimento durante Ataque."""

    inverte = True


class Quarentena(Estrategia):
    """Marca regiões fixas; elas só causam dano depois do aviso."""

    def preparar(self, boss: Miniboss, jogador: Jogador) -> None:
        """Captura a posição inicial; as zonas não perseguem o jogador."""
        r = boss.cfg["raio_zona"]
        centros = [(jogador.x, jogador.y),
                   (boss.rng.uniform(r, LARGURA - r), ALTURA * 0.55)]
        boss.zonas = [pygame.Rect(round(x - r), round(y - r), r * 2, r * 2)
                      for x, y in centros]


class Espelho(Estrategia):
    """Copia o padrão do último disparo; não lê a arma apenas equipada."""

    def ativar(self, boss: Miniboss, jogador: Jogador) -> None:
        """Reverte direções com velocidade limitada e dano inimigo normal.

        Íon vira bala visível: reutilizar o tipo criaria uma coluna instantânea
        de tela inteira. Bombas e Nova mantêm o visual, sem explosão aliada.
        """
        if not boss.ultimo_disparo:
            super().ativar(boss, jogador)
            return
        for vx, vy, raio, _dano, cor, tipo in boss.ultimo_disparo:
            norma = math.hypot(vx, vy) or 1
            vel = boss.cfg["velocidade_tiro"]
            if tipo == "ion":
                vx, vy, norma, tipo = 0, -1, 1, "padrao"
            boss.emitir([Projetil(boss.x, boss.y, -vx / norma * vel, -vy / norma * vel,
                                  1, cor, min(raio, 9), tipo=tipo, origem="inimigo")])


class CicloBlindado(Estrategia):
    """Só aceita dano enquanto o relógio está em Recuperacao."""

    def ativar(self, boss: Miniboss, jogador: Jogador) -> None:
        """Emite o anel existente de oito projéteis."""
        boss.emitir(boss._executar_ataque("8dir", jogador, boss.x, boss.y))

    def dano(self, boss: Miniboss, quantidade: int) -> int:
        """Abre a blindagem exclusivamente na fase vulnerável."""
        return quantidade if isinstance(boss.estado, Recuperacao) else 0
