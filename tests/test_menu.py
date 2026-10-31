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
from game.config import ALTURA, LARGURA, EstadoJogo  # noqa: E402
from game.core import Jogo  # noqa: E402
from game.layout import Layout  # noqa: E402
from game.menu import MenuPrincipal  # noqa: E402
from game.phase_select import PhaseStatus  # noqa: E402
from game.theme import tema_atual  # noqa: E402
from src.infrastructure.graphics.comic_theme import usar_visual  # noqa: E402
from src.infrastructure.graphics.theme import (  # noqa: E402
    MENU_ALPHA_PAINEL_RODAPE,
    MENU_COR_PAINEL_RODAPE,
    MENU_COR_TEXTO,
    MENU_COR_TEXTO_SECUNDARIO,
    MENU_MARGEM_SEGURANCA,
)

ROTULOS_ESPERADOS = [
    "01 // JOGAR",
    "02 // HANGAR",
    "03 // PERFIL",
    "04 // CONFIGURAÇÕES",
    "05 // SAIR",
]


def novo_menu():
    jogo = Jogo()
    perfis = jogo.profile_service.list_profiles()
    perfil = perfis[0] if perfis else jogo.profile_service.create("Jogador")
    jogo.ativar_perfil(perfil.id)
    menu = jogo.menu
    menu.alpha_entrada = 255
    return jogo, menu


def configurar_menu_original(jogo, menu):
    """Ativa o layout ORIGINAL sem afetar os testes de compatibilidade COMIC."""
    jogo.config["estilo_visual"] = "ORIGINAL"
    menu._estilo_layout_opcoes = None
    menu._aplicar_layout_opcoes()


# ---------------------------------------------------------------------------
# Construcao e opcoes
# ---------------------------------------------------------------------------

def test_construcao_subestado_e_opcoes():
    _, menu = novo_menu()
    assert menu.subestado == "MENU"
    assert len(menu.opcoes) == 5
    assert [o.texto for o in menu.opcoes] == ROTULOS_ESPERADOS
    assert menu.x_opcoes <= menu.layout.largura


def test_teclado_mantem_foco_ate_mouse_voltar_a_mover():
    """O cursor parado não deve desfazer a seleção feita pelo teclado."""
    _, menu = novo_menu()
    pos = menu.opcoes[0].get_rect(menu.x_opcoes, menu.fonte_opcao, menu.layout).center
    with mock.patch.object(menu, "_pos_logica", side_effect=lambda p: p):
        menu.tratar_eventos(pygame.event.Event(pygame.MOUSEMOTION, {"pos": pos}))
        menu.tratar_eventos(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN}))
        menu.atualizar()
        assert menu.opcao_selecionada == 1
        menu.tratar_eventos(pygame.event.Event(pygame.MOUSEMOTION, {"pos": pos}))
        assert menu.opcao_selecionada == 0


def test_menu_principal_tem_cinco_acoes_do_mesmo_tamanho():
    """Os cinco destinos mantêm painéis uniformes sem mudar a ordem."""
    jogo, menu = novo_menu()
    configurar_menu_original(jogo, menu)
    rects = [opcao.get_rect(menu.x_opcoes, menu.fonte_opcao, menu.layout)
             for opcao in menu.opcoes]
    assert len({rect.size for rect in rects}) == 1
    assert all(b.top - a.bottom > 0 for a, b in zip(rects, rects[1:]))
    assert menu.destaque.y == menu.opcoes[0].y
    assert [option.texto for option in menu.opcoes] == ROTULOS_ESPERADOS


def test_tab_e_shift_tab_navegam_menu_e_hub():
    _, menu = novo_menu()
    for tela, atributo, quantidade in ((menu.tela_principal, "opcao_selecionada", 5),
                                       (menu.telas["JOGAR"], "selection", 3)):
        dono = menu if atributo == "opcao_selecionada" else tela
        setattr(dono, atributo, 0)
        tela.tratar_tecla(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB, mod=0))
        assert getattr(dono, atributo) == 1
        tela.tratar_tecla(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_TAB, mod=pygame.KMOD_SHIFT))
        assert getattr(dono, atributo) == 0
        tela.tratar_tecla(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_TAB, mod=pygame.KMOD_SHIFT))
        assert getattr(dono, atributo) == quantidade - 1


@pytest.mark.parametrize("resolucao", ["900x700", "1920x1080"])
def test_cartoes_do_hub_contem_resumos_longos_e_nao_encostam_no_voltar(resolucao):
    from types import SimpleNamespace

    jogo, menu = novo_menu()
    jogo.config["resolucao"] = resolucao
    hub = menu.jogar_hub
    desenhos = []
    tela = SimpleNamespace(blit=lambda surf, rect: desenhos.append(rect))
    with mock.patch.object(hub, "_detalhes_cartao", return_value=("RESUMO " * 40,) * 2):
        for (rotulo, acao), rect in zip(hub.entries, hub._rects()):
            desenhos.clear()
            hub._desenhar_cartao(tela, rect, rotulo, acao, MENU_COR_TEXTO)
            assert len(desenhos) == 3
            assert all(rect.contains(desenho) for desenho in desenhos)
            assert all(a.bottom <= b.top for a, b in zip(desenhos, desenhos[1:]))
    assert hub._rects()[-1].bottom < hub._back_rect().top


def test_opcoes_originais_têm_painel_e_selecao_destacada_na_area_clicavel():
    """O painel desenhado coincide com a mesma área usada para clique."""
    jogo, menu = novo_menu()
    configurar_menu_original(jogo, menu)
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

    assert sem_selecao.get_at(amostra).a > 0
    assert com_selecao.get_at(amostra).a > sem_selecao.get_at(amostra).a
    assert opcao.get_rect(menu.x_opcoes, menu.fonte_opcao, menu.layout) == rect


@pytest.mark.parametrize("resolucao", [(900, 700), (1280, 720),
                                        (1920, 1080), (2560, 1080)])
@pytest.mark.parametrize("aspecto", ["AJUSTAR", "PREENCHE"])
def test_retangulo_clicavel_coincide_com_botao_em_todas_as_apresentacoes(
        resolucao, aspecto):
    jogo, menu = novo_menu()
    configurar_menu_original(jogo, menu)
    largura, altura = resolucao
    jogo.config["aspecto"] = aspecto
    jogo.config["resolucao"] = f"{largura}x{altura}"
    jogo.janela = pygame.display.set_mode(resolucao)
    escala_janela = jogo._transformacao_janela()[0]
    assert menu.fonte_secundaria.get_height() * escala_janela >= 14
    opcao = menu.opcoes[3]
    esperado = opcao.get_rect(menu.x_opcoes, menu.fonte_opcao, menu.layout)
    tela = pygame.Surface(jogo.tela.get_size(), pygame.SRCALPHA)

    with usar_visual({"estilo_visual": "ORIGINAL"}):
        tema = tema_atual(jogo.config["tema"])
        opcao.desenhar(tela, menu.fonte_opcao, menu.fonte_opcao_sel, tema,
                       menu.x_opcoes, True, 0, 255, menu.layout)

    assert opcao.get_rect(menu.x_opcoes, menu.fonte_opcao, menu.layout) == esperado
    escala, offset_x, offset_y = jogo._transformacao_janela()
    ponto_janela = (round((esperado.centerx * escala) + offset_x),
                    round((esperado.centery * escala) + offset_y))
    pos_logica = menu._pos_logica(ponto_janela)
    assert abs(pos_logica[0] - esperado.centerx) <= 1
    assert abs(pos_logica[1] - esperado.centery) <= 1
    assert esperado.collidepoint(pos_logica)


def test_clique_fora_do_botao_nao_dispara_callback():
    _, menu = novo_menu()
    opcao = menu.opcoes[3]
    callback = mock.Mock()
    opcao.funcao = callback
    rect = opcao.get_rect(menu.x_opcoes, menu.fonte_opcao, menu.layout)
    menu.tela_principal.tratar_clique((rect.right + 1, rect.centery))
    callback.assert_not_called()
    menu.tela_principal.tratar_clique(rect.center)
    callback.assert_called_once_with()


def test_rotulos_cabem_no_botao_e_nome_longo_do_perfil_usa_reticencias():
    _, menu = novo_menu()
    for opcao in menu.opcoes:
        fonte_ajustada, rotulo = opcao._ajustar_rotulo(
            menu.fonte_opcao, opcao.texto,
            menu.layout.px(opcao.largura_painel - 52), menu.layout)
        assert fonte_ajustada.size(rotulo)[0] <= menu.layout.px(
            opcao.largura_painel - 52)

    fonte = menu.fonte_pequena
    linha = menu._linha_perfil_rodape(fonte, "PILOTO-" + "X" * 80, "123", 300)
    assert linha.endswith("   |   MOEDAS: 123")
    assert "…" in linha
    assert menu._medir_espacado(fonte, linha, 1) <= 300
    linha_especial = menu._linha_perfil_rodape(
        fonte, "ÁUREA_Ω-EXPEDIÇÃO" * 4, "123", 300)
    assert linha_especial.startswith("PILOTO: ÁURE")
    assert "…" in linha_especial
    assert menu._medir_espacado(fonte, linha_especial, 1) <= 300


def test_selecao_inicial_respeita_existencia_de_save():
    jogo, menu = novo_menu()
    with mock.patch.object(jogo.progresso, "existe_save", return_value=True):
        menu._construir_opcoes_menu()
        assert menu.opcao_selecionada == 0
        assert menu.opcoes[0].desabilitado is False
    with mock.patch.object(jogo.progresso, "existe_save", return_value=False):
        menu._construir_opcoes_menu()
        menu.jogar_hub.abrir()
        assert menu.opcao_selecionada == 0
        assert menu.opcoes[0].desabilitado is False
        assert menu.jogar_hub.selection == 1


def test_ativar_perfil_seleciona_lobby_sem_save_e_continuar_com_save():
    jogo, menu = novo_menu()
    perfil_id = jogo.profile_service.active.id
    with mock.patch.object(jogo.progresso, "existe_save", return_value=False):
        jogo.ativar_perfil(perfil_id)
    assert menu.subestado == "MENU"
    assert menu.opcao_selecionada == 0
    assert menu.opcoes[0].desabilitado is False
    with mock.patch.object(jogo.progresso, "existe_save", return_value=True):
        jogo.ativar_perfil(perfil_id)
    assert menu.opcao_selecionada == 0
    assert menu.opcoes[0].desabilitado is False


def test_foco_de_teclado_percorre_grupos_sem_interrupcao_e_clique_coincide():
    jogo, menu = novo_menu()
    configurar_menu_original(jogo, menu)
    menu.opcao_selecionada = 2
    evento = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN, unicode="")
    menu.tela_principal.tratar_tecla(evento)
    assert menu.opcao_selecionada == 3
    evento = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP, unicode="")
    menu.tela_principal.tratar_tecla(evento)
    assert menu.opcao_selecionada == 2
    for indice, opcao in enumerate(menu.opcoes):
        callback = mock.Mock()
        opcao.funcao = callback
        rect = opcao.get_rect(menu.x_opcoes, menu.fonte_opcao, menu.layout)
        menu.tela_principal.tratar_clique(rect.center)
        assert menu.opcao_selecionada == indice
        callback.assert_called_once_with()


def test_glitch_desligado_na_reducao_de_efeitos_e_titulo_em_cache():
    jogo, menu = novo_menu()
    configurar_menu_original(jogo, menu)
    with usar_visual({"estilo_visual": "ORIGINAL"}):
        tema = tema_atual(jogo.config["tema"])
        superficies = menu._titulo_surfaces(tema)
    tela = pygame.Surface(jogo.tela.get_size(), pygame.SRCALPHA)
    jogo.config["intensidade_flash"] = "DESLIGADO"
    with mock.patch("pygame.time.get_ticks", return_value=0):
        menu._desenhar_glitch_titulo(tela, superficies, 0)
    with usar_visual({"estilo_visual": "ORIGINAL"}):
        superficies_segunda_leitura = menu._titulo_surfaces(tema)
    assert tela.get_bounding_rect() == pygame.Rect(0, 0, 0, 0)
    assert superficies_segunda_leitura is superficies


def test_glitch_tem_pulsos_curto_com_frequencia_inferior_a_tres_por_segundo():
    jogo, menu = novo_menu()
    superf = {"incarnate_eco": pygame.Surface((4, 4), pygame.SRCALPHA),
              "incarnate_glitch_ciano": pygame.Surface((4, 4), pygame.SRCALPHA)}
    tela = pygame.Surface(jogo.tela.get_size(), pygame.SRCALPHA)
    with mock.patch.object(menu, "_blit_alfa") as desenhar:
        for instante, chamadas in ((0, 2), (41, 2), (42, 0), (649, 0),
                                   (650, 2)):
            desenhar.reset_mock()
            with mock.patch("pygame.time.get_ticks", return_value=instante):
                menu._desenhar_glitch_titulo(tela, superf, 0)
            assert desenhar.call_count == chamadas


def test_continuar_sem_save_fica_visualmente_desabilitado_no_menu_original():
    jogo, menu = novo_menu()
    configurar_menu_original(jogo, menu)
    superficie = pygame.Surface(jogo.tela.get_size(), pygame.SRCALPHA)
    with mock.patch.object(menu, "_tem_save", return_value=False):
        menu._abrir_jogar()
        menu.jogar_hub.desenhar(superficie)
    assert menu.jogar_hub.selection == 1
    assert menu.opcoes[0].desabilitado is False


def test_contraste_do_rodape_sobre_fundo_real_inclui_planeta():
    jogo, menu = novo_menu()
    fundo = pygame.Surface(jogo.tela.get_size())
    margem = menu.layout.margem(MENU_MARGEM_SEGURANCA)
    topo = menu.layout.altura - menu.layout.px(98)
    amostras = []
    with usar_visual({"estilo_visual": "ORIGINAL"}):
        menu.fundo.desenhar(fundo)
        menu.hud.desenhar(fundo, tema_atual(jogo.config["tema"]))
    for x in range(margem, menu.layout.largura - margem, 17):
        for y in range(topo, menu.layout.altura - margem // 2, 11):
            amostras.append(fundo.get_at((x, y))[:3])

    def luminancia(cor):
        canais = []
        for canal in cor:
            valor = canal / 255
            canais.append(valor / 12.92 if valor <= 0.04045
                          else ((valor + 0.055) / 1.055) ** 2.4)
        return sum(peso * valor for peso, valor in zip((0.2126, 0.7152, 0.0722), canais))

    def contraste(foreground, background):
        clara, escura = sorted((luminancia(foreground), luminancia(background)),
                               reverse=True)
        return (clara + 0.05) / (escura + 0.05)

    ratios = []
    for pixel in amostras:
        alpha = MENU_ALPHA_PAINEL_RODAPE / 255
        composto = tuple(round(MENU_COR_PAINEL_RODAPE[i] * alpha
                               + pixel[i] * (1 - alpha)) for i in range(3))
        ratios.extend((contraste(MENU_COR_TEXTO, composto),
                       contraste(MENU_COR_TEXTO_SECUNDARIO, composto)))
    assert len(amostras) > 100
    assert min(ratios) >= 4.5


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
    from game.menu_scene import FundoMenuParallax

    _, menu = novo_menu()
    assert isinstance(menu.fundo, FundoMenuParallax)
    assert menu.fundo.qualidade == "BAIXA"


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


def test_navegacao_no_seletor_de_resolucao_emite_som():
    _, menu = novo_menu()
    menu._som = mock.Mock()
    menu.config_submodo = "resolucao"

    menu._tecla_config(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN}))
    menu._tecla_config(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))

    assert menu._som.call_args_list == [mock.call("navegar"), mock.call("navegar")]


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


def test_nova_estrutura_tem_cinco_itens_nos_dois_estilos():
    jogo, menu = novo_menu()
    assert [item.texto for item in menu.opcoes] == ROTULOS_ESPERADOS
    for estilo in ("ORIGINAL", "COMIC"):
        jogo.config["estilo_visual"] = estilo
        menu._estilo_layout_opcoes = None
        menu._aplicar_layout_opcoes()
        assert [item.texto for item in menu.opcoes] == ROTULOS_ESPERADOS


def test_hubs_preservam_destinos_antigos_em_no_maximo_duas_acoes():
    jogo, menu = novo_menu()
    with mock.patch.object(menu, "_tem_save", return_value=True):
        menu._abrir_jogar()
        assert menu.jogar_hub.entries == (
            ("CONTINUAR", "continuar"), ("LINEAR", "linear"),
            ("MUNDO ABERTO", "mundo_aberto"))
    menu.jogar_hub.ativar(1)
    assert menu.subestado == "FASES"
    assert jogo.modo_atual == "linear"

    menu._voltar_menu()
    menu._abrir_perfil_hub()
    assert menu.perfil_hub.entries == (
        ("PILOTOS", "pilotos"), ("RECORDES", "recordes"),
        ("MEMÓRIAS", "memorias"))
    for index, destino in enumerate(("PERFIS", "RECORDES", "ARQUIVO")):
        menu._abrir_perfil_hub()
        menu.perfil_hub.ativar(index)
        assert menu.subestado == destino


def test_hub_jogar_sem_save_foca_lobby_e_avisa_ao_ativar_continuar():
    _, menu = novo_menu()
    with mock.patch.object(menu, "_tem_save", return_value=False):
        menu._abrir_jogar()
        assert menu.jogar_hub.selection == 1
        menu.jogar_hub.selection = 0
        menu.jogar_hub.tratar_tecla(pygame.event.Event(
            pygame.KEYDOWN, {"key": pygame.K_RETURN}))
    assert menu.subestado == "JOGAR"
    assert menu.jogar_hub.selection == 0
    assert any(item["tipo"] == "erro"
               for item in menu.notificacoes.notificacoes)


def test_hub_jogar_mostra_progresso_e_inicia_modo_aberto():
    jogo, menu = novo_menu()
    jogo.profile_service.update_progress(
        partidas_jogadas=2, dimensao_maxima=3, nivel_maximo=13,
        bosses_por_tipo={"HEXAGONO": 2}, moedas=170, tempo_total=3661,
    )
    assert jogo.profile_service.mode_progress_summary("linear") == {
        "started": True, "dimension": 3, "level": 13,
        "bosses": 2, "coins": 170, "play_time": 3661,
    }
    assert jogo.profile_service.mode_progress_summary("mundo_aberto") == {
        "started": False, "regions": 0, "echoes": 0, "bosses": 0,
        "coins": 0, "play_time": 0,
    }

    menu._abrir_jogar()
    menu.jogar_hub.ativar(2)

    assert menu.subestado == "JOGAR"
    assert jogo.modo_atual == "mundo_aberto"
    assert jogo.estado == EstadoJogo.JOGANDO


def test_mundo_aberto_salva_e_continua_do_ponto_do_perfil():
    jogo, menu = novo_menu()
    strategy = menu.mode_strategies["mundo_aberto"]

    assert strategy.start_new(jogo) is True
    strategy.world.x = 1240
    strategy.world.y = 710
    strategy.world.elapsed = 95
    strategy.save(jogo)
    jogo.estado = EstadoJogo.MENU
    menu.subestado = "MENU"
    menu._abrir_jogar()
    assert menu._tem_save() is True

    menu.jogar_hub.ativar(0)

    assert jogo.modo_atual == "mundo_aberto"
    assert jogo.estado == EstadoJogo.JOGANDO
    assert (strategy.world.x, strategy.world.y, strategy.world.elapsed) == (
        1240, 710, 95,
    )
    assert jogo.profile_service.continue_summary() == {
        "mode": "mundo_aberto", "dimension": "espaco_profundo",
        "level": "inicio", "total_play_time": 95,
    }


@pytest.mark.parametrize("entrada", ["teclado", "mouse"])
def test_continuar_sem_save_desabilitado_em_ambas_as_entradas(entrada):
    _, menu = novo_menu()
    with mock.patch.object(menu, "_tem_save", return_value=False):
        menu._abrir_jogar()
        hub = menu.jogar_hub
        if entrada == "teclado":
            hub.selection = 0
            hub.tratar_tecla(pygame.event.Event(
                pygame.KEYDOWN, {"key": pygame.K_RETURN}))
        else:
            hub.tratar_clique(hub._rects()[0].center)
    assert menu.subestado == "JOGAR"
    assert any(item["tipo"] == "erro"
               for item in menu.notificacoes.notificacoes)


@pytest.mark.parametrize("resolucao", ["900x700", "1280x720"])
@pytest.mark.parametrize("estilo", ["ORIGINAL", "COMIC"])
def test_alvos_do_hub_nao_se_sobrepoem(resolucao, estilo):
    jogo, menu = novo_menu()
    jogo.config["resolucao"] = resolucao
    jogo.config["estilo_visual"] = estilo
    for hub in (menu.jogar_hub, menu.perfil_hub):
        retangulos = [*hub._rects(), hub._back_rect()]
        for indice, primeiro in enumerate(retangulos):
            assert all(not primeiro.colliderect(outro)
                       for outro in retangulos[indice + 1:])


@pytest.mark.parametrize("resolucao", ["900x700", "1920x1080"])
def test_resumos_do_hub_original_cabem_dentro_de_cada_cartao(resolucao):
    jogo, menu = novo_menu()
    jogo.config["resolucao"] = resolucao
    jogo.config["estilo_visual"] = "ORIGINAL"
    tela = mock.Mock()
    for (rotulo, acao), rect in zip(menu.jogar_hub.entries, menu.jogar_hub._rects()):
        tela.reset_mock()
        menu.jogar_hub._desenhar_cartao(tela, rect, rotulo, acao, (225, 235, 255))
        assert len(tela.blit.call_args_list) == 3
        for chamada in tela.blit.call_args_list:
            assert rect.contains(chamada.args[1])


def test_hubs_mantem_a_mesma_estrutura_nos_dois_estilos():
    jogo, menu = novo_menu()
    estruturas = []
    for estilo in ("ORIGINAL", "COMIC"):
        jogo.config["estilo_visual"] = estilo
        estruturas.append((
            tuple(item.texto for item in menu.opcoes),
            menu.jogar_hub.entries, menu.perfil_hub.entries,
            tuple(rect.size for rect in menu.jogar_hub._rects()),
            tuple(rect.size for rect in menu.perfil_hub._rects()),
        ))
    assert estruturas[0] == estruturas[1]


@pytest.mark.parametrize("entrada", ["teclado", "mouse"])
def test_grafo_de_destinos_antigos_em_ate_duas_acoes(entrada):
    rotas = (
        ("CONTINUAR", 0, 0, "CONTINUAR"),
        ("LOBBY", 0, 1, "FASES"),
        ("HANGAR", 1, None, "LOJA"),
        ("PILOTOS", 2, 0, "PERFIS"),
        ("RECORDES", 2, 1, "RECORDES"),
        ("MEMÓRIAS", 2, 2, "ARQUIVO"),
        ("CONFIGURAÇÕES", 3, None, "CONFIG"),
        ("SAIR", 4, None, "MENU"),
    )
    for _, indice_raiz, indice_hub, destino in rotas:
        jogo, menu = novo_menu()
        jogo.profile_service.active.progress["modo_ultimo"] = "linear"
        with (mock.patch.object(menu, "_tem_save", return_value=True),
              mock.patch.object(jogo.progresso, "existe_save", return_value=True)):
            if entrada == "teclado":
                for _ in range(indice_raiz):
                    menu.tela_principal.tratar_tecla(pygame.event.Event(
                        pygame.KEYDOWN, {"key": pygame.K_DOWN, "unicode": ""}))
                menu.tela_principal.tratar_tecla(pygame.event.Event(
                    pygame.KEYDOWN, {"key": pygame.K_RETURN, "unicode": ""}))
            else:
                rect = menu.opcoes[indice_raiz].get_rect(
                    menu.x_opcoes, menu.fonte_opcao, menu.layout)
                menu.tela_principal.tratar_clique(rect.center)
            if indice_hub is not None:
                hub = menu.jogar_hub if indice_raiz == 0 else menu.perfil_hub
                if entrada == "teclado":
                    for _ in range(indice_hub):
                        hub.tratar_tecla(pygame.event.Event(
                            pygame.KEYDOWN, {"key": pygame.K_DOWN}))
                    hub.tratar_tecla(pygame.event.Event(
                        pygame.KEYDOWN, {"key": pygame.K_RETURN}))
                else:
                    hub.tratar_clique(hub._rects()[indice_hub].center)
            if destino == "CONTINUAR":
                assert menu.transicao_missao.em_andamento() is True
            elif destino == "MENU":
                assert menu.dialogo is not None and menu.dialogo.ativo
            else:
                assert menu.subestado == destino


def test_escape_dos_hubs_e_destinos_restaura_foco_de_origem():
    _, menu = novo_menu()
    menu.opcao_selecionada = 2
    menu._abrir_perfil_hub()
    menu.perfil_hub.tratar_tecla(pygame.event.Event(
        pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))
    assert menu.subestado == "MENU"
    assert menu.opcao_selecionada == 2

    menu.opcao_selecionada = 0
    menu._abrir_jogar()
    menu.jogar_hub.tratar_tecla(pygame.event.Event(
        pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))
    assert menu.subestado == "MENU"
    assert menu.opcao_selecionada == 0

    menu.opcao_selecionada = 2
    menu._abrir_perfil_hub()
    menu.perfil_hub.ativar(1)
    menu.telas["RECORDES"].tratar_tecla(pygame.event.Event(
        pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))
    assert menu.subestado == "MENU"
    assert menu.opcao_selecionada == 2


def test_clique_do_hub_usa_o_mesmo_retangulo_desenhado():
    _, menu = novo_menu()
    menu._abrir_jogar()
    rect = menu.jogar_hub._rects()[1]
    menu.jogar_hub.tratar_clique(rect.center)
    assert menu.subestado == "FASES"


def test_botao_voltar_do_hub_funciona_com_mouse():
    _, menu = novo_menu()
    menu._abrir_jogar()
    menu.jogar_hub.tratar_clique(menu.jogar_hub._back_rect().center)
    assert menu.subestado == "MENU"
    assert menu.opcao_selecionada == 0


@pytest.mark.parametrize("estilo", ["ORIGINAL", "COMIC"])
@pytest.mark.parametrize("resolucao", ["900x700", "1920x1080"])
def test_menu_principal_compartilha_opcoes_uniformes_e_cartao(
        estilo, resolucao):
    jogo, menu = novo_menu()
    jogo.config["estilo_visual"] = estilo
    jogo.config["resolucao"] = resolucao
    menu._estilo_layout_opcoes = None
    menu._aplicar_layout_opcoes()
    jogo.profile_service.rename(jogo.profile_service.active.id, "Árvore Estelar 9")
    jogo.profile_service.update_progress(
        dimensao_maxima=4, nivel_maximo=8, moedas=1200, tempo_total=5400,
        bosses_por_tipo={"HEXAGONO": 2}, partidas_jogadas=1,
    )
    surface = pygame.Surface(jogo.tela_ui.get_size(), pygame.SRCALPHA)
    with usar_visual({"estilo_visual": estilo}):
        menu.tela_principal.desenhar_fundo_cartao(
            surface, jogo.profile_service.menu_profile_summary())
        menu.tela_principal.desenhar(surface)
    rects = [item.get_rect(menu.x_opcoes, menu.fonte_opcao, menu.layout)
             for item in menu.opcoes]
    assert [item.texto for item in menu.opcoes] == ROTULOS_ESPERADOS
    assert all(item.principal for item in menu.opcoes)
    assert len({rect.size for rect in rects}) == 1
    assert all(rect.bottom <= seguinte.top
               for rect, seguinte in zip(rects, rects[1:]))
    assert all(0 <= rect.left < rect.right <= menu.layout.largura
               and 0 <= rect.top < rect.bottom <= menu.layout.altura
               for rect in rects)
    assert rects[0].width < menu.layout.largura
    font = menu.layout.fonte_titulo(20)
    name = menu.tela_principal._truncar_nome(font, "Árvore Estelar 9",
                                             menu.layout.px(120))
    assert name.endswith("…")
    assert font.size(name)[0] <= menu.layout.px(120)


def test_cartao_de_perfil_tem_estado_vazio_sem_perfil_ativo():
    jogo, menu = novo_menu()
    jogo.profile_service.active = None
    surface = pygame.Surface(jogo.tela_ui.get_size(), pygame.SRCALPHA)
    menu._estilo_layout_opcoes = None
    menu._aplicar_layout_opcoes()
    with usar_visual({"estilo_visual": "ORIGINAL"}):
        menu.tela_principal.desenhar_fundo_cartao(surface, None)
        menu.tela_principal.desenhar(surface)
    rect = pygame.Rect(*menu.tela_principal.cartao_rect())
    assert surface.get_at(rect.center).a > 0


def test_selos_do_menu_respeitam_servico_e_hangar_nao_reaparece():
    jogo, menu = novo_menu()
    service = jogo.profile_service
    service.update_progress(
        memorias_desbloqueadas=["introducao"], moedas=500,
        novidades_vistas={"memorias": [], "hangar": []},
        novidades_pendentes={"hangar": []}, skins_desbloqueadas=["padrao"],
    )
    surface = pygame.Surface(jogo.tela_ui.get_size(), pygame.SRCALPHA)
    with usar_visual({"estilo_visual": "ORIGINAL"}):
        menu.tela_principal.desenhar(surface)
    assert menu.opcoes[1].novo is True
    assert menu.opcoes[2].novo is True

    menu._abrir_perfil_hub()
    assert service.novelty_ids("memorias") == ["introducao"]
    menu._abrir_arquivo()
    assert service.novelty_ids("memorias") == []
    service.spend(500)
    assert "fenix" in service.novelty_ids("hangar")
    menu._abrir_loja()
    service.credit(500)
    assert service.novelty_ids("hangar") == []


@pytest.mark.parametrize("estilo", ["ORIGINAL", "COMIC"])
def test_layout_4_3_e_hub_continuar_mostram_resumo_real(estilo):
    jogo, menu = novo_menu()
    jogo.config["estilo_visual"] = estilo
    jogo.config["resolucao"] = "900x700"
    menu._estilo_layout_opcoes = None
    menu._aplicar_layout_opcoes()
    jogo.profile_service.update_progress(
        partidas_jogadas=1, dimensao_maxima=6, nivel_maximo=22, tempo_total=3661,
    )
    assert menu._layout_4_3() is True
    menu.jogar_hub.abrir()
    menu.jogar_hub.selection = 0
    surface = pygame.Surface(jogo.tela_ui.get_size(), pygame.SRCALPHA)
    with usar_visual({"estilo_visual": estilo}):
        menu.jogar_hub.desenhar(surface)
    assert jogo.profile_service.continue_summary() == {
        "mode": "linear", "dimension": 1, "level": 1,
        "total_play_time": 3661,
    }
    assert menu.jogar_hub._panel().width == jogo.layout.px(620)


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
    jogo.fade = 0
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


def test_clique_na_borda_decorativa_nao_aciona_opcao_do_menu():
    jogo, menu = novo_menu()
    jogo.janela = pygame.Surface((2560, 1080))
    jogo.config["aspecto"] = "PREENCHE"
    menu.subestado = "MENU"
    menu.opcao_selecionada = 0
    estado_anterior = menu.subestado

    menu.tratar_eventos(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (80, 540)}))

    assert menu.subestado == estado_anterior
    assert menu.opcao_selecionada == 0


def test_ajuste_de_tela_aplica_zoom_e_offset_no_modo_preenche():
    jogo, menu = novo_menu()
    jogo.janela = pygame.Surface((2560, 1080))
    jogo.config["aspecto"] = "PREENCHE"
    jogo.config["ajuste_escala"] = 1.0
    jogo.config["ajuste_off_x"] = 0
    jogo.config["ajuste_off_y"] = 0

    menu._tecla_ajuste(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_w}))
    menu._tecla_ajuste(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT}))

    escala, off_x, off_y = jogo._transformacao_janela()
    assert escala == pytest.approx(1.5 * 1.01)
    assert off_x == pytest.approx(324)
    assert off_y == 0
    ponto = (640, 360)
    janela = (ponto[0] * escala + off_x, ponto[1] * escala + off_y)
    assert menu._pos_logica(janela) == pytest.approx(ponto, abs=1)


def test_preenche_900x700_usa_bordas_verticais_e_mira_fora_delimitada():
    jogo, menu = novo_menu()
    jogo.janela = pygame.Surface((900, 700))
    jogo.config["aspecto"] = "PREENCHE"
    jogo.config["mira_ativa"] = True
    jogo.estado = EstadoJogo.JOGANDO
    jogo.fade = 0
    jogo.tela.fill((220, 30, 40))
    jogo.tela_ui.fill((0, 0, 0, 0))
    fundo = pygame.Surface((900, 700))
    fundo.fill((20, 170, 60))
    jogo._obter_fundo_preenche = mock.Mock(return_value=fundo)

    jogo._apresentar()
    escala, off_x, off_y = jogo._transformacao_janela()
    destino = pygame.Rect(round(off_x), round(off_y),
                          round(LARGURA * escala), round(ALTURA * escala))
    assert destino.width / destino.height == pytest.approx(16 / 9, abs=0.002)
    assert destino.left == 0 and destino.right == 900
    assert destino.top > 0 and destino.bottom < 700
    assert jogo.janela.get_at((450, 20))[:3] == (20, 170, 60)
    assert all(abs(valor - esperado) <= 4 for valor, esperado in zip(
        jogo.janela.get_at(destino.center)[:3], (220, 30, 40)))

    with mock.patch("pygame.mouse.get_pos", return_value=(450, 20)):
        assert jogo.posicao_mira() is None
    with mock.patch("pygame.mouse.get_pos", return_value=destino.center):
        assert jogo.posicao_mira() == (640, 360)
    assert menu._pos_logica(destino.center) == pytest.approx((640, 360), abs=1)


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
