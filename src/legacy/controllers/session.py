"""Contrato de estado que o controlador de combate precisa durante a partida."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.legacy.domain.entities.bosses import Boss
from src.legacy.infrastructure.graphics.cel_shading import TextoAcao
from src.core.constants import EstadoJogo
from src.legacy.domain.entities.enemies import Inimigo
from src.legacy.domain.world.particles import MensagemFlutuante, SistemaParticulas
from src.legacy.domain.entities.player import Jogador
from src.legacy.domain.entities.powerups import PowerUp
from src.legacy.infrastructure.persistence.save_system import SistemaProgressao
from src.legacy.infrastructure.audio.sounds import Sons
from src.legacy.domain.entities.weapons import Projetil


@runtime_checkable
class SessaoCombate(Protocol):
    """Estado e operacoes expostos ao :class:`ControladorCombate`.

    O contrato evita que o controlador conheca ``Jogo`` ou seus detalhes de
    implementacao. Adaptadores, testes e uma futura sessao do novo nucleo
    podem fornecer essa mesma superficie minima.
    """

    estado: EstadoJogo
    jogador: Jogador
    inimigos: list[Inimigo]
    boss: Boss | None
    projeteis: list[Projetil]
    powerups: list[PowerUp]
    mensagens: list[MensagemFlutuante]
    textos_acao: list[TextoAcao]
    especial: float
    flash: int
    inimigos_abates: int
    bosses_abates: int
    sons: Sons
    particulas: SistemaParticulas
    progresso: SistemaProgressao

    def adicionar_trauma(self, quantidade: float) -> None:
        """Acrescenta tremor de tela ao feedback de combate."""

    def congelar(self, quadros: int) -> None:
        """Solicita uma pausa curta no mundo para reforcar um impacto."""

    def desbloquear_skin(self, skin_id: str) -> bool:
        """Registra e persiste o desbloqueio de uma skin rara."""
