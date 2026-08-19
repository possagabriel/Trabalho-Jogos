"""Testes do jogador, combos e skins.

Cobre ``player``: catálogo de Skins, desenho, ``SistemaCombo`` (bonus por
faixa de combo) e ``Jogador`` (movimento com limites, tiro por tipo de arma,
seleção de arma, dano/escudo/invencibilidade).

Roda headless:

    python tests/test_player.py   # standalone
    pytest tests/test_player.py -v
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
from unittest import mock  # noqa: E402

import pygame  # noqa: E402

from game.config import ALTURA, LARGURA  # noqa: E402
from game.player import (  # noqa: E402
    Jogador, SKINS, Skin, SistemaCombo, _sprite_padrao,
    _sprite_padrao_rotacionada)
from game.weapons import ARMARIA  # noqa: E402


class _Teclas:
    """Superficie de teclado simulada que aceita constantes SDL grandes."""

    def __init__(self):
        self._pressionadas = set()

    def pressionar(self, *indices):
        self._pressionadas.update(indices)
        return self

    def __getitem__(self, indice):
        return 1 if indice in self._pressionadas else 0


def _teclas(*indices):
    t = _Teclas()
    t.pressionar(*indices)
    return t


def novo_jogador():
    return Jogador()


# ---------------------------------------------------------------------------
# Skin
# ---------------------------------------------------------------------------

def test_skins_catalogo_completo():
    ids = [skin["id"] for skin in SKINS]
    assert "padrao" in ids
    assert len(set(ids)) == len(ids)
    for cfg in SKINS:
        assert cfg["preco"] >= 0
        assert len(cfg["cor"]) == 3


def test_skin_desenha_todas_as_skins():
    pygame.init()
    tela = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    jog = novo_jogador()
    jog.x, jog.y = LARGURA // 2, ALTURA // 2
    for cfg in SKINS:
        skin = Skin(cfg)
        skin.desenhar(tela, jog)


def test_skin_padrao_usa_sprite():
    pygame.init()
    if _sprite_padrao() is None:
        return
    tela = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    jog = novo_jogador()
    jog.x, jog.y = LARGURA // 2, ALTURA // 2
    jog.tilt = 5
    Skin(SKINS[0]).desenhar(tela, jog)
    assert _sprite_padrao_rotacionada(5) is not None


def test_skin_padrao_fallback_sem_sprite():
    pygame.init()
    with mock.patch("game.player.carregar_imagem_alpha",
                    return_value=None), \
            mock.patch("game.player._SPRITE_PADRAO", None), \
            mock.patch("game.player._ROTACOES_SPRITE", {}):
        assert _sprite_padrao() is None
        assert _sprite_padrao_rotacionada(3) is None
        tela = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        jog = novo_jogador()
        Skin(SKINS[0]).desenhar(tela, jog)


# ---------------------------------------------------------------------------
# SistemaCombo
# ---------------------------------------------------------------------------

def test_combo_incrementa_e_maximo():
    combo = SistemaCombo()
    combo.adicionar_tiro()
    assert combo.combo_atual == 1
    combo.ultimo_tiro = pygame.time.get_ticks()
    combo.adicionar_tiro()
    assert combo.combo_atual == 2
    combo.adicionar_tiro()
    assert combo.combo_maximo == 3


def test_combo_reseta_sem_tempo():
    combo = SistemaCombo()
    combo.adicionar_tiro()
    combo.ultimo_tiro = -999999
    combo.adicionar_tiro()
    assert combo.combo_atual == 1


def test_combo_bonus_por_faixa():
    assert SistemaCombo().get_bonus() == 1.0
    c = SistemaCombo()
    c.combo_atual = 11
    assert c.get_bonus() == 1.5
    c.combo_atual = 21
    assert c.get_bonus() == 2.0


def test_combo_zerar():
    c = SistemaCombo()
    c.combo_atual = 5
    c.zerar()
    assert c.combo_atual == 0


# ---------------------------------------------------------------------------
# Jogador
# ---------------------------------------------------------------------------

def test_jogador_estado_inicial():
    jog = novo_jogador()
    assert jog.x == LARGURA // 2
    assert jog.y == ALTURA - 100
    assert jog.vida == 5
    assert jog.vivo is True
    assert jog.arma_atual == 0
    assert jog.armas_desbloqueadas == [0]
    assert jog.rect.center == (LARGURA // 2, ALTURA - 100)


def test_jogador_movimento_basico():
    jog = novo_jogador()
    jog.atualizar(_teclas(pygame.K_LEFT))
    assert jog.x < LARGURA // 2
    jog.atualizar(_teclas(pygame.K_UP))
    assert jog.y < ALTURA - 100


def test_jogador_movimento_diagonal_normalizado():
    jog = novo_jogador()
    x0, y0 = jog.x, jog.y
    jog.atualizar(_teclas(pygame.K_LEFT, pygame.K_UP))
    assert abs((x0 - jog.x) - jog.velocidade * 0.7071) < 0.01
    assert abs((y0 - jog.y) - jog.velocidade * 0.7071) < 0.01


def test_jogador_limites_tela():
    jog = novo_jogador()
    jog.x, jog.y = 0, 0
    jog.atualizar(_teclas(pygame.K_LEFT, pygame.K_UP))
    assert jog.x == 20
    assert jog.y == 40
    jog.x, jog.y = LARGURA, ALTURA
    jog.atualizar(_teclas(pygame.K_RIGHT, pygame.K_DOWN))
    assert jog.x == LARGURA - 20
    assert jog.y == ALTURA - 30


def test_jogador_controles_customizados():
    jog = novo_jogador()
    controles = {"cima": pygame.K_i, "baixo": pygame.K_k, "esquerda": pygame.K_j,
                 "direita": pygame.K_l}
    x0, y0 = jog.x, jog.y
    jog.atualizar(_teclas(pygame.K_j), controles)
    assert jog.x < x0
    jog.atualizar(_teclas(pygame.K_i), controles)
    assert jog.y < y0


def test_jogador_cooldown_diminui():
    jog = novo_jogador()
    jog.cooldown_tiro = 5
    jog.atualizar(_teclas())
    assert jog.cooldown_tiro == 4


def test_jogador_atira_todas_as_armas():
    for indice, arma in enumerate(ARMARIA):
        jog = novo_jogador()
        jog.armas_desbloqueadas = list(range(len(ARMARIA)))
        jog.arma_atual = indice
        projs = jog.atirar()
        assert projs, arma["tipo"]
        for proj in projs:
            assert proj.dano == arma["dano"]
        # cooldown aplicado apos disparo (exceto metralhadora em rajada)
        if arma["tipo"] != "metralhadora":
            assert jog.cooldown_tiro > 0
            # respeita o cooldown: segundo disparo imediato nao sai
            assert jog.atirar() == []


def test_jogador_metralhadora_rajada():
    jog = novo_jogador()
    jog.armas_desbloqueadas = list(range(len(ARMARIA)))
    jog.arma_atual = 4  # metralhadora (qtd 5)
    disparos = 0
    for _ in range(40):
        if jog.atirar():
            disparos += 1
        jog.atualizar(_teclas())  # decrementa cooldown_tiro
    assert disparos == 5, "rajada de 5 tiros, depois cooldown"


def test_jogador_morto_nao_atira():
    jog = novo_jogador()
    jog.vivo = False
    assert jog.atirar() == []


def test_jogador_selecionar_arma():
    jog = novo_jogador()
    jog.armas_desbloqueadas = [0, 2]
    jog.selecionar_arma(2)
    assert jog.arma_atual == 2
    jog.selecionar_arma(5)
    assert jog.arma_atual == 2


def test_jogador_dano_sem_escudo():
    jog = novo_jogador()
    vida = jog.vida
    assert jog.sofrer_dano() is True
    assert jog.vida == vida - 1
    assert jog.invencivel == 120
    assert jog.combo.combo_atual == 0


def test_jogador_escudo_absorve():
    jog = novo_jogador()
    jog.escudo = True
    assert jog.sofrer_dano() is True
    assert jog.escudo is False
    assert jog.vida == 5
    assert jog.invencivel == 90


def test_jogador_invencivel_ignora_dano():
    jog = novo_jogador()
    jog.invencivel = 10
    assert jog.sofrer_dano() is False
    assert jog.vida == 5


def test_jogador_morre_com_vida_zero():
    jog = novo_jogador()
    jog.vida = 1
    jog.sofrer_dano()
    assert jog.vida == 0
    assert jog.vivo is False


def test_jogador_desenha_com_escudo():
    pygame.init()
    tela = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    jog = novo_jogador()
    jog.escudo = True
    jog.desenhar(tela)
    jog.invencivel = 4
    jog.desenhar(tela)


def test_jogador_equipar_skin():
    jog = novo_jogador()
    skin = Skin(SKINS[3])
    jog.equipar_skin(skin)
    assert jog.skin is skin


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