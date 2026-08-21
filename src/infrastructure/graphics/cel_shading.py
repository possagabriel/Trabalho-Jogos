"""Cel-shading / toon-shading rendering system.

Thick outlines, flat shadows, comic-book effects and cartoon aesthetics
inspired by Borderlands, Jet Set Radio and Zelda: BotW.

Migrated from game/cel_shading.py -- every function preserved with full
logic.
"""

import math
import random
from typing import List, Sequence, Tuple, Union

import pygame

ESPRESSURA_CONTORNO_PADRAO = 3


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------

def escurecer_cor(cor: Tuple[int, ...], fator: float = 0.6) -> Tuple[int, int, int]:
    """Return a darker version of the colour (flat shadow)."""
    return tuple(max(0, min(255, int(c * fator))) for c in cor[:3])


def clarear_cor(cor: Tuple[int, ...], fator: float = 0.4) -> Tuple[int, int, int]:
    """Return a lighter version of the colour (highlight)."""
    return tuple(min(255, int(c + (255 - c) * fator)) for c in cor[:3])


def cor_sombra_luz(cor: Tuple[int, ...],
                   angulo_luz: float = 45) -> Tuple[int, int, int]:
    """Compute shadow colour based on light angle (2-3 flat levels)."""
    intensidade = abs(math.cos(math.radians(angulo_luz)))
    if intensidade > 0.7:
        return tuple(cor[:3])
    if intensidade > 0.4:
        return escurecer_cor(cor, 0.75)
    return escurecer_cor(cor, 0.5)


# ---------------------------------------------------------------------------
# Outlines -- cartoon stylisation
# ---------------------------------------------------------------------------

def contorno_poligono(tela: pygame.Surface,
                      pontos: Sequence[Tuple[float, float]],
                      espessura: int = ESPRESSURA_CONTORNO_PADRAO,
                      cor_contorno: Tuple[int, int, int] = (0, 0, 0)) -> None:
    """Thick outline around a polygon (Borderlands style).

    Expands vertices from the centroid to create a thicker silhouette,
    then the original polygon is drawn on top.
    """
    if len(pontos) < 3 or espessura <= 0:
        return
    cx = sum(p[0] for p in pontos) / len(pontos)
    cy = sum(p[1] for p in pontos) / len(pontos)
    pontos_expandidos: list = []
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


def contorno_circulo(tela: pygame.Surface,
                     centro: Tuple[float, float], raio: float,
                     espessura: int = ESPRESSURA_CONTORNO_PADRAO,
                     cor_contorno: Tuple[int, int, int] = (0, 0, 0)) -> None:
    """Thick outline around a circle."""
    if espessura <= 0:
        return
    pygame.draw.circle(tela, cor_contorno, (int(centro[0]), int(centro[1])),
                       int(raio) + espessura)


def contorno_retangulo(tela: pygame.Surface, rect: pygame.Rect,
                       espessura: int = ESPRESSURA_CONTORNO_PADRAO,
                       cor_contorno: Tuple[int, int, int] = (0, 0, 0),
                       raio_canto: int = 0) -> None:
    """Thick outline around a rectangle."""
    if espessura <= 0:
        return
    r = rect.inflate(espessura * 2, espessura * 2)
    pygame.draw.rect(tela, cor_contorno, r,
                     border_radius=raio_canto + espessura)


# ---------------------------------------------------------------------------
# Unified shapes with outline
# ---------------------------------------------------------------------------

def poligono_com_contorno(tela: pygame.Surface, cor: Tuple[int, ...],
                          pontos: Sequence[Tuple[float, float]],
                          espessura_contorno: int = 3,
                          cor_contorno: Tuple[int, int, int] = (0, 0, 0),
                          brilho_sombra: float = 0.7,
                          desenhar_borda_interna: bool = True) -> None:
    """Filled polygon with thick outline and inner shadow."""
    if len(pontos) < 3:
        return
    contorno_poligono(tela, pontos, espessura_contorno, cor_contorno)
    pygame.draw.polygon(tela, tuple(cor[:3]), pontos)
    if desenhar_borda_interna:
        pygame.draw.polygon(tela, escurecer_cor(cor, brilho_sombra),
                            pontos, max(1, espessura_contorno // 2))


def circulo_com_contorno(tela: pygame.Surface, cor: Tuple[int, ...],
                         centro: Tuple[float, float], raio: float,
                         espessura_contorno: int = 3,
                         cor_contorno: Tuple[int, int, int] = (0, 0, 0),
                         brilho_sombra: float = 0.7,
                         desenhar_borda_interna: bool = True) -> None:
    """Filled circle with thick outline and inner shadow."""
    contorno_circulo(tela, centro, raio, espessura_contorno, cor_contorno)
    pygame.draw.circle(tela, tuple(cor[:3]),
                       (int(centro[0]), int(centro[1])), int(raio))
    if desenhar_borda_interna:
        pygame.draw.circle(tela, escurecer_cor(cor, brilho_sombra),
                           (int(centro[0]), int(centro[1])), int(raio),
                           max(1, espessura_contorno // 2))


def estrela_com_contorno(tela: pygame.Surface, cor: Tuple[int, ...],
                         pontos: Sequence[Tuple[float, float]],
                         espessura_contorno: int = 3,
                         cor_contorno: Tuple[int, int, int] = (0, 0, 0)) -> None:
    """Filled star with thick outline."""
    contorno_poligono(tela, pontos, espessura_contorno, cor_contorno)
    pygame.draw.polygon(tela, tuple(cor[:3]), pontos)


# ---------------------------------------------------------------------------
# Flat shadows (cartoon style)
# ---------------------------------------------------------------------------

def desenhar_sombra_chapada(tela: pygame.Surface,
                            pontos: Sequence[Tuple[float, float]],
                            cor_sombra: Tuple[int, int, int, int] = (0, 0, 0, 80),
                            deslocamento: Tuple[int, int] = (4, 6)) -> None:
    """Projected cartoon shadow (no gradient)."""
    dx, dy = deslocamento
    pontos_sombra = [(p[0] + dx, p[1] + dy) for p in pontos]
    if len(pontos_sombra) >= 3:
        surf = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(surf, cor_sombra, pontos_sombra)
        tela.blit(surf, (0, 0))


def sombra_circulo(tela: pygame.Surface,
                   centro: Tuple[float, float], raio: float,
                   cor_sombra: Tuple[int, int, int, int] = (0, 0, 0, 80),
                   deslocamento: Tuple[int, int] = (4, 6)) -> None:
    """Projected circular cartoon shadow."""
    dx, dy = deslocamento
    surf = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
    pygame.draw.circle(surf, cor_sombra,
                       (int(centro[0] + dx), int(centro[1] + dy)), int(raio))
    tela.blit(surf, (0, 0))


# ---------------------------------------------------------------------------
# Cartoon highlights
# ---------------------------------------------------------------------------

def desenhar_highlight(tela: pygame.Surface,
                       centro: Tuple[float, float], raio: float,
                       cor: Tuple[int, int, int] = (255, 255, 255),
                       intensidade: float = 0.5) -> None:
    """Circular white highlight (cartoon shine)."""
    hx = int(centro[0] - raio * 0.3)
    hy = int(centro[1] - raio * 0.3)
    hr = max(1, int(raio * 0.35))
    alpha = int(255 * intensidade)
    surf = pygame.Surface((hr * 2, hr * 2), pygame.SRCALPHA)
    pygame.draw.circle(surf, cor[:3] + (alpha,), (hr, hr), hr)
    tela.blit(surf, (hx - hr, hy - hr))


def desenhar_brilho_contorno(tela: pygame.Surface,
                             pontos: Sequence[Tuple[float, float]],
                             cor_brilho: Tuple[int, ...],
                             espessura: int = 2,
                             intensidade: float = 0.6) -> None:
    """Glow around a polygon (for enraged bosses)."""
    if len(pontos) < 3:
        return
    alpha = int(255 * intensidade)
    cx = sum(p[0] for p in pontos) / len(pontos)
    cy = sum(p[1] for p in pontos) / len(pontos)
    pontos_exp: list = []
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
# Cartoon health bar
# ---------------------------------------------------------------------------

def barra_vida_cartoon(tela: pygame.Surface, x: int, y: int,
                       largura: int, vida: int, vida_max: int,
                       altura: int = 6,
                       cor_contorno: Tuple[int, int, int] = (0, 0, 0)) -> None:
    """Cartoon health bar with thick outline and flat colours."""
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
# Comic-book action text (BANG! POW! KABOOM!)
# ---------------------------------------------------------------------------

TEXTOS_ACAO = ["BANG!", "POW!", "KABOOM!", "BOOM!", "WHAM!", "ZAP!",
               "CRASH!", "SMASH!", "BONK!", "SLAM!"]


class TextoAcao:
    """Floating comic-book action text."""

    def __init__(self, x: float, y: float, texto: str = None,
                 cor: Tuple[int, ...] = (255, 200, 50), tamanho: int = 36):
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

    def _gerar_particulas(self) -> List[dict]:
        partes: list = []
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

    def atualizar(self) -> None:
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

    def desenhar(self, tela: pygame.Surface) -> None:
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
        texto_colorido = fonte.render(self.texto, True, tuple(self.cor[:3]))
        texto_colorido.set_alpha(alfa)
        tela.blit(texto_colorido, rect_base)
        for p in self.particulas:
            pa = int(200 * p["vida"] / 30)
            if pa > 0:
                pygame.draw.circle(tela, p["cor"],
                                   (int(p["x"]), int(p["y"])), p["tamanho"])


# ---------------------------------------------------------------------------
# Damage flash (cartoon)
# ---------------------------------------------------------------------------

def flash_dano(tela: pygame.Surface, intensidade: float = 0.4) -> None:
    """White screen flash for damage feedback."""
    if intensidade <= 0:
        return
    overlay = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
    alpha = int(255 * intensidade)
    overlay.fill((255, 255, 255, alpha))
    tela.blit(overlay, (0, 0))


# ---------------------------------------------------------------------------
# Sprite with outline
# ---------------------------------------------------------------------------

def sprite_com_contorno(tela: pygame.Surface, sprite: pygame.Surface,
                        pos: Tuple[float, float], espessura: int = 3,
                        cor_contorno: Tuple[int, int, int] = (0, 0, 0)) -> None:
    """Draw a PNG sprite with a thick outline.

    Uses the alpha mask of the sprite to generate the outline by offsetting
    the silhouette in 8 directions.
    """
    if sprite is None:
        return
    sx, sy = sprite.get_width(), sprite.get_height()
    pad = espessura
    contour_surf = pygame.Surface((sx + pad * 2, sy + pad * 2), pygame.SRCALPHA)
    mask_surf = (sprite if sprite.get_flags() & pygame.SRCALPHA
                 else sprite.copy())
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
# Speed lines (anime / cartoon)
# ---------------------------------------------------------------------------

def desenhar_speed_lines(tela: pygame.Surface, x: float, y: float,
                         direcao: str = "esquerda", quantidade: int = 5,
                         cor: Tuple[int, int, int] = (200, 200, 255),
                         alpha: int = 120) -> None:
    """Anime-style speed lines."""
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
# Action line (comic-book style, for projectiles)
# ---------------------------------------------------------------------------

def linha_acao(tela: pygame.Surface, x1: float, y1: float,
               x2: float, y2: float, espessura: int = 2,
               cor: Tuple[int, ...] = (255, 255, 255),
               alpha: int = 180) -> None:
    """Comic-book action line."""
    pygame.draw.line(tela,
                     cor[:3] + (alpha,) if len(cor) >= 3 else cor,
                     (int(x1), int(y1)), (int(x2), int(y2)), espessura)
