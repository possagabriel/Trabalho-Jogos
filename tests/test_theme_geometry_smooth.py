"""Testes de logica pura e renderizacao suave.

Cobre ``theme`` (paletas, interpolacao de cores), ``geometry`` (geracao de
vertices) e ``smooth`` (easing, gradientes, glow, superficies cacheadas).

Roda headless:

    python tests/test_theme_geometry_smooth.py   # standalone
    pytest tests/test_theme_geometry_smooth.py -v
"""

import os
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["SPACEFURY_DATA_DIR"] = tempfile.mkdtemp(prefix="spacefury_test_")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import math  # noqa: E402

import pygame  # noqa: E402

from game import geometry  # noqa: E402
from game import smooth  # noqa: E402
from game import theme  # noqa: E402
from game.config import ALTURA, LARGURA  # noqa: E402


# ---------------------------------------------------------------------------
# theme
# ---------------------------------------------------------------------------

def test_temas_contem_chaves_obrigatorias():
    for nome, paleta in theme.TEMAS_CORES.items():
        for chave in ("primaria", "secundaria", "terciaria", "detalhe",
                      "fundo_painel", "borda_forte", "borda_fraco"):
            assert chave in paleta, (nome, chave)
            assert len(paleta[chave]) == 3, (nome, chave)


def test_tema_atual_fallback_neon():
    assert theme.tema_atual("NEON") is theme.TEMAS_CORES["NEON"]
    assert theme.tema_atual(None) is theme.TEMAS_CORES["NEON"]
    assert theme.tema_atual("nao-existe") is theme.TEMAS_CORES["NEON"]
    assert theme.tema_atual("aurora") is theme.TEMAS_CORES["AURORA"]
    assert theme.cor_tema("MAGMA", "primaria") == theme.TEMAS_CORES["MAGMA"]["primaria"]


def test_cor_misturar_extremos_e_easing():
    a, b = (0, 0, 0), (255, 255, 255)
    assert theme.cor_misturar(a, b, 0.0) == (0, 0, 0)
    assert theme.cor_misturar(a, b, 1.0) == (255, 255, 255)
    assert theme.cor_misturar(a, b, -5) == (0, 0, 0)
    assert theme.cor_misturar(a, b, 9) == (255, 255, 255)
    # smoothstep: no meio exato o valor e 0.5 * 255 (easing simetrico)
    assert theme.cor_misturar(a, b, 0.5) == (127, 127, 127)
    # simetria: interpolar de A->B em t equivale a B->A em 1-t
    assert theme.cor_misturar(a, b, 0.25) == theme.cor_misturar(b, a, 0.75)


def test_cor_ciclar_retorna_rgb_valido():
    pygame.init()
    for _ in range(5):
        cor = theme.cor_ciclar((10, 20, 30), (200, 150, 100))
        assert len(cor) == 3
        assert all(0 <= c <= 255 for c in cor)


# ---------------------------------------------------------------------------
# geometry
# ---------------------------------------------------------------------------

def test_poligono_vertices_e_primeiro_ponto():
    pts = geometry.poligono((100, 100), 50, 6)
    assert len(pts) == 6
    # primeiro vertice no angulo 0: (cx + raio, cy)
    x, y = pts[0]
    assert abs(x - 150) < 1e-9 and abs(y - 100) < 1e-9
    # angulo inicial desloca o primeiro vertice
    pts2 = geometry.poligono((100, 100), 50, 6, angulo=math.pi / 2)
    x2, y2 = pts2[0]
    assert abs(x2 - 100) < 1e-9 and abs(y2 - 150) < 1e-9


def test_estrela_quantidade_pontas():
    for pontas in range(3, 8):
        pts = geometry.estrela((50, 50), 30, pontas=pontas)
        assert len(pts) == pontas * 2


def test_losango_rotaciona():
    pts = geometry.losango((0, 0), 10, 20, 0.0)
    assert len(pts) == 4
    assert pts[0] == (0, -20)
    pts_r = geometry.losango((0, 0), 10, 20, math.pi / 2)
    x, y = pts_r[0]
    assert abs(x - 20) < 1e-9 and abs(y - 0) < 1e-9


def test_formas_quantidades():
    assert len(geometry.triangulo((0, 0), 5)) == 3
    assert len(geometry.quadrado((0, 0), 5)) == 4
    assert len(geometry.pentagono((0, 0), 5)) == 5
    assert len(geometry.cruz((0, 0), 10)) == 12


def test_cruz_simetrica():
    pts = geometry.cruz((100, 100), 20)
    minimo_x = min(p[0] for p in pts)
    maximo_x = max(p[0] for p in pts)
    minimo_y = min(p[1] for p in pts)
    maximo_y = max(p[1] for p in pts)
    assert minimo_x == 80 and maximo_x == 120
    assert minimo_y == 80 and maximo_y == 120


# ---------------------------------------------------------------------------
# smooth: easing e interpolacao
# ---------------------------------------------------------------------------

def test_easing_clampa_e_pontos_fixos():
    assert smooth.ease_in_out(0.0) == 0.0
    assert smooth.ease_in_out(1.0) == 1.0
    assert abs(smooth.ease_in_out(0.5) - 0.5) < 1e-9
    assert smooth.ease_in_out(-1) == 0.0
    assert smooth.ease_in_out(2) == 1.0
    assert smooth.ease_in(0) == 0 and smooth.ease_in(1) == 1
    assert smooth.ease_out(0) == 0 and smooth.ease_out(1) == 1
    assert abs(smooth.ease_out(0.5) - 0.75) < 1e-9
    assert smooth.lerp(0, 10, 0.3) == 3.0
    assert smooth.lerp(10, 0, 0.5) == 5.0


def test_interpolar_cor_clampa():
    assert smooth.interpolar_cor((0, 0, 0), (255, 255, 255), 0) == (0, 0, 0)
    assert smooth.interpolar_cor((0, 0, 0), (255, 255, 255), 1) == (255, 255, 255)
    assert smooth.interpolar_cor((0, 0, 0), (255, 255, 255), -3) == (0, 0, 0)
    assert smooth.interpolar_cor((0, 0, 0), (255, 255, 255), 3) == (255, 255, 255)


# ---------------------------------------------------------------------------
# smooth: superficies cacheadas
# ---------------------------------------------------------------------------

def test_gradiente_vertical_tamanho_e_cache():
    pygame.init()
    g1 = smooth.gradiente_vertical((10, 20, 30), (5, 5, 5))
    g2 = smooth.gradiente_vertical((10, 20, 30), (5, 5, 5))
    assert g1.get_size() == (LARGURA, ALTURA)
    assert g1 is g2, "gradiente deve vir do cache (mesma superficie)"
    assert g1.get_at((LARGURA // 2, 0))[:3] == (10, 20, 30)
    assert g1.get_at((LARGURA // 2, ALTURA - 1))[:3] == (5, 5, 5)


def test_luz_radial_tamanho_e_alpha():
    pygame.init()
    surf = smooth.luz_radial((255, 0, 0), 20, 0.5)
    ext = max(1, int(20 * 2.2)) * 2
    assert surf.get_size() == (ext, ext)
    assert (surf.get_flags() & pygame.SRCALPHA)
    # centro deve ter alpha visivel (glow radial com intensidade 0.5)
    assert surf.get_at((ext // 2, ext // 2)).a > 50


def test_circulo_suave_cache_e_tamanho():
    pygame.init()
    a = smooth.circulo_suave((50, 100, 150), 12, brilho=1.0)
    b = smooth.circulo_suave((50, 100, 150), 12, brilho=1.0)
    assert a is b
    c = smooth.circulo_suave((50, 100, 150), 12, 2, brilho=1.0)
    assert a is not c


def test_poligono_suave_retorna_surface_e_offset():
    pygame.init()
    pts = [(0, 0), (30, 0), (15, 26)]
    surf, offset = smooth.poligono_suave((255, 255, 255), pts)
    assert isinstance(surf, pygame.Surface)
    assert len(offset) == 2
    assert surf.get_width() > 0 and surf.get_height() > 0


def test_painel_glass_e_vignette_cacheados():
    pygame.init()
    rect = pygame.Rect(10, 10, 200, 80)
    p1 = smooth.painel_glass((255, 0, 0), rect, raio_canto=14, alpha=225,
                             glow_raio=18)
    p2 = smooth.painel_glass((255, 0, 0), rect, raio_canto=14, alpha=225,
                             glow_raio=18)
    assert p1 is p2
    v1 = smooth.superficie_vignette(0.5, 0.5)
    v2 = smooth.superficie_vignette(0.5, 0.5)
    assert v1 is v2
    assert v1.get_size() == (LARGURA, ALTURA)


def test_texto_suave_cache():
    pygame.init()
    fonte = pygame.font.Font(None, 20)
    t1 = smooth.texto_suave(fonte, "OLA", (255, 255, 255), glow_cor=(0, 0, 255))
    t2 = smooth.texto_suave(fonte, "OLA", (255, 255, 255), glow_cor=(0, 0, 255))
    assert t1 is t2
    assert (t1.get_flags() & pygame.SRCALPHA)


def test_desenhos_rodam_sem_excecao():
    pygame.init()
    tela = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    rect = pygame.Rect(20, 20, 300, 100)
    smooth.desenhar_glow(tela, (255, 0, 0), (100, 100), 30, 0.6)
    smooth.desenhar_circulo(tela, (0, 255, 0), (150, 150), 20, brilho=1.0)
    smooth.desenhar_circulo(tela, (0, 255, 0), (200, 200), 20, 2, brilho=1.0)
    smooth.desenhar_poligono(tela, (0, 0, 255),
                            [(0, 0), (40, 0), (20, 34)], glow_cor=(255, 0, 0),
                            glow_raio=10)
    smooth.linha_suave(tela, (255, 255, 255), (0, 0), (200, 200), 3)
    fonte = pygame.font.Font(None, 24)
    smooth.desenhar_texto_suave(tela, fonte, "TESTE", (100, 100),
                                (255, 255, 255), alinhar="centro")
    smooth.desenhar_texto_suave(tela, fonte, "TESTE", (100, 100),
                                (255, 255, 255), alinhar="direita")
    smooth.desenhar_texto_suave(tela, fonte, "TESTE", (100, 100),
                                (255, 255, 255), alinhar="esquerda")
    smooth.retangulo_suave(tela, (100, 100, 100), rect, raio_canto=10,
                           glow_cor=(255, 0, 0), glow_raio=12)
    smooth.barra_suave(tela, 10, 10, 200, 12, 0.7, (0, 255, 0))
    smooth.desenhar_painel(tela, (255, 0, 0), rect, raio_canto=14)
    smooth.desenhar_cantos(tela, (255, 255, 255), rect, tamanho=14)
    smooth.desenhar_vignette(tela, 0.5, 0.5)


def main():
    funcoes = [v for k, v in sorted(globals().items())
               if k.startswith("test_") and callable(v)]
    falhas = 0
    for funcao in funcoes:
        try:
            funcao()
            print(f"OK   {funcao.__name__}")
        except Exception as erro:  # noqa: BLE001
            falhas += 1
            import traceback
            traceback.print_exc()
            print(f"FAIL {funcao.__name__}: {erro}")
    print(f"\n{len(funcoes) - falhas}/{len(funcoes)} testes passaram")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()