"""State: cada fase determina duração e hooks, sem condicionais por miniboss."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.runtime.domain.entities.minibosses.base import Miniboss
    from src.runtime.domain.entities.player import Jogador


class EstadoMiniboss:
    """Fase temporal de um protocolo."""

    chave = "aviso"
    rotulo = "AVISO"

    def __init__(self, duracao: float) -> None:
        self.restante = duracao

    def entrar(self, boss: Miniboss, jogador: Jogador) -> None:
        """Inicializa sinais da fase."""
        boss.estrategia.preparar(boss, jogador)

    def proximo(self, boss: Miniboss) -> EstadoMiniboss:
        """Retorna a fase seguinte do ciclo."""
        return Ataque(boss.cfg["ativo"])


class Aviso(EstadoMiniboss):
    """Telegrava o ataque antes de produzir efeitos ofensivos."""


class Ataque(EstadoMiniboss):
    """Executa a mecânica e mantém seus efeitos por um período limitado."""

    chave = "ativo"
    rotulo = "ATAQUE"

    def entrar(self, boss: Miniboss, jogador: Jogador) -> None:
        """Dispara o protocolo específico."""
        boss.estrategia.ativar(boss, jogador)

    def proximo(self, boss: Miniboss) -> EstadoMiniboss:
        """Abre a janela de recuperação."""
        return Recuperacao(boss.cfg["recuperacao"])


class Recuperacao(EstadoMiniboss):
    """Remove efeitos temporários e oferece uma janela de contra-ataque."""

    chave = "recuperacao"
    rotulo = "VULNERÁVEL"

    def entrar(self, boss: Miniboss, jogador: Jogador) -> None:
        """Encerra a mecânica temporária."""
        boss.estrategia.recuperar(boss, jogador)

    def proximo(self, boss: Miniboss) -> EstadoMiniboss:
        """Reinicia o aviso."""
        return Aviso(boss.cfg["aviso"])
