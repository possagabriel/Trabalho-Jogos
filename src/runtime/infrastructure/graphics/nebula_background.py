"""Nuvens de gás e poeira geradas uma vez para cada setor do mundo."""

import math
import random

import pygame


def _amostra(malha: list[list[float]], x: float, y: float) -> float:
    ix, iy = int(x), int(y)
    fx, fy = x - ix, y - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = malha[iy][ix] * (1 - fx) + malha[iy][ix + 1] * fx
    b = malha[iy + 1][ix] * (1 - fx) + malha[iy + 1][ix + 1] * fx
    return a * (1 - fy) + b * fy


def criar_fundo_nebuloso(tamanho: tuple[int, int], topo: tuple[int, int, int],
                         base: tuple[int, int, int], acento: tuple[int, int, int],
                         semente: int, comic: bool) -> pygame.Surface:
    """Compõe gás turbulento, poeira escura e luz indireta em uma base suave.

    A composição é preparada em baixa resolução e ampliada uma única vez;
    o chamador conserva a superfície resultante em seu cache de setor.
    """
    rng = random.Random(semente)
    largura, altura = max(2, tamanho[0] // 5), max(2, tamanho[1] // 5)
    escalas = (4, 9, 19)
    malhas = [[[rng.random() for _ in range(n + 2)] for _ in range(n + 2)]
              for n in escalas]
    inclinacao = rng.uniform(-0.55, 0.55)
    fase = rng.uniform(0, math.tau)
    luz = tuple(min(170, round(c * 0.7 + 18)) for c in acento)
    tela = pygame.Surface((largura, altura))
    tela.lock()
    for y in range(altura):
        v = y / max(1, altura - 1)
        for x in range(largura):
            u = x / max(1, largura - 1)
            amostras = [_amostra(malha, u * n, v * n)
                        for malha, n in zip(malhas, escalas)]
            ruido = amostras[0] * 0.54 + amostras[1] * 0.3 + amostras[2] * 0.16
            faixa = v - (0.46 + (u - 0.5) * inclinacao
                         + math.sin(u * 4 + fase) * 0.13 + (ruido - 0.5) * 0.35)
            nuvem = math.exp(-(faixa / 0.22) ** 2) * (0.3 + ruido * 0.9)
            poeira = max(0.15, min(1.0, abs(amostras[1] - 0.48) * 6))
            nuvem *= 0.35 + poeira * 0.65
            periferia = min(1.0, math.hypot((u - 0.5) * 1.4, (v - 0.5) * 1.7))
            exposicao = 0.7 + periferia * 0.3
            if comic:
                nuvem = round(nuvem * 7) / 7
            cor = tuple(min(125, round((a * (1 - v) + b * v) * 0.55
                                       + c * (0.06 + nuvem * 0.68)) * exposicao)
                        for a, b, c in zip(topo, base, luz))
            tela.set_at((x, y), tuple(round(c) for c in cor))
    tela.unlock()
    return pygame.transform.smoothscale(tela, tamanho)


def desenhar_planeta(tela: pygame.Surface, centro: tuple[int, int], raio: int,
                     cor: tuple[int, int, int], *, rings: bool = False,
                     craters: bool = False) -> None:
    """Desenha um planeta distante com volume, terminador e atmosfera discreta."""
    x, y = centro
    luz = tuple(min(210, round(c * 1.1 + 20)) for c in cor)
    if rings:
        pygame.draw.ellipse(tela, tuple(round(c * 0.65) for c in luz),
                            (x - raio * 2, y - raio // 3, raio * 4, raio * 2 // 3), 3)
    largura, altura = tela.get_size()
    tela.lock()
    for dy in range(-raio, raio + 1):
        for dx in range(-raio, raio + 1):
            r2 = (dx * dx + dy * dy) / (raio * raio)
            if r2 > 1 or not (0 <= x + dx < largura and 0 <= y + dy < altura):
                continue
            nx, ny = dx / raio, dy / raio
            z = math.sqrt(max(0.0, 1 - r2))
            difusa = max(0.0, -nx * 0.62 - ny * 0.42 + z * 0.5)
            textura = 0.94 + 0.06 * math.sin(ny * 37 + math.sin(nx * 14) * 0.8)
            if craters:
                textura *= 0.92 + 0.08 * math.sin(nx * 31 + ny * 17) ** 2
            atmosfera = max(0.0, (r2 - 0.9) / 0.1) * max(0.0, -nx + 0.3) * 0.25
            pixel = tuple(min(180, round(c * (0.08 + difusa * 0.65) * textura + brilho * atmosfera))
                          for c, brilho in zip(cor, luz))
            tela.set_at((x + dx, y + dy), pixel)
    tela.unlock()
    if rings:
        pygame.draw.arc(tela, tuple(round(c * 0.65) for c in luz),
                        (x - raio * 2, y - raio // 3, raio * 4, raio * 2 // 3),
                        math.pi, math.tau, 3)
