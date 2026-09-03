"""Full HUD (Heads-Up Display) system for INCARNATE.

High-tech sci-fi military spaceship interface with cinematic visual identity:
deep purple + deep blue + cyan + magenta, with white details. All elements sit
at the screen edges (centre free for gameplay) and use the responsive Layout
system, scaling from 1920x1080 down to smaller screens.

Migrated from game/hud.py -- the complete HUD system preserved with full logic.
"""

import colorsys
import math
from typing import Any, Dict, Optional, Tuple

import pygame

from src.infrastructure.graphics.fonts import fonte_texto, fonte_titulo
from src.infrastructure.graphics.geometry import losango
from src.infrastructure.graphics.smooth_rendering import (
    barra_suave,
    desenhar_cantos,
    desenhar_circulo,
    desenhar_glow,
    desenhar_painel,
    desenhar_poligono,
    linha_suave,
)
from src.infrastructure.ui.layout import Layout

AZUL_PROFUNDO = (9, 11, 26)
CIANO_HUD = (25, 217, 255)
MAGENTA_HUD = (255, 23, 107)
BRANCO_HUD = (244, 244, 247)
CINZA_HUD = (150, 158, 200)
VIDA_COR = (255, 96, 140)
ESCUDO_COR = CIANO_HUD
BOOST_COR = CIANO_HUD
ENERGIA_COR = (150, 116, 255)
ESPECIAL_COR = MAGENTA_HUD
OURO_HUD = (255, 200, 87)

SEGMENTOS_VIDA = 12
SEGMENTOS_BOSS = 16

PALETA_HUD_PADRAO = {
    "primaria": CIANO_HUD,
    "secundaria": MAGENTA_HUD,
    "energia": ENERGIA_COR,
    "fundo": AZUL_PROFUNDO,
}


def _cor_vivida(cor: tuple, brilho: float = 0.82,
                saturacao: float = 0.62) -> Tuple[int, int, int]:
    r, g, b = (max(0, min(255, int(c))) for c in cor[:3])
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    v = max(v, brilho)
    s = max(s, saturacao)
    r, g, b = colorsys.hsv_to_rgb(h, min(1.0, s), min(1.0, v))
    return (int(r * 255), int(g * 255), int(b * 255))


def _paleta_fase(cenario: Any) -> Dict[str, tuple]:
    cores = getattr(cenario, "cores_principais", None) or []
    if len(cores) < 2:
        return dict(PALETA_HUD_PADRAO)
    primaria = _cor_vivida(cores[0])
    secundaria = _cor_vivida(cores[1])
    energia = _cor_vivida(cores[2] if len(cores) > 2 else cores[0])
    fundo = tuple(max(6, int(c * 0.34)) for c in primaria[:3])
    return {"primaria": primaria, "secundaria": secundaria,
            "energia": energia, "fundo": fundo}


def _render(fonte: pygame.font.Font, texto: str, cor: tuple) -> pygame.Surface:
    return fonte.render(texto, True, cor[:3])


def _blit_alfa(tela: pygame.Surface, surf: pygame.Surface,
               pos: Any, alfa: int = 255) -> None:
    if alfa <= 0:
        return
    if alfa >= 255:
        tela.blit(surf, pos)
    else:
        s = surf.copy()
        s.set_alpha(alfa)
        tela.blit(s, pos)


def _painel(tela: pygame.Surface, layout: Layout, rect: pygame.Rect,
            cor_borda: tuple, alpha: int = 150, raio: int = 12,
            glow: int = 14, fundo: tuple = AZUL_PROFUNDO) -> None:
    desenhar_painel(tela, cor_borda, rect,
                    cor_fundo=fundo, raio_canto=raio, alpha=alpha,
                    glow_raio=glow)
    desenhar_cantos(tela, tuple(min(255, c + 70) for c in cor_borda[:3]),
                    rect, tamanho=layout.px(9), espessura=2)


def _barra_segmentada(tela: pygame.Surface, layout: Layout,
                      rect: pygame.Rect, fracao: float, cor: tuple,
                      segmentos: int = 12, raio_canto: int = 3) -> None:
    fracao = max(0.0, min(1.0, fracao))
    preenchidos = int(round(fracao * segmentos))
    vaos = layout.px(2)
    larg_seg = (rect.w - vaos * (segmentos - 1)) // segmentos
    for i in range(segmentos):
        x = rect.x + i * (larg_seg + vaos)
        seg = pygame.Rect(x, rect.y, larg_seg, rect.h)
        if i < preenchidos:
            barra_suave(tela, seg.x, seg.y, seg.w, seg.h, 1.0, cor,
                        fundo=(26, 32, 66), raio_canto=raio_canto)
            desenhar_glow(tela, cor, seg.center, max(2, seg.h), 0.35)
        else:
            barra_suave(tela, seg.x, seg.y, seg.w, seg.h, 1.0,
                        (44, 50, 82), fundo=(18, 22, 48), raio_canto=raio_canto)


def _barra_fina(tela: pygame.Surface, layout: Layout,
                rect: pygame.Rect, fracao: float, cor: tuple,
                brilho: bool = True) -> None:
    fracao = max(0.0, min(1.0, fracao))
    barra_suave(tela, rect.x, rect.y, rect.w, rect.h, fracao, cor,
                fundo=(28, 34, 66), raio_canto=2,
                glow=(brilho and fracao > 0 and fracao < 1.0))


def _arc(surf: pygame.Surface, centro: Tuple[float, float], raio: float,
         inicio: float, fim: float, cor: tuple, espessura: int,
         alpha: int = 255) -> None:
    passos = max(8, int(abs(fim - inicio) / (math.pi / 36)))
    pontos = [(int(centro[0] + math.cos(inicio + (fim - inicio) * i / passos)
                    * raio),
               int(centro[1] + math.sin(inicio + (fim - inicio) * i / passos)
                   * raio))
              for i in range(passos + 1)]
    if alpha >= 255:
        linha_suave(surf, cor, pontos[0], pontos[-1], espessura)
        return
    for i in range(len(pontos) - 1):
        linha_suave(surf, cor, pontos[i], pontos[i + 1], espessura)


def _medidor_circular(tela: pygame.Surface, layout: Layout,
                      centro: Tuple[float, float], raio: float,
                      fracao: float, cor: tuple,
                      rotulo: Optional[str] = None,
                      valor: Optional[str] = None) -> None:
    r = raio
    fracao = max(0.0, min(1.0, fracao))
    pad = layout.px(14)
    ext = int(r * 2 + pad * 2)
    surf = pygame.Surface((ext, ext), pygame.SRCALPHA)
    local = (pad + r, pad + r)
    for i in range(12):
        a = -math.pi / 2 + i * math.tau / 12
        r0 = r - layout.px(5)
        r1 = r - layout.px(8)
        p0 = (local[0] + math.cos(a) * r0, local[1] + math.sin(a) * r0)
        p1 = (local[0] + math.cos(a) * r1, local[1] + math.sin(a) * r1)
        cor_tick = (170, 180, 215) if (i % 3 == 0) else (66, 72, 104)
        linha_suave(surf, cor_tick, p0, p1, layout.px(2))
    _arc(surf, local, r - layout.px(3), 0, math.tau, (56, 64, 100),
         layout.px(5), 150)
    if fracao > 0.01:
        fim = -math.pi / 2 + fracao * math.tau
        _arc(surf, local, r - layout.px(3), -math.pi / 2, fim, cor,
             layout.px(5), 255)
        px = local[0] + math.cos(fim) * (r - layout.px(3))
        py = local[1] + math.sin(fim) * (r - layout.px(3))
        desenhar_glow(surf, cor, (px, py), layout.px(8), 0.9)
        desenhar_circulo(surf, cor, (px, py), layout.px(2), brilho=1.4)
    tela.blit(surf, (int(centro[0]) - pad - r, int(centro[1]) - pad - r))
    if valor is not None:
        fonte = fonte_titulo(layout.px(16))
        surf_v = fonte.render(valor, True, BRANCO_HUD)
        _blit_alfa(tela, surf_v, surf_v.get_rect(center=centro), 235)
    if rotulo:
        fonte = fonte_texto(layout.px(11))
        surf_r = fonte.render(rotulo, True, CINZA_HUD)
        _blit_alfa(tela, surf_r,
                   surf_r.get_rect(center=(centro[0], centro[1] +
                                           layout.px(14))), 210)


def _icone_nave(tela: pygame.Surface, centro: Tuple[float, float],
                escala: float, cor: tuple = BRANCO_HUD) -> None:
    c = escala
    pts = [(centro[0], centro[1] - 10 * c),
           (centro[0] + 7 * c, centro[1] + 4 * c),
           (centro[0] + 3 * c, centro[1] + 7 * c),
           (centro[0] - 3 * c, centro[1] + 7 * c),
           (centro[0] - 7 * c, centro[1] + 4 * c)]
    desenhar_glow(tela, cor, centro, 9 * c, 0.8)
    desenhar_poligono(tela, cor, pts)
    desenhar_poligono(tela, (255, 255, 255), [
        (centro[0] - 2 * c, centro[1] - 1 * c),
        (centro[0] + 2 * c, centro[1] - 1 * c),
        (centro[0], centro[1] + 5 * c)])


def _icone_arma(tela: pygame.Surface, tipo: str,
                centro: Tuple[float, float], cor: tuple,
                escala: float = 1.0) -> None:
    x, y = centro
    c = escala
    if tipo == "laser":
        desenhar_glow(tela, cor, (x, y), 8 * c, 0.6)
        pygame.draw.line(tela, cor, (x, y - 8 * c), (x, y + 8 * c), int(2 * c))
        pygame.draw.line(tela, BRANCO_HUD, (x, y - 8 * c), (x, y - 2 * c),
                         int(1 * c))
    elif tipo == "duplo":
        for s in (-1, 1):
            desenhar_glow(tela, cor, (x + s * 4 * c, y), 5 * c, 0.5)
            pygame.draw.line(tela, cor, (x + s * 6 * c, y - 8 * c),
                             (x + s * 6 * c, y + 8 * c), int(2 * c))
    elif tipo == "plasma":
        desenhar_glow(tela, cor, (x, y), 8 * c, 0.9)
        desenhar_circulo(tela, cor, (x, y), int(5 * c))
        desenhar_circulo(tela, BRANCO_HUD, (x, y), int(2 * c), brilho=1.4)
    elif tipo == "metralhadora":
        for i in range(3):
            dx = (i - 1) * 3 * c
            pygame.draw.line(tela, cor, (x + dx, y - 8 * c),
                             (x + dx, y + 8 * c), int(2 * c))
    elif tipo == "espiral":
        for i in range(3):
            a = i * math.tau / 3
            p0 = (x + math.cos(a) * 6 * c, y + math.sin(a) * 6 * c)
            desenhar_circulo(tela, cor, p0, int(2 * c))
    elif tipo == "ion":
        desenhar_glow(tela, cor, (x, y), 8 * c, 0.7)
        pygame.draw.rect(tela, cor, (int(x - 3 * c), int(y - 8 * c),
                                     int(6 * c), int(16 * c)),
                         border_radius=int(3 * c))
        pygame.draw.line(tela, BRANCO_HUD, (x, y - 8 * c), (x, y + 8 * c),
                         int(1 * c))
    elif tipo == "gauss":
        for s in (-1, 1):
            pygame.draw.line(tela, cor, (x, y - 8 * c), (x + s * 7 * c, y),
                             int(2 * c))
            pygame.draw.line(tela, cor, (x, y + 8 * c), (x + s * 7 * c, y),
                             int(2 * c))
    elif tipo == "nova":
        for i in range(6):
            a = i * math.tau / 6
            p0 = (x + math.cos(a) * 3 * c, y + math.sin(a) * 3 * c)
            p1 = (x + math.cos(a) * 8 * c, y + math.sin(a) * 8 * c)
            pygame.draw.line(tela, cor, p0, p1, int(1 * c))
        desenhar_circulo(tela, cor, (x, y), int(2 * c))
    else:
        desenhar_glow(tela, cor, (x, y), 6 * c, 0.6)
        desenhar_circulo(tela, cor, (x, y), int(3 * c))
        desenhar_circulo(tela, BRANCO_HUD, (x, y), int(1 * c), brilho=1.4)


def _icone_abates(tela: pygame.Surface, centro: Tuple[float, float],
                  cor: tuple = CINZA_HUD, escala: float = 1.0) -> None:
    x, y = centro
    c = escala
    desenhar_glow(tela, cor, (x, y), 6 * c, 0.4)
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        pygame.draw.line(tela, cor, (x + dx * 6 * c, y + dy * 6 * c),
                         (x + dx * 8 * c, y + dy * 8 * c), int(2 * c))
    pygame.draw.circle(tela, cor, (int(x), int(y)), int(4 * c), 1)


def _numero(tela: pygame.Surface, layout: Layout, fonte: pygame.font.Font,
            valor: Any, pos: Tuple[float, float], cor: tuple,
            alinhar: str = "centro", alfa: int = 255) -> pygame.Rect:
    if isinstance(valor, (int, float)):
        texto = f"{valor:,.0f}".replace(",", ".")
    else:
        texto = str(valor)
    surf = _render(fonte, texto, cor)
    rect = surf.get_rect()
    if alinhar == "direita":
        rect.topright = pos
    elif alinhar == "esquerda":
        rect.topleft = pos
    else:
        rect.center = pos
    _blit_alfa(tela, surf, rect, alfa)
    return rect


class HudJogo:
    """Renders the full combat HUD over the logical surface."""

    def __init__(self, layout: Optional[Layout] = None):
        self.layout = layout or Layout()
        l = self.layout
        self._f_padrao_xxs = l.fonte_texto(12)
        self._f_padrao_xs = l.fonte_texto(15)
        self._f_padrao_s = l.fonte_texto(18)
        self._f_padrao_m = l.fonte_texto(22)
        self._f_titulo_xs = l.fonte_titulo(13)
        self._f_titulo_s = l.fonte_titulo(17)
        self._f_titulo_m = l.fonte_titulo(24)
        self._f_titulo_g = l.fonte_titulo(34)
        self._f_numero = l.fonte_titulo(30)
        self._paleta: Dict[str, tuple] = dict(PALETA_HUD_PADRAO)

    def _dados(self, jogo: Any) -> Dict[str, Any]:
        jog = jogo.jogador
        arma_atual = getattr(jog, "arma_atual", 0)
        arma: Dict[str, Any] = {"nome": "LASER", "tipo": "laser",
                                "cor": CIANO_HUD, "nivel": 1, "cooldown": 10,
                                "qtd": 1}
        if hasattr(jogo, "_armaria") and jogo._armaria:
            arma = jogo._armaria[arma_atual % len(jogo._armaria)]
        elif hasattr(jogo, "armaria") and jogo.armaria:
            arma = jogo.armaria[arma_atual % len(jogo.armaria)]
        recordes = getattr(jogo, "recordes", []) or []
        combo = getattr(jog, "combo", None)
        combo_atual = combo.combo_atual if combo else 0
        bonus = combo.get_bonus() if combo else 1.0
        restantes = (len(getattr(jogo, "fila_onda", [])) +
                     len(getattr(jogo, "inimigos", [])))
        progresso = max(0.0, min(1.0, 1 - restantes / 22.0))
        if arma.get("tipo") == "metralhadora":
            qtd = arma.get("qtd", 1)
            burst_left = getattr(jog, "burst_left", 0)
            municao = 1 - max(0, burst_left) / max(1, qtd)
        else:
            cooldown = max(1, arma.get("cooldown", 10))
            municao = 1 - max(0, getattr(jog, "cooldown_tiro", 0)) / cooldown
        return {
            "vida": getattr(jog, "vida", 100),
            "vida_max": getattr(jog, "max_vida", 100),
            "escudo": bool(getattr(jog, "escudo", False)),
            "pontos": getattr(jog, "pontuacao", 0),
            "recorde": (recordes[0]["pontos"] if recordes else 0),
            "abates": getattr(jogo, "inimigos_abates", 0),
            "combo": combo_atual,
            "bonus": bonus,
            "nivel": getattr(jog, "nivel", 1),
            "cenario": getattr(getattr(jogo, "cenario", None), "id", 1),
            "regiao": getattr(getattr(jogo, "cenario", None), "nome", "DEEP SPACE"),
            "progresso": progresso,
            "arma": arma,
            "municao": municao,
            "boost": max(0.0, min(1.0, getattr(jogo, "boost", 1.0))),
            "especial": max(0.0, min(1.0, getattr(jogo, "especial", 0.0))),
            "especial_nome": {
                "bomba": "BOMBA", "cura": "REPARO +3",
                "imortal": "IMORTALIDADE",
            }.get(getattr(jogo, "especial_atual", "bomba"), "ESPECIAL"),
            "energia": max(0.0, min(100.0, getattr(jogo, "energia", 100.0))),
            "vel": getattr(jog, "velocidade", 5.0),
            "boss": getattr(jogo, "boss", None),
        }

    def desenhar(self, tela: pygame.Surface, jogo: Any,
                 tempo: Optional[float] = None) -> Dict[str, Any]:
        self._paleta = _paleta_fase(getattr(jogo, "cenario", None))
        d = self._dados(jogo)
        t = (pygame.time.get_ticks() * 0.001) if tempo is None else tempo
        self._topo_esquerda(tela, d, t)
        self._topo_direita(tela, d, t)
        self._topo_centro(tela, d, t)
        self._base_esquerda(tela, d, t)
        self._base_direita(tela, d, t)
        self._base_centro(tela, d, t)
        self._barra_boss(tela, d, t)
        return d

    def _topo_esquerda(self, tela: pygame.Surface, d: dict, t: float) -> None:
        l = self.layout
        m = l.margem(14)
        largura = l.px(232)
        altura = l.px(96)
        painel = pygame.Rect(m, m, largura, altura)
        _painel(tela, l, painel, self._paleta["primaria"], alpha=140, glow=10,
                fundo=self._paleta["fundo"])
        badge_c = (painel.x + l.px(30), painel.y + l.px(30))
        desenhar_poligono(tela, (52, 66, 110),
                          losango(badge_c, l.px(26), l.px(30)),
                          espessura=1, glow_cor=self._paleta["primaria"],
                          glow_raio=8)
        _icone_nave(tela, badge_c, l.escala * 1.15, BRANCO_HUD)
        x0 = painel.x + l.px(62)
        rotulo = _render(self._f_titulo_xs, "PLAYER 01", CINZA_HUD)
        _blit_alfa(tela, rotulo, (x0, painel.y + l.px(14)), 210)
        pulsar = 0.72 + 0.28 * math.sin(t * 2.4)
        status = _render(self._f_padrao_xxs,
                         "SISTEMAS ONLINE" if d["vida"] > 0 else "DANO CRITICO",
                         tuple(int(c * pulsar) for c in VIDA_COR))
        _blit_alfa(tela, status, (x0, painel.y + l.px(30)), 200)
        by = painel.y + l.px(44)
        barra = pygame.Rect(x0, by, l.px(128), l.px(9))
        _barra_segmentada(tela, l, barra, d["vida"] / max(1, d["vida_max"]),
                          VIDA_COR, SEGMENTOS_VIDA)
        _numero(tela, l, self._f_padrao_s, f"{d[chr(118)+chr(105)+chr(100)+chr(97)]}/{d[chr(118)+chr(105)+chr(100)+chr(97)+chr(95)+chr(109)+chr(97)+chr(120)]}",
                (painel.right - l.px(10), by + l.px(5)), VIDA_COR, "direita", 235)
        sy = by + l.px(14)
        escudo_frac = 1.0 if d["escudo"] else 0.0
        if d["escudo"]:
            pulso2 = 0.75 + 0.25 * math.sin(t * 3)
            cor_escudo = tuple(int(c * pulso2) for c in self._paleta["primaria"])
        else:
            cor_escudo = self._paleta["primaria"]
        barra_escudo = pygame.Rect(x0, sy, l.px(128), l.px(5))
        _barra_fina(tela, l, barra_escudo, escudo_frac, cor_escudo,
                    brilho=d["escudo"])
        rot_esc = _render(self._f_padrao_xxs, "SHIELD", (120, 150, 210))
        _blit_alfa(tela, rot_esc, (x0, sy - l.px(2)), 180)
        ey = sy + l.px(10)
        frac_energia = d["energia"] / 100.0
        barra_energia = pygame.Rect(x0, ey, l.px(128), l.px(5))
        _barra_fina(tela, l, barra_energia, frac_energia, self._paleta["energia"])
        rot_ener = _render(self._f_padrao_xxs, "ENERGY", (150, 132, 240))
        _blit_alfa(tela, rot_ener, (x0, ey - l.px(2)), 180)
        _numero(tela, l, self._f_padrao_xxs, f"{int(d['energia'])}",
                (painel.right - l.px(10), ey + l.px(1)),
                self._paleta["energia"], "direita", 210)

    def _topo_direita(self, tela: pygame.Surface, d: dict, t: float) -> None:
        l = self.layout
        m = l.margem(14)
        largura = l.px(228)
        altura = l.px(96)
        painel = pygame.Rect(l.largura - m - largura, m, largura, altura)
        _painel(tela, l, painel, self._paleta["secundaria"], alpha=140,
                glow=10, fundo=self._paleta["fundo"])
        x = painel.right - l.px(12)
        rotulo = _render(self._f_titulo_xs, "SCORE", CINZA_HUD)
        _blit_alfa(tela, rotulo, (x - rotulo.get_width(), painel.y + l.px(10)), 210)
        _numero(tela, l, self._f_numero, d["pontos"],
                (x, painel.y + l.px(28)), BRANCO_HUD, "direita", 245)
        surf_hi = _render(self._f_padrao_xxs, "HIGH SCORE", (120, 130, 170))
        _blit_alfa(tela, surf_hi, (painel.x + l.px(12), painel.y + l.px(14)), 190)
        _numero(tela, l, self._f_padrao_s, d["recorde"],
                (painel.x + l.px(12), painel.y + l.px(32)), OURO_HUD, "esquerda", 215)
        y_abates = painel.y + l.px(56)
        _icone_abates(tela, (painel.x + l.px(24), y_abates), CINZA_HUD, l.escala)
        _numero(tela, l, self._f_padrao_s, d["abates"],
                (painel.x + l.px(38), y_abates + l.px(1)), CINZA_HUD, "esquerda", 220)
        rot_ab = _render(self._f_padrao_xxs, "ABATES", (110, 118, 160))
        _blit_alfa(tela, rot_ab, (painel.x + l.px(64), y_abates - l.px(4)), 180)
        if d["combo"] > 1:
            comb_x = x - l.px(12)
            mult = _render(self._f_titulo_s, f"x{d['bonus']:.1f}", (255, 214, 110))
            _blit_alfa(tela, mult, (comb_x - mult.get_width(), painel.y + l.px(56)), 240)
            fracao = min(1.0, d["combo"] / 20.0)
            barra = pygame.Rect(comb_x - l.px(64), painel.y + l.px(78), l.px(60), l.px(4))
            _barra_fina(tela, l, barra, fracao, OURO_HUD)
            rot_combo = _render(self._f_padrao_xxs, f"COMBO {d['combo']}", (200, 170, 90))
            _blit_alfa(tela, rot_combo, (comb_x - rot_combo.get_width(), painel.y + l.px(82)), 200)

    def _topo_centro(self, tela: pygame.Surface, d: dict, t: float) -> None:
        l = self.layout
        cx = l.largura // 2
        y = l.margem(16)
        setor = _render(self._f_titulo_m, f"SECTOR {d['cenario']:02d}", BRANCO_HUD)
        rect_setor = setor.get_rect(center=(cx, y + l.px(16)))
        _blit_alfa(tela, setor, rect_setor, 240)
        for s in (-1, 1):
            pygame.draw.line(tela, (90, 100, 150),
                             (rect_setor.left - l.px(22), rect_setor.centery),
                             (rect_setor.left - l.px(6), rect_setor.centery), 1)
            pygame.draw.line(tela, (90, 100, 150),
                             (rect_setor.right + l.px(6), rect_setor.centery),
                             (rect_setor.right + l.px(22), rect_setor.centery), 1)
        regiao = _render(self._f_titulo_xs, d["regiao"], self._paleta["primaria"])
        _blit_alfa(tela, regiao, regiao.get_rect(center=(cx, y + l.px(38))), 230)
        largura = l.px(280)
        barra = pygame.Rect(cx - largura // 2, y + l.px(50), largura, l.px(4))
        _barra_fina(tela, l, barra, d["progresso"], self._paleta["primaria"], brilho=False)

    def _base_esquerda(self, tela: pygame.Surface, d: dict, t: float) -> None:
        l = self.layout
        m = l.margem(14)
        centro = (m + l.px(46), l.altura - m - l.px(58))
        raio = l.px(38)
        fracao = d["boost"]
        if fracao < 0.25:
            pulso = 0.55 + 0.45 * abs(math.sin(t * 5))
            cor = tuple(int(c * pulso) for c in self._paleta["primaria"])
        else:
            cor = self._paleta["primaria"]
        _medidor_circular(tela, l, centro, raio, fracao, cor,
                          rotulo="BOOST", valor=f"{int(fracao * 100)}%")
        vx = centro[0]
        vy = centro[1] + raio + l.px(20)
        vel = _render(self._f_padrao_s, f"VEL {d['vel']:.1f}", (170, 178, 220))
        _blit_alfa(tela, vel, vel.get_rect(center=(vx, vy)), 220)
        barra_vel = pygame.Rect(vx - l.px(30), vy + l.px(10), l.px(60), l.px(3))
        _barra_fina(tela, l, barra_vel, min(1.0, d["vel"] / 12.0),
                    self._paleta["primaria"], brilho=False)

    def _base_direita(self, tela: pygame.Surface, d: dict, t: float) -> None:
        l = self.layout
        m = l.margem(14)
        arma = d["arma"]
        largura = l.px(232)
        altura = l.px(92)
        painel = pygame.Rect(l.largura - m - largura, l.altura - m - altura,
                             largura, altura)
        _painel(tela, l, painel, arma["cor"], alpha=140, glow=10,
                fundo=self._paleta["fundo"])
        badge_c = (painel.x + l.px(28), painel.y + l.px(30))
        desenhar_poligono(tela, (52, 66, 110),
                          losango(badge_c, l.px(24), l.px(26)),
                          espessura=1, glow_cor=arma["cor"], glow_raio=8)
        _icone_arma(tela, arma["tipo"], badge_c, arma["cor"], l.escala * 1.1)
        x0 = painel.x + l.px(58)
        nome = _render(self._f_titulo_s, arma["nome"].upper(), BRANCO_HUD)
        _blit_alfa(tela, nome, (x0, painel.y + l.px(12)), 240)
        nivel = _render(self._f_padrao_xxs, f"LVL {arma['nivel']:02d}", CINZA_HUD)
        _blit_alfa(tela, nivel, (x0, painel.y + l.px(30)), 200)
        cy = painel.y + l.px(48)
        barra = pygame.Rect(x0, cy, l.px(118), l.px(6))
        _barra_segmentada(tela, l, barra, d["municao"], arma["cor"], 8,
                          raio_canto=2)
        rot_carga = _render(self._f_padrao_xxs,
                            "CARREGANDO" if d["municao"] < 1.0 else "LISTO",
                            (150, 158, 200) if d["municao"] < 1.0 else arma["cor"])
        _blit_alfa(tela, rot_carga, (x0, cy + l.px(8)), 200)

    def _base_centro(self, tela: pygame.Surface, d: dict, t: float) -> None:
        l = self.layout
        cx = l.largura // 2
        largura = l.px(236)
        altura = l.px(10)
        m = l.margem(14)
        y = l.altura - m - altura
        barra = pygame.Rect(cx - largura // 2, y, largura, altura)
        pronto = d["especial"] >= 1.0
        cor = (self._paleta["secundaria"] if pronto
               else tuple(int(c * 0.42) for c in self._paleta["secundaria"]))
        _barra_segmentada(tela, l, barra, d["especial"], cor, 10, raio_canto=2)
        rotulo = _render(self._f_titulo_xs, d["especial_nome"], CINZA_HUD)
        _blit_alfa(tela, rotulo, (barra.x + l.px(6), barra.y + l.px(12)), 200)
        if pronto:
            pulso = 0.7 + 0.3 * math.sin(t * 4)
            desenhar_glow(tela, self._paleta["secundaria"], barra.center,
                          max(barra.w, barra.h), 0.5 * pulso)
            surf = _render(self._f_titulo_xs, f"{d['especial_nome']} READY",
                           tuple(int(c * pulso) for c in self._paleta["secundaria"]))
            _blit_alfa(tela, surf,
                       surf.get_rect(midright=(barra.right - l.px(6),
                                               barra.y + l.px(12))), 235)

    def _barra_boss(self, tela: pygame.Surface, d: dict, t: float) -> None:
        boss = d["boss"]
        if not boss:
            return
        l = self.layout
        cx = l.largura // 2
        largura = l.px(540)
        altura = l.px(16)
        y = l.margem(58)
        barra = pygame.Rect(cx - largura // 2, y, largura, altura)
        fracao = max(0.0, min(1.0, boss.vida / max(1, boss.vida_max)))
        nome = _render(self._f_titulo_s, boss.nome, BRANCO_HUD)
        rect_nome = nome.get_rect(center=(cx, y - l.px(12)))
        _blit_alfa(tela, nome, rect_nome, 245)
        for s in (-1, 1):
            pygame.draw.line(tela, OURO_HUD,
                             (rect_nome.right if s < 0 else rect_nome.left,
                              rect_nome.centery),
                             (barra.right if s < 0 else barra.left,
                              rect_nome.centery), 1)
        _painel(tela, l, barra.inflate(l.px(16), l.px(14)),
                OURO_HUD, alpha=120, raio=14, glow=16)
        _barra_segmentada(tela, l, barra, fracao, OURO_HUD, SEGMENTOS_BOSS,
                          raio_canto=4)
        desenhar_glow(tela, OURO_HUD, barra.center, max(barra.w, barra.h), 0.25)
