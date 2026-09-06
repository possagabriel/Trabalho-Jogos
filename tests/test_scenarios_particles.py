"""Testes de cenários, estrelas, partículas e mensagens flutuantes.

Cobre ``scenarios`` (construção e desenho dos 6 cenários, estrelas com
wrap-around, mapeamento nível→cenário e ajuste em cover da imagem de fundo)
e ``particles`` (efeitos, ciclo de vida das partículas e mensagens).

Roda headless:

    python tests/test_scenarios_particles.py   # standalone
    pytest tests/test_scenarios_particles.py -v
"""

import os
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["INCARNATE_DATA_DIR"] = tempfile.mkdtemp(prefix="incarnate_test_")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import random  # noqa: E402

import pygame  # noqa: E402

from game.config import ALTURA, LARGURA  # noqa: E402
from game.particles import (  # noqa: E402
    MensagemFlutuante, Particula, SistemaParticulas)
from game.scenarios import CENARIOS, Cenario, Estrela, _ajustar_cover, \
    _superficie_alpha, cenario_do_nivel  # noqa: E402


# ---------------------------------------------------------------------------
# Cenario
# ---------------------------------------------------------------------------

def test_cenarios_configuracao():
    assert len(CENARIOS) == 6
    for cfg in CENARIOS:
        assert cfg["id"] >= 1
        assert cfg["nome"]
        assert cfg["inimigos"]
        assert cfg["especiais"]


def test_cenario_construtor():
    for cid in range(1, 7):
        c = Cenario(cid)
        assert c.id == cid
        assert c.nome == CENARIOS[cid - 1]["nome"]
        assert c.cor_transicao == CENARIOS[cid - 1]["cor_transicao"]
        assert c.efeito == CENARIOS[cid - 1]["efeito"]
        assert c.estrelas


def test_cenario_atualiza_e_desenha_todos():
    pygame.init()
    tela = pygame.Surface((LARGURA, ALTURA))
    for cid in range(1, 7):
        c = Cenario(cid)
        for _ in range(30):
            c.atualizar()
            c.desenhar(tela)


def test_cenario_desenha_efeitos_distorcao_e_raios():
    pygame.init()
    tela = pygame.Surface((LARGURA, ALTURA))
    for cid in (5, 6):  # NULL SPACE (distorcao) e DIVINE PLANE (raios)
        c = Cenario(cid)
        for _ in range(60):
            c.atualizar()
            c.desenhar(tela)


def test_estrela_wrap_around():
    random.seed(1)
    e = Estrela(100, ALTURA + 11, 2, 2.0, (255, 255, 255), "circulo")
    e.atualizar()
    assert e.y == -10
    assert 0 <= e.x <= LARGURA


def test_estrela_desenha_formas():
    pygame.init()
    tela = pygame.Surface((LARGURA, ALTURA))
    for forma in ("circulo", "chama", "bolha", "diamante", "espiral",
                  "cruz"):
        e = Estrela(200, 200, 3, 1.0, (255, 255, 255), forma)
        e.desenhar(tela)


def test_cenario_do_nivel():
    assert cenario_do_nivel(1) == 1
    assert cenario_do_nivel(5) == 1
    assert cenario_do_nivel(6) == 2
    assert cenario_do_nivel(10) == 2
    assert cenario_do_nivel(11) == 3
    assert cenario_do_nivel(25) == 5
    assert cenario_do_nivel(30) == 6
    assert cenario_do_nivel(999) == 6


def test_ajustar_cover():
    pygame.init()
    img = pygame.Surface((100, 50))
    img.fill((255, 0, 0))
    out = _ajustar_cover(img, 900, 700)
    assert out.get_size() == (900, 700)
    # proporcao preservada: 100x50 preenche a altura
    pequena = _ajustar_cover(img, 100, 100)
    assert pequena.get_size() == (100, 100)


def test_superficie_alpha_nao_expoe_cache_mutavel():
    pygame.init()
    primeira = _superficie_alpha(20, (255, 0, 0))
    segunda = _superficie_alpha(20, (255, 0, 0))
    primeira.set_alpha(10)
    assert primeira is not segunda
    assert segunda.get_alpha() != 10


# ---------------------------------------------------------------------------
# Particulas
# ---------------------------------------------------------------------------

def test_particula_atualizar_com_gravidade():
    p = Particula(0, 0, (255, 255, 255), (2, 0), 3, 20, gravidade=0.5,
                  arrasto=1.0)
    p.atualizar()
    assert p.x == 2
    assert p.y == 0.5
    assert p.vida == 19


def test_particula_arrasto():
    p = Particula(0, 0, (255, 255, 255), (10, 10), 3, 20, arrasto=0.5)
    p.atualizar()
    assert p.vx == 5.0 and p.vy == 5.0


def test_particula_morre_apos_vida():
    p = Particula(0, 0, (255, 255, 255), (0, 0), 1, 1)
    p.atualizar()
    assert p.vida == 0


def test_explosao_gera_quantidade():
    sp = SistemaParticulas()
    sp.explosao(100, 100, (255, 0, 0), qtd=25)
    assert len(sp.particulas) == 25


def test_todos_efeitos_geram_particulas():
    sp = SistemaParticulas()
    sp.explosao(100, 100, (255, 0, 0), 5)
    sp.espiral(100, 100, (255, 0, 0), 10)
    sp.estrela(100, 100, (255, 0, 0), 10)
    sp.pulsacao(100, 100, (255, 0, 0), 10)
    sp.mega(100, 100)
    sp.explosao_dupla(100, 100)
    sp.faiscas(100, 100, (255, 0, 0), 6)
    sp.rastro(100, 100, (255, 0, 0))
    sp.chamas(100, 100, (255, 120, 40), 2)
    sp.bolhas(100, 100, (255, 0, 0))
    sp.cristais(100, 100, (255, 0, 0))
    sp.relampago(100, 100, (255, 255, 0))
    sp.buraco_negro(100, 100)
    sp.salto_dimensional(100, 100, (255, 0, 0))
    sp.espiral_revelacao(100, 100, (255, 0, 0))
    assert len(sp.particulas) > 30


def test_atualizar_remove_mortas():
    sp = SistemaParticulas()
    sp.explosao(100, 100, (255, 0, 0), 5)
    for _ in range(100):
        sp.atualizar()
    assert all(p.vida > 0 for p in sp.particulas)


def test_atualizar_limita_particulas_ativas_em_picos():
    sp = SistemaParticulas()
    sp.particulas = [Particula(0, 0, (255, 0, 0), (0, 0), 1, 10)
                     for _ in range(700)]
    sp.atualizar()
    assert len(sp.particulas) == 480


def test_particulas_desenham():
    pygame.init()
    tela = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    sp = SistemaParticulas()
    sp.explosao(200, 200, (255, 0, 0), 10)
    sp.desenhar(tela)
    sp.limpar()
    assert not sp.particulas


def test_particulas_limitam_o_orcamento_visual_em_explosoes_grandes():
    class ParticulaContada:
        def __init__(self):
            self.desenhos = 0

        def desenhar(self, tela):
            self.desenhos += 1

    pygame.init()
    particula = ParticulaContada()
    sp = SistemaParticulas()
    sp.particulas = [particula] * 800
    sp.desenhar(pygame.Surface((LARGURA, ALTURA)))
    assert 0 < particula.desenhos <= 320


# ---------------------------------------------------------------------------
# MensagemFlutuante
# ---------------------------------------------------------------------------

def test_mensagem_ciclo_de_vida():
    pygame.init()
    m = MensagemFlutuante("OLA", 100, 100, tempo=5)
    for _ in range(4):
        assert m.viva is True
        m.atualizar()
    m.atualizar()
    assert m.viva is False


def test_mensagem_desenha():
    pygame.init()
    tela = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    m = MensagemFlutuante("PONTOS +100", 200, 200)
    m.desenhar(tela)
    m.tempo = 0
    m.desenhar(tela)


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
