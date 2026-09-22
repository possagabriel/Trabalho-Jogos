"""Sete cascos corporativos; cada classe fornece sua estratégia."""

from src.runtime.domain.entities.minibosses.base import Miniboss
from src.runtime.domain.entities.minibosses.registry import registrar
from src.runtime.domain.entities.minibosses.strategies import (
    CicloBlindado,
    Emboscada,
    EscudoNuclear,
    Espelho,
    Estrategia,
    Inversao,
    Invocacao,
    Quarentena,
)


@registrar("bastiao")
class Bastiao(Miniboss):
    """Firewall da corporação com dois núcleos de autorização."""

    def criar_estrategia(self) -> Estrategia:
        """Fornece a defesa nuclear."""
        return EscudoNuclear(self.cfg["vida_nucleo"])


@registrar("espectro")
class Espectro(Miniboss):
    """Invasor de canais que salta para trás do casco ocupado."""

    def criar_estrategia(self) -> Estrategia:
        """Fornece teleporte e emboscada."""
        return Emboscada()


@registrar("matriz")
class Matriz(Miniboss):
    """Impressora de cópias de consciências humanas."""

    def criar_estrategia(self) -> Estrategia:
        """Fornece invocação limitada."""
        return Invocacao()


@registrar("censor")
class Censor(Miniboss):
    """Protocolo que interfere no vínculo entre IA e casco."""

    def criar_estrategia(self) -> Estrategia:
        """Fornece inversão temporária."""
        return Inversao()


@registrar("cartografo")
class Cartografo(Miniboss):
    """Isola regiões da dimensão como memória contaminada."""

    def criar_estrategia(self) -> Estrategia:
        """Fornece zonas de quarentena."""
        return Quarentena()


@registrar("eco")
class Eco(Miniboss):
    """Cópia defeituosa que aprende observando os disparos da IA."""

    def criar_estrategia(self) -> Estrategia:
        """Fornece cópia de padrões."""
        return Espelho()


@registrar("cronista")
class Cronista(Miniboss):
    """Sincronizador de consciências com ciclos de blindagem."""

    def criar_estrategia(self) -> Estrategia:
        """Fornece fases de invulnerabilidade."""
        return CicloBlindado()
