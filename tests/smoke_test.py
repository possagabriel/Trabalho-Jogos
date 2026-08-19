"""Smoke tests headless do VOID//SHIFT.

Roda sem janela (drivers dummy do SDL) para verificar que o jogo inicia,
executa o loop de combate e desenha cenas sem excecoes. Uso:

    python tests/smoke_test.py

Para rodar via pytest:

    pytest tests/smoke_test.py -v

Nota: as variaveis SDL_* e SPACEFURY_DATA_DIR sao definidas ANTES de
importar pygame para que video/mixer usem drivers dummy e os JSON de
progresso sejam gravados num diretorio temporario (nao no data/ real).
"""

import os
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SPACEFURY_DATA_DIR", tempfile.mkdtemp(prefix="spacefury_test_"))

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import random  # noqa: E402

from game.core import Jogo  # noqa: E402
from game.enemies import Inimigo  # noqa: E402
from game.scenarios import Cenario, cenario_do_nivel  # noqa: E402
from game.weapons import Projetil  # noqa: E402

MAX_FRAMES = 6000


def novo_jogo():
    jogo = Jogo()
    jogo._preparar_jogo()
    return jogo


def test_jogo_inicia():
    jogo = novo_jogo()
    assert jogo.estado == "PREPARANDO"
    assert jogo.tela.get_size() == (900, 700)
    jogo._desenhar()


def test_loop_combate_avanca_niveis():
    jogo = novo_jogo()
    random.seed(7)
    frames = 0
    while jogo.estado in ("PREPARANDO", "JOGANDO") and frames < MAX_FRAMES:
        jogo._atualizar()
        if jogo.estado == "JOGANDO":
            projs = jogo.jogador.atirar()
            if projs:
                jogo.projeteis.extend(projs)
            if not jogo.fila_onda and not jogo.inimigos and not jogo.boss:
                jogo.fila_onda = ["scout"] * 4
        jogo._desenhar()
        frames += 1
    assert frames > 60, "o loop de combate travou cedo demais"
    assert jogo.jogador.nivel >= 2, "deveria ter avancado de nivel"
    assert jogo.inimigos_abates > 0, "deveria ter abatido inimigos"


def test_cenario_do_nivel():
    assert cenario_do_nivel(1) == 1
    assert cenario_do_nivel(5) == 1
    assert cenario_do_nivel(6) == 2
    assert cenario_do_nivel(30) == 6
    assert cenario_do_nivel(999) == 6


def test_cenarios_desenham():
    jogo = novo_jogo()
    for cenario_id in range(1, 7):
        jogo.cenario = Cenario(cenario_id)
        for _ in range(30):
            jogo.cenario.atualizar()
            jogo.cenario.desenhar(jogo.tela)
    jogo._desenhar()


def test_ion_atravessa_inimigos_na_coluna():
    jogo = novo_jogo()
    jogo.jogador.arma_atual = 6  # canhao de ions
    jogo.inimigos = [Inimigo("scout", 1, x=450, y=150),
                     Inimigo("scout", 1, x=450, y=250)]
    ion = Projetil(450, 300, 0, 0, 5, (200, 220, 255), 6, tipo="ion")
    jogo.projeteis = [ion]
    jogo._atualizar_projeteis()
    assert not jogo.inimigos, "o ion deveria atingir todos os inimigos da coluna"
    assert ion in jogo.projeteis, "o ion nao deveria ser removido ao acertar"


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