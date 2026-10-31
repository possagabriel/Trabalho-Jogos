"""Painéis sóbrios e reutilizáveis para os menus no estilo ORIGINAL."""

from functools import lru_cache

import pygame

FUNDO_SOBRIO = (12, 17, 25)
PAINEL_SOBRIO = (20, 27, 37)
FOCO_SOBRIO = (39, 51, 66)
BORDA_SOBRIA = (58, 70, 85)
TEXTO_SOBRIO = (239, 244, 249)


@lru_cache(maxsize=4)
def veu_menu_sobrio(tamanho: tuple[int, int]) -> pygame.Surface:
    """Atenua o fundo espacial para separar texto e ações sem brilho extra."""
    tela = pygame.Surface(tamanho, pygame.SRCALPHA)
    tela.fill((*FUNDO_SOBRIO, 125))
    return tela


@lru_cache(maxsize=256)
def texto_painel(fonte: pygame.font.Font, texto: str, cor: tuple[int, int, int],
                 largura: int, altura: int) -> pygame.Surface:
    """Cacheia texto ajustado à célula sem modificar a fonte compartilhada."""
    arte = fonte.render(texto, True, cor)
    escala = min(1.0, largura / max(1, arte.get_width()), altura / max(1, arte.get_height()))
    if escala < 1:
        arte = pygame.transform.smoothscale(
            arte, (max(1, round(arte.get_width() * escala)),
                   max(1, round(arte.get_height() * escala))))
    return arte


@lru_cache(maxsize=64)
def painel_original(tamanho: tuple[int, int], fundo: tuple[int, int, int],
                     borda: tuple[int, int, int], *, selecionado: bool = False,
                     raio: int = 12, alpha: int = 240) -> pygame.Surface:
    """Prepara uma superfície plana, escura e com foco sublinhado, sem glow."""
    largura, altura = tamanho
    tela = pygame.Surface(tamanho, pygame.SRCALPHA)
    raio = min(4, raio)
    cor = FOCO_SOBRIO if selecionado else PAINEL_SOBRIO
    pygame.draw.rect(tela, (*cor, alpha), tela.get_rect(), border_radius=raio)
    pygame.draw.rect(tela, (*BORDA_SOBRIA, 155), tela.get_rect(), 1, border_radius=raio)
    if selecionado:
        margem = max(4, min(16, largura // 12))
        pygame.draw.line(tela, (*TEXTO_SOBRIO, 255),
                         (margem, altura - 3), (largura - margem - 1, altura - 3), 2)
    return tela
