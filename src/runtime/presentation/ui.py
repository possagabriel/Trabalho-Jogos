"""Interface do usuario: botoes, paineis e auxiliares de desenho.

Estilo visual unico: neon-glass com cantos em L (brackets) e bordas com glow.
Todas as cores de destaque vem do tema ativo (NEON/AURORA/MAGMA). O
posicionamento usa o sistema de layout responsivo (``game.layout``).
"""

import math

import pygame

from src.core.constants import BRANCO, LARGURA
from src.runtime.infrastructure.graphics.fonts import fonte_texto, fonte_titulo
from src.runtime.infrastructure.graphics.smooth import barra_suave, desenhar_cantos, desenhar_circulo, \
    desenhar_glow, desenhar_painel, desenhar_texto_suave, retangulo_suave
from src.infrastructure.graphics.theme import cor_tema


def cor_primaria():
    return cor_tema(chave="primaria")


def cor_secundaria():
    return cor_tema(chave="secundaria")


def cor_fundo_painel():
    return cor_tema(chave="fundo_painel")


def cor_borda_forte():
    return cor_tema(chave="borda_forte")


class BotaoNeon:
    """Botao com hover, nas duas variantes visuais do jogo.

    - Com ``cor``/``cor_hover`` explicitos: estilo solido usado nas sub-telas
      do menu (painel arredondado + borda).
    - Sem cores explicitas: estilo glass com as cores do tema ativo.
    """

    def __init__(self, texto, rect, cor=None, cor_hover=None):
        self.texto = texto
        self.rect = pygame.Rect(rect)
        self.cor = cor
        self.cor_hover = cor_hover
        self.hover = False

    def atualizar(self, mouse_pos):
        self.hover = self.rect.collidepoint(mouse_pos)

    def desenhar(self, tela, fonte):
        if self.cor is not None:
            self._desenhar_solido(tela, fonte)
        else:
            self._desenhar_glass(tela, fonte)

    def _desenhar_solido(self, tela, fonte):
        cor = self.cor_hover if self.hover else self.cor
        borda = BRANCO if self.hover else (150, 130, 255)
        retangulo_suave(tela, cor, self.rect, 10,
                        glow_cor=cor if self.hover else None,
                        glow_raio=max(4, self.rect.h) if self.hover else 0)
        pygame.draw.rect(tela, borda, self.rect, 2, border_radius=10)
        desenhar_texto_suave(tela, fonte, self.texto, self.rect.center, BRANCO,
                             glow_raio=2)

    def _desenhar_glass(self, tela, fonte):
        cor = cor_primaria()
        if self.hover:
            cor = cor_borda_forte()
        desenhar_painel(tela, cor, self.rect,
                        cor_fundo=cor_fundo_painel(), raio_canto=12,
                        glow_raio=20 if self.hover else 8)
        desenhar_cantos(tela, BRANCO, self.rect, tamanho=10)
        desenhar_texto_suave(tela, fonte, self.texto, self.rect.center, BRANCO,
                             glow_cor=cor, glow_raio=2)


def desenhar_texto(tela, texto, pos, cor, tamanho=28, alinhar="centro",
                   fontes=None):
    """Desenha texto na tela. Retorna o rect."""
    if fontes and tamanho in fontes:
        fonte = fontes[tamanho]
    else:
        fonte = fonte_texto(tamanho)
    return desenhar_texto_suave(tela, fonte, texto, pos, cor,
                                alinhar=alinhar)


def desenhar_titulo(tela, texto, pos, cor=None, tamanho=44):
    """Titulo em fonte Orbitron com glow."""
    fonte = fonte_titulo(tamanho)
    if cor is None:
        cor = cor_primaria()
    return desenhar_texto_suave(tela, fonte, texto, pos, cor,
                                glow_cor=cor, glow_raio=6, sombra=True)


def desenhar_coracoes(tela, vida, x, y, cor=(255, 50, 50)):
    """Desenha uma fileira de coracoes de vida."""
    for i in range(vida):
        desenhar_coracao(tela, x + i * 26, y, cor)


def desenhar_coracao(tela, x, y, cor, tamanho=8):
    desenhar_glow(tela, cor, (x, y), tamanho * 1.5, 0.6)
    desenhar_circulo(tela, cor, (x - tamanho // 2, y - tamanho // 2),
                     tamanho // 2, brilho=1.1)
    desenhar_circulo(tela, cor, (x + tamanho // 2, y - tamanho // 2),
                     tamanho // 2, brilho=1.1)
    pygame.draw.polygon(tela, cor,
                        [(x - tamanho, y + tamanho // 2),
                         (x + tamanho, y + tamanho // 2),
                         (x, y + tamanho * 1.6)])


def desenhar_barra(tela, x, y, largura, altura, fracao, cor,
                   fundo=(40, 40, 70)):
    barra_suave(tela, x, y, largura, altura, fracao, cor, fundo=fundo)


def desenhar_painel_titulo(tela, titulo, subtitulo=None, y=55,
                           cor=None, subtitulo_cor=None):
    """Cabecalho padrao das telas do menu: titulo + linha decorativa."""
    if cor is None:
        cor = cor_primaria()
    desenhar_titulo(tela, titulo, (LARGURA // 2, y), cor)
    t = pygame.time.get_ticks() * 0.002
    x0 = LARGURA // 2 - 150
    largura = 300
    desenhar_glow(tela, cor, (LARGURA // 2, y + 34), 20, 0.4)
    for i in range(0, largura, 6):
        brilho = 0.4 + 0.6 * abs(math.sin(i / 40 + t))
        cor_linha = tuple(int(c * brilho) for c in cor)
        pygame.draw.line(tela, cor_linha,
                         (x0 + i, y + 34), (x0 + i + 4, y + 40), 2)
    if subtitulo:
        if subtitulo_cor is None:
            subtitulo_cor = (200, 205, 240)
        surface = fonte_texto(20).render(subtitulo, True, subtitulo_cor)
        surface.set_alpha(200)
        tela.blit(surface, surface.get_rect(center=(LARGURA // 2, y + 62)))
