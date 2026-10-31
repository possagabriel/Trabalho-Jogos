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
ICONE_DESABILITADO_ORIGINAL = (112, 136, 145)


@lru_cache(maxsize=8)
def plataforma_hangar(tamanho: tuple[int, int]) -> pygame.Surface:
    """Prepara o piso e os anéis do expositor sem superfícies novas por quadro."""
    tela = pygame.Surface(tamanho, pygame.SRCALPHA)
    largura, altura = tamanho
    for proporcao in (.95, .72, .42):
        rect = pygame.Rect(0, 0, round(largura * proporcao), round(altura * proporcao * .5))
        rect.center = (largura // 2, altura * 3 // 4)
        pygame.draw.ellipse(tela, BORDA_ORIGINAL if proporcao == .95 else ACENTO_ORIGINAL,
                            rect, 1)
    return tela


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
                     botao: bool = False, segmentado: bool = True) -> pygame.Surface:
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
    if botao and segmentado and altura >= 44:
        faixa = min(60, round(altura * .85))
        tom = tuple(round(c * .88) for c in cor)
        pygame.draw.polygon(tela, (*tom, alpha),
                            ((corte, 1), (faixa, 1), (faixa, altura - 2),
                             (corte, altura - 2), (1, altura - corte - 1), (1, corte)))
        pygame.draw.line(tela, (*contorno, alpha),
                         (faixa, 8), (faixa, altura - 9), 1)
    pygame.draw.polygon(tela, (*contorno, alpha), pontos, 1)
    detalhe = TEXTO_ATIVO_ORIGINAL if botao and selecionado else ACENTO_ORIGINAL
    pygame.draw.line(tela, (*detalhe, 220), (corte + 5, 2),
                     (min(largura - corte - 2, corte + 52), 2), 2)
    if selecionado:
        pygame.draw.line(tela, (*detalhe, 255), (3, corte), (3, altura - corte - 1), 3)
        if botao and segmentado and altura >= 44:
            x, y = largura - 21, altura // 2
            pygame.draw.lines(tela, (*detalhe, alpha), False,
                               ((x - 4, y - 5), (x + 2, y), (x - 4, y + 5)), 2)
    return tela


def _desenhar_simbolo_hangar(arte: pygame.Surface, indice: str, cor: tuple,
                            espessura: int) -> None:
    """Completa os símbolos de transação e inspeção na superfície em construção."""
    tamanho = arte.get_width()
    centro, raio = tamanho // 2, tamanho * 0.36
    if indice == "comprar":
        pygame.draw.circle(arte, cor, (centro, centro), round(raio), espessura)
        pygame.draw.line(arte, cor, (centro, tamanho * .29), (centro, tamanho * .71), espessura)
        pygame.draw.line(arte, cor, (tamanho * .29, centro), (tamanho * .71, centro), espessura)
    elif indice == "equipar":
        pygame.draw.lines(arte, cor, False, ((tamanho * .18, tamanho * .52),
                                            (tamanho * .4, tamanho * .74),
                                            (tamanho * .82, tamanho * .26)), espessura)
    elif indice == "prévia":
        pygame.draw.ellipse(arte, cor, (tamanho * .08, tamanho * .28,
                                        tamanho * .84, tamanho * .44), espessura)
        pygame.draw.circle(arte, cor, (centro, centro), round(tamanho * .12), espessura)
    else:
        pygame.draw.lines(arte, cor, False, ((tamanho * .46, tamanho * .2),
                                            (tamanho * .16, centro),
                                            (tamanho * .46, tamanho * .8)), espessura)
        pygame.draw.line(arte, cor, (tamanho * .2, centro), (tamanho * .84, centro), espessura)


@lru_cache(maxsize=128)
def icone_menu_original(indice: str, selecionado: bool, tamanho: int, *,
                        desabilitado: bool = False) -> pygame.Surface:
    """Prepara símbolos próprios para jogar, hangar, perfil, opções e saída."""
    arte = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
    cor = (ICONE_DESABILITADO_ORIGINAL if desabilitado else
           TEXTO_ATIVO_ORIGINAL if selecionado else ACENTO_ORIGINAL)
    centro, raio = tamanho // 2, tamanho * 0.36
    espessura = max(1, round(tamanho / 14))
    indice = indice.lstrip("0")
    if indice in ("comprar", "equipar", "prévia", "voltar"):
        _desenhar_simbolo_hangar(arte, indice, cor, espessura)
    elif indice in ("1", "linear"):
        pygame.draw.polygon(arte, cor, ((tamanho * .28, tamanho * .2),
                                       (tamanho * .78, tamanho * .5),
                                       (tamanho * .28, tamanho * .8)), espessura)
    elif indice in ("2", "hangar"):
        pygame.draw.polygon(arte, cor, ((centro, tamanho * .12), (tamanho * .84, tamanho * .83),
                                       (centro, tamanho * .67), (tamanho * .16, tamanho * .83)),
                            espessura)
    elif indice in ("3", "pilotos"):
        pygame.draw.circle(arte, cor, (centro, round(tamanho * .3)), round(tamanho * .16),
                           espessura)
        pygame.draw.arc(arte, cor, (tamanho * .18, tamanho * .48, tamanho * .64, tamanho * .5),
                        0, math.pi, espessura)
    elif indice in ("4", "configuracoes"):
        pontos = tuple((centro + math.cos(i * math.tau / 8) * raio,
                        centro + math.sin(i * math.tau / 8) * raio) for i in range(8))
        pygame.draw.polygon(arte, cor, pontos, espessura)
        pygame.draw.circle(arte, cor, (centro, centro), round(tamanho * .13), espessura)
    elif indice == "recordes":
        for i, altura in enumerate((.25, .5, .7)):
            pygame.draw.rect(arte, cor, (tamanho * (.15 + i * .25), tamanho * (.85 - altura),
                                         tamanho * .16, tamanho * altura), espessura)
    elif indice == "memorias":
        pygame.draw.polygon(arte, cor,
                            ((tamanho * .12, tamanho * .2), (centro, tamanho * .28),
                             (tamanho * .88, tamanho * .2), (tamanho * .88, tamanho * .78),
                             (centro, tamanho * .86), (tamanho * .12, tamanho * .78)), espessura)
        pygame.draw.line(arte, cor, (centro, tamanho * .28), (centro, tamanho * .86), espessura)
    elif indice == "continuar":
        pygame.draw.arc(arte, cor, (tamanho * .15, tamanho * .15, tamanho * .7, tamanho * .7),
                        0, math.pi * 1.7, espessura)
        pygame.draw.line(arte, cor, (centro, tamanho * .3), (centro, centro), espessura)
        pygame.draw.line(arte, cor, (centro, centro), (tamanho * .7, centro), espessura)
    elif indice == "mundo_aberto":
        pygame.draw.circle(arte, cor, (centro, centro), round(raio), espessura)
        pygame.draw.polygon(arte, cor, ((centro, tamanho * .23), (tamanho * .66, tamanho * .69),
                                       (centro, tamanho * .59), (tamanho * .34, tamanho * .69)))
    else:
        pygame.draw.arc(arte, cor, (tamanho * .15, tamanho * .18, tamanho * .7, tamanho * .7),
                        math.pi * .7, math.tau + math.pi * .3, espessura)
        pygame.draw.line(arte, cor, (centro, tamanho * .1), (centro, tamanho * .52), espessura)
    return arte
