"""Artes dos guardiões novos, energia de fase e avisos sem mutar o combate."""

from __future__ import annotations

import math
from functools import lru_cache
from typing import TYPE_CHECKING

import pygame

from src.core.constants import BRANCO
from src.runtime.infrastructure.assets import carregar_imagem_alpha
from src.runtime.infrastructure.graphics.smooth import desenhar_circulo, desenhar_glow, linha_suave

if TYPE_CHECKING:
    from src.runtime.domain.entities.bosses import Boss

ARQUIVOS = {"PRISMA": "prisma", "ORACULO": "oraculo", "OBELISCO": "obelisco"}


@lru_cache(maxsize=12)
def _base(nome: str, diametro: int) -> pygame.Surface | None:
    caminho = ARQUIVOS.get(nome)
    if caminho is None:
        return None
    arte = carregar_imagem_alpha(f"bosses/{caminho}.png")
    if arte is None:
        return None
    area = arte.get_bounding_rect()
    if not area.width or not area.height:
        return None
    escala = diametro / max(area.size)
    return pygame.transform.smoothscale(arte.subsurface(area), (
        max(1, round(area.width * escala)), max(1, round(area.height * escala))))


@lru_cache(maxsize=192)
def quadro_boss(nome: str, diametro: int, indice: int) -> pygame.Surface | None:
    """Obtém uma orientação em cache sem alterar a arte ou a área de colisão.

    Args:
        nome: Nome do guardião no catálogo.
        diametro: Maior lado da arte de referência.
        indice: Orientação quantizada entre zero e 47.
    """
    base = _base(nome, diametro)
    if base is None:
        return None
    if indice % 48 == 0:
        return base
    return pygame.transform.rotozoom(base, -(indice % 48) * 7.5, 1)


def desenhar_guardiao(tela: pygame.Surface, boss: Boss, reduzido: bool) -> bool:
    """Desenha identidade, fase e direção das salvas; retorna se há arte disponível."""
    indice = 0 if reduzido else round(math.degrees(boss.angulo) / 7.5) % 48
    arte = quadro_boss(boss.nome, round(boss.raio * 2), indice)
    if arte is None:
        return False
    centro = (round(boss.x), round(boss.y))
    fase = boss.fase_atual
    desenhar_glow(tela, boss.cor, centro, boss.raio * 1.45, 0.22 + fase * 0.04)
    if fase >= 2:
        desenhar_circulo(tela, boss.cor, centro, boss.raio + 12, 1, brilho=0.4)
    if fase == 3:
        desenhar_circulo(tela, BRANCO, centro, boss.raio + 18, 1, brilho=0.2)
    # As direções permanecem visíveis também com efeitos reduzidos.
    if boss.aviso_ataques and boss.alvo_ataque is not None:
        mira = math.atan2(boss.alvo_ataque[1] - boss.y, boss.alvo_ataque[0] - boss.x)
        for nome in boss.aviso_ataques:
            for angulo in boss.angulos_ataque_especial(nome, mira):
                inicio = (boss.x + math.cos(angulo) * boss.raio,
                          boss.y + math.sin(angulo) * boss.raio)
                fim = (boss.x + math.cos(angulo) * 270,
                       boss.y + math.sin(angulo) * 270)
                linha_suave(tela, boss.cor, inicio, fim, 1, brilho=0.35)
                desenhar_circulo(tela, BRANCO, fim, 3, 1, brilho=0.3)
    tela.blit(arte, arte.get_rect(center=centro))
    # Núcleos orbitais indicam a fase por quantidade, além da cor.
    for i in range(fase):
        angulo = -math.pi / 2 + i * math.tau / fase
        if not reduzido:
            angulo += boss.t / 120
        ponto = (boss.x + math.cos(angulo) * (boss.raio + 10),
                 boss.y + math.sin(angulo) * (boss.raio + 10))
        desenhar_circulo(tela, boss.cor, ponto, 4, brilho=0.35)
    return True
