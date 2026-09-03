"""Sistema de renderizacao Cel Shading / Toon Shading.

Contornos grossos, sombras chapadas, efeitos de quadrinhos e estetica
cartoon inspirada em Borderlands, Jet Set Radio e Zelda: BotW.
"""

import math
import random

import pygame

ESPRESSURA_CONTORNO_PADRAO = 3


# ---------------------------------------------------------------------------
# Funcoes auxiliares de cor
# ---------------------------------------------------------------------------

def escurecer_cor(cor, fator=0.6):
    """Retorna uma versao mais escura da cor (sombra chapada)."""
    return tuple(max(0, min(255, int(c * fator))) for c in cor[:3])


def clarear_cor(cor, fator=0.4):
    """Retorna uma versao mais clara da cor (destaque)."""
    return tuple(min(255, int(c + (255 - c) * fator)) for c in cor[:3])


def cor_sombra_luz(cor, angulo_luz=45):
    """Calcula cor de sombra baseada no angulo da luz.

    Para Cel Shading, usamos apenas 2-3 niveis de sombra (sem degradê).
    """
    intensidade = abs(math.cos(math.radians(angulo_luz)))
    if intensidade > 0.7:
        return cor
    if intensidade > 0.4:
        return escurecer_cor(cor, 0.75)
    return escurecer_cor(cor, 0.5)


# ---------------------------------------------------------------------------
# Contornos (Outlines) - estilizacao cartoon
# ---------------------------------------------------------------------------

def contorno_poligono(tela, pontos, espessura=ESPRESSURA_CONTORNO_PADRAO,
                      cor_contorno=(0, 0, 0)):
    """Desenha contorno grosso ao redor de um poligono (estilo Borderlands).

    Expande os vertices do poligono a partir do centro para criar uma
    silhueta mais grossa, depois desenha o poligono original por cima.
    """
    if len(pontos) < 3 or espessura <= 0:
        return
    cx = sum(p[0] for p in pontos) / len(pontos)
    cy = sum(p[1] for p in pontos) / len(pontos)
    pontos_expandidos = []
    for px, py in pontos:
        dx = px - cx
        dy = py - cy
        dist = math.hypot(dx, dy)
        if dist > 0.5:
            fator = 1 + (espessura * 0.35) / dist
            pontos_expandidos.append((cx + dx * fator, cy + dy * fator))
        else:
            pontos_expandidos.append((px, py))
    if len(pontos_expandidos) >= 3:
        pygame.draw.polygon(tela, cor_contorno, pontos_expandidos)


def contorno_circulo(tela, centro, raio, espessura=ESPRESSURA_CONTORNO_PADRAO,
                     cor_contorno=(0, 0, 0)):
    """Desenha contorno grosso ao redor de um circulo."""
    if espessura <= 0:
        return
    pygame.draw.circle(tela, cor_contorno, (int(centro[0]), int(centro[1])),
                       int(raio) + espessura)


def contorno_retangulo(tela, rect, espessura=ESPRESSURA_CONTORNO_PADRAO,
                       cor_contorno=(0, 0, 0), raio_canto=0):
    """Desenha contorno grosso ao redor de um retangulo."""
    if espessura <= 0:
        return
    r = rect.inflate(espessura * 2, espessura * 2)
    pygame.draw.rect(tela, cor_contorno, r,
                     border_radius=raio_canto + espessura)


# ---------------------------------------------------------------------------
# Poligono com contorno (funcao unificada)
# ---------------------------------------------------------------------------

def poligono_com_contorno(tela, cor, pontos, espessura_contorno=3,
                          cor_contorno=(0, 0, 0), brilho_sombra=0.7,
                          desenhar_borda_interna=True):
    """Desenha poligono preenchido com contorno grosso e sombra interna.

    Estilo cartoon: contorno preto, cor solida, borda interna escura.
    """
    if len(pontos) < 3:
        return
    contorno_poligono(tela, pontos, espessura_contorno, cor_contorno)
    pygame.draw.polygon(tela, cor, pontos)
    if desenhar_borda_interna:
        pygame.draw.polygon(tela, escurecer_cor(cor, brilho_sombra),
                            pontos, max(1, espessura_contorno // 2))


def circulo_com_contorno(tela, cor, centro, raio, espessura_contorno=3,
                         cor_contorno=(0, 0, 0), brilho_sombra=0.7,
                         desenhar_borda_interna=True):
    """Desenha circulo preenchido com contorno grosso e sombra interna."""
    contorno_circulo(tela, centro, raio, espessura_contorno, cor_contorno)
    pygame.draw.circle(tela, cor, (int(centro[0]), int(centro[1])), int(raio))
    if desenhar_borda_interna:
        pygame.draw.circle(tela, escurecer_cor(cor, brilho_sombra),
                           (int(centro[0]), int(centro[1])), int(raio),
                           max(1, espessura_contorno // 2))


def estrela_com_contorno(tela, cor, pontos, espessura_contorno=3,
                         cor_contorno=(0, 0, 0)):
    """Desenha estrela preenchida com contorno grosso."""
    contorno_poligono(tela, pontos, espessura_contorno, cor_contorno)
    pygame.draw.polygon(tela, cor, pontos)


# ---------------------------------------------------------------------------
# Sombras chapadas (flat shadows)
# ---------------------------------------------------------------------------

def desenhar_sombra_chapada(tela, pontos, cor_sombra=(0, 0, 0, 80),
                            deslocamento=(4, 6)):
    """Desenha sombra projetada estilo cartoon (sem degradê).

    A sombra e uma copia deslocada e escurecida do poligono.
    """
    dx, dy = deslocamento
    pontos_sombra = [(p[0] + dx, p[1] + dy) for p in pontos]
    if len(pontos_sombra) >= 3:
        surf = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(surf, cor_sombra, pontos_sombra)
        tela.blit(surf, (0, 0))


def sombra_circulo(tela, centro, raio, cor_sombra=(0, 0, 0, 80),
                   deslocamento=(4, 6)):
    """Desenha sombra projetada circular estilo cartoon."""
    dx, dy = deslocamento
    surf = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
    pygame.draw.circle(surf, cor_sombra,
                       (int(centro[0] + dx), int(centro[1] + dy)), int(raio))
    tela.blit(surf, (0, 0))


# ---------------------------------------------------------------------------
# Destaque / Highlight estilo cartoon
# ---------------------------------------------------------------------------

def desenhar_highlight(tela, centro, raio, cor=(255, 255, 255),
                       intensidade=0.5):
    """Desenha um destaque circular branco (brilho cartoon).

    Posiciona o destaque no canto superior-esquerdo do objeto.
    """
    hx = int(centro[0] - raio * 0.3)
    hy = int(centro[1] - raio * 0.3)
    hr = max(1, int(raio * 0.35))
    alpha = int(255 * intensidade)
    surf = pygame.Surface((hr * 2, hr * 2), pygame.SRCALPHA)
    pygame.draw.circle(surf, cor[:3] + (alpha,), (hr, hr), hr)
    tela.blit(surf, (hx - hr, hy - hr))


def desenhar_brilho_contorno(tela, pontos, cor_brilho, espessura=2,
                             intensidade=0.6):
    """Desenha brilho ao redor de um poligono (para bosses enraivecidos)."""
    if len(pontos) < 3:
        return
    alpha = int(255 * intensidade)
    cx = sum(p[0] for p in pontos) / len(pontos)
    cy = sum(p[1] for p in pontos) / len(pontos)
    pontos_exp = []
    for px, py in pontos:
        dx = px - cx
        dy = py - cy
        dist = math.hypot(dx, dy)
        if dist > 0.5:
            fator = 1 + (espessura * 0.5) / dist
            pontos_exp.append((cx + dx * fator, cy + dy * fator))
        else:
            pontos_exp.append((px, py))
    if len(pontos_exp) >= 3:
        surf = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(surf, cor_brilho[:3] + (alpha,), pontos_exp)
        tela.blit(surf, (0, 0))


# ---------------------------------------------------------------------------
# Barra de vida estilo cartoon
# ---------------------------------------------------------------------------

def barra_vida_cartoon(tela, x, y, largura, vida, vida_max,
                       altura=6, cor_contorno=(0, 0, 0)):
    """Barra de vida estilo cartoon com contorno grosso e cores chapadas."""
    if vida >= vida_max:
        return
    proporcao = max(0, vida / vida_max)
    rect_fundo = pygame.Rect(x, y, largura, altura)
    pygame.draw.rect(tela, cor_contorno,
                     rect_fundo.inflate(4, 4), border_radius=4)
    pygame.draw.rect(tela, (180, 40, 40), rect_fundo, border_radius=2)
    if proporcao > 0.5:
        cor_vida = (50, 200, 50)
    elif proporcao > 0.3:
        cor_vida = (200, 200, 50)
    else:
        cor_vida = (200, 50, 50)
    larg_vida = max(0, int(largura * proporcao))
    if larg_vida > 0:
        rect_vida = pygame.Rect(x, y, larg_vida, altura)
        pygame.draw.rect(tela, cor_vida, rect_vida, border_radius=2)


# ---------------------------------------------------------------------------
# Textos de acao estilo quadrinhos (BANG! POW! KABOOM!)
# ---------------------------------------------------------------------------

TEXTOS_ACAO = ["PÁ!", "POW!", "CABUM!", "BUM!", "ZAP!", "TUM!",
               "CRASH!", "ESMAGOU!", "TOC!", "PUM!"]


class TextoAcao:
    """Texto de acao flutuante estilo quadrinhos."""

    def __init__(self, x, y, texto=None, cor=(255, 200, 50), tamanho=36):
        self.x = x
        self.y = y
        self.texto = texto or random.choice(TEXTOS_ACAO)
        self.cor = cor
        self.tamanho = tamanho
        self.vida = 45
        self.vida_max = 45
        self.ativo = True
        self.escala = 1.0
        self.rotacao = random.uniform(-15, 15)
        self.particulas = self._gerar_particulas()

    def _gerar_particulas(self):
        partes = []
        for _ in range(12):
            ang = random.uniform(0, math.tau)
            vel = random.uniform(1, 4)
            partes.append({
                "x": self.x + random.uniform(-15, 15),
                "y": self.y + random.uniform(-15, 15),
                "vx": math.cos(ang) * vel,
                "vy": math.sin(ang) * vel - 2,
                "vida": random.randint(15, 30),
                "tamanho": random.randint(2, 5),
                "cor": random.choice([self.cor, clarear_cor(self.cor),
                                      escurecer_cor(self.cor)])
            })
        return partes

    def atualizar(self):
        self.vida -= 1
        progresso = 1 - self.vida / self.vida_max
        self.escala = 1.0 + progresso * 0.3
        self.y -= 1.5
        if self.vida <= 0:
            self.ativo = False
        for p in self.particulas:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vida"] -= 1
        self.particulas = [p for p in self.particulas if p["vida"] > 0]

    def desenhar(self, tela):
        if not self.ativo:
            return
        alfa = int(255 * min(1.0, self.vida / 15))
        tam = int(self.tamanho * self.escala)
        fonte = pygame.font.Font(None, tam)
        texto_surf = fonte.render(self.texto, True, (0, 0, 0))
        texto_surf.set_alpha(alfa)
        rect_base = texto_surf.get_rect(center=(int(self.x), int(self.y)))
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            tela.blit(texto_surf, (rect_base.x + dx, rect_base.y + dy))
        texto_colorido = fonte.render(self.texto, True, self.cor)
        texto_colorido.set_alpha(alfa)
        tela.blit(texto_colorido, rect_base)
        for p in self.particulas:
            pa = int(200 * p["vida"] / 30)
            if pa > 0:
                pygame.draw.circle(tela, p["cor"],
                                   (int(p["x"]), int(p["y"])), p["tamanho"])


# ---------------------------------------------------------------------------
# Efeito de dano estilo cartoon (flash branco)
# ---------------------------------------------------------------------------

def flash_dano(tela, intensidade=0.4):
    """Aplica flash branco na tela para feedback de dano."""
    if intensidade <= 0:
        return
    overlay = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
    alpha = int(255 * intensidade)
    overlay.fill((255, 255, 255, alpha))
    tela.blit(overlay, (0, 0))


# ---------------------------------------------------------------------------
# Desenho de sprite com contorno (para a nave padrao com imagem)
# ---------------------------------------------------------------------------

def sprite_com_contorno(tela, sprite, pos, espessura=3,
                        cor_contorno=(0, 0, 0)):
    """Desenha um sprite PNG com contorno grosso ao redor.

    Utiliza a mascara alpha do sprite para gerar o contorno
    deslocando a silhueta em 8 direcoes.
    """
    if sprite is None:
        return
    sx, sy = sprite.get_width(), sprite.get_height()
    pad = espessura
    contour_surf = pygame.Surface((sx + pad * 2, sy + pad * 2), pygame.SRCALPHA)
    mask_surf = sprite if sprite.get_flags() & pygame.SRCALPHA else sprite.copy()
    direcoes = [
        (-pad, -pad), (0, -pad), (pad, -pad),
        (-pad, 0), (pad, 0),
        (-pad, pad), (0, pad), (pad, pad),
    ]
    for dx, dy in direcoes:
        contour_surf.blit(mask_surf, (dx + pad, dy + pad))
    contour_surf.fill(cor_contorno + (255,), None, pygame.BLEND_RGBA_MULT)
    contour_surf.blit(sprite, (pad, pad))
    rect = contour_surf.get_rect(center=(int(pos[0]), int(pos[1])))
    tela.blit(contour_surf, rect)


# ---------------------------------------------------------------------------
# Efeito de velocidade linhas de acao (speed lines)
# ---------------------------------------------------------------------------

def desenhar_speed_lines(tela, x, y, direcao="esquerda", quantidade=5,
                         cor=(200, 200, 255), alpha=120):
    """Desenha linhas de velocidade estilo anime/cartoon."""
    surf = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
    for _ in range(quantidade):
        if direcao == "esquerda":
            sx = x + random.randint(10, 40)
            sy = y + random.randint(-15, 15)
            ex = sx - random.randint(15, 35)
            ey = sy + random.randint(-3, 3)
        elif direcao == "baixo":
            sx = x + random.randint(-15, 15)
            sy = y - random.randint(10, 30)
            ex = sx + random.randint(-3, 3)
            ey = sy - random.randint(15, 35)
        else:
            sx = x - random.randint(10, 40)
            sy = y + random.randint(-15, 15)
            ex = sx + random.randint(15, 35)
            ey = sy + random.randint(-3, 3)
        pygame.draw.line(surf, cor[:3] + (alpha,), (int(sx), int(sy)),
                         (int(ex), int(ey)), random.randint(1, 2))
    tela.blit(surf, (0, 0))


# ---------------------------------------------------------------------------
# Linha de acao estilo quadrinhos (para projeteis)
# ---------------------------------------------------------------------------

def linha_acao(tela, x1, y1, x2, y2, espessura=2, cor=(255, 255, 255),
               alpha=180):
    """Desenha uma linha de acao estilo quadrinhos."""
    pygame.draw.line(tela, cor[:3] + (alpha,) if len(cor) >= 3 else cor,
                     (int(x1), int(y1)), (int(x2), int(y2)), espessura)
