"""Primitivas de tinta, cenários impressos e efeitos reutilizáveis em software."""

import math
import random
from functools import lru_cache

import pygame

from src.infrastructure.graphics.comic_pipeline import gerar_paleta, superficie_alpha
from src.infrastructure.graphics.comic_theme import (
    COMPOSICOES_FUNDO,
    CONTORNO,
    CORES_COMPOSICAO,
    FONTE_COMIC,
    FONTE_SISTEMA,
    FUNDOS,
    LARANJA,
    PAPEL,
    PASSO_HALFTONE,
    SOMBRA,
    TINTA,
    espessura_contorno_sprite,
    opcoes_atuais,
    passo_hachura_sprite,
)
from src.shared.paths import PASTA_FONTES


def poligono_tinta(tela: pygame.Surface, cor: tuple, pontos: list,
                    espessura: int = CONTORNO) -> None:
    """Desenha geometria procedural com três tons e hachuras dentro da face."""
    if len(pontos) < 3:
        return
    largura = max(p[0] for p in pontos) - min(p[0] for p in pontos)
    altura = max(p[1] for p in pontos) - min(p[1] for p in pontos)
    extensao = max(1, int(min(largura, altura)))
    espessura = espessura_contorno_sprite(extensao, espessura)
    passo_hachura = passo_hachura_sprite(extensao)
    sombra, base, luz = gerar_paleta(cor)
    centro = (sum(p[0] for p in pontos) / len(pontos),
              sum(p[1] for p in pontos) / len(pontos))
    pygame.draw.polygon(tela, base, pontos)
    for i, a in enumerate(pontos):
        b = pontos[(i + 1) % len(pontos)]
        face = [centro, a, b]
        escura = (a[0] + b[0]) / 2 > centro[0]
        pygame.draw.polygon(tela, sombra if escura else luz, face)
        if escura and opcoes_atuais().hachuras and passo_hachura:
            passos = max(1, int(math.dist(a, b) / passo_hachura))
            for j in range(1, passos):
                t = j / passos
                inicio = (a[0] + (centro[0] - a[0]) * t,
                          a[1] + (centro[1] - a[1]) * t)
                fim = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                pygame.draw.line(tela, TINTA, inicio, fim)
    pygame.draw.polygon(tela, TINTA, pontos, max(1, espessura))
    # Segunda passada curta simula pressão variável da caneta.
    pygame.draw.line(tela, TINTA, pontos[-1], pontos[0], max(1, espessura + 1))


@lru_cache(maxsize=512)
def disco_tinta(cor: tuple, raio: int, hachuras: bool,
                espessura: int = CONTORNO) -> pygame.Surface:
    """Prepara esfera em três faixas, contorno irregular e hachuras fixas."""
    r = max(1, raio)
    espessura = espessura_contorno_sprite(r * 2, espessura)
    passo_hachura = passo_hachura_sprite(r * 2)
    pad = espessura + 1
    surf = superficie_alpha((2 * (r + pad), 2 * (r + pad)))
    c = r + pad
    sombra, base, luz = gerar_paleta(cor)
    pygame.draw.circle(surf, TINTA, (c, c), r + espessura)
    pygame.draw.circle(surf, sombra, (c, c), r)
    pygame.draw.circle(surf, base, (c - r // 5, c - r // 5), max(1, r * 4 // 5))
    pygame.draw.circle(surf, luz, (c - r // 3, c - r // 3), max(1, r // 3))
    if hachuras and passo_hachura:
        for y in range(-r // 3, r, passo_hachura):
            borda = int(math.sqrt(max(0, r * r - y * y)))
            pygame.draw.line(surf, TINTA, (c + borda // 2, c + y),
                             (c + borda, c + y - 2))
    return surf


def circulo_tinta(tela: pygame.Surface, cor: tuple, centro: tuple,
                   raio: float, espessura: int = CONTORNO) -> None:
    """Compõe uma esfera preparada, sem superfícies temporárias."""
    surf = disco_tinta(tuple(cor[:3]), int(raio), opcoes_atuais().hachuras,
                       espessura)
    tela.blit(surf, surf.get_rect(center=centro))


@lru_cache(maxsize=32)
def textura(tamanho: tuple[int, int], papel: bool, halftone: bool,
            alta: bool = False) -> pygame.Surface:
    """Pré-renderiza papel e retícula com RNG independente do gameplay."""
    surf = superficie_alpha(tamanho)
    w, h = tamanho
    rng = random.Random(813)
    if halftone:
        for y in range(0, h, PASSO_HALFTONE):
            for x in range((y // PASSO_HALFTONE % 2) * 6, w, PASSO_HALFTONE):
                pygame.draw.circle(surf, (*TINTA, 48), (x, y), 1 + (y // 140) % 2)
    if papel:
        for _ in range(w * h // (65 if alta else 120)):
            x, y = rng.randrange(w), rng.randrange(h)
            pygame.draw.line(surf, (*PAPEL, 24), (x, y), (x + rng.randrange(1, 4), y))
    return surf


def _compor_orbital(surf: pygame.Surface, setor: int) -> None:
    """Planeta distante e rotas orbitais finas, com o corredor central livre."""
    w, h = surf.get_size()
    centro = (int(w * .78), int(h * .35))
    raio = int(h * .24)
    pygame.draw.ellipse(surf, CORES_COMPOSICAO[0][0],
                        (centro[0] - raio * 2, centro[1] - 32, raio * 4, 64), 3)
    pygame.draw.circle(surf, CORES_COMPOSICAO[0][1], centro, raio)
    pygame.draw.circle(surf, FUNDOS[setor - 1],
                       (centro[0] + raio // 2, centro[1] - raio // 3), raio)
    for offset in (-65, 25, 88):
        pygame.draw.arc(surf, CORES_COMPOSICAO[0][0],
                        pygame.Rect(60, 70 + offset, w - 120, h - 130), .15, 2.7, 2)


def _compor_vulcanico(surf: pygame.Surface) -> None:
    """Cristas vulcânicas enquadram a área central da dimensão."""
    w, h = surf.get_size()
    cor, detalhe = CORES_COMPOSICAO[1]
    for x0, sign in ((0, 1), (w, -1)):
        pontos = [(x0, h), (x0 + sign * 170, int(h * .68)),
                  (x0 + sign * 105, int(h * .48)),
                  (x0 + sign * 245, int(h * .18)), (x0 + sign * 290, 0)]
        pygame.draw.lines(surf, cor, False, pontos, 5)
        for offset in (32, 72):
            pygame.draw.lines(surf, detalhe, False,
                              [(x + sign * offset, y) for x, y in pontos], 2)


def _compor_oceanico(surf: pygame.Surface) -> None:
    """Ondas em planos baixos e recifes laterais."""
    w, h = surf.get_size()
    escuro, claro = CORES_COMPOSICAO[2]
    for faixa, base_y in enumerate((int(h * .57), int(h * .70), int(h * .83), h)):
        pontos = [(x, base_y + int(math.sin(x * .012 + faixa) * (10 + faixa * 3)))
                  for x in range(-20, w + 24, 24)]
        pygame.draw.aalines(surf, escuro if faixa % 2 else claro, False, pontos)
    for x, altura in ((50, 95), (145, 58), (w - 150, 82), (w - 48, 112)):
        pygame.draw.polygon(surf, escuro, ((x - 35, h), (x, h - altura), (x + 40, h)))
        pygame.draw.line(surf, claro, (x, h - altura), (x + 35, h), 2)


def _compor_cristalino(surf: pygame.Surface) -> None:
    """Cristais verticais enquadram o corredor central."""
    w, h = surf.get_size()
    escuro, claro = CORES_COMPOSICAO[3]
    for x, altura, largura in ((20, 260, 100), (130, 150, 70),
                               (w - 130, 180, 82), (w - 24, 290, 105)):
        pontos = ((x, h - altura), (x + largura // 2, h - 20),
                  (x, h), (x - largura // 2, h - 20))
        pygame.draw.polygon(surf, escuro, pontos)
        pygame.draw.lines(surf, claro, True, pontos, 3)
        pygame.draw.line(surf, (111, 133, 108), pontos[0], pontos[2], 2)


def _compor_fenda(surf: pygame.Surface) -> None:
    """Arcos de uma fenda e linhas interrompidas em profundidades diferentes."""
    w, h = surf.get_size()
    cx, cy = int(w * .72), int(h * .50)
    for raio in (65, 100, 145, 195):
        pygame.draw.arc(surf, CORES_COMPOSICAO[4][0],
                        pygame.Rect(cx - raio, cy - raio // 2, raio * 2, raio),
                        .1, 2.5, 2)
    for indice, y in enumerate(range(35, h, 115)):
        gap = 90 + (indice % 3) * 25
        cor = CORES_COMPOSICAO[4][1]
        pygame.draw.line(surf, cor, (0, y), (w // 2 - gap, y + 18), 2)
        pygame.draw.line(surf, cor, (w // 2 + gap, y - 12), (w, y + 6), 2)


def _compor_divino(surf: pygame.Surface) -> None:
    """Raios largos e anéis altos marcam a dimensão final."""
    w, h = surf.get_size()
    centro = (w // 2, int(h * .12))
    for x in range(-150, w + 200, 180):
        pygame.draw.polygon(surf, (91, 84, 70),
                            (centro, (x, h), (x + 55, h)))
    for raio in (72, 112, 154):
        pygame.draw.circle(surf, CORES_COMPOSICAO[5][0], centro, raio, 2)


_RENDERIZADORES_COMPOSICAO = {
    "orbital": _compor_orbital,
    "vulcanica": _compor_vulcanico,
    "oceanica": _compor_oceanico,
    "cristalina": _compor_cristalino,
    "fenda": _compor_fenda,
    "divina": _compor_divino,
}


@lru_cache(maxsize=24)
def fundo_comic(tamanho: tuple[int, int], setor: int, qualidade: str,
                papel: bool = True, halftone: bool = True) -> pygame.Surface:
    """Cria uma composição exclusiva por dimensão, sem filtro por quadro."""
    w, h = tamanho
    surf = superficie_alpha(tamanho)
    base = FUNDOS[(setor - 1) % len(FUNDOS)]
    surf.fill(base)
    rng = random.Random(913 + setor)
    setor_index = (setor - 1) % len(COMPOSICOES_FUNDO)
    renderizador = _RENDERIZADORES_COMPOSICAO[COMPOSICOES_FUNDO[setor_index]]
    if setor_index == 0:
        renderizador(surf, setor_index + 1)
    else:
        renderizador(surf)
    # Destroços menores e menos numerosos sustentam a sensação de escala.
    for _ in range(18):
        x, y = rng.randrange(w), rng.randrange(h)
        r = rng.randrange(3, max(5, h // 32))
        pts = [(x - r, y), (x - r // 2, y - r), (x + r, y - r // 3),
               (x + r // 2, y + r), (x - r // 3, y + r // 2)]
        pygame.draw.polygon(surf, (45, 44, 45), pts)
        pygame.draw.polygon(surf, (30, 29, 31), pts, 1)
        pygame.draw.line(surf, CORES_COMPOSICAO[setor_index][0], pts[0], pts[1], 1)
    for _ in range(48):
        x, y = rng.randrange(w), rng.randrange(h)
        pygame.draw.line(surf, PAPEL, (x, y), (x, y + 2))
    if qualidade != "BAIXA":
        surf.blit(textura(tamanho, papel, halftone, qualidade == "ALTA"), (0, 0))
    return surf


def desenhar_fundo(tela: pygame.Surface, setor: int = 1) -> None:
    """Compõe o fundo escolhido com um único blit."""
    o = opcoes_atuais()
    tela.blit(fundo_comic(tela.get_size(), setor, o.qualidade, o.papel, o.halftone), (0, 0))


@lru_cache(maxsize=128)
def painel_tinta(tamanho: tuple[int, int], destaque: tuple = LARANJA) -> pygame.Surface:
    """Prepara uma placa angular com margem compatível com painel_glass."""
    w, h = tamanho
    surf = superficie_alpha((w + 24, h + 24))
    corte = min(14, h // 3, w // 3)
    pts = [(12 + corte, 12), (w + 12, 12), (w + 12, h + 12 - corte),
           (w + 12 - corte, h + 12), (12, h + 12), (12, 12 + corte)]
    pygame.draw.polygon(surf, SOMBRA, pts)
    pygame.draw.polygon(surf, TINTA, pts, 5)
    pygame.draw.line(surf, destaque, (12 + corte, 15), (w + 7, 15), 3)
    pygame.draw.line(surf, PAPEL, (16, h + 7), (w // 3, h + 7), 1)
    for x in range(w - 36, w - 8, 7):
        pygame.draw.line(surf, destaque, (x, h + 6), (x + 5, h - 1), 2)
    return surf


@lru_cache(maxsize=32)
def fonte_comic(tamanho: int) -> pygame.font.Font:
    """Carrega fonte livre opcional, com fallback local em negrito e itálico."""
    try:
        return pygame.font.Font(str(PASTA_FONTES / FONTE_COMIC), tamanho)
    except (OSError, pygame.error):
        return pygame.font.SysFont(FONTE_SISTEMA, tamanho, bold=True, italic=True)


@lru_cache(maxsize=512)
def texto_tinta(texto: str, tamanho: int, cor: tuple = PAPEL) -> pygame.Surface:
    """Prepara lettering com contorno; não altera fontes ou superfícies compartilhadas."""
    fonte = fonte_comic(tamanho)
    cor_segura = tuple(max(0, min(255, int(c))) for c in cor[:3])
    base = fonte.render(texto, True, cor_segura).convert_alpha()
    tinta = fonte.render(texto, True, TINTA).convert_alpha()
    surf = superficie_alpha((base.get_width() + 4, base.get_height() + 4))
    for dx, dy in ((0, 2), (4, 2), (2, 0), (2, 4)):
        surf.blit(tinta, (dx, dy))
    surf.blit(base, (2, 2))
    return surf


@lru_cache(maxsize=256)
def burst(raio: int, cor: tuple) -> pygame.Surface:
    """Pré-renderiza uma explosão serrilhada de quadrinhos."""
    r = max(2, raio)
    surf = superficie_alpha((r * 2 + 8, r * 2 + 8))
    c = r + 4
    pontos = []
    for i in range(18):
        a = i * math.tau / 18
        dist = r if i % 2 == 0 else r * .43
        pontos.append((c + math.cos(a) * dist, c + math.sin(a) * dist))
    pygame.draw.polygon(surf, TINTA, pontos)
    internos = [(c + (x - c) * .78, c + (y - c) * .78) for x, y in pontos]
    pygame.draw.polygon(surf, cor, internos)
    pygame.draw.circle(surf, PAPEL, (c, c), max(1, r // 4))
    return surf


def trilha_tinta(tela: pygame.Surface, centro: tuple, velocidade: tuple, cor: tuple) -> None:
    """Desenha duas linhas curtas de velocidade usando somente coordenadas visuais."""
    vx, vy = velocidade
    norma = math.hypot(vx, vy)
    if norma < .1:
        return
    dx, dy = vx / norma, vy / norma
    x, y = centro
    for lado in (-1, 1):
        a = (x - dx * 9 + dy * lado * 4, y - dy * 9 - dx * lado * 4)
        b = (a[0] - dx * 12, a[1] - dy * 12)
        pygame.draw.line(tela, TINTA, a, b, 3)
        pygame.draw.line(tela, cor, a, b, 1)
