"""Console orbital: painéis recortados azul-petróleo com acentos âmbar."""

import math
from functools import lru_cache

import pygame

FUNDO_ORIGINAL = (3, 17, 27)
PAINEL_ORIGINAL = (8, 33, 45)
FOCO_ORIGINAL = (18, 60, 74)
BORDA_ORIGINAL = (58, 111, 125)
TEXTO_ORIGINAL = (231, 243, 243)
ACENTO_ORIGINAL = (240, 180, 84)
TEXTO_ATIVO_ORIGINAL = (14, 32, 42)


@lru_cache(maxsize=4)
def veu_menu_original(tamanho: tuple[int, int]) -> pygame.Surface:
    """Atenua o fundo espacial para separar texto e ações sem brilho extra."""
    tela = pygame.Surface(tamanho, pygame.SRCALPHA)
    tela.fill((*FUNDO_ORIGINAL, 155))
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
                     raio: int = 12, alpha: int = 240,
                     botao: bool = False) -> pygame.Surface:
    """Cacheia um painel recortado; botões ativos recebem preenchimento âmbar."""
    largura, altura = tamanho
    tela = pygame.Surface(tamanho, pygame.SRCALPHA)
    corte = max(3, min(16, raio + 4, largura // 8, altura // 3))
    pontos = ((corte, 0), (largura - corte - 1, 0), (largura - 1, corte),
              (largura - 1, altura - corte - 1), (largura - corte - 1, altura - 1),
              (corte, altura - 1), (0, altura - corte - 1), (0, corte))
    cor = (ACENTO_ORIGINAL if botao and selecionado else
           FOCO_ORIGINAL if selecionado else PAINEL_ORIGINAL)
    contorno = TEXTO_ATIVO_ORIGINAL if botao and selecionado else BORDA_ORIGINAL
    pygame.draw.polygon(tela, (*cor, alpha), pontos)
    pygame.draw.polygon(tela, (*contorno, alpha), pontos, 1)
    detalhe = TEXTO_ATIVO_ORIGINAL if botao and selecionado else ACENTO_ORIGINAL
    pygame.draw.line(tela, (*detalhe, 220), (corte + 5, 2),
                     (min(largura - corte - 2, corte + 52), 2), 2)
    if selecionado:
        pygame.draw.line(tela, (*detalhe, 255), (3, corte), (3, altura - corte - 1), 3)
    return tela


@lru_cache(maxsize=40)
def icone_menu_original(indice: str, selecionado: bool, tamanho: int) -> pygame.Surface:
    """Prepara símbolos próprios para jogar, hangar, perfil, opções e saída."""
    arte = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
    cor = TEXTO_ATIVO_ORIGINAL if selecionado else ACENTO_ORIGINAL
    centro, raio = tamanho // 2, tamanho * 0.36
    espessura = max(1, round(tamanho / 14))
    indice = indice.lstrip("0")
    if indice == "1":
        pygame.draw.polygon(arte, cor, ((tamanho * .28, tamanho * .2),
                                       (tamanho * .78, tamanho * .5),
                                       (tamanho * .28, tamanho * .8)), espessura)
    elif indice == "2":
        pygame.draw.polygon(arte, cor, ((centro, tamanho * .12), (tamanho * .84, tamanho * .83),
                                       (centro, tamanho * .67), (tamanho * .16, tamanho * .83)),
                            espessura)
    elif indice == "3":
        pygame.draw.circle(arte, cor, (centro, round(tamanho * .3)), round(tamanho * .16),
                           espessura)
        pygame.draw.arc(arte, cor, (tamanho * .18, tamanho * .48, tamanho * .64, tamanho * .5),
                        0, math.pi, espessura)
    elif indice == "4":
        pontos = tuple((centro + math.cos(i * math.tau / 8) * raio,
                        centro + math.sin(i * math.tau / 8) * raio) for i in range(8))
        pygame.draw.polygon(arte, cor, pontos, espessura)
        pygame.draw.circle(arte, cor, (centro, centro), round(tamanho * .13), espessura)
    else:
        pygame.draw.arc(arte, cor, (tamanho * .15, tamanho * .18, tamanho * .7, tamanho * .7),
                        math.pi * .7, math.tau + math.pi * .3, espessura)
        pygame.draw.line(arte, cor, (centro, tamanho * .1), (centro, tamanho * .52), espessura)
    return arte
