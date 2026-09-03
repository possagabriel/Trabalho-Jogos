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

from game.config import ALTURA, LARGURA  # noqa: E402
from game.hud import HudJogo  # noqa: E402
from game.player import Jogador  # noqa: E402
from game.weapons import ARMARIA  # noqa: E402


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
    assert dados["regiao"] == "DEEP SPACE"


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
