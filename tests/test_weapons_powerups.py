"""Testes de armas, projeteis e power-ups.

Cobre ``weapons`` (catálogo ARMARIA e classe Projetil: movimento, teleguiado,
reflexao, saída da tela e cores) e ``powerups`` (aplicação de cada efeito e
sorteio de tipo).

Roda headless:

    python tests/test_weapons_powerups.py   # standalone
    pytest tests/test_weapons_powerups.py -v
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

import pygame  # noqa: E402

from game.config import ALTURA, LARGURA  # noqa: E402
from game.powerups import PowerUp, sortear_tipo  # noqa: E402
from game.weapons import ARMARIA, CORES_ARCO_IRIS, Projetil  # noqa: E402


# ---------------------------------------------------------------------------
# ARMARIA
# ---------------------------------------------------------------------------

def test_armaria_estrutura():
    assert len(ARMARIA) == 9
    for arma in ARMARIA:
        for chave in ("nome", "nivel", "cor", "raio", "vel", "dano",
                      "cooldown", "tipo"):
            assert chave in arma, arma
        assert arma["raio"] > 0
        assert arma["dano"] > 0
        assert arma["cooldown"] > 0


def test_armaria_niveis_crescentes():
    niveis = [arma["nivel"] for arma in ARMARIA]
    assert niveis == sorted(niveis)
    assert niveis[0] == 1


# ---------------------------------------------------------------------------
# Projetil
# ---------------------------------------------------------------------------

def test_projetil_movimento():
    proj = Projetil(100, 100, 5, -3, 2, (255, 255, 255), 4)
    proj.atualizar()
    assert proj.x == 105
    assert proj.y == 97
    assert proj.tempo == 1


def test_projetil_ion_nao_movimenta():
    proj = Projetil(100, 100, 0, 0, 5, (200, 220, 255), 6, tipo="ion")
    proj.atualizar()
    assert proj.x == 100 and proj.y == 100
    assert proj.tempo == 1
    # rect do ion cobre a tela inteira em altura
    rect = proj.rect
    assert rect.top == 0 and rect.bottom == ALTURA
    assert rect.w == 14


def test_projetil_rect():
    proj = Projetil(50, 60, 0, -1, 1, (255, 255, 255), 10)
    r = proj.rect
    assert r.x == 40 and r.y == 50
    assert r.w == 20 and r.h == 20


def test_projetil_teleguiado():
    proj = Projetil(100, 100, 0, 0, 1, (255, 255, 255), 5, teleguiado=True)
    vel_antes = (proj.vel_x, proj.vel_y)
    proj.atualizar_teleguiado(200, 200)
    # a velocidade deve girar em direcao ao alvo
    proj_norm = math.hypot(proj.vel_x, proj.vel_y)
    assert proj_norm > 0
    assert proj.x > 100 and proj.y > 100
    assert (proj.vel_x, proj.vel_y) != vel_antes
    assert proj.tempo == 1


def test_projetil_refletir():
    proj = Projetil(100, 100, 5, 5, 1, (255, 255, 255), 4)
    proj.refletir()
    assert proj.vel_x == -5 and proj.vel_y == -5
    assert proj.origem == "inimigo"
    assert proj.refletor is True


def test_projetil_saiu_da_tela():
    proj = Projetil(-100, 100, 0, 0, 1, (255, 255, 255), 4)
    assert proj.saiu_da_tela() is True
    proj2 = Projetil(LARGURA + 100, 100, 0, 0, 1, (255, 255, 255), 4)
    assert proj2.saiu_da_tela() is True
    proj3 = Projetil(100, ALTURA + 100, 0, 0, 1, (255, 255, 255), 4)
    assert proj3.saiu_da_tela() is True
    proj4 = Projetil(100, 100, 0, 0, 1, (255, 255, 255), 4)
    assert proj4.saiu_da_tela() is False


def test_projetil_ion_saiu_apos_tempo():
    proj = Projetil(100, 100, 0, 0, 5, (255, 255, 255), 6, tipo="ion")
    assert proj.saiu_da_tela() is False
    for _ in range(15):
        proj.atualizar()
    assert proj.saiu_da_tela() is True


def test_projetil_cor_espiral_cicla():
    proj = Projetil(100, 100, 0, -1, 1, (255, 255, 255), 5, tipo="espiral")
    cores_vistas = set()
    for _ in range(len(CORES_ARCO_IRIS) * 6 + 3):
        proj.atualizar()
        cores_vistas.add(proj._cor_atual())
    assert len(cores_vistas) == len(CORES_ARCO_IRIS)


def test_projetil_desenha_sem_excecao():
    pygame.init()
    tela = pygame.Surface((LARGURA, ALTURA))
    for tipo in ("padrao", "laser", "plasma", "ion", "feixe", "gauss",
                 "nova", "espiral", "bomba"):
        proj = Projetil(200, 200, 0, -1, 1, (255, 255, 255), 6, tipo=tipo)
        proj.desenhar(tela)


# ---------------------------------------------------------------------------
# PowerUp
# ---------------------------------------------------------------------------

def test_powerup_movimento():
    pu = PowerUp("vida", 100, 100)
    pu.vel_y = 2
    pu.tempo = 0
    y_antes = pu.y
    pu.atualizar()
    assert pu.y == y_antes + 2
    assert pu.tempo == 1
    assert pu.rect.w == 28


def test_powerup_vida():
    from game.player import Jogador
    jog = Jogador()
    jog.vida = 3
    msg = PowerUp("vida", 0, 0).aplicar(jog)
    assert jog.vida == 4
    assert msg == "Vida +1"
    jog.vida = jog.max_vida
    msg_max = PowerUp("vida", 0, 0).aplicar(jog)
    assert jog.vida == jog.max_vida
    assert "maximo" in msg_max


def test_powerup_escudo():
    from game.player import Jogador
    jog = Jogador()
    assert jog.escudo is False
    msg = PowerUp("escudo", 0, 0).aplicar(jog)
    assert jog.escudo is True
    assert msg == "Escudo ativado!"


def test_powerup_velocidade():
    from game.player import Jogador
    jog = Jogador()
    vel = jog.velocidade
    PowerUp("velocidade", 0, 0).aplicar(jog)
    assert jog.velocidade == min(9, vel + 1)
    jog.velocidade = 9
    PowerUp("velocidade", 0, 0).aplicar(jog)
    assert jog.velocidade == 9


def test_powerup_moedas():
    from game.player import Jogador
    jog = Jogador()
    PowerUp("moedas", 0, 0).aplicar(jog)
    assert jog.moedas_jogo == 100


def test_powerup_arma():
    from game.player import Jogador
    jog = Jogador()
    jog.arma_atual = len(ARMARIA) - 1
    msg = PowerUp("arma", 0, 0).aplicar(jog)
    assert jog.moedas_jogo == 200
    assert "maxima" in msg

    jog2 = Jogador()
    assert jog2.arma_atual == 0
    PowerUp("arma", 0, 0).aplicar(jog2)
    assert jog2.arma_atual == 0
    assert 1 in jog2.armas_desbloqueadas


def test_powerup_skin():
    from game.player import Jogador
    jog = Jogador()

    def desbloquear(skin_id):
        return True
    msg = PowerUp("skin", 0, 0).aplicar(jog, desbloquear)
    assert msg == "VISUAL CRISTAL DESBLOQUEADO!"

    def ja_tem(skin_id):
        return False
    jog2 = Jogador()
    msg2 = PowerUp("skin", 0, 0).aplicar(jog2, ja_tem)
    assert jog2.moedas_jogo == 500
    assert "repetido" in msg2


def test_powerup_tipo_invalido():
    from game.player import Jogador
    assert PowerUp("nao-existe", 0, 0).aplicar(Jogador()) == ""


def test_sortear_tipo_sempre_valido():
    tipos_validos = {"escudo", "vida", "arma", "velocidade", "moedas"}
    for _ in range(100):
        assert sortear_tipo() in tipos_validos


def test_powerup_desenha():
    pygame.init()
    tela = pygame.Surface((LARGURA, ALTURA))
    for tipo in ("escudo", "vida", "arma", "velocidade", "moedas", "skin"):
        pu = PowerUp(tipo, 200, 200)
        pu.desenhar(tela)


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
