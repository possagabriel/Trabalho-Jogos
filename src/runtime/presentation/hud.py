"""HUD de combate profissional do INCARNATE.

Interface de nave espacial militar de alta tecnologia, em identidade visual
sci-fi cinematografica: roxo escuro + azul profundo + ciano + magenta, com
detalhes em branco. Todos os elementos ficam nas bordas da tela (centro
livre para o gameplay) e usam o sistema responsivo ``game.layout``, entao
escalam de 1920x1080 ate telas menores preservando as proporcoes.

Componentes:
  - canto superior esquerdo: icone da nave, PLAYER 01, vida, escudo, energia;
  - canto superior direito: SCORE, HIGH SCORE, abates e multiplicador combo;
  - topo central: SECTOR xx, nome da regiao e progresso da fase;
  - canto inferior esquerdo: medidor circular de BOOST e velocidade;
  - canto inferior direito: arma equipada (icone, nome, carga, nivel);
  - base central: barra de bomba com aviso BOMBA READY;
  - topo (somente com boss): barra de chefe segmentada e centralizada.

Uso:

    hud = HudJogo()
    hud.desenhar(tela, jogo)   # tela = superficie logica 1280x720

O ``HudJogo`` le apenas os atributos de que precisa de ``jogo`` (duck typing),
entao funciona com o ``core.Jogo`` real ou com um objeto de demonstracao.
"""

import colorsys
import math

import pygame

from src.core.constants import (
    DIMENSION_GOLD,
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
from src.runtime.infrastructure.graphics.geometry import losango
from src.runtime.infrastructure.graphics.smooth import (
    barra_suave,
    desenhar_cantos,
    desenhar_circulo,
    desenhar_glow,
    desenhar_painel,
    desenhar_poligono,
    linha_suave,
    retangulo_suave,
)
from src.runtime.infrastructure.graphics.style_tokens import (
    CONTRASTE_TEXTO_HUD_AJUSTE,
    CONTRASTE_TEXTO_MINIMO,
    FUNDO_TEXTO_HUD,
    HUD_ALTURA_PAINEL_ARMA_COMPACTO,
    HUD_ALTURA_PAINEL_ARMA_PADRAO,
    HUD_ALTURA_PAINEL_COMPACTO,
    HUD_ALTURA_PAINEL_PADRAO,
    HUD_ALTURA_PAINEL_PONTUACAO_COMPACTO,
    HUD_ALTURA_PAINEL_STATUS_PADRAO,
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
    HUD_LARGURA_BARRA_BOSS,
    HUD_LARGURA_PAINEL_CENTRAL,
    HUD_LARGURA_PAINEL_DIREITO,
    HUD_LARGURA_PAINEL_ESQUERDO,
    HUD_MARGEM_BASE,
    HUD_MARGEM_PLAQUETA_TEXTO,
    HUD_RAIO_PLAQUETA_TEXTO,
    HUD_SEGMENTOS_BOSS,
    HUD_SEGMENTOS_VIDA,
    HUD_TAMANHO_CANTO,
    HUD_Y_BARRA_BOSS_COMPACTO,
    HUD_Y_BARRA_BOSS_PADRAO,
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
    return {"primaria": primaria, "secundaria": secundaria,
            "energia": energia, "fundo": fundo}


# ---------------------------------------------------------------------------
# Utilidades de desenho
# ---------------------------------------------------------------------------

def _render(fonte, texto, cor):
    cor = cor_com_contraste(cor, FUNDO_TEXTO_HUD, CONTRASTE_TEXTO_HUD_AJUSTE)
    if opcoes_atuais().ativo:
        return texto_tinta(str(texto), max(9, int(fonte.get_height() * .7)), tuple(cor[:3]))
    return fonte.render(texto, True, cor[:3])


def _luminancia(cor):
    """Calcula luminância relativa sRGB para a razão WCAG."""
    canais = []
    for canal in cor[:3]:
        valor = canal / 255
        canais.append(valor / 12.92 if valor <= 0.04045
                      else ((valor + 0.055) / 1.055) ** 2.4)
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
        candidata = tuple(round(a + (b - a) * fator)
                          for a, b in zip(cor, destino))
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
    # Texto essencial permanece opaco para cumprir o contraste após composição.
    tela.blit(surf, pos)


def _painel(tela, layout, rect, cor_borda, alpha=150, raio=12, glow=0,
            fundo=AZUL_PROFUNDO):
    """Painel holografico translucido com borda neon e cantos em L."""
    desenhar_painel(tela, cor_borda, rect,
                    cor_fundo=fundo, raio_canto=raio, alpha=alpha,
                    glow_raio=glow)
    desenhar_cantos(tela, tuple(min(255, c + 70) for c in cor_borda[:3]),
                    rect, tamanho=layout.px(HUD_TAMANHO_CANTO),
                    espessura=HUD_ESPESSURA_CONTORNO)


def _barra_segmentada(tela, layout, rect, fracao, cor, segmentos=12,
                      raio_canto=3):
    """Barra de progresso com segmentos visuais separados por vao."""
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
        else:
            barra_suave(tela, seg.x, seg.y, seg.w, seg.h, 1.0,
                        (44, 50, 82), fundo=(18, 22, 48), raio_canto=raio_canto)


def _barra_fina(tela, layout, rect, fracao, cor, brilho=False):
    """Barra extremamente discreta, de 4px, para progressos secundarios."""
    fracao = max(0.0, min(1.0, fracao))
    barra_suave(tela, rect.x, rect.y, rect.w, rect.h, fracao, cor,
                fundo=(28, 34, 66), raio_canto=2,
                glow=(brilho and fracao > 0 and fracao < 1.0))


def _arc(surf, centro, raio, inicio, fim, cor, espessura, alpha=255):
    """Desenha um arco anti-aliased numa surface SRCALPHA."""
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


def _medidor_circular(tela, layout, centro, raio, fracao, cor,
                      rotulo=None, valor=None, rotulo_abaixo=False):
    """Gauge circular com arco de fundo, ticks e arco de valor com brilho.

    Desenha diretamente na superfície de destino, sem alocar temporários
    durante cada quadro.
    """
    r = raio
    fracao = max(0.0, min(1.0, fracao))
    local = centro
    pygame.draw.circle(
        tela, (*FUNDO_TEXTO_HUD, OPACIDADE_PAINEL_HUD), local,
        max(1, r - layout.px(10)),
    )

    pygame.draw.circle(
        tela, (*FUNDO_TEXTO_HUD, OPACIDADE_PAINEL_HUD), local,
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
    _arc(tela, local, r - layout.px(3), 0, math.tau, (56, 64, 100),
         layout.px(5), 150)

    # arco de valor com brilho na ponta
    if fracao > 0.01:
        fim = -math.pi / 2 + fracao * math.tau
        _arc(tela, local, r - layout.px(3), -math.pi / 2, fim, cor,
             layout.px(5), 255)
        px = local[0] + math.cos(fim) * (r - layout.px(3))
        py = local[1] + math.sin(fim) * (r - layout.px(3))
        desenhar_circulo(tela, cor, (px, py), layout.px(2))

    surf_v = None
    if valor is not None:
        fonte = _fonte_com_altura_efetiva(
            layout, 16, TEXTO_ESSENCIAL_MIN_PX, titulo=True)
        surf_v = fonte.render(valor, True, BRANCO_HUD)
    surf_r = None
    if rotulo:
        fonte = _fonte_com_altura_efetiva(
            layout, 11, TEXTO_SECUNDARIO_MIN_PX)
        cor = cor_com_contraste(
            CINZA_HUD, FUNDO_TEXTO_HUD, CONTRASTE_TEXTO_HUD_AJUSTE)
        surf_r = fonte.render(rotulo, True, cor)

    if rotulo_abaixo and surf_r is not None:
        if surf_v is not None:
            _blit_alfa(tela, surf_v, surf_v.get_rect(center=centro))
        _blit_alfa(tela, surf_r, surf_r.get_rect(center=(
            centro[0], centro[1] + raio + layout.px(4))))
    elif surf_v is not None and surf_r is not None:
        gap = layout.px(7)
        total = surf_v.get_height() + gap + surf_r.get_height()
        topo = centro[1] - total // 2
        _blit_alfa(tela, surf_v, surf_v.get_rect(
            center=(centro[0], topo + surf_v.get_height() // 2)))
        _blit_alfa(tela, surf_r, surf_r.get_rect(
            center=(centro[0], topo + surf_v.get_height() + gap
                    + surf_r.get_height() // 2)))
    elif surf_v is not None:
        _blit_alfa(tela, surf_v, surf_v.get_rect(center=centro))
    elif surf_r is not None:
        _blit_alfa(tela, surf_r, surf_r.get_rect(center=centro))


def _icone_nave(tela, centro, escala, cor=BRANCO_HUD):
    """Glyph vetorial compacto da nave do jogador."""
    c = escala
    pts = [(centro[0], centro[1] - 10 * c), (centro[0] + 7 * c, centro[1] + 4 * c),
           (centro[0] + 3 * c, centro[1] + 7 * c), (centro[0] - 3 * c, centro[1] + 7 * c),
           (centro[0] - 7 * c, centro[1] + 4 * c)]
    desenhar_poligono(tela, cor, pts)
    desenhar_poligono(tela, (255, 255, 255), [
        (centro[0] - 2 * c, centro[1] - 1 * c),
        (centro[0] + 2 * c, centro[1] - 1 * c),
        (centro[0], centro[1] + 5 * c)])


def _icone_arma(tela, tipo, centro, cor, escala=1.0):
    """Glyph geometrico da arma equipada (vetorial, por tipo)."""
    x, y = centro
    c = escala
    if tipo == "laser":
        linha_suave(tela, cor, (x, y - 8 * c), (x, y + 8 * c), int(2 * c))
        linha_suave(tela, BRANCO_HUD, (x, y - 8 * c), (x, y - 2 * c),
                    int(1 * c))
    elif tipo == "duplo":
        for s in (-1, 1):
            linha_suave(tela, cor, (x + s * 6 * c, y - 8 * c),
                        (x + s * 6 * c, y + 8 * c), int(2 * c))
    elif tipo == "plasma":
        desenhar_circulo(tela, cor, (x, y), int(5 * c))
        desenhar_circulo(tela, BRANCO_HUD, (x, y), int(2 * c))
    elif tipo == "metralhadora":
        for i in range(3):
            dx = (i - 1) * 3 * c
            linha_suave(tela, cor, (x + dx, y - 8 * c),
                        (x + dx, y + 8 * c), int(2 * c))
    elif tipo == "espiral":
        for i in range(3):
            a = i * math.tau / 3
            p0 = (x + math.cos(a) * 6 * c, y + math.sin(a) * 6 * c)
            desenhar_circulo(tela, cor, p0, int(2 * c))
    elif tipo == "ion":
        retangulo_suave(tela, cor, pygame.Rect(
            int(x - 3 * c), int(y - 8 * c), int(6 * c), int(16 * c)),
            int(3 * c))
        linha_suave(tela, BRANCO_HUD, (x, y - 8 * c), (x, y + 8 * c),
                    int(1 * c))
    elif tipo == "gauss":
        for s in (-1, 1):
            linha_suave(tela, cor, (x, y - 8 * c), (x + s * 7 * c, y),
                        int(2 * c))
            linha_suave(tela, cor, (x, y + 8 * c), (x + s * 7 * c, y),
                        int(2 * c))
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
        linha_suave(tela, cor, (x + dx * 6 * c, y + dy * 6 * c),
                    (x + dx * 8 * c, y + dy * 8 * c), int(2 * c))
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

    def __init__(self, layout=None):
        self.layout = layout or Layout()
        layout = self.layout
        self.compacto = layout.altura < 620
        self._f_padrao_xxs = self._fonte(
            layout, HUD_FONTE_PADRAO_XXS, TEXTO_SECUNDARIO_MIN_PX)
        self._f_padrao_xs = self._fonte(
            layout, HUD_FONTE_PADRAO_XS, TEXTO_SECUNDARIO_MIN_PX)
        self._f_padrao_s = self._fonte(
            layout, HUD_FONTE_PADRAO_S, TEXTO_ESSENCIAL_MIN_PX)
        self._f_padrao_m = self._fonte(
            layout, HUD_FONTE_PADRAO_M, TEXTO_ESSENCIAL_MIN_PX)
        self._f_titulo_xs = self._fonte(
            layout, HUD_FONTE_TITULO_XS, TEXTO_SECUNDARIO_MIN_PX, True)
        self._f_titulo_s = self._fonte(
            layout, HUD_FONTE_TITULO_S, TEXTO_ESSENCIAL_MIN_PX, True)
        self._f_titulo_m = self._fonte(
            layout, HUD_FONTE_TITULO_M, TEXTO_ESSENCIAL_MIN_PX, True)
        self._f_titulo_g = self._fonte(
            layout, HUD_FONTE_TITULO_G, TEXTO_ESSENCIAL_MIN_PX, True)
        self._f_numero = self._fonte(
            layout, HUD_FONTE_NUMERO, TEXTO_ESSENCIAL_MIN_PX, True)
        self._telemetria_surface = None
        self._telemetria_chave = None

    @staticmethod
    def _fonte(layout, tamanho_base, minimo, titulo=False):
        """Cria fonte em pixels de saída, impondo o mínimo de leitura efetivo."""
        return _fonte_com_altura_efetiva(layout, tamanho_base, minimo, titulo)

    # ------------------------------------------------------------- dados

    def _dados(self, jogo):
        jog = jogo.jogador
        arma = ARMARIA[jog.arma_atual % len(ARMARIA)]
        recordes = getattr(jogo, "recordes", []) or []
        combo = jog.combo
        # progresso da fase: inimigos restantes / onda nominal (discreto)
        restantes = (len(getattr(jogo, "fila_onda", [])) +
                     len(getattr(jogo, "inimigos", [])))
        progresso = max(0.0, min(1.0, 1 - restantes / 22.0))
        # carga da arma atual
        if arma["tipo"] == "metralhadora":
            qtd = arma.get("qtd", 1)
            municao = 1 - max(0, jog.burst_left) / max(1, qtd)
        else:
            cooldown = max(1, arma["cooldown"])
            municao = 1 - max(0, jog.cooldown_tiro) / cooldown
        return {
            "vida": jog.vida,
            "vida_max": jog.max_vida,
            "escudo": bool(getattr(jog, "escudo", False)),
            "pontos": jog.pontuacao,
            "recorde": (recordes[0]["pontos"] if recordes else 0),
            "abates": getattr(jogo, "inimigos_abates", 0),
            "combo": combo.combo_atual,
            "bonus": combo.get_bonus(),
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
            "esquiva": max(0.0, 1 - getattr(jog, "cooldown_esquiva", 0) /
                           max(30, round(90 * getattr(
                               jog, "multiplicador_recarga_esquiva", 1.0)))),
            "boss": jogo.boss or getattr(jogo, "miniboss", None),
        }

    # ----------------------------------------------------------- desenhar

    def desenhar(self, tela, jogo, tempo=None):
        self._paleta = _paleta_fase(getattr(jogo, "cenario", None))
        d = self._dados(jogo)
        t = (pygame.time.get_ticks() * 0.001) if tempo is None else tempo
        self._topo_esquerda(tela, d, t)
        self._topo_direita(tela, d, t)
        # O protocolo ocupa o cabeçalho durante o encontro; evita sobrepor
        # o nome e a barra do miniboss ao indicador de setor.
        if not getattr(jogo, "miniboss", None):
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
            texto = (f"{fps:02d} FPS  {quadro:02d} ms  P95 {p95:02d} ms  "
                     f"1% {fps_1_baixo:02d} FPS  {qualidade}  {escala}")
            self._telemetria_surface = _render(self._f_padrao_xxs, texto, CIANO_HUD)
            self._telemetria_chave = chave
        if self._telemetria_surface is None:
            return
        layout = self.layout
        rect = self._telemetria_surface.get_rect(midtop=(layout.x(0.5), layout.px(112)))
        fundo = rect.inflate(layout.px(16), layout.px(8))
        retangulo_suave(tela, (9, 18, 38), fundo, layout.px(5), 1,
                         )
        _blit_alfa(tela, self._telemetria_surface, rect, 220)

    # -------------------------------------------------------- modulos

    def _topo_esquerda(self, tela, d, t):
        layout = self.layout
        m = layout.margem(HUD_MARGEM_BASE)
        largura = layout.px(HUD_LARGURA_PAINEL_ESQUERDO)
        altura = layout.px(
            HUD_ALTURA_PAINEL_COMPACTO if self.compacto
            else HUD_ALTURA_PAINEL_STATUS_PADRAO)
        painel = pygame.Rect(m, m, largura, altura)
        _painel(tela, layout, painel, self._paleta["primaria"],
                alpha=OPACIDADE_PAINEL_HUD, glow=0,
                fundo=FUNDO_TEXTO_HUD)

        # icone da nave em badge losangular
        badge_c = (painel.x + layout.px(30), painel.y + layout.px(30))
        desenhar_poligono(tela, (52, 66, 110),
                          losango(badge_c, layout.px(26), layout.px(30)),
                          espessura=1)
        _icone_nave(tela, badge_c, layout.escala * 1.15, BRANCO_HUD)

        # identificacao
        x0 = painel.x + layout.px(62)
        rotulo = _render(self._f_titulo_xs, "PILOTO 01", CINZA_HUD)
        _blit_alfa(tela, rotulo, (x0, painel.y + layout.px(8)))
        # barra de vida (segmentada) + numerico
        by = painel.y + layout.px(75 if self.compacto else 50)
        barra = pygame.Rect(x0, by, layout.px(100 if self.compacto else 128), layout.px(9))
        _barra_segmentada(tela, layout, barra, d["vida"] / max(1, d["vida_max"]),
                          VIDA_COR, SEGMENTOS_VIDA)
        _numero(tela, layout, self._f_padrao_s, f"{d['vida']}/{d['vida_max']}",
                (painel.right - layout.px(10), painel.y + layout.px(34)), VIDA_COR,
                "direita", 235)

        # barra de escudo (fina, ciano) - aparece quando o escudo esta ativo
        sy = painel.y + layout.px(90 if self.compacto else 84)
        escudo_frac = 1.0 if d["escudo"] else 0.0
        if d["escudo"]:
            pulso = 0.75 + 0.25 * math.sin(t * 3)
            cor_escudo = tuple(int(c * pulso)
                               for c in self._paleta["primaria"])
        else:
            cor_escudo = self._paleta["primaria"]
        barra_escudo = pygame.Rect(x0, sy, layout.px(100 if self.compacto else 128), layout.px(5))
        _barra_fina(tela, layout, barra_escudo, escudo_frac, cor_escudo,
                    brilho=False)
        # energia de sistemas (mini barra + valor)
        ey = painel.y + layout.px(130 if self.compacto else 118)
        frac_energia = d["energia"] / 100.0
        barra_energia = pygame.Rect(x0, ey, layout.px(100 if self.compacto else 128), layout.px(5))
        _barra_fina(tela, layout, barra_energia, frac_energia,
                    self._paleta["energia"])
        rot_ener = _render(self._f_padrao_xxs, "ENERGIA", CINZA_HUD)
        rotulo_y = painel.y + layout.px(105 if self.compacto else 97)
        _blit_alfa(tela, rot_ener, (x0, rotulo_y))
        _numero(tela, layout, self._f_padrao_xxs, f"{int(d['energia'])}",
                (painel.right - layout.px(10), rotulo_y),
                self._paleta["energia"], "direita")

    def _topo_direita(self, tela, d, t):
        layout = self.layout
        m = layout.margem(HUD_MARGEM_BASE)
        largura = layout.px(HUD_LARGURA_PAINEL_DIREITO)
        altura = layout.px(
            HUD_ALTURA_PAINEL_PONTUACAO_COMPACTO if self.compacto
            else HUD_ALTURA_PAINEL_PADRAO)
        painel = pygame.Rect(layout.largura - m - largura, m, largura, altura)
        _painel(tela, layout, painel, self._paleta["secundaria"],
                alpha=OPACIDADE_PAINEL_HUD,
                glow=0, fundo=FUNDO_TEXTO_HUD)

        x = painel.right - layout.px(12)
        if self.compacto:
            rotulo = _render(self._f_titulo_xs, "PONTOS", CINZA_HUD)
            _blit_alfa(tela, rotulo, (painel.x + layout.px(12),
                                      painel.y + layout.px(8)))
            _numero(tela, layout, self._f_numero, d["pontos"],
                    (x, painel.y + layout.px(8)), BRANCO_HUD, "direita")
            surf_hi = _render(self._f_padrao_xxs, "RECORDE", CINZA_HUD)
            _blit_alfa(tela, surf_hi, (painel.x + layout.px(12),
                                       painel.y + layout.px(48)))
            _numero(tela, layout, self._f_padrao_s, d["recorde"],
                    (x, painel.y + layout.px(48)), OURO_HUD, "direita")
            y_abates = painel.y + layout.px(91)
            _icone_abates(tela, (painel.x + layout.px(24), y_abates), CINZA_HUD,
                          layout.escala)
            _numero(tela, layout, self._f_padrao_s, d["abates"],
                    (painel.x + layout.px(38), y_abates), CINZA_HUD, "esquerda")
            if d["combo"] > 1:
                mult = _render(self._f_titulo_s, f"x{d['bonus']:.1f}",
                               (255, 214, 110))
                _blit_alfa(tela, mult, (painel.right - layout.px(12) -
                                        mult.get_width(), y_abates))
            return

        rotulo = _render(self._f_titulo_xs, "PONTOS", CINZA_HUD)
        _blit_alfa(tela, rotulo, (x - rotulo.get_width(), painel.y + layout.px(10)),
                   210)
        _numero(tela, layout, self._f_numero, d["pontos"],
                (x, painel.y + layout.px(28)), BRANCO_HUD, "direita", 245)

        # high score
        surf_hi = _render(self._f_padrao_xxs, "RECORDE", (120, 130, 170))
        _blit_alfa(tela, surf_hi, (painel.x + layout.px(12), painel.y + layout.px(14)),
                   190)
        _numero(tela, layout, self._f_padrao_s, d["recorde"],
                (painel.x + layout.px(12), painel.y + layout.px(32)), OURO_HUD,
                "esquerda", 215)

        # abates
        y_abates = painel.y + layout.px(56)
        _icone_abates(tela, (painel.x + layout.px(24), y_abates), CINZA_HUD,
                      layout.escala)
        _numero(tela, layout, self._f_padrao_s, d["abates"],
                (painel.x + layout.px(38), y_abates + layout.px(1)), CINZA_HUD,
                "esquerda", 220)
        rot_ab = _render(self._f_padrao_xxs, "ABATES", (110, 118, 160))
        _blit_alfa(tela, rot_ab, (painel.x + layout.px(64), y_abates - layout.px(4)),
                   180)

        # combo multiplicador (visivel quando > 1)
        if d["combo"] > 1:
            comb_x = x - layout.px(12)
            mult = _render(self._f_titulo_s, f"x{d['bonus']:.1f}",
                           (255, 214, 110))
            _blit_alfa(tela, mult, (comb_x - mult.get_width(),
                                    painel.y + layout.px(56)), 240)
            fracao = min(1.0, d["combo"] / 20.0)
            barra = pygame.Rect(comb_x - layout.px(64), painel.y + layout.px(78),
                                layout.px(60), layout.px(4))
            _barra_fina(tela, layout, barra, fracao, OURO_HUD)
            rot_combo = _render(self._f_padrao_xxs, f"COMBO {d['combo']}",
                                (200, 170, 90))
            _blit_alfa(tela, rot_combo, (comb_x - rot_combo.get_width(),
                                         painel.y + layout.px(82)), 200)

    def _topo_centro(self, tela, d, t):
        layout = self.layout
        cx = layout.largura // 2
        y = layout.margem(16)
        painel = pygame.Rect(0, 0, layout.px(HUD_LARGURA_PAINEL_CENTRAL),
                             layout.px(82))
        painel.midtop = (cx, y - layout.px(8))
        _painel(tela, layout, painel, self._paleta["primaria"],
                alpha=OPACIDADE_PAINEL_HUD, raio=8, glow=0,
                fundo=FUNDO_TEXTO_HUD)

        setor = _render(self._f_titulo_m,
                        f"SETOR {d['cenario']:02d}", BRANCO_HUD)
        rect_setor = setor.get_rect(center=(
            cx, y + layout.px(22 if self.compacto else 16)))
        _blit_alfa(tela, setor, rect_setor, 240)
        # acentos laterais discretos
        for s in (-1, 1):
            linha_suave(tela, (90, 100, 150),
                        (rect_setor.left - layout.px(22), rect_setor.centery),
                        (rect_setor.left - layout.px(6), rect_setor.centery), 1)
            linha_suave(tela, (90, 100, 150),
                        (rect_setor.right + layout.px(6), rect_setor.centery),
                        (rect_setor.right + layout.px(22), rect_setor.centery), 1)

        regiao = _render(self._f_titulo_xs, d["regiao"], self._paleta["primaria"])
        _blit_alfa(tela, regiao, regiao.get_rect(center=(
            cx, y + layout.px(46 if self.compacto else 38))),
                   230)

        # progresso da fase (extremamente discreto)
        largura = layout.px(280)
        barra = pygame.Rect(cx - largura // 2,
                            y + layout.px(70 if self.compacto else 54),
                            largura, layout.px(4))
        _barra_fina(tela, layout, barra, d["progresso"], self._paleta["primaria"],
                    brilho=False)

    def _base_esquerda(self, tela, d, t):
        layout = self.layout
        m = layout.margem(HUD_MARGEM_BASE)
        centro = (m + layout.px(82), layout.altura - m -
                  layout.px(120 if self.compacto else 82))
        raio = layout.px(38)
        fracao = d["boost"]
        if fracao < 0.25:
            pulso = 0.55 + 0.45 * abs(math.sin(t * 5))
            cor = tuple(int(c * pulso) for c in self._paleta["primaria"])
        else:
            cor = self._paleta["primaria"]
        _medidor_circular(tela, layout, centro, raio, fracao, cor,
                          rotulo="IMPULSO", valor=f"{int(fracao * 100)}%",
                          rotulo_abaixo=self.compacto)

        # velocidade
        vx = centro[0]
        vy = centro[1] + raio + layout.px(40 if self.compacto else 20)
        vel = _render(self._f_padrao_s, f"VEL {d['vel']:.1f}",
                      (170, 178, 220))
        _blit_alfa(tela, vel, vel.get_rect(center=(vx, vy)))
        barra_vel = pygame.Rect(
            vx - layout.px(30), vy + layout.px(10),
            layout.px(60), layout.px(3))
        _barra_fina(tela, layout, barra_vel, min(1.0, d["vel"] / 12.0),
                    self._paleta["primaria"], brilho=False)
        esquiva = _render(
            self._f_padrao_xxs,
            "ESQUIVA PRONTA" if d["esquiva"] >= 1 else f"ESQUIVA {d['esquiva']:.0%}",
            self._paleta["primaria"] if d["esquiva"] >= 1 else CINZA_HUD,
        )
        _blit_alfa(tela, esquiva, esquiva.get_rect(center=(
            vx, vy + layout.px(45 if self.compacto else 25))))

    def _base_direita(self, tela, d, t):
        layout = self.layout
        m = layout.margem(HUD_MARGEM_BASE)
        arma = d["arma"]
        largura = layout.px(HUD_LARGURA_PAINEL_ESQUERDO)
        altura = layout.px(
            HUD_ALTURA_PAINEL_ARMA_COMPACTO if self.compacto
            else HUD_ALTURA_PAINEL_ARMA_PADRAO)
        painel = pygame.Rect(layout.largura - m - largura, layout.altura - m - altura,
                             largura, altura)
        _painel(tela, layout, painel, arma["cor"],
                alpha=OPACIDADE_PAINEL_HUD, glow=0,
                fundo=FUNDO_TEXTO_HUD)

        badge_c = (painel.x + layout.px(28), painel.y + layout.px(30))
        desenhar_poligono(tela, (52, 66, 110),
                          losango(badge_c, layout.px(24), layout.px(26)),
                          espessura=1)
        _icone_arma(tela, arma["tipo"], badge_c, arma["cor"], layout.escala * 1.1)

        x0 = painel.x + layout.px(58)
        cor_nome = BRANCO_HUD
        if opcoes_atuais().ativo:
            indice = next(i for i, item in enumerate(ARMARIA) if item["tipo"] == arma["tipo"])
            cor_nome = RARIDADES[RARIDADE_ARMAS[indice]]
        if self.compacto and " " in arma["nome"]:
            palavras = arma["nome"].upper().split(maxsplit=1)
            for indice, palavra in enumerate(palavras):
                nome = _render(self._f_titulo_s, palavra, cor_nome)
                _blit_alfa(tela, nome, (x0, painel.y + layout.px(4 + indice * 32)))
        else:
            nome = _render(self._f_titulo_s, arma["nome"].upper(), cor_nome)
            _blit_alfa(tela, nome,
                       (x0, painel.y + layout.px(4 if self.compacto else 12)))
        legenda = f"NV {arma['nivel']:02d}"
        if opcoes_atuais().ativo and not self.compacto:
            legenda += " / " + RARIDADE_ARMAS[indice].upper()
        nivel = _render(
            self._f_padrao_xxs, legenda, cor_nome if opcoes_atuais().ativo else CINZA_HUD)
        _blit_alfa(tela, nivel, (x0, painel.y + layout.px(64 if self.compacto else 30)))

        # carga / municao da arma
        cy = painel.y + layout.px(88 if self.compacto else 48)
        barra = pygame.Rect(x0, cy, layout.px(118), layout.px(6))
        _barra_segmentada(tela, layout, barra, d["municao"], arma["cor"], 8,
                          raio_canto=2)
        rot_carga = _render(self._f_padrao_xxs,
                            "CARREGANDO" if d["municao"] < 1.0 else "PRONTA",
                            (150, 158, 200) if d["municao"] < 1.0 else arma["cor"])
        _blit_alfa(tela, rot_carga, (x0, cy + layout.px(10 if self.compacto else 8)))

    def _base_centro(self, tela, d, t):
        layout = self.layout
        cx = layout.largura // 2
        largura = layout.px(236)
        altura = layout.px(10)
        m = layout.margem(14)
        y = layout.altura - m - altura - layout.px(18)
        barra = pygame.Rect(cx - largura // 2, y, largura, altura)

        pronto = d["especial"] >= 1.0
        cor = (self._paleta["secundaria"] if pronto
               else tuple(int(c * 0.42)
                          for c in self._paleta["secundaria"]))
        _barra_segmentada(tela, layout, barra, d["especial"], cor, 10,
                          raio_canto=2)

        intangivel = d["especial_atual"] == "intangivel"
        nome = "INTANGÍVEL" if intangivel else "BOMBA"
        rotulo = _render(self._f_titulo_xs, nome, CINZA_HUD)
        _blit_alfa(tela, rotulo,
                   (barra.x + layout.px(6), barra.y + layout.px(12)), 200)

        if pronto or d["tempo_intangivel"] > 0:
            pulso = 0.7 + 0.3 * math.sin(t * 4)
            desenhar_glow(tela, self._paleta["secundaria"], barra.center,
                          max(barra.w, barra.h), 0.5 * pulso)
            status = (f"INTANGÍVEL {math.ceil(d['tempo_intangivel'] / 60)}s"
                      if d["tempo_intangivel"] > 0 else f"{nome} PRONTA")
            surf = _render(self._f_titulo_xs, status,
                           tuple(int(c * pulso)
                                 for c in self._paleta["secundaria"]))
            _blit_alfa(tela, surf,
                       surf.get_rect(midright=(barra.right - layout.px(6),
                                               barra.y + layout.px(12))), 235)

    def _barra_boss(self, tela, d, t):
        boss = d["boss"]
        if not boss:
            return
        layout = self.layout
        cx = layout.largura // 2
        largura = layout.px(HUD_LARGURA_BARRA_BOSS)
        altura = layout.px(16)
        y = layout.px(
            HUD_Y_BARRA_BOSS_COMPACTO if self.compacto
            else HUD_Y_BARRA_BOSS_PADRAO)
        barra = pygame.Rect(cx - largura // 2, y, largura, altura)

        fracao = max(0.0, min(1.0, boss.vida / max(1, boss.vida_max)))

        nome = _render(self._f_titulo_s, boss.nome, BRANCO_HUD)
        rect_nome = nome.get_rect(center=(
            cx, y - layout.px(30 if self.compacto else 20)))
        retangulo_suave(
            tela, FUNDO_TEXTO_HUD,
            rect_nome.inflate(layout.px(HUD_MARGEM_PLAQUETA_TEXTO),
                              layout.px(HUD_MARGEM_PLAQUETA_TEXTO)),
            layout.px(HUD_RAIO_PLAQUETA_TEXTO),
        )
        _blit_alfa(tela, nome, rect_nome, 245)
        # linhas de ancoragem do nome
        for s in (-1, 1):
            linha_suave(tela, OURO_HUD,
                        (rect_nome.right if s < 0 else rect_nome.left,
                         rect_nome.centery),
                        (barra.right if s < 0 else barra.left,
                         rect_nome.centery), 1)

        _painel(tela, layout, barra.inflate(layout.px(16), layout.px(14)),
                OURO_HUD, alpha=120, raio=14, glow=16)
        _barra_segmentada(tela, layout, barra, fracao, OURO_HUD, SEGMENTOS_BOSS,
                          raio_canto=4)
        desenhar_glow(tela, OURO_HUD, barra.center, max(barra.w, barra.h),
                      0.25)

        fase_atual = getattr(boss, "fase_atual", None)
        if fase_atual is None:
            fase_atual = 1 if fracao > 0.66 else 2 if fracao > 0.33 else 3
        estado_miniboss = getattr(boss, "estado", None)
        rotulo = getattr(estado_miniboss, "rotulo", f"FASE {fase_atual}/3")
        fase = _render(self._f_padrao_xxs, rotulo, OURO_HUD)
        rect_fase = fase.get_rect(midleft=(barra.right + layout.px(14),
                                           barra.centery))
        retangulo_suave(
            tela, FUNDO_TEXTO_HUD,
            rect_fase.inflate(layout.px(HUD_MARGEM_PLAQUETA_TEXTO),
                              layout.px(HUD_MARGEM_PLAQUETA_TEXTO)),
            layout.px(HUD_RAIO_PLAQUETA_TEXTO),
        )
        _blit_alfa(tela, fase, rect_fase, 220)
