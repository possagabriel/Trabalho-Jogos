"""Tela de escolhas taticas exibida entre dois niveis."""

from __future__ import annotations

import pygame

from src.core.constants import BRANCO, CIANO, DOURADO, LARGURA, RIFT_MAGENTA, VOID_BLACK
from src.infrastructure.ui.layout import Layout
from src.runtime.infrastructure.graphics.smooth import (
    desenhar_cantos,
    desenhar_glow,
    desenhar_painel,
    retangulo_suave,
)
from src.runtime.infrastructure.graphics.fonts import fonte_texto, fonte_titulo


class TelaMelhorias:
    """Apresenta tres melhorias e destaca a opcao navegada."""

    def __init__(self, layout: Layout) -> None:
        self.layout = layout
        self.fonte_titulo = fonte_titulo(42)
        self.fonte_nome = fonte_titulo(25)
        self.fonte_texto = fonte_texto(19)
        self.fonte_tecla = fonte_titulo(18)

    @staticmethod
    def _texto_centralizado(
            tela: pygame.Surface, fonte: pygame.font.Font, texto: str,
            centro: tuple[int, int], cor: tuple[int, int, int]) -> None:
        superficie = fonte.render(texto, True, cor)
        tela.blit(superficie, superficie.get_rect(center=centro))

    def desenhar(self, tela: pygame.Surface, jogo: object) -> None:
        """Desenha o modal sobre o ultimo quadro do campo de batalha."""
        sombra = getattr(jogo, "_tela_sombra")
        sombra.fill((4, 5, 15, 220))
        tela.blit(sombra, (0, 0))
        opcoes = getattr(jogo, "melhorias_oferecidas", [])
        selecionada = int(getattr(jogo, "melhoria_selecionada", 0))
        proximo = int(getattr(jogo, "nivel_pendente", 1))

        self._texto_centralizado(
            tela, self.fonte_titulo, "APRIMORAMENTO TÁTICO",
            (LARGURA // 2, 105), BRANCO,
        )
        self._texto_centralizado(
            tela, self.fonte_texto, f"Escolha um módulo antes do setor {proximo:02d}",
            (LARGURA // 2, 145), CIANO,
        )

        largura, altura, espaco = 310, 300, 28
        inicio = (LARGURA - (largura * 3 + espaco * 2)) // 2
        for indice, melhoria in enumerate(opcoes):
            rect = pygame.Rect(inicio + indice * (largura + espaco), 205, largura, altura)
            ativa = indice == selecionada
            cor = DOURADO if ativa else (72, 82, 125)
            if ativa:
                desenhar_glow(tela, DOURADO, rect.center, rect.w // 2, 0.2)
            desenhar_painel(
                tela, cor, rect, cor_fundo=(13, 17, 36),
                raio_canto=16, alpha=238, glow_raio=14 if ativa else 4,
            )
            desenhar_cantos(tela, cor, rect, tamanho=16, espessura=2)
            badge = pygame.Rect(rect.centerx - 22, rect.y + 30, 44, 34)
            retangulo_suave(tela, cor, badge, 9)
            self._texto_centralizado(
                tela, self.fonte_tecla, str(indice + 1), badge.center, VOID_BLACK,
            )
            self._texto_centralizado(
                tela, self.fonte_nome, melhoria["nome"],
                (rect.centerx, rect.y + 105), BRANCO,
            )
            self._texto_centralizado(
                tela, self.fonte_texto, melhoria["descricao"],
                (rect.centerx, rect.y + 160), CIANO if ativa else (165, 175, 205),
            )
            nivel = melhoria.get("nivel", 0)
            self._texto_centralizado(
                tela, self.fonte_texto, f"NÍVEL ATUAL {nivel}",
                (rect.centerx, rect.bottom - 55), RIFT_MAGENTA,
            )

        self._texto_centralizado(
            tela, self.fonte_texto,
            "← → / A D para navegar   •   ENTER ou 1–3 para instalar",
            (LARGURA // 2, 570), (175, 185, 215),
        )
