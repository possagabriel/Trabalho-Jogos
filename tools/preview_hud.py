#!/usr/bin/env python3
"""Demonstracao do HUD profissional do INCARNATE.

Renderiza o ``HudJogo`` em 1920x1080 sobre um fundo neutro escuro, com todos
os componentes visiveis e animados (vida, escudo, energia, boost, especial,
combo, abates, arma e barra de boss). Salva ``images/preview_hud.png``.

Uso:
    python3 preview_hud.py            # abre uma janela interativa
    python3 preview_hud.py --save     # salva o frame demonstrativo em PNG
"""

import os
import sys

if "--save" in sys.argv:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import math
import time
from types import SimpleNamespace

import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.assets import PASTA_IMAGENS
from game.config import VOID_BLACK
from game.fonts import fonte_titulo
from game.hud import HudJogo
from game.layout import Layout
from game.player import Jogador
from game.weapons import ARMARIA

TAMANHO = (1920, 1080)


def _fundo_neutro():
    """Fundo cinza-azulado muito escuro com leve vinheta central."""
    surf = pygame.Surface(TAMANHO)
    surf.fill((10, 12, 20))
    cx, cy = TAMANHO[0] // 2, TAMANHO[1] // 2
    for i in range(90, 0, -1):
        cor = tuple(int(c * (0.10 + 0.55 * (i / 90) ** 2)) for c in (30, 36, 70))
        pygame.draw.circle(surf, cor, (cx, cy), int(900 * i / 90), 2)
    return surf


class Demonstracao:
    """Objeto 'jogo' minimo (duck typing) consumido pelo HUD."""

    def __init__(self):
        self.jogador = Jogador(nome="PLAYER 01")
        self.jogador.max_vida = 8
        self.jogador.arma_atual = 0
        self.cenario = SimpleNamespace(id=3, nome="DEEP SPACE")
        self.recordes = [{"pontos": 134_870}]
        self.inimigos_abates = 42
        self.fila_onda = [1, 1, 1, 1, 1, 1]
        self.inimigos = []
        self.boss = SimpleNamespace(nome="VOID GUARDIAN", vida=210,
                                    vida_max=280)
        self.boost = 0.85
        self.especial = 1.0
        self.energia = 62.0

    def _atualizar(self, t):
        jog = self.jogador
        jog.vida = max(1, min(8, 5 + 3 * math.sin(t * 0.55)))
        jog.escudo = math.sin(t * 1.15) > -0.4
        jog.pontuacao = int(48_000 + t * 320 + 900 * math.sin(t * 0.3))
        jog.combo.combo_atual = int(1 + 8 * max(0.0, math.sin(t * 0.45)))
        jog.arma_atual = int(t / 1.6) % len(ARMARIA)
        self.boost = max(0.06, min(1.0, 0.5 + 0.5 * math.sin(t * 0.9)))
        self.especial = min(1.0, (t % 7) / 6.0)
        self.energia = max(0.0, min(100.0, 50 + 50 * math.sin(t * 0.7)))
        self.inimigos_abates = 42 + int(t * 3.2)
        with_boss = (t % 12) < 9
        self.boss_mostrado = with_boss
        if not with_boss:
            self.boss = None
        else:
            if self.boss is None:
                self.boss = SimpleNamespace(nome="VOID GUARDIAN", vida=210,
                                            vida_max=280)
            self.boss.vida = max(1, int(self.boss.vida_max *
                                        (0.2 + 0.8 * abs(math.cos(t * 0.4)))))


def _rodar(salvar=False):
    pygame.init()
    tela = pygame.display.set_mode(TAMANHO, pygame.SCALED)
    pygame.display.set_caption("INCARNATE - HUD")
    fundo = _fundo_neutro()
    layout = Layout(TAMANHO[0], TAMANHO[1])
    hud = HudJogo(layout)
    demo = Demonstracao()
    relogio = pygame.time.Clock()
    t0 = time.time()
    rodando = True
    alvo = 6.4 if salvar else 0.0
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                rodando = False
        t = (time.time() - t0) % 12
        demo._atualizar(t)
        demo.boss = demo.boss if demo.boss_mostrado else None
        tela.blit(fundo, (0, 0))
        hud.desenhar(tela, demo, tempo=t)
        if salvar and t >= alvo:
            pygame.image.save(tela, os.path.join(PASTA_IMAGENS, "preview_hud.png"))
            rodando = False
        elif not salvar:
            pygame.display.flip()
            relogio.tick(60)
    pygame.quit()
    print("images/preview_hud.png salvo." if salvar else "preview encerrado.")


if __name__ == "__main__":
    _rodar(salvar="--save" in sys.argv)