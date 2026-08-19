"""Testes dos componentes visuais do menu.

Cobre ``menu_scene``: fundo cinematográfico (incluindo o carregamento da
imagem ``fundo-menuprincipal.png`` e o fallback procedural), HUD diegético,
nave em destaque, destaque deslizante das opções, transição de missão e o
helper de texto espaçado.

Roda headless:

    python tests/test_menu_scene.py   # standalone
    pytest tests/test_menu_scene.py -v
"""

import os
import sys
import tempfile
from unittest import mock

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["SPACEFURY_DATA_DIR"] = tempfile.mkdtemp(prefix="spacefury_test_")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402

from game.config import LARGURA  # noqa: E402
from game.layout import Layout  # noqa: E402
from game.menu_scene import (  # noqa: E402
    DestaqueMenu, FundoCinematico, HudMenu, NaveMenu, TransicaoMissao,
    texto_espacado)
from game.player import SKINS, Skin  # noqa: E402
from game.theme import TEMAS_CORES  # noqa: E402

RAIZ_JOGO = os.path.dirname(RAIZ)
ARQUIVO_IMAGEM = os.path.join(RAIZ_JOGO, "images", "fundo-menuprincipal.png")


def _tema():
    return TEMAS_CORES["NEON"]


# ---------------------------------------------------------------------------
# texto_espacado
# ---------------------------------------------------------------------------

def test_texto_espacado():
    pygame.init()
    fonte = pygame.font.Font(None, 24)
    surf = texto_espacado(fonte, "AB", 4, (255, 255, 255))
    larguras = [fonte.size(ch)[0] for ch in "AB"]
    assert surf.get_width() >= sum(larguras) + 4
    assert (surf.get_flags() & pygame.SRCALPHA)


# ---------------------------------------------------------------------------
# FundoCinematico
# ---------------------------------------------------------------------------

def test_fundo_carrega_imagem_do_menu():
    if not os.path.exists(ARQUIVO_IMAGEM):
        return
    pygame.init()
    fundo = FundoCinematico()
    assert fundo.fundo_imagem is not None, \
        "fundo-menuprincipal.png deve ser carregado"
    assert fundo.fundo_imagem.get_size() == (900, 700)


def test_fundo_fallback_sem_imagem():
    pygame.init()
    with mock.patch("game.assets.pygame.image.load",
                    side_effect=FileNotFoundError("sem imagem")):
        fundo = FundoCinematico()
        assert fundo.fundo_imagem is None


def test_fundo_responsivo_1280():
    pygame.init()
    layout = Layout(1280, 720)
    fundo = FundoCinematico(layout)
    fundo.desenhar(pygame.Surface((1280, 720)))


def test_fundo_atualiza_e_desenha():
    pygame.init()
    tela = pygame.Surface((900, 700))
    fundo = FundoCinematico()
    for _ in range(60):
        fundo.atualizar()
        fundo.desenhar(tela)


# ---------------------------------------------------------------------------
# HudMenu
# ---------------------------------------------------------------------------

def test_hud_atualiza_e_desenha():
    pygame.init()
    tela = pygame.Surface((900, 700))
    hud = HudMenu()
    for _ in range(30):
        hud.atualizar()
        hud.desenhar(tela, _tema())


def test_hud_desenha_em_outra_resolucao():
    pygame.init()
    layout = Layout(1280, 720)
    tela = pygame.Surface((1280, 720))
    hud = HudMenu(layout)
    hud.desenhar(tela, _tema())


# ---------------------------------------------------------------------------
# NaveMenu
# ---------------------------------------------------------------------------

def test_nave_menu_desenha():
    pygame.init()
    tela = pygame.Surface((900, 700), pygame.SRCALPHA)
    nave = NaveMenu()
    skin = Skin(SKINS[0])
    nave.atualizar()
    nave.desenhar(tela, skin, 450, 350)


# ---------------------------------------------------------------------------
# DestaqueMenu
# ---------------------------------------------------------------------------

def test_destaque_aproxima_do_alvo():
    d = DestaqueMenu()
    d.y = 0
    d.alvo = 100
    for _ in range(120):
        d.atualizar()
    assert d.y > 90


def test_destaque_pulsar_e_desenhar():
    pygame.init()
    tela = pygame.Surface((900, 700))
    d = DestaqueMenu()
    d.pulsar()
    for _ in range(10):
        d.atualizar()
        d.desenhar(tela, 100, _tema())


# ---------------------------------------------------------------------------
# TransicaoMissao
# ---------------------------------------------------------------------------

def test_transicao_dispara_acao():
    pygame.init()
    t = TransicaoMissao(duracao=100)
    chamou = []

    def acao():
        chamou.append(True)
    ticks = [0, 50, 200]
    with mock.patch("game.menu_scene.pygame.time.get_ticks",
                    side_effect=lambda: ticks.pop(0)):
        t.iniciar(acao)
        assert t.em_andamento() is True
        assert t.progresso() == 0.5
        assert t.atualizar() is True
    assert chamou == [True]
    assert t.em_andamento() is False


def test_transicao_sem_acao_nao_quebra():
    pygame.init()
    t = TransicaoMissao(duracao=10)
    ticks = [0, 100]
    with mock.patch("game.menu_scene.pygame.time.get_ticks",
                    side_effect=lambda: ticks.pop(0)):
        t.iniciar(None)
        t.atualizar()


def test_transicao_desenha():
    pygame.init()
    tela = pygame.Surface((900, 700))
    t = TransicaoMissao(duracao=100)
    t.desenhar(tela, _tema())
    t.iniciar(None)
    for _ in range(3):
        t.desenhar(tela, _tema())


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