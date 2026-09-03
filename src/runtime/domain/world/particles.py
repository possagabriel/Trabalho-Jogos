"""Sistema de particulas e mensagens flutuantes."""

from __future__ import annotations

import math
import random
from typing import TypeAlias

import pygame

from src.runtime.infrastructure.graphics.cel_shading import escurecer_cor
from src.core.constants import BRANCO, CIANO, DOURADO, LARANJA, ROXO, VERMELHO
from src.runtime.infrastructure.graphics.smooth import desenhar_circulo, luz_radial

_CACHE = {}
_CACHE_ALPHA = {}
_LIMITE_DESENHO = 320

Cor: TypeAlias = tuple[int, int, int]
Velocidade: TypeAlias = tuple[float, float]


def _superficie_cor(cor, raio):
    """Cacheia superficies circulares de cor unica para performance."""
    chave = (cor, raio)
    if chave not in _CACHE:
        surf = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
        desenhar_circulo(surf, cor + (255,), (raio, raio), raio)
        _CACHE[chave] = surf
    return _CACHE[chave]


def _superficie_alfa(chave, superficie, alfa):
    """Retorna uma variante opaca cacheada sem copiar a cada particula.

    A opacidade e quantizada em 16 niveis. Isso preserva o fade visual e
    elimina ate tres ``Surface.copy`` por particula em cada quadro.
    """
    nivel = max(0, min(15, int(alfa) * 15 // 255))
    chave_cache = (chave, nivel)
    if chave_cache not in _CACHE_ALPHA:
        variante = superficie.copy()
        variante.set_alpha(nivel * 17)
        _CACHE_ALPHA[chave_cache] = variante
    return _CACHE_ALPHA[chave_cache]


class Particula:
    def __init__(self, x: float, y: float, cor: Cor, vel: Velocidade,
                 tamanho: float, vida: int, gravidade: float = 0.0,
                 arrasto: float = 0.98) -> None:
        self.x, self.y = x, y
        self.vx, self.vy = vel
        self.cor = cor
        self.tamanho = tamanho
        self.vida = vida
        self.vida_max = vida
        self.gravidade = gravidade
        self.arrasto = arrasto

    def atualizar(self) -> None:
        self.vx *= self.arrasto
        self.vy *= self.arrasto
        self.vy += self.gravidade
        self.x += self.vx
        self.y += self.vy
        self.vida -= 1

    def desenhar(self, tela: pygame.Surface) -> None:
        if self.vida <= 0:
            return
        alfa = int(255 * self.vida / self.vida_max)
        tam = max(1, int(self.tamanho))
        raio_glow = max(2, tam * 2)
        glow = _superficie_alfa(
            ("glow", self.cor, raio_glow),
            luz_radial(self.cor, raio_glow, 0.6), int(alfa * 0.7))
        gx = int(self.x) - glow.get_width() // 2
        gy = int(self.y) - glow.get_height() // 2
        tela.blit(glow, (gx, gy))
        if tam >= 3:
            contorno = _superficie_alfa(
                ("contorno", tam + 1), _superficie_cor((0, 0, 0), tam + 1),
                int(alfa * 0.8))
            tela.blit(contorno, (int(self.x - tam - 1), int(self.y - tam - 1)))
        surf = _superficie_alfa(("cor", self.cor, tam),
                                _superficie_cor(self.cor, tam), alfa)
        tela.blit(surf, (int(self.x - tam), int(self.y - tam)))


class SistemaParticulas:
    """Coletanea de efeitos de particulas usados pelo jogo."""

    def __init__(self) -> None:
        self.particulas: list[Particula] = []

    def explosao(self, x: float, y: float, cor: Cor, qtd: int = 20,
                 forca: float = 6.0, gravidade: float = 0.0) -> None:
        for _ in range(qtd):
            ang = random.uniform(0, math.tau)
            v = random.uniform(1, forca)
            self.particulas.append(
                Particula(x, y, cor,
                          (math.cos(ang) * v, math.sin(ang) * v),
                          random.randint(2, 5), random.randint(15, 35),
                          gravidade))

    def espiral(self, x: float, y: float, cor: Cor, qtd: int) -> None:
        for i in range(qtd):
            frac = i / qtd
            ang = frac * math.tau * 2
            raio = frac * 45
            px = x + math.cos(ang) * raio
            py = y + math.sin(ang) * raio
            vx = math.cos(ang) * 3
            vy = math.sin(ang) * 3
            self.particulas.append(
                Particula(px, py, cor, (vx, vy), random.randint(2, 4), 40))

    def estrela(self, x: float, y: float, cor: Cor, qtd: int) -> None:
        for i in range(qtd):
            ponta = i % 5
            ang = ponta * math.tau / 5 - math.pi / 2
            raio = random.uniform(5, 60)
            px = x + math.cos(ang) * raio
            py = y + math.sin(ang) * raio
            self.particulas.append(
                Particula(px, py, cor,
                          (math.cos(ang) * 2, math.sin(ang) * 2),
                          random.randint(2, 5), random.randint(25, 45)))

    def pulsacao(self, x: float, y: float, cor: Cor, qtd: int) -> None:
        for _ in range(qtd):
            ang = random.uniform(0, math.tau)
            v = random.uniform(4, 8)
            self.particulas.append(
                Particula(x, y, cor, (math.cos(ang) * v, math.sin(ang) * v),
                          random.randint(3, 6), random.randint(10, 22)))

    def mega(self, x: float, y: float) -> None:
        cores = [BRANCO, CIANO, VERMELHO, LARANJA, ROXO, DOURADO]
        for _ in range(100):
            ang = random.uniform(0, math.tau)
            v = random.uniform(2, 10)
            cor = random.choice(cores)
            self.particulas.append(
                Particula(x, y, cor, (math.cos(ang) * v, math.sin(ang) * v),
                          random.randint(2, 6), random.randint(25, 55)))

    def explosao_dupla(self, x: float, y: float) -> None:
        self.explosao(x, y, LARANJA, 35, 7)
        self.explosao(x, y, VERMELHO, 25, 5)

    def faiscas(self, x: float, y: float, cor: Cor, qtd: int = 6,
                forca: float = 4.0) -> None:
        """Faiscas curtas de impacto ao acertar um alvo."""
        for _ in range(qtd):
            ang = random.uniform(0, math.tau)
            v = random.uniform(1.5, forca)
            self.particulas.append(
                Particula(x, y, cor, (math.cos(ang) * v, math.sin(ang) * v),
                          random.randint(1, 2), random.randint(5, 13)))

    def rastro(self, x: float, y: float, cor: Cor, forca: float = 1.5) -> None:
        self.particulas.append(
            Particula(x + random.uniform(-2, 2), y + random.uniform(-2, 2),
                      cor, (random.uniform(-forca, forca),
                            random.uniform(-forca, forca)),
                      random.randint(1, 3), random.randint(8, 18)))

    def chamas(self, x: float, y: float, cor: Cor, qtd: int = 2) -> None:
        """Particulas de chama subindo (cenario flamejante / skins)."""
        for _ in range(qtd):
            self.particulas.append(
                Particula(x + random.uniform(-3, 3), y,
                          random.choice([cor, LARANJA, DOURADO]),
                          (random.uniform(-0.5, 0.5),
                           random.uniform(-2.5, -1.0)),
                          random.randint(2, 5), random.randint(15, 30)))

    def bolhas(self, x: float, y: float, cor: Cor, qtd: int = 1) -> None:
        """Particulas de bolha subindo lentamente (Oceano Cosmico)."""
        for _ in range(qtd):
            self.particulas.append(
                Particula(x + random.uniform(-2, 2), y, cor,
                          (random.uniform(-0.3, 0.3),
                           random.uniform(-1.2, -0.5)),
                          random.randint(2, 5), random.randint(40, 90),
                          arrasto=0.99))

    def cristais(self, x: float, y: float, cor: Cor, qtd: int = 1) -> None:
        """Particulas de cristal caindo lentamente (Floresta de Cristais)."""
        for _ in range(qtd):
            self.particulas.append(
                Particula(x + random.uniform(-2, 2), y, cor,
                          (random.uniform(-0.4, 0.4),
                           random.uniform(0.8, 1.5)),
                          random.randint(1, 3), random.randint(40, 90),
                          arrasto=0.99))

    def relampago(self, x: float, y: float, cor: Cor) -> None:
        """Raio eletrico que se propaga a partir de um ponto."""
        pontos = [(x, y)]
        px, py = x, y
        for _ in range(random.randint(4, 7)):
            px += random.uniform(-25, 25)
            py += random.randint(20, 40)
            pontos.append((px, py))
        for i in range(len(pontos) - 1):
            a, b = pontos[i], pontos[i + 1]
            qtd = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 6))
            for _ in range(qtd):
                t = random.random()
                ex = a[0] + (b[0] - a[0]) * t
                ey = a[1] + (b[1] - a[1]) * t
                self.particulas.append(
                    Particula(ex, ey, cor,
                              (random.uniform(-0.4, 0.4),
                               random.uniform(-0.4, 0.4)),
                              random.randint(1, 2), random.randint(8, 16)))

    def buraco_negro(self, x: float, y: float) -> None:
        """Espiral de particulas girando em torno de um ponto."""
        for i in range(14):
            ang = random.uniform(0, math.tau)
            self.particulas.append(
                Particula(x + math.cos(ang) * 16, y + math.sin(ang) * 16,
                          (150, 80, 220),
                          (-math.sin(ang) * 1.5, math.cos(ang) * 1.5),
                          random.randint(1, 3), random.randint(12, 30)))

    def salto_dimensional(self, x: float, y: float, cor: Cor) -> None:
        """Espiral de particulas usada na transicao de cenarios."""
        for i in range(30):
            frac = i / 30
            ang = frac * math.tau * 3
            raio = frac * 260
            px = x + math.cos(ang) * raio
            py = y + math.sin(ang) * raio
            self.particulas.append(
                Particula(px, py, cor,
                          (math.cos(ang) * 2.2, math.sin(ang) * 2.2),
                          random.randint(2, 5), random.randint(30, 60)))

    def espiral_revelacao(self, x: float, y: float, cor: Cor) -> None:
        """Revelacao com particulas nas cores do novo cenario."""
        for i in range(50):
            px = random.uniform(0, 900)
            py = random.uniform(0, 700)
            self.particulas.append(
                Particula(px, py, cor,
                          (random.uniform(-1, 1), random.uniform(-1, 1)),
                          random.randint(3, 8), random.randint(20, 50)))

    def atualizar(self) -> None:
        for p in self.particulas:
            p.atualizar()
        self.particulas = [p for p in self.particulas if p.vida > 0]

    def desenhar(self, tela: pygame.Surface) -> None:
        total = len(self.particulas)
        passo = max(1, math.ceil(total / _LIMITE_DESENHO))
        for p in self.particulas[::passo]:
            p.desenhar(tela)

    def limpar(self) -> None:
        self.particulas.clear()


class MensagemFlutuante:
    def __init__(self, texto: str, x: float, y: float, cor: Cor = BRANCO,
                 tempo: int = 70, fonte: pygame.font.Font | None = None) -> None:
        self.texto = texto
        self.x, self.y = x, y
        self.cor = cor
        self.tempo = tempo
        self.tempo_max = tempo
        self._fonte = fonte or pygame.font.Font(None, 26)

    def atualizar(self) -> None:
        self.y -= 1.0
        self.tempo -= 1

    @property
    def viva(self) -> bool:
        return self.tempo > 0

    def desenhar(self, tela: pygame.Surface) -> None:
        if self.tempo <= 0:
            return
        from src.runtime.infrastructure.graphics.smooth import texto_suave
        superficie = texto_suave(self._fonte, self.texto, self.cor,
                                 glow_cor=self.cor, glow_raio=3)
        superficie.set_alpha(int(255 * self.tempo / self.tempo_max))
        tela.blit(superficie, superficie.get_rect(center=(int(self.x),
                                                          int(self.y))))
