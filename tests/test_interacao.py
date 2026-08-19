"""Testes de interacao: eventos de teclado e mouse.

Dispara eventos reais (pygame.event) atraves de `Jogo._tratar_eventos` e
`MenuPrincipal.tratar_eventos` para verificar navegacao do menu, config,
loja, pausa, game over e encerramento.

Roda headless:

    python tests/test_interacao.py   # standalone
    pytest tests/test_interacao.py -v
"""

import os
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["SPACEFURY_DATA_DIR"] = tempfile.mkdtemp(prefix="spacefury_test_")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402
from unittest import mock  # noqa: E402

from game.config import ALTURA, LARGURA  # noqa: E402
from game.core import Jogo  # noqa: E402
from game.menu import ACOES_CONTROLE  # noqa: E402


def novo_jogo_estado(estado="MENU"):
    jogo = Jogo()
    jogo.estado = estado
    jogo.menu.alpha_entrada = 255
    return jogo


def novo_jogo_partida():
    jogo = Jogo()
    jogo._preparar_jogo()
    jogo.estado = "JOGANDO"
    jogo.inimigos = []
    jogo.boss = None
    jogo.projeteis = []
    jogo.powerups = []
    jogo.fila_onda = []
    return jogo


def tecla(key, unicode="", unicode_txt=None):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key,
                                         unicode=unicode))


def mouse(tipo, pos, button=1):
    pygame.event.post(pygame.event.Event(tipo, pos=pos, button=button))


def janela(jogo, x, y):
    """Converte ponto logico (900x700) para coordenadas da janela."""
    escala, off_x, off_y = jogo._transformacao_janela()
    return int(x * escala + off_x), int(y * escala + off_y)


def limpar_eventos():
    pygame.event.clear()


# ---------------------------------------------------------------------------
# Menu principal: teclado
# ---------------------------------------------------------------------------

def test_tecla_navega_opcoes_com_setas():
    jogo = novo_jogo_estado()
    menu = jogo.menu
    tecla(pygame.K_DOWN)
    assert jogo._tratar_eventos()
    assert menu.opcao_selecionada == 1
    tecla(pygame.K_DOWN)
    jogo._tratar_eventos()
    assert menu.opcao_selecionada == 2
    tecla(pygame.K_UP)
    jogo._tratar_eventos()
    assert menu.opcao_selecionada == 1
    # UP na primeira opcao da a volta (wrap)
    for _ in range(2):
        tecla(pygame.K_UP)
        jogo._tratar_eventos()
    assert menu.opcao_selecionada == len(menu.opcoes) - 1


def test_tecla_w_s_tambem_navega():
    jogo = novo_jogo_estado()
    tecla(pygame.K_s)
    jogo._tratar_eventos()
    assert jogo.menu.opcao_selecionada == 1
    tecla(pygame.K_w)
    jogo._tratar_eventos()
    assert jogo.menu.opcao_selecionada == 0


def test_tecla_escape_abre_dialogo_de_sair():
    jogo = novo_jogo_estado()
    tecla(pygame.K_ESCAPE)
    jogo._tratar_eventos()
    assert jogo.menu.dialogo is not None
    assert jogo.menu.dialogo.ativo


def test_tecla_enter_ativa_opcao_exit():
    jogo = novo_jogo_estado()
    jogo.menu.opcao_selecionada = len(jogo.menu.opcoes) - 1
    tecla(pygame.K_RETURN)
    jogo._tratar_eventos()
    assert jogo.menu.dialogo is not None
    assert jogo.menu.dialogo.ativo


def test_tecla_digita_nome_com_limite():
    jogo = novo_jogo_estado()
    jogo.nome_jogador = ""
    for _ in range(15):
        tecla(pygame.K_a, unicode="a")
        jogo._tratar_eventos()
    assert len(jogo.nome_jogador) == 12
    assert jogo.nome_jogador == "a" * 12


def test_tecla_especial_nao_digita_no_nome():
    jogo = novo_jogo_estado()
    jogo.nome_jogador = ""
    tecla(pygame.K_UP)
    jogo._tratar_eventos()
    tecla(pygame.K_SPACE, unicode=" ")
    jogo._tratar_eventos()
    assert jogo.nome_jogador == " "


# ---------------------------------------------------------------------------
# Telas do menu: teclado
# ---------------------------------------------------------------------------

def test_tecla_continuar_alterna_e_volta():
    jogo = novo_jogo_estado()
    menu = jogo.menu
    menu._abrir_continuar()
    tecla(pygame.K_DOWN)
    jogo._tratar_eventos()
    assert menu.continuar_selecao == 1
    tecla(pygame.K_UP)
    jogo._tratar_eventos()
    assert menu.continuar_selecao == 0
    tecla(pygame.K_BACKSPACE)
    jogo._tratar_eventos()
    assert menu.subestado == "MENU"


def test_tecla_recordes_volta_ao_menu():
    jogo = novo_jogo_estado()
    jogo.recordes = []
    jogo.menu._abrir_recordes()
    tecla(pygame.K_ESCAPE)
    jogo._tratar_eventos()
    assert jogo.menu.subestado == "MENU"


def test_tecla_loja_navega_grade():
    jogo = novo_jogo_estado()
    menu = jogo.menu
    menu._abrir_loja()
    n = len(jogo.loja.skins)
    tecla(pygame.K_RIGHT)
    jogo._tratar_eventos()
    assert menu.loja_selecao == 1
    tecla(pygame.K_LEFT)
    jogo._tratar_eventos()
    assert menu.loja_selecao == 0
    tecla(pygame.K_UP)
    jogo._tratar_eventos()
    assert menu.loja_selecao == 0  # nao desce abaixo de zero
    tecla(pygame.K_DOWN)
    jogo._tratar_eventos()
    assert menu.loja_selecao == min(4, n - 1)


def test_tecla_loja_enter_preview_e_equipa():
    jogo = novo_jogo_estado()
    menu = jogo.menu
    menu._abrir_loja()
    menu.loja_selecao = menu._indice_skin_atual()
    tecla(pygame.K_RETURN)
    jogo._tratar_eventos()
    assert menu.preview_skin is not None
    tecla(pygame.K_RETURN)
    jogo._tratar_eventos()
    assert menu.preview_skin is None


def test_tecla_loja_escape_volta():
    jogo = novo_jogo_estado()
    menu = jogo.menu
    menu._abrir_loja()
    tecla(pygame.K_ESCAPE)
    jogo._tratar_eventos()
    assert menu.subestado == "MENU"


def test_tecla_config_entra_em_controles_e_sai():
    jogo = novo_jogo_estado()
    menu = jogo.menu
    menu._abrir_config()
    for _ in range(5):  # posiciona em CONTROLES (selecao 5)
        tecla(pygame.K_DOWN)
        jogo._tratar_eventos()
    assert menu.config_selecao == 5
    tecla(pygame.K_RETURN)
    jogo._tratar_eventos()
    assert menu.config_submodo == "controles"
    tecla(pygame.K_ESCAPE)
    jogo._tratar_eventos()
    assert menu.config_submodo is None
    tecla(pygame.K_ESCAPE)
    jogo._tratar_eventos()
    assert menu.subestado == "MENU"


def test_tecla_remap_tecla_de_controle():
    jogo = novo_jogo_estado()
    menu = jogo.menu
    menu._abrir_config()
    menu.config_submodo = "controles"
    menu.controle_selecao = ACOES_CONTROLE.index("cima")
    tecla(pygame.K_RETURN)
    jogo._tratar_eventos()
    assert menu.remapando == "cima"
    tecla(pygame.K_f)
    jogo._tratar_eventos()
    assert menu.remapando is None
    assert jogo.config.controles["cima"] == pygame.K_f


def test_tecla_remap_esc_cancela():
    jogo = novo_jogo_estado()
    menu = jogo.menu
    menu._abrir_config()
    menu.config_submodo = "controles"
    tecla(pygame.K_RETURN)
    jogo._tratar_eventos()
    tecla(pygame.K_ESCAPE)
    jogo._tratar_eventos()
    assert menu.remapando is None


# ---------------------------------------------------------------------------
# Partida: teclado
# ---------------------------------------------------------------------------

def test_tecla_escape_pausa_e_despausa():
    jogo = novo_jogo_partida()
    tecla(pygame.K_ESCAPE)
    jogo._tratar_eventos()
    assert jogo.estado == "PAUSA"
    tecla(pygame.K_ESCAPE)
    jogo._tratar_eventos()
    assert jogo.estado == "JOGANDO"


def test_tecla_p_pausa():
    jogo = novo_jogo_partida()
    tecla(pygame.K_p)
    jogo._tratar_eventos()
    assert jogo.estado == "PAUSA"


def test_tecla_numero_seleciona_arma_desbloqueada():
    jogo = novo_jogo_partida()
    jogo.jogador.armas_desbloqueadas = [0, 1, 2]
    tecla(pygame.K_2)
    jogo._tratar_eventos()
    assert jogo.jogador.arma_atual == 1


def test_tecla_m_na_pausa_volta_ao_menu():
    jogo = novo_jogo_partida()
    tecla(pygame.K_ESCAPE)
    jogo._tratar_eventos()
    tecla(pygame.K_m)
    jogo._tratar_eventos()
    assert jogo.estado == "MENU"


def test_game_over_enter_recomeca():
    jogo = novo_jogo_partida()
    jogo.estado = "GAME_OVER"
    tecla(pygame.K_RETURN)
    jogo._tratar_eventos()
    assert jogo.estado == "PREPARANDO"


def test_game_over_escape_volta_ao_menu():
    jogo = novo_jogo_partida()
    jogo.estado = "GAME_OVER"
    tecla(pygame.K_ESCAPE)
    jogo._tratar_eventos()
    assert jogo.estado == "MENU"


def test_evento_quit_encerra_loop():
    jogo = novo_jogo_estado()
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    assert jogo._tratar_eventos() is False


# ---------------------------------------------------------------------------
# Mouse
# ---------------------------------------------------------------------------

def test_mouse_motion_atualiza_posicao_logica():
    jogo = novo_jogo_estado()
    x, y = janela(jogo, 200, 300)
    mouse(pygame.MOUSEMOTION, (x, y))
    jogo._tratar_eventos()
    mx, my = jogo.menu.mouse
    assert abs(mx - 200) <= 1
    assert abs(my - 300) <= 1


def test_clique_em_opcao_abre_continuar():
    jogo = novo_jogo_estado()
    menu = jogo.menu
    rect = menu.opcoes[0].get_rect(menu.x_opcoes, menu.fonte_opcao,
                                   menu.layout)
    mouse(pygame.MOUSEBUTTONDOWN, janela(jogo, rect.centerx, rect.centery))
    jogo._tratar_eventos()
    assert menu.subestado == "CONTINUAR"


def test_clique_em_botao_continuar_sem_save_avisa():
    jogo = novo_jogo_estado()
    menu = jogo.menu
    menu._abrir_continuar()
    botao = menu._botoes_continuar()[0]
    with mock.patch.object(jogo.progresso, "existe_save",
                           return_value=False):
        mouse(pygame.MOUSEBUTTONDOWN, janela(jogo, botao.rect.centerx,
                                             botao.rect.centery))
        jogo._tratar_eventos()
    assert menu.subestado == "CONTINUAR"
    assert any(n["tipo"] == "erro"
               for n in menu.notificacoes.notificacoes)


def test_clique_em_cartao_de_skin_seleciona():
    jogo = novo_jogo_estado()
    menu = jogo.menu
    menu._abrir_loja()
    rect = menu._rects_loja()[1]
    mouse(pygame.MOUSEBUTTONDOWN, janela(jogo, rect.centerx, rect.centery))
    jogo._tratar_eventos()
    assert menu.loja_selecao == 1


def test_clique_no_voltar_da_loja():
    jogo = novo_jogo_estado()
    menu = jogo.menu
    menu._abrir_loja()
    botao = menu._botoes_loja()["voltar"]
    mouse(pygame.MOUSEBUTTONDOWN, janela(jogo, botao.rect.centerx,
                                         botao.rect.centery))
    jogo._tratar_eventos()
    assert menu.subestado == "MENU"


def test_clique_fora_nao_muda_tela():
    jogo = novo_jogo_estado()
    mouse(pygame.MOUSEBUTTONDOWN, (0, 0))
    jogo._tratar_eventos()
    assert jogo.menu.subestado == "MENU"


def main():
    pygame.init()
    limpar_eventos()
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
        finally:
            limpar_eventos()
    print(f"\n{len(funcoes) - falhas}/{len(funcoes)} testes passaram")
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())