"""Testes de inimigos, inimigos especiais e bosses.

Cobre ``enemies`` (movimento e ataque por tipo, dano, formas de desenho,
composição de ondas e sorteio de especiais) e ``bosses`` (entrada em cena,
fases de vida, ataques por nome e enraivecer).

Roda headless:

    python tests/test_enemies_bosses.py   # standalone
    pytest tests/test_enemies_bosses.py -v
"""

import os
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["INCARNATE_DATA_DIR"] = tempfile.mkdtemp(prefix="incarnate_test_")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import math  # noqa: E402
import random  # noqa: E402

import pygame  # noqa: E402

from game.bosses import BOSSES_POR_CENARIO, Boss  # noqa: E402
from game.config import ALTURA, LARGURA  # noqa: E402
from game.enemies import (  # noqa: E402
    FORMAS, Inimigo, InimigoEspecial, TIPOS, composicao_onda,
    sortear_inimigo_especial)
from game.player import Jogador  # noqa: E402
from game.scenarios import Cenario  # noqa: E402


def novo_jogador():
    return Jogador()


# ---------------------------------------------------------------------------
# Inimigo
# ---------------------------------------------------------------------------

def test_tipos_completos():
    assert len(TIPOS) == 15
    for tipo, cfg in TIPOS.items():
        for chave in ("cor", "raio", "vida", "pontos", "vel", "mov", "ataque"):
            assert chave in cfg, tipo
        assert tipo in FORMAS, tipo


def test_inimigo_escala_por_nivel():
    e1 = Inimigo("forja", 1, x=100)
    e10 = Inimigo("forja", 10, x=100)
    assert e10.vida > e1.vida
    assert e10.vel > e1.vel
    assert e10.rect.collidepoint(100, -40)


def test_inimigo_movimento_reta():
    e = Inimigo("scout", 1, x=100, y=50)
    y0 = e.y
    e.atualizar(novo_jogador())
    assert e.y == y0 + e.vel


def test_inimigo_movimento_zigzag():
    e = Inimigo("soldado", 1, x=300, y=50)
    e.fase = 0
    e.atualizar(novo_jogador())
    assert abs(e.x - (300 + math.sin(0.05) * 70)) < 0.001
    assert e.y > 50


def test_inimigo_movimento_persegue_aproxima():
    jog = novo_jogador()
    jog.x, jog.y = 450, 200
    e = Inimigo("estelar", 1, x=100, y=500)
    d0 = math.hypot(jog.x - e.x, jog.y - e.y)
    e.atualizar(jog)
    d1 = math.hypot(jog.x - e.x, jog.y - e.y)
    assert d1 < d0


def test_inimigo_todos_movimentos_rodam():
    jog = novo_jogador()
    for tipo in TIPOS:
        e = Inimigo(tipo, 5, x=300, y=100)
        for _ in range(5):
            e.atualizar(jog)


def test_inimigo_ataca():
    jog = novo_jogador()
    for tipo, cfg in TIPOS.items():
        if cfg["ataque"] == "nenhum":
            continue
        e = Inimigo(tipo, 1, x=300, y=100)
        e.timer_ataque = 0
        projs = e.atualizar(jog)
        assert projs, tipo
        for p in projs:
            assert p.origem == "inimigo"


def test_inimigo_sem_ataque_nao_gera_projeteis():
    e = Inimigo("scout", 1, x=300, y=100)
    e.timer_ataque = 0
    assert e.atualizar(novo_jogador()) == []


def test_inimigo_sofrer_dano():
    e = Inimigo("scout", 1, x=100)
    assert e.sofrer_dano(1) is True
    e2 = Inimigo("forja", 1, x=100)
    assert e2.sofrer_dano(1) is False
    assert e2.vida == e2.vida_max - 1
    assert e2.flash == 6


def test_inimigo_todos_desenham():
    pygame.init()
    tela = pygame.Surface((LARGURA, ALTURA))
    for tipo in TIPOS:
        e = Inimigo(tipo, 1, x=300, y=150)
        e.desenhar(tela)


def test_inimigo_invisivel_nao_desenha():
    pygame.init()
    tela = pygame.Surface((LARGURA, ALTURA))
    e = Inimigo("assombra", 1, x=300, y=150)
    e.invisivel = 40
    e.desenhar(tela)  # nao deve levantar erro


# ---------------------------------------------------------------------------
# InimigoEspecial
# ---------------------------------------------------------------------------

def test_especial_todos_recebem_tiro():
    for tipo in ("acumulador", "esponja", "condutor", "mutante", "cristalino",
                 "evocador"):
        e = InimigoEspecial(tipo, 3, cenario_id=1)
        dano_vida = e.vida
        e.receber_tiro(1)
        assert e.carga > 0, tipo
        if tipo != "esponja":
            assert e.vida < dano_vida or e.carga >= e.carga_maxima


def test_especial_esponja_absorve_sem_dano():
    e = InimigoEspecial("esponja", 3, cenario_id=1)
    vida = e.vida
    for _ in range(10):
        assert e.receber_tiro(1) is False
    assert e.vida == vida
    assert e.carga > 0


def test_especial_carrega_ate_100():
    e = InimigoEspecial("acumulador", 3, cenario_id=1)
    while not e.carregado:
        e.receber_tiro(1)
    assert e.carregado is True


def test_especial_acoes_acumulador():
    e = InimigoEspecial("acumulador", 3, cenario_id=1)
    e.carga = e.carga_maxima
    e.carregado = True
    acoes = e.acoes_carregado()
    assert len(acoes["projeteis"]) == 8
    assert acoes["morrer"] is True
    assert acoes["mensagem"]
    assert e.acoes_carregado() == {}, "efeito dispara apenas uma vez"


def test_especial_acoes_esponja():
    e = InimigoEspecial("esponja", 3, cenario_id=1)
    e.carga = e.carga_maxima
    e.carregado = True
    acoes = e.acoes_carregado()
    assert len(acoes["inimigos"]) == 4
    assert acoes["morrer"] is True


def test_especial_acoes_condutor():
    e = InimigoEspecial("condutor", 3, cenario_id=1)
    e.carga = e.carga_maxima
    e.carregado = True
    acoes = e.acoes_carregado()
    assert len(acoes["projeteis"]) == 1
    assert acoes["projeteis"][0].teleguiado is True
    assert e.carga == 0 and e.carregado is False
    assert e.e_feito_ja_atirado() is False, "condutor recarrega"


def test_especial_acoes_mutante():
    e = InimigoEspecial("mutante", 3, cenario_id=1)
    e.carga = e.carga_maxima
    e.carregado = True
    vida = e.vida
    acoes = e.acoes_carregado()
    assert e.mini_boss is True
    assert e.vida == vida + 60
    assert e.raio == 36
    assert e.ataque == "leque"


def test_especial_acoes_cristalino():
    e = InimigoEspecial("cristalino", 3, cenario_id=1)
    e.carga = e.carga_maxima
    e.carregado = True
    e.acoes_carregado()
    assert e.campo_forca is True


def test_especial_acoes_evocador():
    e = InimigoEspecial("evocador", 3, cenario_id=1)
    e.carga = e.carga_maxima
    e.carregado = True
    acoes = e.acoes_carregado()
    assert len(acoes["inimigos"]) == 3
    assert e.carga == 0 and e.carregado is False


def test_especial_desenha_todos():
    pygame.init()
    tela = pygame.Surface((LARGURA, ALTURA))
    for tipo in ("acumulador", "esponja", "condutor", "mutante",
                 "cristalino", "evocador"):
        e = InimigoEspecial(tipo, 3, cenario_id=1)
        e.desenhar(tela)
        e.desenhar_barra_carga(tela)


# ---------------------------------------------------------------------------
# Ondas e sorteio
# ---------------------------------------------------------------------------

def test_composicao_onda():
    random.seed(1)
    tipos, qtd, xs = composicao_onda(1, ["scout", "soldado"])
    assert qtd == min(5 + 1 // 2, 22)
    assert tipos == ["scout", "soldado"]
    assert len(xs) == qtd
    # em niveis altos a quantidade cresce ate o teto
    _, qtd_alta, _ = composicao_onda(40, ["scout"])
    assert qtd_alta == 22


def test_sortear_inimigo_especial():
    random.seed(3)
    vistos = set()
    for _ in range(200):
        res = sortear_inimigo_especial(5, ["acumulador", "esponja"])
        if res:
            vistos.add(res)
    # com 12% de chance, em 200 sorteios ao menos um deve sair
    assert vistos
    assert sortear_inimigo_especial(5, []) is None


# ---------------------------------------------------------------------------
# Boss
# ---------------------------------------------------------------------------

def test_bosses_por_cenario():
    assert len(BOSSES_POR_CENARIO) == 6
    for cid, cfg in BOSSES_POR_CENARIO.items():
        for chave in ("nome", "cor", "raio", "vida", "pontos", "mov",
                      "ataques", "alvo_y", "efeito", "nivel"):
            assert chave in cfg, cid
        assert cfg["vida"] > 0


def test_boss_entra_em_cena():
    boss = Boss(5, Cenario(1))
    assert boss.entrando is True
    boss.atualizar(novo_jogador())
    assert boss.y == -boss.raio - 18
    boss.y = boss.alvo_y - 1
    boss.atualizar(novo_jogador())
    assert boss.entrando is False
    assert boss.y == boss.alvo_y


def test_boss_escala_vida_por_nivel():
    b5 = Boss(5, Cenario(1))
    b10 = Boss(10, Cenario(1))
    assert b10.vida > b5.vida


def test_boss_ataques_por_nome():
    jog = novo_jogador()
    for cid in range(1, 7):
        boss = Boss(BOSSES_POR_CENARIO[cid]["nivel"], Cenario(cid))
        for nome in boss.ataques:
            projs = boss._executar_ataque(nome, jog, 300, 150)
            assert projs, nome
            for p in projs:
                assert p.origem == "inimigo"


def test_boss_fases_de_ataque():
    boss = Boss(5, Cenario(1))
    boss.ataques = ["leque", "8dir", "mira"]
    boss.vida = boss.vida_max
    assert boss._ataques_por_fase() == ["leque"]
    boss.vida = boss.vida_max * 0.5
    assert boss._ataques_por_fase() == ["leque", "8dir"]
    boss.vida = boss.vida_max * 0.3
    assert boss._ataques_por_fase() == ["leque", "8dir", "mira"]


def test_boss_atacar_gera_projeteis():
    jog = novo_jogador()
    boss = Boss(5, Cenario(1))
    boss.entrando = False
    boss.timer_ataque = 0
    random.seed(5)
    projs = boss.atualizar(jog)
    assert projs


def test_boss_sofrer_dano_e_enraivecer():
    boss = Boss(5, Cenario(1))
    boss.entrando = False
    vida = boss.vida
    assert boss.sofrer_dano(1) is False
    assert boss.vida == vida - 1
    boss.vida = boss.vida_max * 0.3
    boss.atualizar(novo_jogador())
    assert boss.enraivecido is True


def test_boss_desenha_todos():
    pygame.init()
    tela = pygame.Surface((LARGURA, ALTURA))
    for cid in range(1, 7):
        boss = Boss(BOSSES_POR_CENARIO[cid]["nivel"], Cenario(cid))
        boss.entrando = False
        boss.y = boss.alvo_y
        boss.desenhar(tela)
        boss.enraivecido = True
        boss.timer_ataque = 30
        boss.desenhar(tela)


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