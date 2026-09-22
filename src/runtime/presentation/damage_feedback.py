"""Feedback de dano exclusivamente visual, sem sorteios ou regras de combate."""

from typing import Any

import pygame

from src.infrastructure.graphics.comic_render import texto_tinta
from src.infrastructure.graphics.comic_theme import ELEMENTOS, opcoes_atuais
from src.runtime.domain.world.particles import MensagemFlutuante
from src.runtime.infrastructure.graphics.smooth import superficie_com_alpha


class NumeroDano(MensagemFlutuante):
    """Número de dano já aplicado; usa o ciclo de vida das mensagens existentes."""

    def desenhar(self, tela: pygame.Surface) -> None:
        """Compõe o número somente no estilo comic."""
        if self.tempo <= 0 or not opcoes_atuais().ativo:
            return
        surf = texto_tinta(self.texto, 22, tuple(self.cor))
        surf = superficie_com_alpha(surf, int(255 * self.tempo / self.tempo_max))
        tela.blit(surf, surf.get_rect(center=(round(self.x), round(self.y))))


def registrar_impacto(sessao: Any, alvo: Any, proj: Any, vida_antes: float) -> None:
    """Publica apenas a diferença de vida efetivamente aplicada ao alvo.

    Args:
        sessao: Destino das mensagens visuais, sem acesso ao save.
        alvo: Entidade atingida, consultada sem modificações.
        proj: Projétil para identificar a cor elemental.
        vida_antes: Vida registrada imediatamente antes do acerto.
    """
    dano = max(0, vida_antes - alvo.vida)
    if dano <= 0:
        return
    elemento = proj.tipo if proj.tipo in ELEMENTOS else "normal"
    if proj.tipo == "padrao" and proj.dano > 1 + sessao.jogador.bonus_dano:
        elemento = "critico"
    texto = f"{dano:g}" + ("!" if elemento == "critico" else "")
    sessao.mensagens.append(NumeroDano(texto, alvo.x, alvo.y, ELEMENTOS[elemento], tempo=35))
