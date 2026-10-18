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
os.environ["INCARNATE_DATA_DIR"] = tempfile.mkdtemp(prefix="incarnate_test_")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402
import pytest  # noqa: E402

from game import phase_select  # noqa: E402
from game.config import ALTURA, LARGURA  # noqa: E402
from game.core import Jogo  # noqa: E402
from game.layout import Layout  # noqa: E402
from game.menu import MenuPrincipal  # noqa: E402
from game.phase_select import PhaseStatus  # noqa: E402
from game.theme import tema_atual  # noqa: E402
from src.infrastructure.graphics.comic_theme import usar_visual  # noqa: E402

ROTULOS_ESPERADOS = [
    "01 // CONTINUAR",
    "02 // LOBBY",
    "03 // HANGAR",
    "04 // RECORDES",
    "05 // CONFIGURAÇÕES",
    "06 // ARQUIVO DE MEMÓRIAS",
    "07 // PERFIS",
    "08 // SAIR",
]


def novo_menu():
    jogo = Jogo()
    perfis = jogo.profile_service.list_profiles()
    perfil = perfis[0] if perfis else jogo.profile_service.create("Jogador")
    jogo.ativar_perfil(perfil.id)
    menu = jogo.menu
    menu.alpha_entrada = 255
    return jogo, menu


# ---------------------------------------------------------------------------
# Construcao e opcoes
# ---------------------------------------------------------------------------

def test_construcao_subestado_e_opcoes():
    _, menu = novo_menu()
    assert menu.subestado == "MENU"
    assert len(menu.opcoes) == 8
    assert [o.texto for o in menu.opcoes] == ROTULOS_ESPERADOS
    assert menu.x_opcoes <= menu.layout.largura


def test_opcoes_principais_tem_tamanho_uniforme_e_nao_usam_indicador_antigo():
    """Todos os painéis compartilham a área; seleção não cria bloco extra."""
    _, menu = novo_menu()
    rects = [opcao.get_rect(menu.x_opcoes, menu.fonte_opcao, menu.layout)
             for opcao in menu.opcoes]
    assert {rect.size for rect in rects} == {rects[0].size}
    assert all(b.top - a.bottom > 0 for a, b in zip(rects, rects[1:]))
    assert menu.destaque.y == menu.opcoes[0].y  # estado mantido para compatibilidade


def test_opcao_selecionada_no_estilo_original_tem_fundo_visivel():
    """O fundo de selecao ocupa a area clicavel e nao aparece nas demais opcoes."""
    jogo, menu = novo_menu()
    opcao = menu.opcoes[0]
    rect = opcao.get_rect(menu.x_opcoes, menu.fonte_opcao, menu.layout)
    amostra = (rect.x + menu.layout.px(12), rect.centery)
    sem_selecao = pygame.Surface(jogo.tela.get_size(), pygame.SRCALPHA)
    com_selecao = pygame.Surface(jogo.tela.get_size(), pygame.SRCALPHA)

    with usar_visual({"estilo_visual": "ORIGINAL"}):
        tema = tema_atual(jogo.config["tema"])
        for tela, selecionado in ((sem_selecao, False), (com_selecao, True)):
            opcao.desenhar(tela, menu.fonte_opcao, menu.fonte_opcao_sel, tema,
                           menu.x_opcoes, selecionado, 0, 255, menu.layout)

    assert sem_selecao.get_at(amostra).a == 0
    assert com_selecao.get_at(amostra).a > 0


def test_menu_widescreen_separa_titulo_da_coluna_de_opcoes():
    _, menu = novo_menu()

    limite_titulo = menu.layout.px(520)
    inicio_opcoes = menu.x_opcoes - menu.layout.px(46)

    assert menu.layout.largura == 1280
    assert inicio_opcoes > limite_titulo


def test_submenus_usam_a_mesma_fileira_de_acoes():
    _, menu = novo_menu()
    grupos = [
        menu._botoes_continuar(),
        list(menu._botoes_loja().values()),
        [menu._botao_voltar()],
        menu._botoes_rodape(["SALVAR", "VOLTAR"]),
    ]

    alturas = {botao.rect.height for grupo in grupos for botao in grupo}
    posicoes_y = {botao.rect.y for grupo in grupos for botao in grupo}

    assert len(alturas) == 1
    assert len(posicoes_y) == 1


def test_painel_do_hangar_contem_todos_os_cards():
    _, menu = novo_menu()
    painel = menu._painel_loja()

    assert all(painel.contains(rect) for rect in menu._rects_loja())


def test_paineis_amplos_dos_submenus_compartilham_alinhamento():
    _, menu = novo_menu()

    assert menu._painel_loja().top == menu._painel_recordes().top
    assert menu._painel_loja().height == menu._painel_recordes().height


def test_construcao_carregou_fundo_do_menu():
    _, menu = novo_menu()
    assert menu.fundo.fundo_imagem is not None or menu.fundo.gradiente


def test_escolher_resolucao_preserva_tela_cheia_ativa():
    jogo, menu = novo_menu()
    jogo.config["tela_cheia"] = True
    jogo._aplicar_modo_video = mock.Mock()

    menu._aplicar_resolucao(1)

    assert jogo.config["resolucao"] == "1024x768"
    assert jogo.config["tela_cheia"] is True
    jogo._aplicar_modo_video.assert_called_once()


def test_ciclar_resolucao_preserva_tela_cheia_ativa():
    jogo, menu = novo_menu()
    jogo.config["tela_cheia"] = True
    jogo._aplicar_modo_video = mock.Mock()

    menu._ciclar_resolucao()

    assert jogo.config["tela_cheia"] is True
    jogo._aplicar_modo_video.assert_called_once()


def test_tela_cheia_reverte_se_a_resolucao_nao_for_suportada():
    jogo, menu = novo_menu()
    jogo.config.salvar = mock.Mock()
    jogo._aplicar_modo_video = mock.Mock(side_effect=[pygame.error(), None])

    menu._toggle_tela_cheia()

    assert jogo.config["tela_cheia"] is False
    assert jogo._aplicar_modo_video.call_count == 2
    jogo.config.salvar.assert_not_called()


def test_resolucao_so_e_salva_apos_confirmacao():
    jogo, menu = novo_menu()
    anterior = jogo.config["resolucao"]
    jogo._aplicar_modo_video = mock.Mock()
    jogo.config.salvar = mock.Mock()

    menu._aplicar_resolucao(1)

    assert menu._resolucao_pendente["resolucao"] == anterior
    assert jogo.config["resolucao"] == "1024x768"
    jogo.config.salvar.assert_not_called()
    menu.desenhar(pygame.Surface((LARGURA, ALTURA)))

    menu._confirmar_resolucao()

    assert menu._resolucao_pendente is None
    jogo.config.salvar.assert_called_once()


def test_resolucao_reverte_quando_o_tempo_expira():
    jogo, menu = novo_menu()
    anterior = jogo.config["resolucao"]
    jogo._aplicar_modo_video = mock.Mock()

    menu._aplicar_resolucao(1)
    menu._prazo_confirmacao_resolucao = 0
    menu.atualizar()

    assert menu._resolucao_pendente is None
    assert jogo.config["resolucao"] == anterior
    assert jogo._aplicar_modo_video.call_count == 2


def test_confirmacao_de_resolucao_aceita_enter_e_escape():
    jogo, menu = novo_menu()
    jogo._aplicar_modo_video = mock.Mock()
    jogo.config.salvar = mock.Mock()

    menu._aplicar_resolucao(1)
    menu.tratar_eventos(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
    assert menu._resolucao_pendente is None
    jogo.config.salvar.assert_called_once()

    resolucao_confirmada = jogo.config["resolucao"]
    menu._aplicar_resolucao(2)
    menu.tratar_eventos(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))
    assert menu._resolucao_pendente is None
    assert jogo.config["resolucao"] == resolucao_confirmada


def test_teste_de_resolucao_nao_emite_som():
    jogo, menu = novo_menu()
    jogo._aplicar_modo_video = mock.Mock()
    menu._som = mock.Mock()

    menu._aplicar_resolucao(1)
    menu._confirmar_resolucao()
    menu._aplicar_resolucao(2)
    menu._reverter_resolucao()

    menu._som.assert_not_called()


def test_qualidade_visual_e_monitor_de_fps_sao_configuraveis():
    jogo, menu = novo_menu()
    jogo._aplicar_qualidade_grafica = mock.Mock()
    jogo.config.salvar = mock.Mock()

    menu._ciclar_qualidade_grafica()
    menu._toggle_monitor_desempenho()

    assert jogo.config["qualidade_grafica"] == "EQUILIBRADA"
    assert jogo.config["mostrar_desempenho"] is True
    jogo._aplicar_qualidade_grafica.assert_called_once()
    assert jogo.config.salvar.call_count == 2


def test_logo_principal_e_gerado_por_tipografia():
    _, menu = novo_menu()
    tema = menu.jogo.config["tema"]
    from game.theme import tema_atual
    surfaces = menu._titulo_surfaces(tema_atual(tema))
    assert surfaces["incarnate"].get_width() > 0
    assert surfaces["incarnate_eco"].get_width() > 0
    assert not hasattr(menu, "_logo_menu")


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

def test_lobby_abre_selecao_de_fases_sem_reiniciar_campanha():
    jogo, menu = novo_menu()
    # A suite compartilha o diretorio temporario de dados: declare o estado
    # inicial que este caso cobre, em vez de depender da ordem dos testes.
    jogo.progresso.jogador["progresso_campanha"].update(
        {"fases_concluidas": [], "fase_atual": "lealdade", "nivel_atual": 1})
    menu._abrir_lobby()
    assert menu.subestado == "FASES"
    assert menu.phase_screen.nova_campanha_pendente is False
    assert menu.phase_screen.statuses["lealdade"] == PhaseStatus.AVAILABLE
    assert menu.phase_screen.statuses["funcao"] == PhaseStatus.LOCKED


def test_novo_jogo_direto_abre_selecao_de_fases():
    _, menu = novo_menu()
    menu._novo_jogo_direto()
    assert menu.subestado == "FASES"
    assert menu.phase_screen.nova_campanha_pendente is True


def test_lobby_retomar_fase_e_nivel_salvos():
    jogo, menu = novo_menu()
    campanha = jogo.progresso.jogador["progresso_campanha"]
    campanha.update({"fases_concluidas": [1, 2], "fase_atual": "identidade",
                     "nivel_atual": 13})
    menu._abrir_lobby()
    assert menu.phase_screen.selected == 2
    assert menu.phase_screen.confirm() is True
    assert jogo.jogador.nivel == 13
    assert campanha["fase_atual"] == "identidade"


def test_lobby_usa_carteira_viva_e_sincroniza_compra():
    jogo, menu = novo_menu()
    tela = menu.phase_screen
    jogo.progresso.jogador["moedas"] = 25
    jogo.loja.moedas = 600

    assert tela._saldo_moedas() == 600
    with mock.patch.object(jogo.progresso, "salvar_arquivo", return_value=True):
        assert tela._buy_upgrade(0) is True

    assert jogo.loja.moedas == 300
    assert jogo.progresso.jogador["moedas"] == 300
    assert jogo.progresso.jogador["melhorias"]["blindagem"] == 1


def test_lobby_desfaz_compra_quando_save_falha():
    jogo, menu = novo_menu()
    tela = menu.phase_screen
    jogo.loja.moedas = 500
    jogo.progresso.sincronizar_loja(jogo.loja)

    with mock.patch.object(jogo.progresso, "salvar_arquivo", return_value=False):
        assert tela._buy_upgrade(1) is False

    assert jogo.loja.moedas == 500
    assert jogo.progresso.jogador["moedas"] == 500
    assert jogo.progresso.jogador["melhorias"]["motor"] == 0


def test_melhorias_compradas_no_lobby_afetam_nova_partida():
    jogo, _ = novo_menu()
    jogo.progresso.jogador["melhorias"] = {"blindagem": 2, "motor": 3}

    jogo.progressao_controller.novo_jogo("Piloto", zerar_estado=False)

    assert jogo.jogador.vida == 7
    assert jogo.jogador.max_vida == 10
    assert jogo.jogador.melhorias["blindagem"] == 2
    assert jogo.jogador.melhorias["motor"] == 3
    assert jogo.jogador.multiplicador_velocidade == pytest.approx(1.3)


def test_lobby_comic_usa_fundo_lettering_e_paineis_de_tinta():
    jogo, menu = novo_menu()
    tela = pygame.Surface((LARGURA, ALTURA))
    lobby = menu.phase_screen

    with usar_visual({"estilo_visual": "COMIC", "qualidade_comic": "MEDIA"}):
        with mock.patch.object(
            phase_select, "desenhar_fundo", wraps=phase_select.desenhar_fundo,
        ) as fundo, mock.patch.object(
            phase_select, "painel_tinta", wraps=phase_select.painel_tinta,
        ) as paineis:
            lobby.draw(tela)

    fundo.assert_called_once()
    assert paineis.call_count >= len(lobby.phases) + 2


def test_cancelar_novo_jogo_preserva_campanha():
    jogo, menu = novo_menu()
    campanha = jogo.progresso.jogador["progresso_campanha"]
    campanha["fases_concluidas"] = [1, 2]
    menu._novo_jogo_direto()
    menu._voltar_menu()
    assert campanha["fases_concluidas"] == [1, 2]
    assert menu.phase_screen.nova_campanha_pendente is False


def test_confirmar_novo_jogo_reseta_campanha():
    jogo, menu = novo_menu()
    jogo.progresso.jogador["progresso_campanha"]["fases_concluidas"] = [1, 2]
    menu._novo_jogo_direto()
    with mock.patch.object(jogo, "_preparar_jogo"):
        assert menu.phase_screen.confirm() is True
    campanha = jogo.progresso.jogador["progresso_campanha"]
    assert campanha["fases_concluidas"] == []
    assert menu.phase_screen.nova_campanha_pendente is False


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


def test_pos_mouse_usa_a_mesma_transformacao_do_gameplay():
    jogo, menu = novo_menu()
    rect = menu.opcoes[0].get_rect(menu.x_opcoes, menu.fonte_opcao,
                                  menu.layout)
    escala, off_x, off_y = jogo._transformacao_janela()
    pos_janela = (rect.centerx * escala + off_x,
                  rect.centery * escala + off_y)
    pos_logica = menu._pos_logica(pos_janela)
    assert abs(pos_logica[0] - rect.centerx) <= 1
    assert abs(pos_logica[1] - rect.centery) <= 1
    assert rect.collidepoint(pos_logica)


@pytest.mark.parametrize("modo", ["AJUSTAR", "PREENCHE"])
@pytest.mark.parametrize("tamanho", [
    (900, 700), (1280, 720), (1920, 1080), (2560, 1080),
])
def test_mouse_mira_e_transformacao_preservam_16_por_9(modo, tamanho):
    """A conversão de mouse é a inversa da mesma escala uniforme da cena."""
    jogo, menu = novo_menu()
    jogo.janela = pygame.Surface(tamanho)
    jogo.config["aspecto"] = modo
    escala, off_x, off_y = jogo._transformacao_janela()

    assert escala == pytest.approx(min(tamanho[0] / LARGURA,
                                       tamanho[1] / ALTURA))
    largura_destino = LARGURA * escala
    altura_destino = ALTURA * escala
    assert largura_destino / altura_destino == pytest.approx(16 / 9)

    ponto_logico = (LARGURA * 0.73, ALTURA * 0.61)
    ponto_janela = (ponto_logico[0] * escala + off_x,
                    ponto_logico[1] * escala + off_y)
    ponto_revertido = menu._pos_logica(ponto_janela)
    assert ponto_revertido == pytest.approx(ponto_logico, abs=1)


@pytest.mark.parametrize("tamanho", [
    (900, 700), (1280, 720), (1920, 1080), (2560, 1080),
])
def test_preenche_estende_fundo_sem_ampliar_cena_jogavel(tamanho):
    jogo = Jogo()
    jogo.janela = pygame.Surface(tamanho)
    jogo.config["aspecto"] = "PREENCHE"
    jogo.tela.fill((220, 30, 40))
    jogo.tela_ui.fill((0, 0, 0, 0))
    jogo._obter_fundo_preenche = mock.Mock(
        return_value=pygame.Surface(tamanho))
    jogo._obter_fundo_preenche.return_value.fill((20, 170, 60))

    jogo._apresentar()

    escala, off_x, off_y = jogo._transformacao_janela()
    caixa = pygame.Rect(round(off_x), round(off_y),
                        round(LARGURA * escala), round(ALTURA * escala))
    centro = jogo.janela.get_at(caixa.center)[:3]
    assert all(abs(valor - esperado) <= 4
               for valor, esperado in zip(centro, (220, 30, 40)))
    borda = (0, tamanho[1] // 2)
    if not caixa.collidepoint(borda):
        assert jogo.janela.get_at(borda)[:3] == (20, 170, 60)


def test_selecao_fases_responsiva_e_cacheada():
    jogo, _ = novo_menu()
    layout = Layout(1920, 1080)
    menu = MenuPrincipal(jogo, layout=layout)
    tela = pygame.Surface((layout.largura, layout.altura))
    menu.phase_screen.draw(tela)
    limite = tela.get_rect()
    assert all(limite.contains(menu.phase_screen.card_rect(i))
               for i in range(len(menu.phase_screen.phases)))
    assert limite.collidepoint(menu.phase_screen.ship_position())
    thumbs = dict(menu.phase_screen._thumbs_escaladas)
    menu.phase_screen.draw(tela)
    assert menu.phase_screen._thumbs_escaladas == thumbs


# ---------------------------------------------------------------------------
# Atualizar e desenhar
# ---------------------------------------------------------------------------

def test_atualizar_menu_principal():
    _, menu = novo_menu()
    for _ in range(10):
        menu.atualizar()


def test_animacoes_do_menu_abrem_sem_demora():
    _, menu = novo_menu()
    menu.alpha_entrada = 0
    menu.entrada_t = 0.0
    for _ in range(27):
        menu.atualizar()
    assert menu.alpha_entrada == 255
    assert menu.entrada_t >= menu.entrada_total

    menu.subestado = "CONFIG"
    menu.sub_anim = 0.0
    for _ in range(18):
        menu.atualizar()
    assert menu.sub_anim >= menu.sub_anim_total


def test_desenhar_todas_as_telas():
    jogo, menu = novo_menu()
    tela = pygame.Surface((LARGURA, ALTURA))
    jogo.recordes = []
    for subestado in (
        "MENU", "CONTINUAR", "LOJA", "RECORDES", "CONFIG", "FASES",
    ):
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
