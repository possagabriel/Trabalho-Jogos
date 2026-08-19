"""Testes do menu principal (game.menu.MenuPrincipal).

Cobre construcao, navegacao entre telas, save, loja, dialogo de saida e
posicionamento logico do mouse.

Roda headless:

    python tests/test_menu.py   # standalone
    pytest tests/test_menu.py -v
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

from game.config import ALTURA, LARGURA  # noqa: E402
from game.core import Jogo  # noqa: E402
from game.menu import MenuPrincipal  # noqa: E402

ROTULOS_ESPERADOS = [
    "01 // CONTINUAR",
    "02 // NOVA MISSAO",
    "03 // HANGAR",
    "04 // RECORDS",
    "05 // SETTINGS",
    "06 // EXIT",
]


def novo_menu():
    jogo = Jogo()
    menu = jogo.menu
    menu.alpha_entrada = 255
    return jogo, menu


# ---------------------------------------------------------------------------
# Construcao e opcoes
# ---------------------------------------------------------------------------

def test_construcao_subestado_e_opcoes():
    _, menu = novo_menu()
    assert menu.subestado == "MENU"
    assert len(menu.opcoes) == 6
    assert [o.texto for o in menu.opcoes] == ROTULOS_ESPERADOS
    assert menu.x_opcoes <= menu.layout.largura


def test_construcao_carregou_fundo_do_menu():
    _, menu = novo_menu()
    assert menu.fundo.fundo_imagem is not None or menu.fundo.gradiente


def test_selecionar_muda_destaque():
    _, menu = novo_menu()
    menu._selecionar(2)
    assert menu.opcao_selecionada == 2
    assert menu.destaque.alvo == menu.opcoes[2].y


def test_selecionar_mesma_opcao_e_noop():
    _, menu = novo_menu()
    alvo = menu.destaque.alvo
    menu._selecionar(0)
    assert menu.opcao_selecionada == 0
    assert menu.destaque.alvo == alvo


# ---------------------------------------------------------------------------
# Navegacao entre telas
# ---------------------------------------------------------------------------

def test_abrir_continuar():
    _, menu = novo_menu()
    menu._abrir_continuar()
    assert menu.subestado == "CONTINUAR"
    assert menu.continuar_selecao == 0


def test_abrir_loja_seleciona_skin_atual():
    jogo, menu = novo_menu()
    jogo.loja.moedas = 9999
    jogo.loja.comprar_skin(2)
    jogo.loja.equipar_skin(2)
    menu._abrir_loja()
    assert menu.subestado == "LOJA"
    assert menu.loja_selecao == menu._indice_skin_atual() == 2


def test_abrir_recordes():
    jogo, menu = novo_menu()
    jogo.recordes = []
    menu._abrir_recordes()
    assert menu.subestado == "RECORDES"


def test_abrir_config():
    _, menu = novo_menu()
    menu._abrir_config()
    assert menu.subestado == "CONFIG"
    assert menu.config_submodo is None


def test_voltar_menu():
    _, menu = novo_menu()
    menu._abrir_config()
    menu.config_submodo = "controles"
    menu._voltar_menu()
    assert menu.subestado == "MENU"
    assert menu.config_submodo is None
    assert menu.remapando is None


# ---------------------------------------------------------------------------
# Missao nova
# ---------------------------------------------------------------------------

def test_novo_jogo_direto_inicia_transicao():
    jogo, menu = novo_menu()
    menu._novo_jogo_direto()
    assert menu.transicao_missao.em_andamento() is True


def test_acao_continuar_sem_save_avisa():
    jogo, menu = novo_menu()
    with mock.patch.object(jogo.progresso, "existe_save", return_value=False):
        menu._acao_continuar(0)
    assert menu.transicao_missao.em_andamento() is False
    assert any(n["tipo"] == "erro" for n in menu.notificacoes.notificacoes)


def test_acao_continuar_com_save_inicia_missao():
    jogo, menu = novo_menu()
    with mock.patch.object(jogo.progresso, "existe_save", return_value=True):
        menu._acao_continuar(0)
    assert menu.transicao_missao.em_andamento() is True


def test_acao_continuar_novo_jogo_mostra_dialogo():
    jogo, menu = novo_menu()
    menu._acao_continuar(1)
    assert menu.dialogo is not None
    assert menu.dialogo.ativo


def test_acao_continuar_voltar():
    _, menu = novo_menu()
    menu._acao_continuar(2)
    assert menu.subestado == "MENU"


def test_tem_save_reflete_progresso():
    jogo, menu = novo_menu()
    with mock.patch.object(jogo.progresso, "existe_save", return_value=True):
        assert menu._tem_save() is True
    with mock.patch.object(jogo.progresso, "existe_save", return_value=False):
        assert menu._tem_save() is False


# ---------------------------------------------------------------------------
# Sair
# ---------------------------------------------------------------------------

def test_sair_mostra_dialogo_de_confirmacao():
    _, menu = novo_menu()
    menu._sair()
    assert menu.dialogo is not None
    assert menu.dialogo.ativo


def test_confirmar_sair_encerra_jogo():
    jogo, menu = novo_menu()
    menu._confirmar_sair()
    assert jogo.rodando is False


# ---------------------------------------------------------------------------
# Loja
# ---------------------------------------------------------------------------

def test_indice_skin_atual():
    jogo, menu = novo_menu()
    jogo.loja.moedas = 9999
    jogo.loja.comprar_skin(3)
    jogo.loja.equipar_skin(3)
    assert menu._indice_skin_atual() == 3


def test_acao_loja_principal_preview_da_skin_equipada():
    jogo, menu = novo_menu()
    menu._abrir_loja()
    menu.loja_selecao = menu._indice_skin_atual()
    menu._acao_loja_principal()
    assert menu.preview_skin is not None
    assert menu.preview_skin.id == jogo.loja.skin_atual


def test_acao_botao_loja_voltar():
    _, menu = novo_menu()
    menu._abrir_loja()
    menu._acao_botao_loja("voltar")
    assert menu.subestado == "MENU"


# ---------------------------------------------------------------------------
# Posicao logica do mouse
# ---------------------------------------------------------------------------

def test_pos_logica_mantem_dentro_da_tela():
    jogo, menu = novo_menu()
    x, y = menu._pos_logica((450, 350))
    assert 0 <= x <= LARGURA
    assert 0 <= y <= ALTURA


# ---------------------------------------------------------------------------
# Atualizar e desenhar
# ---------------------------------------------------------------------------

def test_atualizar_menu_principal():
    _, menu = novo_menu()
    for _ in range(10):
        menu.atualizar()


def test_desenhar_todas_as_telas():
    jogo, menu = novo_menu()
    tela = pygame.Surface((LARGURA, ALTURA))
    jogo.recordes = []
    for subestado in ("MENU", "CONTINUAR", "LOJA", "RECORDES", "CONFIG"):
        menu.subestado = subestado
        menu.atualizar()
        menu.desenhar(tela)


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
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())