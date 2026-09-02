"""Testes do sistema de layout responsivo e da recomposicao do menu.

Cobre as resolucoes-alvo do jogo (1280x720, 1366x768, 1920x1080, 2560x1440 e
3840x2160, alem da base 900x700):

- Aritmetica do ``Layout`` (ancoras, proporcoes, safe areas, fileiras) e
  verificada em TODAS as resolucoes — barata, pois e matematica pura.
- A recomposicao do menu (desenho) e validada na base 900x700 e num formato
  maior (1280x720), incluindo a conferencia de que nenhum botao/painel
  ultrapassa os limites da superficie.

Roda headless:

    python tests/test_layout.py          # standalone
    pytest tests/test_layout.py -v      # via pytest
"""

import os
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("INCARNATE_DATA_DIR", tempfile.mkdtemp(prefix="incarnate_test_"))

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402

from game.core import Jogo  # noqa: E402
from game.layout import (  # noqa: E402
    ANCRAS, ALTURA_BASE, BASE_CENTRO, BASE_DIREITA, BASE_ESQUERDA, CENTRO,
    LARGURA_BASE, MEIO_DIREITA, MEIO_ESQUERDA, TOPO_CENTRO, TOPO_DIREITA,
    TOPO_ESQUERDA, Layout)
from game.menu import MenuPrincipal  # noqa: E402

RESOLUCOES_ALVO = [(900, 700), (1280, 720), (1366, 768), (1920, 1080),
                   (2560, 1440), (3840, 2160)]


def novo_jogo():
    return Jogo()


def test_escala_base_e_identidade():
    layout = Layout(900, 700)
    assert layout.escala == 1.0
    assert layout.px(180) == 180
    assert layout.centro == (450, 350)


def test_proporcoes_mantidas_em_todas_as_resolucoes():
    for largura, altura in RESOLUCOES_ALVO:
        layout = Layout(largura, altura)
        assert abs(layout.escala - min(largura / LARGURA_BASE,
                                       altura / ALTURA_BASE)) < 1e-9
        assert layout.x(0.5) == largura // 2
        assert layout.y(0.5) == altura // 2
        # valores de design escalam preservando as proporcoes da superficie
        assert abs(layout.px(180) / altura - 180 / ALTURA_BASE) < 0.01


def test_pontos_ancorados():
    layout = Layout(1920, 1080)
    assert layout.ponto(CENTRO) == (960, 540)
    assert layout.ponto(TOPO_DIREITA) == (1920, 0)
    assert layout.ponto(BASE_ESQUERDA) == (0, 1080)


def test_retangulos_ancorados_dentro_da_superficie():
    """Containers ancorados nunca ultrapassam a superficie (safe areas)."""
    for largura, altura in RESOLUCOES_ALVO:
        layout = Layout(largura, altura)
        for ancora in ANCRAS:
            ret = layout.rect(ancora, 0.8, 0.8)
            assert ret.x >= 0, (largura, altura, ancora)
            assert ret.y >= 0, (largura, altura, ancora)
            assert ret.right <= largura, (largura, altura, ancora)
            assert ret.bottom <= altura, (largura, altura, ancora)


def test_fileira_centralizada():
    layout = Layout(900, 700)
    rects = layout.fileira(3, 0.2, 0.06, 18, ancora=BASE_CENTRO, dy=-80)
    assert len(rects) == 3
    centro = (rects[0].centerx + rects[2].centerx) // 2
    assert centro == layout.x(0.5)


def test_menu_desenha_todas_as_telas():
    menu = novo_jogo().menu
    for subestado in ("MENU", "CONTINUAR", "LOJA", "RECORDES", "CONFIG"):
        menu.subestado = subestado
        menu.desenhar(menu.jogo.tela)
    menu.subestado = "CONFIG"
    menu.config_submodo = "controles"
    menu.desenhar(menu.jogo.tela)


def _conferir_dentro(menu, tela):
    limite = tela.get_rect()
    menu.subestado = "MENU"
    for opcao in menu.opcoes:
        assert limite.contains(opcao.get_rect(menu.x_opcoes,
                                              menu.fonte_opcao, menu.layout))
    menu.subestado = "RECORDES"
    assert limite.contains(menu._botao_voltar().rect)
    for botao in menu._botoes_continuar():
        assert limite.contains(botao.rect)
    for botao in menu._botoes_loja().values():
        assert limite.contains(botao.rect)
    for rect in menu._rects_loja():
        assert limite.contains(rect)


def test_menu_recomposto_em_resolucao_1280x720():
    """O menu se recompoe numa superficie logica maior sem coordenadas
    rigidas: desenha sem erros e nenhum elemento ultrapassa os limites."""
    jogo = novo_jogo()
    layout = Layout(1280, 720)
    menu = MenuPrincipal(jogo, layout=layout)
    tela = pygame.Surface((layout.largura, layout.altura))

    for subestado in ("MENU", "CONTINUAR", "LOJA", "RECORDES", "CONFIG"):
        menu.subestado = subestado
        menu.desenhar(tela)

    _conferir_dentro(menu, tela)


def test_layout_em_todas_as_resolucoes_alvo():
    """A aritmetica de posicionamento atende as 5 resolucoes-alvo."""
    for largura, altura in RESOLUCOES_ALVO:
        layout = Layout(largura, altura)
        for ancora in ANCRAS:
            ret = layout.rect(ancora, 0.5, 0.5)
            assert ret.x >= 0 and ret.y >= 0
            assert ret.right <= largura and ret.bottom <= altura
        # containers principais preservam a proporcao em qualquer resolucao
        painel = layout.rect(CENTRO, 520 / LARGURA_BASE, 330 / ALTURA_BASE,
                             dy=-35)
        assert abs(painel.w / largura - 520 / LARGURA_BASE) < 0.01
        assert abs(painel.h / altura - 330 / ALTURA_BASE) < 0.01


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
            print(f"FAIL {funcao.__name__}: {erro}")
    print(f"\n{len(funcoes) - falhas}/{len(funcoes)} testes passaram")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
