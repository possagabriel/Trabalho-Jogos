"""Overlay F3 de métricas e hitboxes, separado da lógica de combate."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.core.constants import QUANTUM_CYAN, VERDE, VERMELHO, VOID_BLACK
from src.runtime.infrastructure.graphics.fonts import fonte_texto

if TYPE_CHECKING:
    from src.runtime.application.core import Jogo


class OverlayDebug:
    """Mostra métricas por glifos cacheados e contornos de colisão."""

    def __init__(self) -> None:
        self._fonte = fonte_texto(18)
        self._glifos: dict[str, pygame.Surface] = {}
        self._fundo = pygame.Surface((760, 408), pygame.SRCALPHA)
        self._fundo.fill((*VOID_BLACK, 215))

    def desenhar(self, tela: pygame.Surface, jogo: Jogo, mira: tuple[int, int] | None) -> None:
        """Desenha desempenho e avanço sem criar superfícies por quadro."""
        tela.blit(self._fundo, (12, 12))
        avanco = jogo.avanco_controller.modelo
        fundo = getattr(jogo.cenario, "parallax", None)
        progresso_nivel = jogo.progressao_controller.progresso_visual.valor
        particulas = len(jogo.particulas.particulas)
        if fundo is not None:
            particulas += fundo.particulas_ativas
        narrativa = jogo.cutscene_controller.sequenciador
        cena_id = narrativa.cena.id if narrativa.cena else "--"
        vistas = jogo.progresso.cenas_vistas
        flags = ", ".join(vistas[-2:]) or "--"
        profile = jogo.profile_service.active
        linhas = (
            f"PERFIL: {profile.name} [{profile.id[:8]}]" if profile else "PERFIL: --",
            f"SALVO: {jogo.profile_service.last_save or '--'} | "
            f"PENDENTE: {'SIM' if jogo.profile_service.dirty else 'NÃO'}",
            f"FPS: {jogo.fps_atual:.0f}",
            f"AVANÇO: {avanco.estado.value}",
            f"VELOCIDADE: {avanco.velocidade:.1f} px/s",
            f"CAMADAS: {fundo.numero_camadas if fundo else 0}",
            f"PARTÍCULAS: {particulas}",
            f"PERCURSO: {progresso_nivel * 100:.0f}% | EVOLUÇÃO: "
            f"{fundo.fator_evolucao:.2f}" if fundo else "PERCURSO: --",
            f"MARCO ATUAL: {fundo.marco_atual}" if fundo else "MARCO ATUAL: --",
            f"PRÓXIMOS: {fundo.proximos_marcos}" if fundo else "PRÓXIMOS: --",
            f"SEMENTE: {jogo.avanco_semente if hasattr(jogo, 'avanco_semente') else '--'}",
            f"MIRA: {mira[0]}, {mira[1]}" if mira else "MIRA: --",
            f"ENTIDADES: {len(jogo.inimigos) + int(bool(jogo.boss)) + int(bool(jogo.miniboss))}",
            f"CENA: {cena_id} / PASSO: {narrativa.indice if narrativa.ativo else '--'}",
            f"CENAS VISTAS: {len(vistas)} | F8: SELETOR",
            f"FLAGS: {flags}",
        )
        for indice, linha in enumerate(linhas):
            x, y = 22, 20 + indice * 21
            for caractere in linha:
                if caractere not in self._glifos:
                    self._glifos[caractere] = self._fonte.render(caractere, True, QUANTUM_CYAN)
                glifo = self._glifos[caractere]
                tela.blit(glifo, (x, y))
                x += glifo.get_width()
        pygame.draw.rect(tela, VERDE, jogo.jogador.rect, 1)
        for inimigo in jogo.inimigos:
            pygame.draw.rect(tela, VERMELHO, inimigo.rect, 1)
        for entidade in (jogo.boss, jogo.miniboss):
            if entidade is not None:
                pygame.draw.rect(tela, VERMELHO, entidade.rect, 1)
        for proj in jogo.projeteis:
            pygame.draw.rect(tela, QUANTUM_CYAN, proj.rect, 1)
