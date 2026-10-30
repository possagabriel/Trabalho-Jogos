"""Testes do HUD profissional de combate.

Cobre ``game.hud``: renderizacao de todos os modulos (jogador, score, setor,
boost, arma, especial e barra de boss) sobre a superficie logica 1280x720,
a dinamica dos segmentos de vida e do boss, e a leitura de dados por duck
typing (sem depender do ``core.Jogo`` real).

Roda headless:

    python tests/test_hud.py   # standalone
    pytest tests/test_hud.py -v
"""

import os
import sys
import tempfile
from types import SimpleNamespace

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["INCARNATE_DATA_DIR"] = tempfile.mkdtemp(prefix="incarnate_test_")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402

import src.runtime.presentation.hud as hud_runtime  # noqa: E402
from game.config import ALTURA, LARGURA  # noqa: E402
from game.hud import HudJogo  # noqa: E402
from game.player import Jogador  # noqa: E402
from game.weapons import ARMARIA  # noqa: E402
from src.infrastructure.graphics.comic_theme import usar_visual  # noqa: E402
from src.infrastructure.ui.layout import Layout  # noqa: E402
from src.runtime.infrastructure.graphics.style_tokens import (  # noqa: E402
    CONTRASTE_TEXTO_HUD_AJUSTE,
    CONTRASTE_TEXTO_MINIMO,
    FUNDO_TEXTO_HUD,
    OPACIDADE_PAINEL_HUD,
    TEXTO_ESSENCIAL_MIN_PX,
    TEXTO_SECUNDARIO_MIN_PX,
)

# ---------------------------------------------------------------------------
# Apoio: estado de jogo ficticio (duck typing)
# ---------------------------------------------------------------------------

class JogoFake:
    """Estado minimo que o HUD consome (mesma interface do ``core.Jogo``)."""

    def __init__(self, vida=5, escudo=False, combo=1, pontuacao=1200,
                 abates=7, arma=0, nivel=2, boss_vida=None,
                 boss_nome="VOID GUARDIAN"):
        self.jogador = Jogador(nome="PLAYER 01")
        self.jogador.max_vida = 8
        self.jogador.vida = vida
        self.jogador.escudo = escudo
        self.jogador.pontuacao = pontuacao
        self.jogador.nivel = nivel
        self.jogador.arma_atual = arma
        self.jogador.cooldown_tiro = 0
        self.jogador.burst_left = 0
        self.jogador.combo.combo_atual = combo
        self.cenario = SimpleNamespace(id=3, nome="DEEP SPACE")
        self.recordes = [{"pontos": 5000}]
        self.inimigos_abates = abates
        self.fila_onda = [1, 1, 1]
        self.inimigos = []
        self.boost = 0.6
        self.especial = 0.4
        self.energia = 55.0
        self.boss = None
        if boss_vida is not None:
            self.boss = SimpleNamespace(nome=boss_nome, vida=boss_vida,
                                        vida_max=280)


def _tela():
    return pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)


def _hud():
    pygame.init()
    return HudJogo()


def _desenha(jogo, t=0.0):
    tela = _tela()
    hud = _hud()
    dados = hud.desenhar(tela, jogo, tempo=t)
    return tela, hud, dados


# ---------------------------------------------------------------------------
# Modulos do HUD
# ---------------------------------------------------------------------------

def test_desenha_hud_sem_erros():
    tela, _, _ = _desenha(JogoFake())
    assert tela.get_width() == LARGURA
    assert tela.get_height() == ALTURA


def test_desenha_hud_com_boss():
    tela, _, _ = _desenha(JogoFake(boss_vida=140))
    assert tela.get_width() == LARGURA


def test_mundo_aberto_reserva_topo_direito_para_o_minimapa(monkeypatch):
    jogo = JogoFake()
    hud = _hud()
    chamadas = []
    monkeypatch.setattr(hud, "_topo_direita", lambda *_args: chamadas.append(True))

    jogo.modo_atual = "mundo_aberto"
    hud.desenhar(_tela(), jogo)
    assert not chamadas

    jogo.modo_atual = "linear"
    hud.desenhar(_tela(), jogo)
    assert chamadas


def test_monitor_de_desempenho_e_renderizado_quando_habilitado():
    jogo = JogoFake()
    jogo.config = {
        "mostrar_desempenho": True,
        "qualidade_grafica": "DESEMPENHO",
    }
    jogo.fps_atual = 58.7
    jogo.tempo_quadro_ms = 17.2
    jogo._escala_rapida = True

    _, hud, _ = _desenha(jogo)

    assert hud._telemetria_surface is not None


def test_dados_lidos_do_jogo():
    jogo = JogoFake(vida=3, escudo=True, combo=6, pontuacao=99999, abates=13)
    _, _, dados = _desenha(jogo)
    assert dados["vida"] == 3
    assert dados["escudo"] is True
    assert dados["combo"] == 6
    assert dados["pontos"] == 99999
    assert dados["abates"] == 13
    assert dados["cenario"] == 3
    assert dados["regiao"] == "DEEP SPACE"
    assert dados["recorde"] == 5000


def test_dados_dos_medidores():
    _, _, dados = _desenha(JogoFake())
    assert 0.0 <= dados["boost"] <= 1.0
    assert 0.0 <= dados["especial"] <= 1.0
    assert 0.0 <= dados["energia"] <= 100.0
    assert dados["municao"] >= 0.0


def test_dados_arma_por_tipo():
    for indice in range(len(ARMARIA)):
        _, _, dados = _desenha(JogoFake(arma=indice))
        assert dados["arma"]["nome"] == ARMARIA[indice]["nome"]


def test_fontes_hud_respeitam_minimos_em_janela_pequena():
    pygame.init()
    hud = hud_runtime.HudJogo(Layout(900, 506))

    for fonte in (hud._f_padrao_xxs, hud._f_padrao_xs, hud._f_titulo_xs):
        assert fonte.render("Ag0", True, (255, 255, 255)).get_bounding_rect().height >= (
            TEXTO_SECUNDARIO_MIN_PX)
    for fonte in (hud._f_padrao_s, hud._f_padrao_m, hud._f_titulo_s,
                  hud._f_titulo_m, hud._f_titulo_g, hud._f_numero):
        assert fonte.render("Ag0", True, (255, 255, 255)).get_bounding_rect().height >= (
            TEXTO_ESSENCIAL_MIN_PX)


def test_medidor_separa_valor_e_rotulo(monkeypatch):
    pygame.init()
    registros = []

    def capturar_blit(_tela, surf, pos, alfa=255):
        registros.append(pygame.Rect(pos))

    monkeypatch.setattr(hud_runtime, "_blit_alfa", capturar_blit)
    for largura, altura, rotulo_abaixo in ((900, 506, True), (1280, 720, False)):
        registros.clear()
        layout = Layout(largura, altura)
        tela = pygame.Surface((largura, altura), pygame.SRCALPHA)
        centro = (layout.px(82), altura - layout.px(120))
        hud_runtime._medidor_circular(
            tela, layout, centro, layout.px(38), 0.8, (255, 112, 72),
            rotulo="IMPULSO", valor="80%", rotulo_abaixo=rotulo_abaixo,
        )

        assert len(registros) == 2
        rect_valor, rect_rotulo = registros
        assert rect_rotulo.top >= rect_valor.bottom + layout.px(3)
        if not rotulo_abaixo:
            assert rect_rotulo.top >= centro[1]


def test_lettering_comic_respeita_minimos_em_janela_pequena():
    pygame.init()
    pygame.display.set_mode((900, 506))
    hud = hud_runtime.HudJogo(Layout(900, 506))
    jogo = JogoFake()
    jogo.config = {"estilo_visual": "COMIC", "qualidade_comic": "MEDIA"}

    with usar_visual(jogo.config):
        secundarios = (hud._f_padrao_xxs, hud._f_padrao_xs, hud._f_titulo_xs)
        essenciais = (hud._f_padrao_s, hud._f_padrao_m, hud._f_titulo_s,
                      hud._f_titulo_m, hud._f_titulo_g, hud._f_numero)
        for fonte in secundarios:
            altura = hud_runtime._render(fonte, "Ag0", (255, 255, 255))
            assert altura.get_bounding_rect().height >= TEXTO_SECUNDARIO_MIN_PX
        for fonte in essenciais:
            altura = hud_runtime._render(fonte, "Ag0", (255, 255, 255))
            assert altura.get_bounding_rect().height >= TEXTO_ESSENCIAL_MIN_PX


def test_cores_de_texto_hud_alcancam_contraste_wcag_minimo():
    amostras = (
        (150, 158, 200), (120, 130, 170), (110, 118, 160),
        (150, 132, 240), (200, 170, 90), (255, 214, 110),
        (64, 226, 230), (255, 96, 140),
    )
    fundo_brilhante_com_painel = tuple(
        round(c * OPACIDADE_PAINEL_HUD / 255 +
              255 * (255 - OPACIDADE_PAINEL_HUD) / 255)
        for c in FUNDO_TEXTO_HUD
    )

    for cor in amostras:
        ajustada = hud_runtime.cor_com_contraste(
            cor, FUNDO_TEXTO_HUD, CONTRASTE_TEXTO_HUD_AJUSTE)
        assert hud_runtime.razao_contraste(ajustada, fundo_brilhante_com_painel) >= (
            CONTRASTE_TEXTO_MINIMO)
        assert hud_runtime.razao_contraste(ajustada, FUNDO_TEXTO_HUD) >= (
            CONTRASTE_TEXTO_MINIMO)


# ---------------------------------------------------------------------------
# Barra de boss
# ---------------------------------------------------------------------------

def test_sem_boss_nao_desenha_barra():
    tela, _, dados = _desenha(JogoFake())
    assert dados["boss"] is None
    assert tela.get_size() == (LARGURA, ALTURA)


def test_boss_com_segmentos_espelha_vida():
    fracao = 0.5
    tela, _, dados = _desenha(JogoFake(boss_vida=int(280 * fracao)))
    assert dados["boss"] is not None
    assert dados["boss"].nome == "VOID GUARDIAN"
    # o HUD nao levanta excecoes com a barra parcial
    assert tela.get_size() == (LARGURA, ALTURA)


def test_boss_nome_exibido():
    tela, _, _ = _desenha(JogoFake(boss_vida=10, boss_nome="HEXAGONO"))
    assert tela.get_size() == (LARGURA, ALTURA)


def test_boss_combo_e_especial_estao_ativos():
    jogo = JogoFake(boss_vida=10, combo=12)
    jogo.especial = 1.0
    _, _, dados = _desenha(jogo)
    assert dados["combo"] == 12
    assert dados["especial"] == 1.0


# ---------------------------------------------------------------------------
# Leitura de dados parciais (campos opcionais)
# ---------------------------------------------------------------------------

def test_sem_recordes_usa_zero():
    jogo = JogoFake()
    jogo.recordes = []
    _, _, dados = _desenha(jogo)
    assert dados["recorde"] == 0


def test_sem_cenario_usado_padrao():
    jogo = JogoFake()
    jogo.cenario = None
    _, _, dados = _desenha(jogo)
    assert dados["cenario"] == 1
    assert dados["regiao"] == "ESPAÇO PROFUNDO"


def test_velocidade_reduzida_nao_quebra_hud():
    jogo = JogoFake()
    jogo.jogador.velocidade = 0.0
    _, _, dados = _desenha(jogo)
    assert dados["vel"] == 0.0


def test_vida_zero():
    _, _, dados = _desenha(JogoFake(vida=0))
    assert dados["vida"] == 0


def test_boost_zero():
    jogo = JogoFake()
    jogo.boost = 0.0
    _, _, dados = _desenha(jogo)
    assert dados["boost"] == 0.0


# ---------------------------------------------------------------------------
# Dinamica de tempo (anima coes nao quebram)
# ---------------------------------------------------------------------------

def test_tempo_variado():
    for t in (0.0, 0.5, 3.7, 9.9):
        _desenha(JogoFake(boss_vida=80), t=t)


def test_renderizacao_repetida_estavel():
    jogo = JogoFake(boss_vida=80)
    tela = _tela()
    hud = _hud()
    for t in range(30):
        tela.fill((0, 0, 0))
        hud.desenhar(tela, jogo, tempo=t / 10.0)
    assert tela.get_size() == (LARGURA, ALTURA)


# ---------------------------------------------------------------------------
# main() standalone
# ---------------------------------------------------------------------------

def main():
    funcoes = [v for k, v in sorted(globals().items())
               if k.startswith("test_") and callable(v)]
    for fn in funcoes:
        fn()
    print(f"{len(funcoes)} testes OK.")


if __name__ == "__main__":
    main()
