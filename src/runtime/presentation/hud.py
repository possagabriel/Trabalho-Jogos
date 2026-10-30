"""HUD de combate profissional do INCARNATE.

Interface de nave espacial militar de alta tecnologia, em identidade visual
sci-fi cinematografica: roxo escuro + azul profundo + ciano + magenta, com
detalhes em branco. Todos os elementos ficam nas bordas da tela (centro
livre para o gameplay) e usam ``src.infrastructure.ui.layout``, entao
escalam de 1920x1080 ate telas menores preservando as proporcoes.

Componentes:
  - canto superior esquerdo: piloto, casco, alerta crítico, escudo e energia;
  - canto superior direito: pontuação, recorde, abates e tempo do combo;
  - topo central: setor, onda, nome da região e progresso da fase;
  - canto inferior esquerdo: impulso, velocidade e atalho da esquiva;
  - canto inferior direito: arma equipada (icone, nome, carga, nivel);
  - base central: carga do especial, prontidão e atalho da Bomba Vortex;
  - topo (no lugar do setor): nome, fase e vida de chefes e minibosses.

Uso:

    hud = HudJogo()
    hud.desenhar(tela, jogo)   # tela = superficie logica 1280x720

O ``HudJogo`` le apenas os atributos de que precisa de ``jogo`` (duck typing),
entao funciona com o ``core.Jogo`` real ou com um objeto de demonstracao.
"""

import colorsys
import math
from functools import lru_cache
from typing import Any

import pygame

from src.core.constants import (
    ALTURA,
    DIMENSION_GOLD,
    LARGURA,
)
from src.infrastructure.graphics.comic_render import texto_tinta
from src.infrastructure.graphics.comic_theme import (
    CIANO,
    LARANJA,
    RARIDADE_ARMAS,
    RARIDADES,
    SOMBRA,
    opcoes_atuais,
)
from src.infrastructure.ui.layout import Layout
from src.runtime.domain.entities.weapons import ARMARIA
from src.runtime.infrastructure.graphics.fonts import fonte_texto, fonte_titulo
from src.runtime.infrastructure.graphics.smooth import (
    barra_suave,
    desenhar_cantos,
    desenhar_circulo,
    desenhar_painel,
    desenhar_poligono,
    linha_suave,
    retangulo_suave,
)
from src.runtime.infrastructure.graphics.style_tokens import (
    CONTRASTE_TEXTO_HUD_AJUSTE,
    CONTRASTE_TEXTO_MINIMO,
    FUNDO_TEXTO_HUD,
    HUD_COR_ALERTA,
    HUD_COR_CIANO,
    HUD_COR_DOURADO,
    HUD_COR_ENERGIA,
    HUD_COR_FUNDO,
    HUD_COR_TEXTO,
    HUD_COR_TEXTO_MUTED,
    HUD_ESPESSURA_CONTORNO,
    HUD_FONTE_NUMERO,
    HUD_FONTE_PADRAO_M,
    HUD_FONTE_PADRAO_S,
    HUD_FONTE_PADRAO_XS,
    HUD_FONTE_PADRAO_XXS,
    HUD_FONTE_TITULO_G,
    HUD_FONTE_TITULO_M,
    HUD_FONTE_TITULO_S,
    HUD_FONTE_TITULO_XS,
    HUD_SEGMENTOS_BOSS,
    HUD_SEGMENTOS_VIDA,
    HUD_TAMANHO_CANTO,
    OPACIDADE_PAINEL_HUD,
    TEXTO_ESSENCIAL_MIN_PX,
    TEXTO_SECUNDARIO_MIN_PX,
)

# ---------------------------------------------------------------------------
# Paleta do HUD (derivada da marca INCARNATE, nunca saturada em excesso)
# ---------------------------------------------------------------------------

AZUL_PROFUNDO = HUD_COR_FUNDO
CIANO_HUD = HUD_COR_CIANO
SECUNDARIA_HUD = HUD_COR_DOURADO
BRANCO_HUD = HUD_COR_TEXTO
CINZA_HUD = HUD_COR_TEXTO_MUTED
VIDA_COR = HUD_COR_ALERTA
ESCUDO_COR = CIANO_HUD
BOOST_COR = CIANO_HUD
ENERGIA_COR = HUD_COR_ENERGIA
ESPECIAL_COR = SECUNDARIA_HUD
OURO_HUD = DIMENSION_GOLD

# Segmentos das barras segmentadas
SEGMENTOS_VIDA = HUD_SEGMENTOS_VIDA
SEGMENTOS_BOSS = HUD_SEGMENTOS_BOSS


# ---------------------------------------------------------------------------
# Paleta do HUD por fase: o tom acompanha a dimensao em curso
# ---------------------------------------------------------------------------

PALETA_HUD_PADRAO = {
    "primaria": CIANO_HUD,
    "secundaria": SECUNDARIA_HUD,
    "energia": ENERGIA_COR,
    "fundo": AZUL_PROFUNDO,
}


def _cor_vivida(cor, brilho=0.82, saturacao=0.62):
    """Eleva o brilho/saturacao de uma cor para leitura sobre fundo escuro."""
    r, g, b = (max(0, min(255, int(c))) for c in cor[:3])
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    v = max(v, brilho)
    s = max(s, saturacao)
    r, g, b = colorsys.hsv_to_rgb(h, min(1.0, s), min(1.0, v))
    return (int(r * 255), int(g * 255), int(b * 255))


def _paleta_fase(cenario):
    """Acentos do HUD adaptados ao tom do cenario atual (fase).

    Deriva a identidade visual da dimensao em curso a partir das cores
    principais do cenario (``cores_principais``); sem elas, cai no padrao da
    marca (ciano/magenta).
    """
    if opcoes_atuais().ativo:
        return {"primaria": LARANJA, "secundaria": CIANO, "energia": LARANJA, "fundo": SOMBRA}
    cores = getattr(cenario, "cores_principais", None) or []
    if len(cores) < 2:
        return dict(PALETA_HUD_PADRAO)
    primaria = _cor_vivida(cores[0])
    secundaria = _cor_vivida(cores[1])
    energia = _cor_vivida(cores[2] if len(cores) > 2 else cores[0])
    fundo = tuple(max(6, int(c * 0.34)) for c in primaria[:3])
    return {"primaria": primaria, "secundaria": secundaria, "energia": energia, "fundo": fundo}


# ---------------------------------------------------------------------------
# Utilidades de desenho
# ---------------------------------------------------------------------------


def _render(fonte, texto, cor):
    return _texto_cacheado(fonte, str(texto), tuple(cor[:3]), opcoes_atuais().ativo)


@lru_cache(maxsize=512)
def _texto_cacheado(fonte, texto, cor, comic):
    """Reutiliza os rótulos e valores sem alterar superfícies compartilhadas."""
    if comic:
        return texto_tinta(str(texto), max(9, int(fonte.get_height() * 0.7)), tuple(cor[:3]))
    return fonte.render(texto, True, cor[:3])


@lru_cache(maxsize=256)
def _texto_limitado(fonte, texto, cor, comic, largura, altura):
    """Ajusta texto ao espaço disponível; nomes extensos recebem reticências."""
    surf = _texto_cacheado(fonte, texto, cor, comic)
    while len(texto) > 4 and surf.get_width() > largura * 1.3:
        texto = texto[:-4] + "..."
        surf = _texto_cacheado(fonte, texto, cor, comic)
    escala = min(1.0, largura / max(1, surf.get_width()), altura / max(1, surf.get_height()))
    if escala < 1:
        surf = pygame.transform.smoothscale(
            surf, (max(1, int(surf.get_width() * escala)), max(1, int(surf.get_height() * escala)))
        )
    return surf


@lru_cache(maxsize=128)
def _com_alpha(surf, alfa):
    copia = surf.copy()
    copia.set_alpha(alfa)
    return copia


def _luminancia(cor):
    """Calcula luminância relativa sRGB para a razão WCAG."""
    canais = []
    for canal in cor[:3]:
        valor = canal / 255
        canais.append(valor / 12.92 if valor <= 0.04045 else ((valor + 0.055) / 1.055) ** 2.4)
    return 0.2126 * canais[0] + 0.7152 * canais[1] + 0.0722 * canais[2]


def razao_contraste(cor_a, cor_b):
    """Retorna a razão de contraste WCAG entre duas cores RGB."""
    clara, escura = sorted((_luminancia(cor_a), _luminancia(cor_b)), reverse=True)
    return (clara + 0.05) / (escura + 0.05)


def cor_com_contraste(cor, fundo, minimo=CONTRASTE_TEXTO_MINIMO):
    """Ajusta a luminosidade preservando a cor até alcançar o contraste mínimo."""
    cor = tuple(max(0, min(255, int(c))) for c in cor[:3])
    fundo = tuple(max(0, min(255, int(c))) for c in fundo[:3])
    if razao_contraste(cor, fundo) >= minimo:
        return cor

    destino = (255, 255, 255) if _luminancia(fundo) < 0.5 else (0, 0, 0)
    baixo, alto = 0.0, 1.0
    for _ in range(8):
        fator = (baixo + alto) / 2
        candidata = tuple(round(a + (b - a) * fator) for a, b in zip(cor, destino))
        if razao_contraste(candidata, fundo) >= minimo:
            alto = fator
        else:
            baixo = fator
    return tuple(round(a + (b - a) * alto) for a, b in zip(cor, destino))


def _fonte_com_altura_efetiva(layout, tamanho_base, minimo, titulo=False):
    """Garante altura de tinta mínima, medida no glifo desenhado."""
    criar = fonte_titulo if titulo else fonte_texto
    tamanho = max(layout.px(tamanho_base), minimo)
    fonte = criar(tamanho)
    while fonte.render("Ag0", True, (255, 255, 255)).get_bounding_rect().height < minimo:
        tamanho += 1
        fonte = criar(tamanho)
    return fonte


def _blit_alfa(tela, surf, pos, alfa=255):
    if alfa <= 0:
        return
    if alfa >= 255:
        tela.blit(surf, pos)
    else:
        tela.blit(_com_alpha(surf, alfa), pos)


def _painel(tela, layout, rect, cor_borda, alpha=235, raio=8, glow=3, fundo=AZUL_PROFUNDO):
    """Painel holografico translucido com borda neon e cantos em L."""
    desenhar_painel(
        tela, cor_borda, rect, cor_fundo=fundo, raio_canto=raio, alpha=alpha, glow_raio=glow
    )
    desenhar_cantos(
        tela,
        tuple(min(255, c + 70) for c in cor_borda[:3]),
        rect,
        tamanho=layout.px(HUD_TAMANHO_CANTO),
        espessura=HUD_ESPESSURA_CONTORNO,
    )


def _barra_segmentada(tela, layout, rect, fracao, cor, segmentos=12, raio_canto=3):
    """Barra de progresso com segmentos visuais separados por vao."""
    fracao = max(0.0, min(1.0, fracao))
    preenchidos = int(round(fracao * segmentos))
    vaos = layout.px(2)
    larg_seg = (rect.w - vaos * (segmentos - 1)) // segmentos
    for i in range(segmentos):
        x = rect.x + i * (larg_seg + vaos)
        seg = pygame.Rect(x, rect.y, larg_seg, rect.h)
        if i < preenchidos:
            barra_suave(
                tela,
                seg.x,
                seg.y,
                seg.w,
                seg.h,
                1.0,
                cor,
                fundo=AZUL_PROFUNDO,
                raio_canto=raio_canto,
                glow=False,
            )
        else:
            barra_suave(
                tela,
                seg.x,
                seg.y,
                seg.w,
                seg.h,
                1.0,
                (44, 50, 82),
                fundo=AZUL_PROFUNDO,
                raio_canto=raio_canto,
                glow=False,
            )


def _barra_fina(tela, layout, rect, fracao, cor, brilho=False):
    """Barra extremamente discreta, de 4px, para progressos secundarios."""
    fracao = max(0.0, min(1.0, fracao))
    barra_suave(
        tela,
        rect.x,
        rect.y,
        rect.w,
        rect.h,
        fracao,
        cor,
        fundo=(28, 34, 66),
        raio_canto=2,
        glow=(brilho and fracao > 0 and fracao < 1.0),
    )


def _arc(surf, centro, raio, inicio, fim, cor, espessura, alpha=255):
    """Desenha um arco anti-aliased numa surface SRCALPHA."""
    passos = max(8, int(abs(fim - inicio) / (math.pi / 36)))
    pontos = [
        (
            int(centro[0] + math.cos(inicio + (fim - inicio) * i / passos) * raio),
            int(centro[1] + math.sin(inicio + (fim - inicio) * i / passos) * raio),
        )
        for i in range(passos + 1)
    ]
    for i in range(len(pontos) - 1):
        linha_suave(surf, tuple(cor[:3]) + (alpha,), pontos[i], pontos[i + 1], espessura)


def _medidor_circular(
    tela, layout, centro, raio, fracao, cor, rotulo=None, valor=None, rotulo_abaixo=False
):
    """Gauge circular com arco de fundo, ticks e arco de valor com brilho.

    Desenha diretamente na superfície de destino, sem alocar temporários
    durante cada quadro.
    """
    r = raio
    fracao = max(0.0, min(1.0, fracao))
    local = centro
    pygame.draw.circle(
        tela,
        (*FUNDO_TEXTO_HUD, OPACIDADE_PAINEL_HUD),
        local,
        max(1, r - layout.px(10)),
    )

    pygame.draw.circle(
        tela,
        (*FUNDO_TEXTO_HUD, OPACIDADE_PAINEL_HUD),
        local,
        max(1, r - layout.px(10)),
    )

    # ticks de fundo a cada 30 graus
    for i in range(12):
        a = -math.pi / 2 + i * math.tau / 12
        r0 = r - layout.px(5)
        r1 = r - layout.px(8)
        p0 = (local[0] + math.cos(a) * r0, local[1] + math.sin(a) * r0)
        p1 = (local[0] + math.cos(a) * r1, local[1] + math.sin(a) * r1)
        cor_tick = (170, 180, 215) if (i % 3 == 0) else (66, 72, 104)
        linha_suave(tela, cor_tick, p0, p1, layout.px(2))

    # arco de fundo (quase cheio, bem discreto)
    _arc(tela, local, r - layout.px(3), 0, math.tau, (56, 64, 100), layout.px(5), 150)

    # arco de valor com brilho na ponta
    if fracao > 0.01:
        fim = -math.pi / 2 + fracao * math.tau
        _arc(tela, local, r - layout.px(3), -math.pi / 2, fim, cor, layout.px(5), 255)
        px = local[0] + math.cos(fim) * (r - layout.px(3))
        py = local[1] + math.sin(fim) * (r - layout.px(3))
        desenhar_circulo(tela, cor, (px, py), layout.px(2))

    surf_v = None
    if valor is not None:
        fonte = _fonte_com_altura_efetiva(layout, 16, TEXTO_ESSENCIAL_MIN_PX, titulo=True)
        surf_v = fonte.render(valor, True, BRANCO_HUD)
    surf_r = None
    if rotulo:
        fonte = _fonte_com_altura_efetiva(layout, 11, TEXTO_SECUNDARIO_MIN_PX)
        cor = cor_com_contraste(CINZA_HUD, FUNDO_TEXTO_HUD, CONTRASTE_TEXTO_HUD_AJUSTE)
        surf_r = fonte.render(rotulo, True, cor)

    if rotulo_abaixo and surf_r is not None:
        if surf_v is not None:
            _blit_alfa(tela, surf_v, surf_v.get_rect(center=centro))
        _blit_alfa(
            tela, surf_r, surf_r.get_rect(center=(centro[0], centro[1] + raio + layout.px(4)))
        )
    elif surf_v is not None and surf_r is not None:
        gap = layout.px(7)
        total = surf_v.get_height() + gap + surf_r.get_height()
        topo = centro[1] - total // 2
        _blit_alfa(
            tela, surf_v, surf_v.get_rect(center=(centro[0], topo + surf_v.get_height() // 2))
        )
        _blit_alfa(
            tela,
            surf_r,
            surf_r.get_rect(
                center=(centro[0], topo + surf_v.get_height() + gap + surf_r.get_height() // 2)
            ),
        )
    elif surf_v is not None:
        _blit_alfa(tela, surf_v, surf_v.get_rect(center=centro))
    elif surf_r is not None:
        _blit_alfa(tela, surf_r, surf_r.get_rect(center=centro))


def _icone_nave(tela, centro, escala, cor=BRANCO_HUD):
    """Glyph vetorial compacto da nave do jogador."""
    c = escala
    pts = [
        (centro[0], centro[1] - 10 * c),
        (centro[0] + 7 * c, centro[1] + 4 * c),
        (centro[0] + 3 * c, centro[1] + 7 * c),
        (centro[0] - 3 * c, centro[1] + 7 * c),
        (centro[0] - 7 * c, centro[1] + 4 * c),
    ]
    desenhar_poligono(tela, cor, pts)
    desenhar_poligono(
        tela,
        (255, 255, 255),
        [
            (centro[0] - 2 * c, centro[1] - 1 * c),
            (centro[0] + 2 * c, centro[1] - 1 * c),
            (centro[0], centro[1] + 5 * c),
        ],
    )


def _icone_arma(tela, tipo, centro, cor, escala=1.0):
    """Glyph geometrico da arma equipada (vetorial, por tipo)."""
    x, y = centro
    c = escala
    if tipo == "laser":
        linha_suave(tela, cor, (x, y - 8 * c), (x, y + 8 * c), int(2 * c))
        linha_suave(tela, BRANCO_HUD, (x, y - 8 * c), (x, y - 2 * c), int(1 * c))
    elif tipo == "duplo":
        for s in (-1, 1):
            linha_suave(
                tela, cor, (x + s * 6 * c, y - 8 * c), (x + s * 6 * c, y + 8 * c), int(2 * c)
            )
    elif tipo == "plasma":
        desenhar_circulo(tela, cor, (x, y), int(5 * c))
        desenhar_circulo(tela, BRANCO_HUD, (x, y), int(2 * c))
    elif tipo == "metralhadora":
        for i in range(3):
            dx = (i - 1) * 3 * c
            linha_suave(tela, cor, (x + dx, y - 8 * c), (x + dx, y + 8 * c), int(2 * c))
    elif tipo == "espiral":
        for i in range(3):
            a = i * math.tau / 3
            p0 = (x + math.cos(a) * 6 * c, y + math.sin(a) * 6 * c)
            desenhar_circulo(tela, cor, p0, int(2 * c))
    elif tipo == "ion":
        retangulo_suave(
            tela,
            cor,
            pygame.Rect(int(x - 3 * c), int(y - 8 * c), int(6 * c), int(16 * c)),
            int(3 * c),
        )
        linha_suave(tela, BRANCO_HUD, (x, y - 8 * c), (x, y + 8 * c), int(1 * c))
    elif tipo == "gauss":
        for s in (-1, 1):
            linha_suave(tela, cor, (x, y - 8 * c), (x + s * 7 * c, y), int(2 * c))
            linha_suave(tela, cor, (x, y + 8 * c), (x + s * 7 * c, y), int(2 * c))
    elif tipo == "nova":
        for i in range(6):
            a = i * math.tau / 6
            p0 = (x + math.cos(a) * 3 * c, y + math.sin(a) * 3 * c)
            p1 = (x + math.cos(a) * 8 * c, y + math.sin(a) * 8 * c)
            linha_suave(tela, cor, p0, p1, int(1 * c))
        desenhar_circulo(tela, cor, (x, y), int(2 * c))
    else:  # padrao
        desenhar_circulo(tela, cor, (x, y), int(3 * c))
        desenhar_circulo(tela, BRANCO_HUD, (x, y), int(1 * c))


def _icone_abates(tela, centro, cor=CINZA_HUD, escala=1.0):
    """Crosshair compacto para o contador de inimigos abatidos."""
    x, y = centro
    c = escala
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        linha_suave(
            tela,
            cor,
            (x + dx * 6 * c, y + dy * 6 * c),
            (x + dx * 8 * c, y + dy * 8 * c),
            int(2 * c),
        )
    desenhar_circulo(tela, cor, (x, y), int(4 * c), 1)


def _numero(tela, layout, fonte, valor, pos, cor, alinhar="centro", alfa=255):
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


# ---------------------------------------------------------------------------
# HUD
# ---------------------------------------------------------------------------


class HudJogo:
    """Renderiza o HUD completo de combate sobre a superficie logica."""

    def __init__(self, layout: Layout | None = None) -> None:
        self.layout = layout or Layout(LARGURA, ALTURA)
        self.compacto = self.layout.altura < 620
        self._preparar_fontes()
        self._telemetria_surface = None
        self._telemetria_chave = None

    def _preparar_fontes(self):
        layout = self.layout
        self._escala_fontes = layout.escala
        self.compacto = layout.altura < 620
        self._f_padrao_xxs = _fonte_com_altura_efetiva(
            layout, HUD_FONTE_PADRAO_XXS, TEXTO_SECUNDARIO_MIN_PX
        )
        self._f_padrao_xs = _fonte_com_altura_efetiva(
            layout, HUD_FONTE_PADRAO_XS, TEXTO_SECUNDARIO_MIN_PX
        )
        self._f_padrao_s = _fonte_com_altura_efetiva(
            layout, HUD_FONTE_PADRAO_S, TEXTO_ESSENCIAL_MIN_PX
        )
        self._f_padrao_m = _fonte_com_altura_efetiva(
            layout, HUD_FONTE_PADRAO_M, TEXTO_ESSENCIAL_MIN_PX
        )
        self._f_titulo_xs = _fonte_com_altura_efetiva(
            layout, HUD_FONTE_TITULO_XS, TEXTO_SECUNDARIO_MIN_PX, True
        )
        self._f_titulo_s = _fonte_com_altura_efetiva(
            layout, HUD_FONTE_TITULO_S, TEXTO_ESSENCIAL_MIN_PX, True
        )
        self._f_titulo_m = _fonte_com_altura_efetiva(
            layout, HUD_FONTE_TITULO_M, TEXTO_ESSENCIAL_MIN_PX, True
        )
        self._f_titulo_g = _fonte_com_altura_efetiva(
            layout, HUD_FONTE_TITULO_G, TEXTO_ESSENCIAL_MIN_PX, True
        )
        self._f_numero = _fonte_com_altura_efetiva(
            layout, HUD_FONTE_NUMERO, TEXTO_ESSENCIAL_MIN_PX, True
        )

    # ------------------------------------------------------------- dados

    def _dados(self, jogo):
        jog = jogo.jogador
        arma = ARMARIA[jog.arma_atual % len(ARMARIA)]
        recordes = getattr(jogo, "recordes", []) or []
        combo = jog.combo
        # progresso da fase: inimigos restantes / onda nominal (discreto)
        restantes = len(getattr(jogo, "fila_onda", [])) + len(getattr(jogo, "inimigos", []))
        progresso = max(0.0, min(1.0, 1 - restantes / 22.0))
        # carga da arma atual
        if arma["tipo"] == "metralhadora":
            qtd = arma.get("qtd", 1)
            municao = 1 - max(0, jog.burst_left) / max(1, qtd)
        else:
            cooldown = max(1, arma["cooldown"])
            municao = 1 - max(0, jog.cooldown_tiro) / cooldown
        return {
            "nome": getattr(jog, "nome", "PILOTO 01"),
            "vida": jog.vida,
            "vida_max": jog.max_vida,
            "escudo": bool(getattr(jog, "escudo", False)),
            "pontos": jog.pontuacao,
            "recorde": (recordes[0]["pontos"] if recordes else 0),
            "abates": getattr(jogo, "inimigos_abates", 0),
            "combo": combo.combo_atual,
            "bonus": combo.get_bonus(),
            "combo_tempo": max(
                0.0,
                min(
                    1.0,
                    getattr(combo, "quadros_restantes", 0)
                    / max(1, getattr(combo, "janela_acertos", 1)),
                ),
            ),
            "nivel": jog.nivel,
            "cenario": getattr(jogo.cenario, "id", 1),
            "regiao": getattr(jogo.cenario, "nome", "ESPAÇO PROFUNDO"),
            "progresso": progresso,
            "arma": arma,
            "municao": municao,
            "boost": max(0.0, min(1.0, getattr(jogo, "boost", 1.0))),
            "especial": max(0.0, min(1.0, getattr(jogo, "especial", 0.0))),
            "especial_atual": getattr(jogo, "especial_atual", "bomba"),
            "tempo_intangivel": getattr(jog, "tempo_intangivel", 0),
            "energia": max(0.0, min(100.0, getattr(jogo, "energia", 100.0))),
            "vel": getattr(jog, "velocidade", 5.0),
            "tecla_esquiva": pygame.key.name(
                getattr(jogo, "controles", {}).get("esquivar", pygame.K_x)
            ).upper(),
            "esquiva": max(
                0.0,
                1
                - getattr(jog, "cooldown_esquiva", 0)
                / max(30, round(90 * getattr(jog, "multiplicador_recarga_esquiva", 1.0))),
            ),
            "boss": jogo.boss or getattr(jogo, "miniboss", None),
        }

    # ----------------------------------------------------------- desenhar

    def desenhar(
        self, tela: pygame.Surface, jogo: Any, tempo: float | None = None
    ) -> dict[str, Any]:
        """Compõe os instrumentos nas bordas e retorna os dados apresentados.

        Args:
            tela: Superfície lógica de destino.
            jogo: Estado da partida com jogador e medidores.
            tempo: Tempo visual em segundos, opcional para previews.
        """
        if self._escala_fontes != self.layout.escala:
            self._preparar_fontes()
            self._telemetria_chave = None
        self._paleta = _paleta_fase(getattr(jogo, "cenario", None))
        d = self._dados(jogo)
        t = (pygame.time.get_ticks() * 0.001) if tempo is None else tempo
        self._topo_esquerda(tela, d, t)
        if getattr(jogo, "modo_atual", "linear") != "mundo_aberto":
            self._topo_direita(tela, d, t)
        # Todo chefe ocupa o cabeçalho durante o encontro, inclusive minibosses.
        if not d["boss"]:
            self._topo_centro(tela, d, t)
        self._base_esquerda(tela, d, t)
        self._base_direita(tela, d, t)
        self._base_centro(tela, d, t)
        self._barra_boss(tela, d, t)
        self._desenhar_telemetria(tela, jogo)
        return d

    def _desenhar_telemetria(self, tela, jogo) -> None:
        """Mostra FPS e perfil visual somente quando o monitor esta habilitado."""
        try:
            if not jogo.config["mostrar_desempenho"]:
                return
            qualidade = jogo.config["qualidade_grafica"]
        except (AttributeError, KeyError):
            return
        fps = max(0, round(getattr(jogo, "fps_atual", 0)))
        quadro = max(0, round(getattr(jogo, "tempo_quadro_ms", 0)))
        p95 = max(0, round(getattr(jogo, "p95_quadro_ms", 0)))
        fps_1_baixo = max(0, round(getattr(jogo, "fps_1_baixo", 0)))
        escala = "RÁPIDA" if getattr(jogo, "_escala_rapida", False) else "SUAVE"
        chave = (fps, quadro, p95, fps_1_baixo, qualidade, escala, opcoes_atuais().estilo)
        if chave != self._telemetria_chave:
            texto = (
                f"{fps:02d} FPS  {quadro:02d} ms  P95 {p95:02d} ms  "
                f"1% {fps_1_baixo:02d} FPS  {qualidade}  {escala}"
            )
            self._telemetria_surface = _render(self._f_padrao_xxs, texto, CIANO_HUD)
            self._telemetria_chave = chave
        if self._telemetria_surface is None:
            return
        layout = self.layout
        rect = self._telemetria_surface.get_rect(midtop=(layout.x(0.5), layout.px(138)))
        fundo = rect.inflate(layout.px(16), layout.px(8))
        retangulo_suave(
            tela, AZUL_PROFUNDO, fundo, layout.px(5), 1, glow_cor=CIANO_HUD, glow_raio=layout.px(4)
        )
        _blit_alfa(tela, self._telemetria_surface, rect, 220)

    # -------------------------------------------------------- modulos

    def _regioes(self) -> dict[str, pygame.Rect]:
        """Reserva colunas separadas com folga para nomes e indicadores."""
        layout = self.layout
        margem = layout.margem(14)
        lateral = layout.px(232)
        livre = layout.largura - 2 * (margem + lateral + layout.px(14))
        centro = min(layout.px(420), livre)
        topo = layout.px(114)
        base = layout.px(96)
        especial = layout.px(52)
        direita = layout.largura - margem - lateral
        return {
            "piloto": pygame.Rect(margem, margem, lateral, topo),
            "pontos": pygame.Rect(direita, margem, lateral, topo),
            "setor": pygame.Rect((layout.largura - centro) // 2, margem, centro, topo),
            "impulso": pygame.Rect(margem, layout.altura - margem - base, lateral, base),
            "arma": pygame.Rect(direita, layout.altura - margem - base, lateral, base),
            "especial": pygame.Rect(
                (layout.largura - min(centro, layout.px(236))) // 2,
                layout.altura - margem - especial,
                min(centro, layout.px(236)),
                especial,
            ),
        }

    def _texto(self, tela, texto, rect, fonte, cor=BRANCO_HUD, alinhar="esquerda"):
        """Mantém cada rótulo dentro de sua célula, inclusive no estilo comic."""
        surf = _texto_limitado(
            fonte, str(texto), tuple(cor[:3]), opcoes_atuais().ativo, max(1, rect.w), max(1, rect.h)
        )
        destino = surf.get_rect(centery=rect.centery)
        if alinhar == "direita":
            destino.right = rect.right
        elif alinhar == "centro":
            destino.centerx = rect.centerx
        else:
            destino.left = rect.left
        tela.blit(surf, destino)
        return destino

    def _celula(self, painel, x, y, largura, altura):
        layout = self.layout
        return pygame.Rect(
            painel.x + layout.px(x), painel.y + layout.px(y), layout.px(largura), layout.px(altura)
        )

    def _topo_esquerda(self, tela, d, t):
        layout = self.layout
        painel = self._regioes()["piloto"]
        critico = d["vida"] / max(1, d["vida_max"]) <= 0.3
        cor = VIDA_COR if critico else self._paleta["primaria"]
        _painel(tela, layout, painel, cor, fundo=AZUL_PROFUNDO)
        _icone_nave(tela, self._celula(painel, 12, 10, 28, 28).center, layout.escala, cor)
        self._texto(
            tela, d["nome"].upper(), self._celula(painel, 48, 9, 170, 18), self._f_titulo_xs
        )
        status = "CASCO CRÍTICO" if critico else "SISTEMAS ATIVOS"
        if d["vida"] <= 0:
            status = "NAVE DESTRUÍDA"
        self._texto(
            tela,
            status,
            self._celula(painel, 48, 28, 170, 14),
            self._f_padrao_xs,
            VIDA_COR if critico else CINZA_HUD,
        )
        self._texto(
            tela, "CASCO", self._celula(painel, 12, 48, 70, 16), self._f_padrao_xs, CINZA_HUD
        )
        self._texto(
            tela,
            f"{d['vida']:g} / {d['vida_max']:g}",
            self._celula(painel, 116, 48, 104, 16),
            self._f_padrao_s,
            VIDA_COR,
            "direita",
        )
        _barra_segmentada(
            tela,
            layout,
            self._celula(painel, 12, 68, 208, 8),
            d["vida"] / max(1, d["vida_max"]),
            VIDA_COR,
            min(12, max(1, int(d["vida_max"]))),
        )
        escudo = "ESCUDO ATIVO" if d["escudo"] else "SEM ESCUDO"
        self._texto(
            tela,
            escudo,
            self._celula(painel, 12, 84, 102, 16),
            self._f_padrao_xs,
            self._paleta["primaria"] if d["escudo"] else CINZA_HUD,
        )
        self._texto(
            tela,
            f"ENERGIA {d['energia']:.0f}%",
            self._celula(painel, 120, 84, 100, 16),
            self._f_padrao_xs,
            CINZA_HUD,
            "direita",
        )
        _barra_fina(
            tela,
            layout,
            self._celula(painel, 120, 102, 100, 3),
            d["energia"] / 100,
            self._paleta["energia"],
            brilho=False,
        )

    def _topo_direita(self, tela, d, t):
        layout = self.layout
        painel = self._regioes()["pontos"]
        _painel(tela, layout, painel, self._paleta["secundaria"], fundo=AZUL_PROFUNDO)
        self._texto(
            tela, "PONTUAÇÃO", self._celula(painel, 12, 9, 120, 16), self._f_titulo_xs, CINZA_HUD
        )
        self._texto(
            tela,
            f"{d['pontos']:,}".replace(",", "."),
            self._celula(painel, 12, 28, 208, 32),
            self._f_numero,
            BRANCO_HUD,
            "direita",
        )
        recorde = f"RECORDE  {d['recorde']:,}".replace(",", ".")
        self._texto(
            tela,
            recorde,
            self._celula(painel, 12, 64, 208, 16),
            self._f_padrao_xs,
            OURO_HUD,
            "direita",
        )
        self._texto(
            tela,
            f"{d['abates']} ABATES",
            self._celula(painel, 12, 86, 90, 16),
            self._f_padrao_xs,
            CINZA_HUD,
        )
        texto = f"COMBO {d['combo']}  x{d['bonus']:.1f}" if d["combo"] > 1 else "SEM COMBO"
        self._texto(
            tela,
            texto,
            self._celula(painel, 106, 86, 114, 16),
            self._f_padrao_xs,
            OURO_HUD if d["combo"] > 1 else CINZA_HUD,
            "direita",
        )
        if d["combo"] > 1:
            _barra_fina(
                tela,
                layout,
                self._celula(painel, 106, 104, 114, 3),
                d["combo_tempo"],
                OURO_HUD,
                brilho=False,
            )

    def _topo_centro(self, tela, d, t):
        layout = self.layout
        painel = self._regioes()["setor"]
        area = painel.inflate(-layout.px(24), 0)
        area.height = layout.px(20)
        area.y += layout.px(12)
        self._texto(
            tela,
            f"SETOR {d['cenario']:02d}  /  ONDA {d['nivel']:02d}",
            area,
            self._f_titulo_xs,
            CINZA_HUD,
            "centro",
        )
        area.y += layout.px(24)
        self._texto(
            tela, d["regiao"].upper(), area, self._f_titulo_s, self._paleta["primaria"], "centro"
        )
        barra = pygame.Rect(area.x, area.bottom + layout.px(10), area.w, layout.px(3))
        _barra_fina(tela, layout, barra, d["progresso"], self._paleta["primaria"], brilho=False)

    def _base_esquerda(self, tela, d, t):
        layout = self.layout
        painel = self._regioes()["impulso"]
        cor = self._paleta["primaria"]
        _painel(tela, layout, painel, cor, fundo=AZUL_PROFUNDO)
        centro = self._celula(painel, 12, 10, 62, 62).center
        _medidor_circular(
            tela, layout, centro, layout.px(30), d["boost"], cor, valor=f"{d['boost']:.0%}"
        )
        self._texto(tela, "IMPULSO", self._celula(painel, 86, 12, 132, 18), self._f_titulo_xs)
        self._texto(
            tela,
            "SHIFT / CTRL",
            self._celula(painel, 86, 34, 132, 16),
            self._f_padrao_xs,
            CINZA_HUD,
        )
        self._texto(
            tela,
            f"VELOCIDADE {d['vel']:.1f}",
            self._celula(painel, 86, 54, 132, 16),
            self._f_padrao_xs,
            CINZA_HUD,
        )
        esquiva = "PRONTA" if d["esquiva"] >= 1 else f"{d['esquiva']:.0%}"
        self._texto(
            tela,
            f"[{d['tecla_esquiva']}] ESQUIVA {esquiva}",
            self._celula(painel, 12, 76, 208, 16),
            self._f_padrao_xs,
            cor if d["esquiva"] >= 1 else CINZA_HUD,
        )

    def _base_direita(self, tela, d, t):
        layout = self.layout
        painel = self._regioes()["arma"]
        arma = d["arma"]
        _painel(tela, layout, painel, arma["cor"], fundo=AZUL_PROFUNDO)
        badge = self._celula(painel, 12, 12, 28, 28)
        _icone_arma(tela, arma["tipo"], badge.center, arma["cor"], layout.escala)
        indice = next(i for i, item in enumerate(ARMARIA) if item["tipo"] == arma["tipo"])
        cor = RARIDADES[RARIDADE_ARMAS[indice]] if opcoes_atuais().ativo else BRANCO_HUD
        self._texto(
            tela, arma["nome"].upper(), self._celula(painel, 48, 9, 172, 22), self._f_titulo_s, cor
        )
        legenda = f"NV {arma['nivel']:02d}"
        if opcoes_atuais().ativo and not self.compacto:
            legenda += " / " + RARIDADE_ARMAS[indice].upper()
        self._texto(
            tela, legenda, self._celula(painel, 48, 33, 172, 16), self._f_padrao_xs, CINZA_HUD
        )
        _barra_segmentada(
            tela,
            layout,
            self._celula(painel, 12, 58, 208, 6),
            d["municao"],
            arma["cor"],
            8,
            raio_canto=2,
        )
        self._texto(
            tela,
            "PRONTA" if d["municao"] >= 1 else "RECARREGANDO",
            self._celula(painel, 12, 73, 110, 16),
            self._f_padrao_xs,
            arma["cor"],
        )
        self._texto(
            tela,
            "[1–9] TROCAR",
            self._celula(painel, 126, 73, 94, 16),
            self._f_padrao_xs,
            CINZA_HUD,
            "direita",
        )

    def _base_centro(self, tela, d, t):
        layout = self.layout
        painel = self._regioes()["especial"]
        pronto = d["especial"] >= 1.0
        intangivel = d["especial_atual"] == "intangivel"
        tempo_intangivel = d["tempo_intangivel"]
        cor = self._paleta["secundaria"] if pronto else CINZA_HUD
        _painel(tela, layout, painel, cor, fundo=AZUL_PROFUNDO)
        self._texto(
            tela,
            "INTANGÍVEL" if intangivel else "BOMBA VORTEX",
            self._celula(painel, 12, 4, 148, 18),
            self._f_titulo_xs,
            CINZA_HUD,
        )
        self._texto(
            tela, "[E]", self._celula(painel, 176, 4, 46, 18), self._f_titulo_xs, cor, "direita"
        )
        self._texto(
            tela,
            (
                f"INTANGÍVEL {math.ceil(tempo_intangivel / 60)}s"
                if tempo_intangivel > 0
                else "PRONTO PARA ATIVAR"
                if pronto
                else f"CARREGANDO {d['especial']:.0%}"
            ),
            self._celula(painel, 12, 36, 210, 13),
            self._f_padrao_xs,
            cor,
        )
        _barra_segmentada(
            tela,
            layout,
            self._celula(painel, 12, 27, 210, 6),
            d["especial"],
            self._paleta["secundaria"],
            10,
            raio_canto=2,
        )

    def _barra_boss(self, tela, d, t):
        boss = d["boss"]
        if not boss:
            return
        layout = self.layout
        painel = self._regioes()["setor"]
        _painel(tela, layout, painel, OURO_HUD, fundo=AZUL_PROFUNDO)
        fracao = max(0.0, min(1.0, boss.vida / max(1, boss.vida_max)))
        area = painel.inflate(-layout.px(24), 0)
        area.y += layout.px(9)
        area.height = layout.px(16)
        self._texto(tela, "AMEAÇA DETECTADA", area, self._f_titulo_xs, OURO_HUD, "centro")
        area.y += layout.px(22)
        area.height = layout.px(22)
        self._texto(tela, boss.nome.upper(), area, self._f_titulo_s, BRANCO_HUD, "centro")
        barra = pygame.Rect(area.x, painel.y + layout.px(64), area.w, layout.px(10))
        _barra_segmentada(tela, layout, barra, fracao, OURO_HUD, SEGMENTOS_BOSS, raio_canto=2)
        fase_atual = getattr(boss, "fase_atual", None)
        if fase_atual is None:
            fase_atual = 1 if fracao > 0.66 else 2 if fracao > 0.33 else 3
        estado = getattr(boss, "estado", None)
        rotulo = getattr(estado, "rotulo", f"FASE {fase_atual}/3")
        area.y = painel.y + layout.px(86)
        area.height = layout.px(18)
        area.w -= layout.px(62)
        self._texto(tela, rotulo, area, self._f_padrao_xs, OURO_HUD)
        porcentagem = pygame.Rect(area.right, area.y, layout.px(62), area.h)
        self._texto(tela, f"{fracao:.0%}", porcentagem, self._f_padrao_s, OURO_HUD, "direita")
