"""Smooth rendering: anti-aliasing, glow, gradients and easing functions.

Central visual-quality system for the game.  All raw ``pygame.draw.*`` calls
pass through here to gain smooth edges, radial glow and interpolation.
Surfaces are cached by key to maintain 60 FPS.

Migrated from game/smooth.py -- every public function preserved with full
logic.
"""

import math
from typing import Sequence, Tuple, Union

import pygame

# ---------------------------------------------------------------------------
# Internal caches
# ---------------------------------------------------------------------------

_CACHE_CIRCULO: dict = {}
_CACHE_POLIGONO: dict = {}
_CACHE_LINHA: dict = {}
_CACHE_TEXTO: dict = {}
_CACHE_GRADIENTE: dict = {}
_CACHE_GLOW: dict = {}
_CACHE_PAINEL: dict = {}
_CACHE_VIGNETTE: dict = {}
_CACHE_PAINEL_CARTOON: dict = {}

# Supersampling factor for anti-aliasing.
_SCALA_AA = 2


def limpar_cache() -> None:
    """Flush every rendering cache."""
    _CACHE_CIRCULO.clear()
    _CACHE_POLIGONO.clear()
    _CACHE_LINHA.clear()
    _CACHE_TEXTO.clear()
    _CACHE_GRADIENTE.clear()
    _CACHE_GLOW.clear()
    _CACHE_PAINEL.clear()
    _CACHE_VIGNETTE.clear()
    _CACHE_PAINEL_CARTOON.clear()


# ---------------------------------------------------------------------------
# Easing functions
# ---------------------------------------------------------------------------

def ease_in_out(t: float) -> float:
    """Smoothstep: gentle acceleration in and out."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) * (1 - t)


def ease_in(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t


def ease_out_back(t: float) -> float:
    t = max(0.0, min(1.0, t))
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def interpolar_cor(cor1: Tuple[int, ...], cor2: Tuple[int, ...],
                   t: float) -> Tuple[int, int, int]:
    """Interpolate two colours with easing."""
    t = max(0.0, min(1.0, t))
    t = ease_in_out(t)
    return tuple(int(c1 + (c2 - c1) * t) for c1, c2 in zip(cor1[:3], cor2[:3]))


# ---------------------------------------------------------------------------
# Gradients
# ---------------------------------------------------------------------------

def gradiente_vertical(topo: Tuple[int, int, int],
                       base: Tuple[int, int, int],
                       largura: int = 900, altura: int = 700) -> pygame.Surface:
    """Surface *largura*x*altura* with a smooth vertical gradient (cached)."""
    chave = (tuple(topo[:3]), tuple(base[:3]), largura, altura)
    if chave in _CACHE_GRADIENTE:
        return _CACHE_GRADIENTE[chave]
    surf = pygame.Surface((largura, altura))
    for y in range(altura):
        t = y / altura
        cor = tuple(int(topo[i] + (base[i] - topo[i]) * t) for i in range(3))
        pygame.draw.line(surf, cor, (0, y), (largura, y))
    _CACHE_GRADIENTE[chave] = surf
    return surf


# ---------------------------------------------------------------------------
# Glow / radial light
# ---------------------------------------------------------------------------

def luz_radial(cor: Tuple[int, ...], raio: int,
               intensidade: float = 1.0) -> pygame.Surface:
    """Surface with smooth radial falloff (bloom / glow).

    The radius is expanded to 2.2x so the glow breathes around the object.
    """
    raio = max(1, int(raio))
    chave = (tuple(cor[:3]), raio, round(intensidade, 2))
    if chave in _CACHE_GLOW:
        return _CACHE_GLOW[chave]
    ext = max(1, int(raio * 2.2))
    surf = pygame.Surface((ext * 2, ext * 2), pygame.SRCALPHA)
    cx = cy = ext
    cor3 = tuple(cor[:3])
    for r in range(ext, 0, -1):
        t = r / ext
        alfa = int(min(255, 255 * (1 - t) ** 2.2 * intensidade))
        if alfa <= 0:
            continue
        pygame.draw.circle(surf, cor3 + (alfa,), (cx, cy), r)
    _CACHE_GLOW[chave] = surf
    return surf


def desenhar_glow(tela: pygame.Surface, cor: Tuple[int, ...],
                  centro: Tuple[float, float], raio: int,
                  intensidade: float = 1.0) -> None:
    """Draw smooth radial glow centred at *centro*."""
    surf = luz_radial(cor, raio, intensidade)
    ext = surf.get_width() // 2
    tela.blit(surf, (int(centro[0]) - ext, int(centro[1]) - ext))


# ---------------------------------------------------------------------------
# Smooth circles (anti-aliased via radial gradient)
# ---------------------------------------------------------------------------

def circulo_suave(cor: Tuple[int, ...], raio: int, espessura: int = 0,
                  brilho: float = 1.0) -> pygame.Surface:
    """Surface of an anti-aliased circle.

    Filled: uses a radial gradient for a soft edge.
    Outline (``espessura > 0``): draws N rings with decaying alpha.
    """
    raio = max(1, int(raio))
    espessura = int(espessura)
    chave = (tuple(cor[:3]), raio, espessura, round(brilho, 2))
    if chave in _CACHE_CIRCULO:
        return _CACHE_CIRCULO[chave]

    cor3 = tuple(cor[:3])

    if espessura <= 0:
        ext = raio + 6
        surf = pygame.Surface((ext * 2, ext * 2), pygame.SRCALPHA)
        cx = cy = ext
        pygame.draw.circle(surf, cor3 + (255,), (cx, cy), raio)
        for r in range(raio + 1, ext):
            t = (r - raio) / 6
            alfa = int(160 * (1 - t) ** 2 * brilho)
            if alfa > 0:
                pygame.draw.circle(surf, cor3 + (alfa,), (cx, cy), r)
    else:
        ext = raio + espessura + 8
        surf = pygame.Surface((ext * 2, ext * 2), pygame.SRCALPHA)
        cx = cy = ext
        for i in range(espessura, 0, -1):
            alfa = int(255 * (i / espessura))
            pygame.draw.circle(surf, cor3 + (alfa,), (cx, cy),
                               raio - i // 2 + 1, max(1, i))

    _CACHE_CIRCULO[chave] = surf
    return surf


def desenhar_circulo(tela: pygame.Surface, cor: Tuple[int, ...],
                     centro: Tuple[float, float], raio: int,
                     espessura: int = 0, brilho: float = 1.0) -> None:
    """Draw an anti-aliased circle."""
    surf = circulo_suave(cor, raio, espessura, brilho)
    tela.blit(surf, surf.get_rect(center=(int(centro[0]), int(centro[1]))))


# ---------------------------------------------------------------------------
# Smooth polygons (supersampling + smoothscale)
# ---------------------------------------------------------------------------

def poligono_suave(cor: Tuple[int, ...],
                   pontos: Sequence[Tuple[float, float]],
                   espessura: int = 0,
                   brilho: float = 1.0) -> Tuple[pygame.Surface, Tuple[int, int]]:
    """Surface of an anti-aliased polygon.

    Renders at higher resolution (``_SCALA_AA``) and downscales with
    ``smoothscale``.  Returns ``(surface, offset)``.
    """
    cor3 = tuple(cor[:3])
    esp = int(espessura)
    pts = [(float(p[0]), float(p[1])) for p in pontos]
    chave = (cor3, tuple((int(p[0] * 4), int(p[1] * 4)) for p in pts),
             esp, round(brilho, 2))
    if chave in _CACHE_POLIGONO:
        return _CACHE_POLIGONO[chave]

    min_x = min(p[0] for p in pts) - 4
    max_x = max(p[0] for p in pts) + 4
    min_y = min(p[1] for p in pts) - 4
    max_y = max(p[1] for p in pts) + 4
    larg = max(1, int(max_x - min_x))
    alt = max(1, int(max_y - min_y))

    big = pygame.Surface((larg * _SCALA_AA, alt * _SCALA_AA), pygame.SRCALPHA)
    pts_big = [((p[0] - min_x) * _SCALA_AA, (p[1] - min_y) * _SCALA_AA)
               for p in pts]
    if esp <= 0:
        pygame.draw.polygon(big, cor3 + (255,), pts_big)
    else:
        pygame.draw.polygon(big, cor3 + (255,), pts_big, esp * _SCALA_AA)

    surf = pygame.transform.smoothscale(big, (larg, alt))
    _CACHE_POLIGONO[chave] = (surf, (int(min_x), int(min_y)))
    return surf, (int(min_x), int(min_y))


def desenhar_poligono(tela: pygame.Surface, cor: Tuple[int, ...],
                      pontos: Sequence[Tuple[float, float]],
                      espessura: int = 0, brilho: float = 1.0,
                      glow_cor: "Tuple[int, ...] | None" = None,
                      glow_raio: int = 0) -> None:
    """Draw an anti-aliased polygon with optional glow underneath."""
    if glow_cor and glow_raio > 0:
        cx = sum(p[0] for p in pontos) / len(pontos)
        cy = sum(p[1] for p in pontos) / len(pontos)
        desenhar_glow(tela, glow_cor, (cx, cy), glow_raio, brilho)
    surf, (ox, oy) = poligono_suave(cor, pontos, espessura, brilho)
    tela.blit(surf, (ox, oy))


# ---------------------------------------------------------------------------
# Smooth lines
# ---------------------------------------------------------------------------

def linha_suave(tela: pygame.Surface, cor: Tuple[int, ...],
                inicio: Tuple[float, float], fim: Tuple[float, float],
                espessura: int = 2, brilho: float = 1.0) -> None:
    """Anti-aliased line with smooth width (parallel layers)."""
    esp = max(1, int(espessura))
    if esp <= 1:
        pygame.draw.aaline(tela, tuple(cor[:3]) + (255,), inicio, fim)
        return
    dx = fim[0] - inicio[0]
    dy = fim[1] - inicio[1]
    compr = math.hypot(dx, dy) or 1
    nx = -dy / compr
    ny = dx / compr
    base = int(esp / 2)
    for i in range(-base, base + 1):
        alfa = int(255 * (1 - abs(i) / (base + 1)) ** 1.5 * brilho)
        off = i * 0.6
        p1 = (inicio[0] + nx * off, inicio[1] + ny * off)
        p2 = (fim[0] + nx * off, fim[1] + ny * off)
        pygame.draw.aaline(tela, tuple(cor[:3]) + (alfa,), p1, p2)


# ---------------------------------------------------------------------------
# Smooth text with glow and shadow
# ---------------------------------------------------------------------------

def texto_suave(fonte: pygame.font.Font, texto: str,
                cor: Tuple[int, ...],
                glow_cor: "Tuple[int, ...] | None" = None,
                glow_raio: int = 4, sombra: bool = True) -> pygame.Surface:
    """Surface of text with glow and soft shadow (cached)."""
    cor_rgb = tuple(max(0, min(255, int(c))) for c in cor[:3])
    glow_rgb = (tuple(max(0, min(255, int(c))) for c in glow_cor[:3])
                if glow_cor else None)
    chave = (fonte.size(texto), texto, cor_rgb, glow_rgb, glow_raio, sombra)
    if chave in _CACHE_TEXTO:
        return _CACHE_TEXTO[chave]

    base = fonte.render(texto, True, cor_rgb)
    larg = base.get_width() + glow_raio * 2 + 6
    alt = base.get_height() + glow_raio * 2 + 6
    surf = pygame.Surface((larg, alt), pygame.SRCALPHA)
    ox = oy = glow_raio + 3

    if sombra:
        sombra_surf = fonte.render(texto, True, (0, 0, 0))
        for i in range(3, 0, -1):
            sombra_surf.set_alpha(int(90 * (1 - i / 4)))
            surf.blit(sombra_surf, (ox + i, oy + i + 1))

    if glow_cor and glow_raio > 0:
        for i in range(glow_raio, 0, -2):
            glow_surf = fonte.render(texto, True, glow_rgb)
            glow_surf.set_alpha(int(110 * (1 - i / (glow_raio + 1))))
            surf.blit(glow_surf, (ox - i // 2, oy - i // 2))

    surf.blit(base, (ox, oy))
    _CACHE_TEXTO[chave] = surf
    return surf


def desenhar_texto_suave(tela: pygame.Surface, fonte: pygame.font.Font,
                         texto: str, pos: Tuple[float, float],
                         cor: Tuple[int, ...],
                         glow_cor: "Tuple[int, ...] | None" = None,
                         glow_raio: int = 4, sombra: bool = True,
                         alinhar: str = "centro") -> pygame.Rect:
    """Draw smooth text.  Returns the bounding rect."""
    surf = texto_suave(fonte, texto, cor, glow_cor, glow_raio, sombra)
    rect = surf.get_rect()
    if alinhar == "centro":
        rect.center = pos
    elif alinhar == "direita":
        rect.topright = pos
    else:
        rect.topleft = pos
    tela.blit(surf, rect)
    return rect


# ---------------------------------------------------------------------------
# Smooth borders (rounded rectangles with glow)
# ---------------------------------------------------------------------------

def retangulo_suave(tela: pygame.Surface, cor: Tuple[int, ...],
                    rect: pygame.Rect, raio_canto: int = 8,
                    espessura: int = 0, brilho: float = 1.0,
                    glow_cor: "Tuple[int, ...] | None" = None,
                    glow_raio: int = 0) -> None:
    """Rounded rectangle with smooth edges and optional glow."""
    if glow_cor and glow_raio > 0:
        desenhar_glow(tela, glow_cor, rect.center,
                      max(rect.w, rect.h), brilho * 0.6)
    escala = _SCALA_AA
    pad = 6
    big = pygame.Surface(((rect.w + pad * 2) * escala,
                          (rect.h + pad * 2) * escala), pygame.SRCALPHA)
    big_rect = pygame.Rect(pad * escala, pad * escala,
                           rect.w * escala, rect.h * escala)
    if espessura <= 0:
        pygame.draw.rect(big, tuple(cor[:3]) + (255,), big_rect,
                         border_radius=int(raio_canto * escala))
    else:
        pygame.draw.rect(big, tuple(cor[:3]) + (255,), big_rect,
                         int(espessura * escala),
                         border_radius=int(raio_canto * escala))
    surf = pygame.transform.smoothscale(big, (rect.w + pad * 2,
                                              rect.h + pad * 2))
    tela.blit(surf, (rect.x - pad, rect.y - pad))


def barra_suave(tela: pygame.Surface, x: int, y: int, largura: int,
                altura: int, fracao: float, cor: Tuple[int, ...],
                fundo: Tuple[int, int, int] = (40, 40, 70),
                raio_canto: int = 6, glow: bool = True) -> None:
    """Progress bar with rounded corners and smooth glow."""
    fracao = max(0.0, min(1.0, fracao))
    rect_fundo = pygame.Rect(x, y, largura, altura)
    retangulo_suave(tela, fundo, rect_fundo, raio_canto)
    if fracao > 0:
        larg_cheia = max(raio_canto * 2, int(largura * fracao))
        rect_cheia = pygame.Rect(x, y, larg_cheia, altura)
        retangulo_suave(tela, cor, rect_cheia, raio_canto,
                        glow_cor=cor if glow else None,
                        glow_raio=max(2, altura))


# ---------------------------------------------------------------------------
# "Glass" panels with neon corners (visual identity)
# ---------------------------------------------------------------------------

def painel_glass(cor_borda: Tuple[int, ...], rect: pygame.Rect,
                 cor_fundo: Tuple[int, int, int] = (12, 14, 32),
                 raio_canto: int = 14, alpha: int = 225,
                 glow_raio: int = 18) -> pygame.Surface:
    """Translucent panel with neon border (cached).

    The central UI component: rounded rectangle with dark translucent fill
    and a coloured border with glow.
    """
    chave = (tuple(cor_borda[:3]), tuple(cor_fundo[:3]), rect.size,
             raio_canto, alpha, glow_raio)
    if chave in _CACHE_PAINEL:
        return _CACHE_PAINEL[chave]

    pad = 12
    w, h = rect.w, rect.h
    surf = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)

    if glow_raio > 0:
        glow = luz_radial(cor_borda, max(w, h) // 2, 0.8)
        surf.blit(glow, glow.get_rect(center=((w + pad * 2) // 2,
                                              (h + pad * 2) // 2)))

    fundo = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(fundo, tuple(cor_fundo[:3]) + (alpha,),
                     (0, 0, w, h), border_radius=raio_canto)
    surf.blit(fundo, (pad, pad))

    for esp, alfa in ((3, 120), (1, 255)):
        b = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(b, tuple(cor_borda[:3]) + (alfa,),
                         (0, 0, w, h), esp, border_radius=raio_canto)
        surf.blit(b, (pad, pad))

    _CACHE_PAINEL[chave] = surf
    return surf


def desenhar_painel(tela: pygame.Surface, cor_borda: Tuple[int, ...],
                    rect: pygame.Rect,
                    cor_fundo: Tuple[int, int, int] = (12, 14, 32),
                    raio_canto: int = 14, alpha: int = 225,
                    glow_raio: int = 18) -> None:
    """Draw a glass panel with neon border."""
    surf = painel_glass(cor_borda, rect, cor_fundo, raio_canto, alpha,
                        glow_raio)
    tela.blit(surf, (rect.x - 12, rect.y - 12))


def desenhar_cantos(tela: pygame.Surface, cor: Tuple[int, ...],
                    rect: pygame.Rect, tamanho: int = 14,
                    espessura: int = 3) -> None:
    """L-shaped decorative brackets (HUD sci-fi style)."""
    x, y, w, h = rect.x, rect.y, rect.w, rect.h
    for (cx, cy, dx, dy) in (
            (x, y, 1, 1), (x + w, y, -1, 1),
            (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
        pygame.draw.line(tela, cor, (cx, cy), (cx + dx * tamanho, cy),
                         espessura)
        pygame.draw.line(tela, cor, (cx, cy), (cx, cy + dy * tamanho),
                         espessura)


# ---------------------------------------------------------------------------
# Cinematic vignette
# ---------------------------------------------------------------------------

def superficie_vignette(largura: int = 900, altura: int = 700,
                        intensidade: float = 0.85,
                        raio_interno: float = 0.55) -> pygame.Surface:
    """Surface with dark vignette on edges (cinematic effect)."""
    chave = ("vignette", largura, altura,
             round(intensidade, 2), round(raio_interno, 2))
    if chave in _CACHE_VIGNETTE:
        return _CACHE_VIGNETTE[chave]

    surf = pygame.Surface((largura, altura), pygame.SRCALPHA)
    cx, cy = largura / 2, altura / 2
    max_dist = math.hypot(cx, cy)
    raio_alpha = raio_interno * max_dist
    raio_total = max_dist
    for y in range(0, altura, 3):
        for x in range(0, largura, 3):
            dist = math.hypot(x - cx, y - cy)
            if dist <= raio_alpha:
                continue
            t = (dist - raio_alpha) / (raio_total - raio_alpha)
            alfa = int(255 * (t ** 2.2) * intensidade)
            if alfa <= 0:
                continue
            surf.set_at((x, y), (0, 0, 0, alfa))
            surf.set_at((min(x + 1, largura - 1), y), (0, 0, 0, alfa))
            surf.set_at((x, min(y + 1, altura - 1)), (0, 0, 0, alfa))
            surf.set_at((min(x + 1, largura - 1), min(y + 1, altura - 1)),
                        (0, 0, 0, alfa))
    surf = pygame.transform.smoothscale(surf, (largura, altura))
    _CACHE_VIGNETTE[chave] = surf
    return surf


def desenhar_vignette(tela: pygame.Surface, intensidade: float = 0.85,
                      raio_interno: float = 0.55) -> None:
    """Draw the vignette overlay."""
    w, h = tela.get_size()
    tela.blit(superficie_vignette(w, h, intensidade, raio_interno), (0, 0))


# ---------------------------------------------------------------------------
# Cartoon style: thick borders, rounded corners, bubble buttons
# ---------------------------------------------------------------------------

def painel_cartoon(cor_borda: Tuple[int, ...], rect: pygame.Rect,
                   cor_fundo: Tuple[int, int, int] = (18, 18, 35),
                   raio_canto: int = 22, espessura_borda: int = 5,
                   alpha: int = 240, glow_raio: int = 20) -> pygame.Surface:
    """Cartoon-style panel: thick black outline + rounded fill."""
    chave = ("cartoon", tuple(cor_borda[:3]), tuple(cor_fundo[:3]),
             rect.size, raio_canto, espessura_borda, alpha, glow_raio)
    if chave in _CACHE_PAINEL_CARTOON:
        return _CACHE_PAINEL_CARTOON[chave]

    pad = 20
    w, h = rect.w, rect.h
    surf = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)

    if glow_raio > 0:
        glow = luz_radial(cor_borda, max(w, h) // 2, 0.6)
        surf.blit(glow, glow.get_rect(center=((w + pad * 2) // 2,
                                               (h + pad * 2) // 2)))

    contorno = pygame.Surface((w + 8, h + 8), pygame.SRCALPHA)
    pygame.draw.rect(contorno, (0, 0, 0, 160), (4, 4, w, h),
                     border_radius=raio_canto + 4)
    surf.blit(contorno, (pad - 4, pad - 4))

    fundo = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(fundo, tuple(cor_fundo[:3]) + (alpha,),
                     (0, 0, w, h), border_radius=raio_canto)
    surf.blit(fundo, (pad, pad))

    borda_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(borda_surf, tuple(cor_borda[:3]) + (255,),
                     (0, 0, w, h), espessura_borda, border_radius=raio_canto)
    surf.blit(borda_surf, (pad, pad))

    highlight = pygame.Surface((w - 20, h // 3), pygame.SRCALPHA)
    for i in range(h // 6):
        t_i = i / (h // 6)
        alfa = int(45 * (1 - t_i))
        pygame.draw.rect(highlight, (255, 255, 255, alfa),
                         (0, i, w - 20, 1), border_radius=8)
    surf.blit(highlight, (pad + 10, pad + 8))

    _CACHE_PAINEL_CARTOON[chave] = surf
    return surf


def desenhar_painel_cartoon(tela: pygame.Surface, cor_borda: Tuple[int, ...],
                            rect: pygame.Rect,
                            cor_fundo: Tuple[int, int, int] = (18, 18, 35),
                            raio_canto: int = 22, espessura_borda: int = 5,
                            alpha: int = 240, glow_raio: int = 20) -> None:
    """Draw a cartoon panel."""
    surf = painel_cartoon(cor_borda, rect, cor_fundo, raio_canto,
                          espessura_borda, alpha, glow_raio)
    tela.blit(surf, (rect.x - 20, rect.y - 20))


def botao_cartoon(texto: str, rect: pygame.Rect,
                  cor_fundo: Tuple[int, ...],
                  cor_borda: "Tuple[int, ...] | None" = None,
                  fonte: "pygame.font.Font | None" = None,
                  hover: bool = False,
                  habilitado: bool = True) -> Tuple[pygame.Surface, Tuple[int, int]]:
    """Cartoon button: rounded fill, thick border, text with shadow.

    Returns ``(surface, absolute_position)`` for blitting.
    """
    if cor_borda is None:
        cor_borda = tuple(min(255, c + 60) for c in cor_fundo[:3])

    x, y, w, h = rect
    pad = 4
    surf = pygame.Surface((w + pad * 2, h + pad * 2 + 6), pygame.SRCALPHA)

    sombra = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(sombra, (0, 0, 0, 100), (0, 0, w, h),
                     border_radius=h // 2)
    surf.blit(sombra, (pad, pad + 6))

    cor = cor_fundo
    if hover and habilitado:
        cor = tuple(min(255, c + 30) for c in cor_fundo[:3])
    fundo = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(fundo, tuple(cor[:3]) + (240,), (0, 0, w, h),
                     border_radius=h // 2)
    surf.blit(fundo, (pad, pad))

    borda_s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(borda_s, tuple(cor_borda[:3]) + (255,),
                     (0, 0, w, h), 4, border_radius=h // 2)
    surf.blit(borda_s, (pad, pad))

    hl = pygame.Surface((w - 16, h // 3), pygame.SRCALPHA)
    for i in range(h // 5):
        t_i = i / (h // 5)
        a = int(50 * (1 - t_i))
        pygame.draw.rect(hl, (255, 255, 255, a), (0, i, w - 16, 1),
                         border_radius=4)
    surf.blit(hl, (pad + 8, pad + 5))

    if fonte:
        txt_surf = fonte.render(texto, True, (255, 255, 255))
        sombra_txt = fonte.render(texto, True, (0, 0, 0))
        sombra_txt.set_alpha(120)
        tx = (w - txt_surf.get_width()) // 2
        ty = (h - txt_surf.get_height()) // 2
        surf.blit(sombra_txt, (pad + tx + 2, pad + ty + 2))
        surf.blit(txt_surf, (pad + tx, pad + ty))

    return surf, (x - pad, y - pad)


def desenhar_botao_cartoon(tela: pygame.Surface, texto: str,
                           rect: pygame.Rect, cor_fundo: Tuple[int, ...],
                           cor_borda: "Tuple[int, ...] | None" = None,
                           fonte: "pygame.font.Font | None" = None,
                           hover: bool = False,
                           habilitado: bool = True) -> pygame.Rect:
    """Draw a cartoon button and return the bounding rect."""
    surf, pos = botao_cartoon(texto, rect, cor_fundo, cor_borda, fonte,
                              hover, habilitado)
    tela.blit(surf, pos)
    return pygame.Rect(pos[0], pos[1], surf.get_width(), surf.get_height())


def desenhar_estrela(tela: pygame.Surface,
                     centro: Tuple[float, float], raio: float,
                     cor: Tuple[int, ...], pontas: int = 5,
                     rotacao: float = 0.0) -> None:
    """Cartoon star with shadow and highlight."""
    cx, cy = centro
    pontos: list = []
    for i in range(pontas * 2):
        angulo = math.radians(rotacao + i * 360 / (pontas * 2) - 90)
        r = raio if i % 2 == 0 else raio * 0.4
        pontos.append((cx + r * math.cos(angulo), cy + r * math.sin(angulo)))
    sombra_pts = [(p[0] + 2, p[1] + 3) for p in pontos]
    pygame.draw.polygon(tela, (0, 0, 0, 80), sombra_pts)
    pygame.draw.polygon(tela, tuple(cor[:3]), pontos)
    pygame.draw.polygon(tela, (0, 0, 0), pontos, 2)
    pygame.draw.circle(tela, (255, 255, 255, 180),
                       (int(cx - raio * 0.2), int(cy - raio * 0.2)),
                       max(2, int(raio // 4)))
