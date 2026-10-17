"""Animação de troca de dimensão avançada pelo loop principal."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from src.core.constants import ALTURA, LARGURA
from src.runtime.domain.world.particles import SistemaParticulas
from src.runtime.domain.world.scenarios import Cenario

INICIO_FLASH = 24
INICIO_REVELACAO = 46
DURACAO_TRANSICAO = 64


@dataclass
class TransicaoDimensional:
    """Mantém o quadro e desenha as fases do salto dimensional."""

    cenario_anterior: Cenario
    cor: tuple[int, int, int]
    quadro: int = 0

    def atualizar(self, cenario_novo: Cenario, particulas: SistemaParticulas) -> bool:
        """Avança um passo fixo e informa se a animação terminou."""
        self.quadro += 1
        if self.quadro == INICIO_REVELACAO:
            particulas.limpar()
            particulas.espiral_revelacao(LARGURA // 2, ALTURA // 2, self.cor)
        particulas.atualizar()
        cenario = self.cenario_anterior if self.quadro < INICIO_REVELACAO else cenario_novo
        cenario.atualizar()
        return self.quadro >= DURACAO_TRANSICAO

    def desenhar(self, tela: pygame.Surface, cenario_novo: Cenario,
                particulas: SistemaParticulas, superficie_flash: pygame.Surface,
                escala_flash: float) -> None:
        """Renderiza o cenário e o flash usando a superfície já alocada."""
        cenario = self.cenario_anterior if self.quadro < INICIO_REVELACAO else cenario_novo
        cenario.desenhar(tela)
        particulas.desenhar(tela)
        if INICIO_FLASH <= self.quadro < INICIO_REVELACAO:
            alpha = min(255, int((self.quadro - INICIO_FLASH) * 12 * escala_flash))
            if alpha:
                superficie_flash.fill((255, 255, 255))
                superficie_flash.set_alpha(alpha)
                tela.blit(superficie_flash, (0, 0))
