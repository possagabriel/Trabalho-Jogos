"""Testes do núcleo do jogo (core.Jogo).

Cobre estados, início de partida, níveis/boss, desbloqueio de armas,
combate (projéteis, explosões, Nova em área, power-ups), dano ao jogador e
fim de jogo (recordes, moedas).

Roda headless:

    python tests/test_core.py   # standalone
    pytest tests/test_core.py -v
"""

import os
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["INCARNATE_DATA_DIR"] = tempfile.mkdtemp(prefix="incarnate_test_")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from unittest import mock  # noqa: E402

import pygame  # noqa: E402

from game.combat_session import SessaoCombate  # noqa: E402
from game.config import ALTURA, LARGURA, EstadoJogo  # noqa: E402
from game.core import Jogo  # noqa: E402
from game.enemies import Inimigo, InimigoEspecial  # noqa: E402
from game.game_over_controller import ControladorGameOver  # noqa: E402
from game.loop_controller import ControladorLoop  # noqa: E402
from game.pause_controller import ControladorPausa  # noqa: E402
from game.powerups import PowerUp  # noqa: E402
from game.render_controller import ControladorRenderizacao  # noqa: E402
from game.theme import tema_atual  # noqa: E402
from game.weapons import ARMARIA, Projetil  # noqa: E402
from src.core.settings import (  # noqa: E402
    Configuracoes,  # noqa: E402
    OpcoesShaderComic,  # noqa: E402
)
from src.runtime.domain.entities.player import Jogador  # noqa: E402


def _patch_recordes():
    """Isola recordes e save num diretorio temporario.

    Sob pytest a suite inteira roda num unico processo e compartilha o
    mesmo diretorio de dados; isolar evita que um teste veja pontuacoes
    ou moedas gravadas por outro (ex.: o loop de combate do smoke_test).
    """
    from game import save_system
    dados = tempfile.mkdtemp(prefix="spacefury_fimjogo_")
    return mock.patch.multiple(
        save_system,
        ARQUIVO_RECORDES=os.path.join(dados, "records.json"),
        ARQUIVO_SAVE=os.path.join(dados, "save.json"))


def novo_jogo():
    jogo = Jogo()
    jogo._preparar_jogo()
    jogo.estado = "JOGANDO"
    return jogo


def _limpar_campo(jogo):
    jogo.inimigos = []
    jogo.boss = None
    jogo.projeteis = []
    jogo.powerups = []
    jogo.fila_onda = []


# ---------------------------------------------------------------------------
# Partida e estados
# ---------------------------------------------------------------------------

def test_preparar_jogo():
    jogo = Jogo()
    jogo._preparar_jogo()
    assert jogo.estado == "PREPARANDO"
    assert jogo.jogador.nivel == 1
    assert jogo.carregamento == 0


def test_carregamento_transiciona_para_jogando():
    jogo = Jogo()
    jogo._preparar_jogo()
    jogo.carregamento = 99
    jogo._atualizar()
    assert jogo.estado == "CUTSCENE"
    while jogo.cutscene_controller.ativo:
        jogo.cutscene_controller.pular_direto()
    assert jogo.estado == "JOGANDO"
    assert jogo.carregamento == 100


def test_loop_nao_atualiza_mundo_de_combate_no_menu():
    jogo = Jogo()
    jogo.menu.atualizar = mock.Mock()
    jogo.particulas.atualizar = mock.Mock()
    jogo.cenario.atualizar = mock.Mock()

    jogo.loop_controller.atualizar()

    jogo.menu.atualizar.assert_called_once()
    jogo.particulas.atualizar.assert_not_called()
    jogo.cenario.atualizar.assert_not_called()


def test_loop_atualiza_mundo_quando_partida_esta_visivel():
    jogo = novo_jogo()
    jogo._atualizar_jogando = mock.Mock()
    jogo.particulas.atualizar = mock.Mock()
    jogo.cenario.atualizar = mock.Mock()

    jogo.loop_controller.atualizar()

    jogo.particulas.atualizar.assert_called_once()
    jogo.cenario.atualizar.assert_called_once()


def test_novo_jogo_estado_jogando():
    jogo = Jogo()
    jogo._novo_jogo("Teste")
    assert jogo.estado == "JOGANDO"
    assert jogo.jogador.nome == "Teste"
    assert jogo.inimigos == [] or jogo.fila_onda


def test_nome_vazio_vira_jogador():
    jogo = Jogo()
    jogo._novo_jogo("   ")
    assert jogo.jogador.nome == "Jogador"


def test_estado_do_jogo_usa_enum_e_aceita_compatibilidade_textual():
    jogo = Jogo()
    assert jogo.estado is EstadoJogo.MENU
    jogo.estado = "PREPARANDO"
    assert jogo.estado is EstadoJogo.PREPARANDO


def test_jogo_expoe_contrato_da_sessao_de_combate():
    jogo = Jogo()
    assert isinstance(jogo, SessaoCombate)
    assert jogo.combate_controller.sessao is jogo


def test_jogo_delega_fluxos_aos_controladores_extraidos():
    jogo = Jogo()
    assert isinstance(jogo.loop_controller, ControladorLoop)
    assert isinstance(jogo.pausa_controller, ControladorPausa)
    assert isinstance(jogo.game_over_controller, ControladorGameOver)
    assert isinstance(jogo.render_controller, ControladorRenderizacao)


def test_pausa_config_renderiza_volume_zero():
    jogo = novo_jogo()
    jogo.config["musica_volume"] = 0.0
    jogo.config["efeitos_volume"] = 0.0
    jogo._desenhar_pausa_config({
        "primaria": (255, 0, 0), "secundaria": (0, 255, 255),
        "borda_fraco": (100, 100, 100),
    }, 0.0)


def test_pausa_mostra_nome_da_skin_sem_representacao_python():
    jogo = novo_jogo()
    jogo.jogador.skin = jogo.loja.pegar_skin("fenix")
    with mock.patch("src.runtime.application.core.desenhar_texto") as texto:
        jogo._desenhar_pausa_principal(tema_atual("NEON"), 0.0)
    linhas = [chamada.args[1] for chamada in texto.call_args_list]
    assert any("VISUAL FENIX" in linha for linha in linhas)
    assert all("src.runtime" not in linha for linha in linhas)


# ---------------------------------------------------------------------------
# Niveis, boss e armas
# ---------------------------------------------------------------------------

def test_iniciar_nivel_cria_boss_a_cada_5():
    jogo = novo_jogo()
    jogo._iniciar_nivel(5)
    assert jogo.boss is not None
    assert jogo.boss_intro == 130
    jogo._iniciar_nivel(6)
    assert jogo.boss is None
    assert jogo.fila_onda


def test_iniciar_nivel_troca_cenario():
    from game.scenarios import Cenario
    jogo = novo_jogo()
    jogo.cenario = Cenario(1)
    jogo._iniciar_nivel(6)
    assert jogo.cenario.id == 2


def test_voltar_ao_menu_salva_checkpoint_da_fase_atual():
    jogo = novo_jogo()
    jogo._iniciar_nivel(13)
    with mock.patch.object(jogo.progresso, "salvar_arquivo") as salvar:
        jogo.pausa_controller.confirmar_saida()
    campanha = jogo.progresso.campanha
    assert jogo.estado is EstadoJogo.MENU
    assert campanha["fase_atual"] == "identidade"
    assert campanha["nivel_atual"] == 13
    salvar.assert_called_once()


def test_verificar_desbloqueio_arma():
    jogo = novo_jogo()
    jogo.jogador.armas_desbloqueadas = [0]
    jogo.jogador.nivel = 3
    jogo._verificar_desbloqueio_arma()
    assert 1 in jogo.jogador.armas_desbloqueadas
    assert jogo.jogador.arma_atual == 1
    assert ARMARIA[1]["nome"] == "Laser"


def test_verificar_desbloqueio_arma_nao_repete():
    jogo = novo_jogo()
    jogo.jogador.armas_desbloqueadas = [0, 1]
    jogo.jogador.nivel = 6
    jogo._verificar_desbloqueio_arma()
    assert 1 in jogo.jogador.armas_desbloqueadas


def test_escolha_de_melhoria_aplica_efeito_e_inicia_proximo_nivel():
    jogo = novo_jogo()
    jogo.nivel_pendente = 2
    jogo.melhorias_oferecidas = [{
        "id": "potencia", "nome": "MUNIÇÃO PESADA",
        "descricao": "+1 dano", "nivel": 0,
    }]
    jogo.estado = EstadoJogo.MELHORIA

    assert jogo.progressao_controller.selecionar_melhoria(0) is True

    assert jogo.jogador.bonus_dano == 1
    assert jogo.jogador.nivel == 2
    assert jogo.estado is EstadoJogo.JOGANDO


def test_escolhas_oferecem_modulo_com_custo_e_aplicam_consequencias():
    from src.runtime.domain.systems.upgrades import MELHORIAS_COM_CUSTO

    jogo = novo_jogo()
    jogo.progressao_controller.oferecer_melhorias(2)
    assert any(opcao["id"] in MELHORIAS_COM_CUSTO and opcao["custo"]
               for opcao in jogo.melhorias_oferecidas)

    jogo.melhorias_oferecidas = [{"id": "reator_instavel"}]
    vida_max = jogo.jogador.max_vida
    jogo.progressao_controller.selecionar_melhoria(0)
    assert jogo.jogador.bonus_dano == 2
    assert jogo.jogador.max_vida == vida_max - 1

    jogo.nivel_pendente = 3
    jogo.melhorias_oferecidas = [{"id": "blindagem_pesada"}]
    jogo.progressao_controller.selecionar_melhoria(0)
    assert jogo.jogador.max_vida == vida_max + 1
    assert jogo.jogador.multiplicador_recarga_esquiva > 1

    jogo.nivel_pendente = 4
    jogo.melhorias_oferecidas = [{"id": "motor_emergencia"}]
    jogo.progressao_controller.selecionar_melhoria(0)
    assert jogo.jogador.multiplicador_cadencia > 1
    assert jogo.jogador.multiplicador_recarga_esquiva < 1
    jogo.jogador.cooldown_tiro = 0
    assert jogo.jogador.atirar()
    arma = ARMARIA[jogo.jogador.arma_atual]
    assert jogo.jogador.cooldown_tiro == round(
        arma["cooldown"] * jogo.jogador.multiplicador_cadencia)


def test_modulo_de_risco_respeita_limite_sem_mutar_jogador():
    from src.runtime.domain.systems.upgrades import aplicar_melhoria, sortear_melhorias

    jogador = Jogador()
    assert aplicar_melhoria(jogador, "reator_instavel")
    assert aplicar_melhoria(jogador, "reator_instavel")
    dano, vida = jogador.bonus_dano, jogador.max_vida
    assert aplicar_melhoria(jogador, "reator_instavel") is False
    assert (jogador.bonus_dano, jogador.max_vida) == (dano, vida)
    for chave in ("blindagem_pesada", "motor_emergencia"):
        assert aplicar_melhoria(jogador, chave)
        assert aplicar_melhoria(jogador, chave)
    assert all(chave not in {"reator_instavel", "blindagem_pesada",
                             "motor_emergencia"} for chave in sortear_melhorias(jogador))


def test_transicao_dimensional_avanca_sem_bloquear_eventos():
    jogo = novo_jogo()
    with mock.patch.object(jogo, "_apresentar") as apresentar:
        jogo._iniciar_nivel(6)
    apresentar.assert_not_called()
    assert jogo.progressao_controller.transicao is not None
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_p}))
    assert jogo._tratar_eventos() is True
    assert jogo.estado is EstadoJogo.PAUSA
    jogo.estado = EstadoJogo.JOGANDO
    for _ in range(64):
        jogo._atualizar()
    assert jogo.progressao_controller.transicao is None


def test_acessibilidade_pode_desligar_flash_e_tremor():
    jogo = novo_jogo()
    jogo.config["intensidade_flash"] = "DESLIGADO"
    jogo.config["intensidade_tremor"] = "DESLIGADO"
    jogo.flash, jogo.fade, jogo.trauma = 10, 0, 1.0
    jogo.tela.fill((20, 30, 40))

    jogo.render_controller._desenhar_overlays_logicos()
    jogo.render_controller.aplicar_shake()

    assert jogo.tela.get_at((10, 10))[:3] == (20, 30, 40)
    assert jogo.trauma < 1.0


def test_configuracoes_expoem_opcoes_de_acessibilidade():
    jogo = novo_jogo()
    menu = jogo.menu
    tipos = [tipo for _, tipo in menu._linhas_config()]
    assert {"intensidade_flash", "intensidade_tremor", "mostrar_hitbox"}.issubset(tipos)
    assert "tutorial_ativo" not in tipos
    menu.config_selecao = tipos.index("intensidade_flash")
    with mock.patch.object(jogo.config, "salvar"):
        menu._ajustar_config(1)
    assert jogo.config["intensidade_flash"] == "REDUZIDO"


# ---------------------------------------------------------------------------
# Combate
# ---------------------------------------------------------------------------

def test_projetil_jogador_remove_inimigo():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    jogo.inimigos = [Inimigo("scout", 1, x=450, y=170)]
    jogo.projeteis = [Projetil(450, 180, 0, -8, 1, (255, 255, 255), 4)]
    jogo._atualizar_projeteis()
    assert not jogo.inimigos
    assert jogo.inimigos_abates == 1


def test_plasma_causa_dano_secundario_em_alvo_proximo():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    principal = Inimigo("forja", 1, x=450, y=170)
    vizinho = Inimigo("forja", 1, x=490, y=170)
    vida_vizinho = vizinho.vida
    jogo.inimigos = [principal, vizinho]
    plasma = Projetil(450, 170, 0, -7, 3, (150, 50, 200), 8, tipo="plasma")

    assert jogo._projetil_jogador_atinge(plasma) is True

    assert vizinho.vida < vida_vizinho


def test_ion_atravessa_inimigos_na_coluna():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    jogo.jogador.arma_atual = 6
    jogo.inimigos = [Inimigo("scout", 1, x=450, y=150),
                     Inimigo("scout", 1, x=450, y=250)]
    ion = Projetil(450, 300, 0, 0, 5, (200, 220, 255), 6, tipo="ion")
    jogo.projeteis = [ion]
    jogo._atualizar_projeteis()
    assert not jogo.inimigos
    assert ion in jogo.projeteis


def test_combo_so_aumenta_apos_acertar_alvo():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    assert jogo.jogador.atirar()
    assert jogo.jogador.combo.combo_atual == 0
    inimigo = Inimigo("forja", 1, x=450, y=170)
    jogo.inimigos = [inimigo]
    proj = Projetil(450, 170, 0, -1, 1, (255, 255, 255), 4)
    assert jogo._projetil_jogador_atinge(proj)
    assert jogo.jogador.combo.combo_atual == 1


def test_ion_atinge_cada_alvo_uma_vez_por_projetil():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    inimigo = Inimigo("forja", 1, x=450, y=170)
    jogo.inimigos = [inimigo]
    ion = Projetil(450, 300, 0, 0, 1, (200, 220, 255), 6, tipo="ion")
    jogo.projeteis = [ion]
    vida_antes = inimigo.vida
    for _ in range(5):
        jogo._atualizar_projeteis()
    assert inimigo.vida == vida_antes - 1
    assert jogo.jogador.combo.combo_atual == 1


def test_gauss_atravessa_mas_danifica():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    jogo.inimigos = [Inimigo("forja", 1, x=450, y=290),
                     Inimigo("forja", 1, x=450, y=240)]
    gauss = Projetil(450, 300, 0, -14, 3, (180, 220, 255), 3, tipo="gauss")
    jogo.projeteis = [gauss]
    jogo._atualizar_projeteis()
    # gauss e penetrante: danifica mas nao e consumido
    assert gauss in jogo.projeteis
    assert jogo.inimigos
    assert jogo.inimigos[0].vida == 2
    # atravessa e atinge o segundo tambem
    for _ in range(30):
        jogo._atualizar_projeteis()
    assert all(e.vida < e.vida_max for e in jogo.inimigos)


def test_projetil_inimigo_danifica_jogador():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    jog = jogo.jogador
    jog.x, jog.y = 450, 100
    jogo.projeteis = [Projetil(450, 100, 0, 0, 1, (255, 0, 0), 4,
                               origem="inimigo")]
    jogo._atualizar_projeteis()
    assert jog.vida == 4
    assert not jogo.projeteis


def test_campo_forca_reflete_tiro():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    especial = InimigoEspecial("cristalino", 3, cenario_id=1)
    especial.campo_forca = True
    especial.x, especial.y = 450, 150
    jogo.inimigos = [especial]
    proj = Projetil(450, 180, 0, -8, 1, (255, 255, 255), 4)
    jogo.projeteis = [proj]
    jogo._atualizar_projeteis()
    assert proj.refletor is True
    assert proj.origem == "inimigo"


def test_explodir_inimigo_pontua_com_combo():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    inimigo = Inimigo("scout", 1, x=450, y=150)
    jogo.inimigos = [inimigo]
    jogo.jogador.combo.combo_atual = 12  # multiplicador 1.5
    pontos_iniciais = jogo.jogador.pontuacao
    jogo._explodir_inimigo(inimigo)
    assert jogo.jogador.pontuacao > pontos_iniciais
    assert jogo.inimigos_abates == 1
    assert not jogo.inimigos


def test_explodir_nova_area():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    jogo.inimigos = [Inimigo("scout", 1, x=450, y=150)]
    proj = Projetil(450, 160, 0, -6, 6, (255, 150, 0), 9, tipo="nova")
    assert jogo._explodir_nova(proj) is True
    assert not jogo.inimigos


def test_explodir_nova_sem_alvo_continua():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    proj = Projetil(450, 200, 0, -6, 6, (255, 150, 0), 9, tipo="nova")
    assert jogo._explodir_nova(proj) is False


def test_ativar_especial_lanca_bomba():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    jogo.especial = 1.0
    assert jogo._ativar_especial() is True
    assert jogo.especial == 0.0
    bombas = [p for p in jogo.projeteis if p.tipo == "bomba"]
    assert len(bombas) == 1
    assert bombas[0].dano > 6  # dano maior que a Nova


def test_ativar_especial_exige_carga():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    jogo.especial = 0.9
    assert jogo._ativar_especial() is False
    assert not any(p.tipo == "bomba" for p in jogo.projeteis)


def test_bomba_explode_em_area():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    jogo.inimigos = [Inimigo("scout", 1, x=450, y=150)]
    proj = Projetil(450, 160, 0, -3.5, 25, (255, 120, 40), 20, tipo="bomba")
    assert jogo._explodir_bomba(proj) is True
    assert not jogo.inimigos


def test_bomba_sem_alvo_continua():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    proj = Projetil(450, 200, 0, -3.5, 25, (255, 120, 40), 20, tipo="bomba")
    assert jogo._explodir_bomba(proj) is False


def test_bomba_explode_no_topo_sem_alvo():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    proj = Projetil(450, 30, 0, -3.5, 25, (255, 120, 40), 20, tipo="bomba")
    assert jogo._explodir_bomba(proj) is True


def test_bomba_detona_antes_de_ser_descartada_no_topo():
    """Um frame lento nao pode fazer a Bomba Vortex desaparecer sem explodir."""
    jogo = novo_jogo()
    _limpar_campo(jogo)
    jogo.projeteis = [Projetil(450, -29, 0, -3.5, 25,
                               (255, 120, 40), 20, tipo="bomba")]
    jogo._atualizar_projeteis()
    assert jogo.projeteis == []
    assert jogo.flash == 16


def test_carga_especial_mais_lenta():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    inimigo = Inimigo("scout", 1, x=450, y=150)
    jogo.inimigos = [inimigo]
    jogo._explodir_inimigo(inimigo)
    assert 0.0 < jogo.especial <= 0.03  # demora mais para carregar


def test_powerup_aplicado_ao_colidir():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    jogo.jogador.x, jogo.jogador.y = 450, 100
    jogo.powerups = [PowerUp("moedas", 450, 100)]
    jogo._atualizar_powerups()
    assert not jogo.powerups
    assert jogo.jogador.moedas_jogo == 100


def test_powerup_passou_da_tela_e_removido():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    pu = PowerUp("moedas", 450, ALTURA + 40)
    jogo.powerups = [pu]
    jogo._atualizar_powerups()
    assert not jogo.powerups


# ---------------------------------------------------------------------------
# Dano ao jogador
# ---------------------------------------------------------------------------

def test_aplicar_dano_jogador_sem_escudo():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    jog = jogo.jogador
    vida = jog.vida
    assert jogo._aplicar_dano_jogador() is True
    assert jog.vida == vida - 1
    assert jogo.flash == 10


def test_aplicar_dano_jogador_com_escudo():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    jog = jogo.jogador
    jog.escudo = True
    assert jogo._aplicar_dano_jogador() is True
    assert jog.escudo is False
    assert jog.vida == 5
    assert jogo.trauma > 0


def test_aplicar_dano_jogador_invencivel():
    jogo = novo_jogo()
    _limpar_campo(jogo)
    jog = jogo.jogador
    jog.invencivel = 30
    assert jogo._aplicar_dano_jogador() is False
    assert jog.vida == 5


# ---------------------------------------------------------------------------
# Fim de jogo
# ---------------------------------------------------------------------------

def test_fim_de_jogo():
    with _patch_recordes():
        jogo = novo_jogo()
        _limpar_campo(jogo)
        jog = jogo.jogador
        jog.pontuacao = 500
        jog.moedas_jogo = 100
        jog.nivel = 3
        jogo.bosses_abates = 1
        jogo.tempo_partida = 30
        jogo._fim_de_jogo()
    assert jogo.estado == "GAME_OVER"
    assert jogo.moedas_ganhas == 100 + 50 * 1 + 100 * 1
    assert jogo.novo_recorde is True
    assert jogo.recordes[0]["pontos"] == 500
    assert jogo.loja.moedas == 100 + 50 * 1 + 100 * 1


def test_fim_de_jogo_nao_e_recorde():
    with _patch_recordes():
        from game.save_system import SistemaProgressao
        SistemaProgressao.salvar_recorde("Top", 1000, 9, "Padrao")
        jogo = novo_jogo()
        _limpar_campo(jogo)
        jogo.recordes = SistemaProgressao.carregar_recordes()
        jog = jogo.jogador
        jog.pontuacao = 100
        jogo._fim_de_jogo()
    assert jogo.novo_recorde is True  # recordes legados globais não afetam o perfil


# ---------------------------------------------------------------------------
# Shake / trauma
# ---------------------------------------------------------------------------

def test_aplicar_shake_move_a_tela():
    jogo = novo_jogo()
    jogo.trauma = 1.0
    jogo.tela.fill((255, 0, 0))
    jogo._aplicar_shake()
    assert jogo.trauma < 1.0
    jogo.trauma = 0.0
    jogo._aplicar_shake()
    assert jogo.trauma == 0.0


def test_adicionar_trauma_limita_a_1():
    jogo = novo_jogo()
    jogo._adicionar_trauma(0.8)
    jogo._adicionar_trauma(0.8)
    assert jogo.trauma == 1.0


# ---------------------------------------------------------------------------
# Desenho e apresentacao
# ---------------------------------------------------------------------------

def test_interface_generica_permanece_no_canvas_logico():
    jogo = Jogo()
    assert jogo.tela_ui is not jogo.tela
    assert jogo.tela_ui.get_flags() & pygame.SRCALPHA
    assert jogo.tela_ui.get_size() == jogo.tela.get_size()
    assert (jogo.layout.largura, jogo.layout.altura) == (LARGURA, ALTURA)


def test_hud_e_composto_no_canvas_logico_antes_da_apresentacao():
    jogo = novo_jogo()
    jogo._desenhar_jogo = mock.Mock()
    jogo._apresentar = mock.Mock()
    jogo._desenhar_hud = mock.Mock()

    jogo.render_controller.desenhar()

    jogo._desenhar_hud.assert_called_once()
    jogo._apresentar.assert_called_once()


def test_apresentador_gpu_recebe_mundo_interface_e_destino_fisico():
    jogo = Jogo()
    jogo.janela = pygame.Surface((1920, 1080))
    jogo._apresentador_gpu = mock.Mock()

    jogo._apresentar()

    jogo._apresentador_gpu.aplicar_opcoes_shader.assert_called_once_with(
        OpcoesShaderComic.de_config(jogo.config))
    jogo._apresentador_gpu.apresentar.assert_called_once_with(
        jogo.tela, (0, 0, 1920, 1080), (1920, 1080), (8, 8, 13),
        interface=jogo.tela_ui, fundo=None, efeito_borda=None, hud=None)


def test_fallback_cpu_compoe_interface_sobre_o_mundo():
    jogo = Jogo()
    jogo.tela.fill((200, 10, 10))
    jogo.tela_ui.fill((0, 0, 0, 0))
    jogo.tela_ui.set_at((10, 10), (10, 220, 20, 255))

    composto = jogo._quadro_composto()

    assert composto.get_at((0, 0))[:3] == (200, 10, 10)
    assert composto.get_at((10, 10))[:3] == (10, 220, 20)


def test_gpu_processa_interface_junto_quando_preservacao_esta_desligada():
    jogo = Jogo()
    jogo.janela = pygame.Surface((1920, 1080))
    jogo.config["preservar_interface"] = False
    jogo._apresentador_gpu = mock.Mock()

    jogo._apresentar()

    argumentos = jogo._apresentador_gpu.apresentar.call_args
    assert argumentos.args[0] is jogo._tela_composta
    assert argumentos.kwargs["interface"] is None


def test_hud_nativo_usa_area_16_por_9_e_reutiliza_canvas():
    jogo = Jogo()
    jogo.janela = pygame.Surface((900, 700))
    jogo.config["aspecto"] = "PREENCHE"

    jogo._desenhar_hud()
    primeira = jogo._hud_superficie_nativa
    jogo._desenhar_hud()

    assert primeira.get_size() == (900, 506)
    assert jogo._hud_superficie_nativa is primeira


def test_hud_nativo_recria_canvas_apenas_quando_muda_a_area():
    jogo = Jogo()
    jogo.janela = pygame.Surface((1920, 1080))
    jogo._desenhar_hud()
    anterior = jogo._hud_superficie_nativa

    jogo.janela = pygame.Surface((900, 700))
    jogo._desenhar_hud()

    assert jogo._hud_superficie_nativa.get_size() == (900, 506)
    assert jogo._hud_superficie_nativa is not anterior


def test_apresentador_cpu_compoe_hud_nativo_no_viewport():
    jogo = Jogo()
    jogo.janela = pygame.Surface((1280, 720))
    jogo.fade = 0
    jogo.flash = 0
    jogo._hud_superficie_nativa = pygame.Surface((1280, 720), pygame.SRCALPHA)
    jogo._hud_superficie_nativa.fill((0, 0, 0, 0))
    jogo._hud_superficie_nativa.set_at((40, 40), (240, 30, 50, 255))
    jogo._hud_nativo_pronto = True

    jogo._apresentar()

    assert jogo.janela.get_at((40, 40))[:3] == (240, 30, 50)


def test_hud_nativo_fica_abaixo_dos_fades_de_tela():
    jogo = Jogo()
    jogo.fade = 18
    jogo._hud_nativo_pronto = True

    assert not jogo._hud_nativo_visivel()


def test_status_do_shader_distingue_configuracao_e_fallback():
    jogo = Jogo()
    jogo._apresentador_gpu = None
    assert jogo.status_shader_comic() == "SEM GPU"

    jogo.config["shader_comic"] = False
    assert jogo.status_shader_comic() == "DESLIGADO"

    jogo.config["shader_comic"] = True
    jogo.config["estilo_visual"] = "ORIGINAL"
    assert jogo.status_shader_comic() == "INATIVO (ORIGINAL)"


def test_canvas_logico_16_por_9_preenche_full_hd_sem_barras():
    jogo = Jogo()
    jogo.janela = pygame.Surface((1920, 1080))

    escala, off_x, off_y = jogo._escala_janela()

    assert (jogo.tela.get_width(), jogo.tela.get_height()) == (1280, 720)
    assert escala == 1.5
    assert off_x == 0
    assert off_y == 0


def test_mira_alinha_com_mouse_nos_dois_modos_e_resolucoes_alvo():
    jogo = Jogo()
    jogo.estado = EstadoJogo.JOGANDO
    jogo.config["mira_ativa"] = True
    ponto_logico = (640, 360)

    for tamanho in ((900, 700), (1280, 720), (1920, 1080), (2560, 1080)):
        jogo.janela = pygame.Surface(tamanho)
        for modo in ("AJUSTAR", "PREENCHE"):
            jogo.config["aspecto"] = modo
            escala, off_x, off_y = jogo._transformacao_janela()
            ponto_janela = (round(ponto_logico[0] * escala + off_x),
                            round(ponto_logico[1] * escala + off_y))
            with mock.patch("pygame.mouse.get_pos", return_value=ponto_janela):
                assert jogo.posicao_mira() == ponto_logico


def test_flash_e_fade_da_troca_de_dimensao_alcancam_bordas_preenche():
    from src.runtime.presentation.dimension_transition import (
        INICIO_FLASH,
        TransicaoDimensional,
    )

    jogo = Jogo()
    jogo.janela = pygame.Surface((2560, 1080))
    jogo.config["aspecto"] = "PREENCHE"
    jogo.fade = 0
    jogo.tela.fill((20, 40, 60))
    jogo.tela_ui.fill((0, 0, 0, 0))
    fundo = pygame.Surface((2560, 1080))
    fundo.fill((10, 20, 30))
    jogo._obter_fundo_preenche = mock.Mock(return_value=fundo)
    jogo.cenario.desenhar = mock.Mock(
        side_effect=lambda tela: tela.fill((10, 20, 30)))
    jogo.particulas.desenhar = mock.Mock()
    transicao = TransicaoDimensional(jogo.cenario, (255, 255, 255))
    transicao.quadro = INICIO_FLASH + 4
    jogo.progressao_controller.transicao = transicao
    jogo.progressao_controller.frame_transicao()
    jogo._apresentar()
    pixel_borda = jogo.janela.get_at((20, 540))[:3]
    assert pixel_borda[0] > 10
    assert pixel_borda[1] > 20
    assert pixel_borda[2] > 30
    pixel_central = jogo.janela.get_at((1280, 540))[:3]
    assert all(valor > 10 for valor in pixel_central)

    jogo.progressao_controller.transicao = None
    jogo.fade = 255
    jogo.render_controller._desenhar_overlays_logicos()
    jogo._apresentar()
    assert jogo.janela.get_at((20, 540))[:3] == (0, 0, 0)
    assert max(jogo.janela.get_at((1280, 540))[:3]) <= 16


def test_shake_nao_desloca_a_borda_decorativa():
    jogo = Jogo()
    jogo.janela = pygame.Surface((2560, 1080))
    jogo.config["aspecto"] = "PREENCHE"
    jogo.fade = 0
    jogo.tela.fill((220, 30, 40))
    fundo = pygame.Surface((2560, 1080))
    fundo.fill((20, 170, 60))
    jogo._obter_fundo_preenche = mock.Mock(return_value=fundo)

    jogo._apresentar()
    antes = jogo.janela.get_at((20, 540))[:3]
    jogo.trauma = 1.0
    with mock.patch("src.runtime.controllers.render.random.uniform", return_value=20):
        jogo.render_controller.aplicar_shake()
    jogo._apresentar()

    assert jogo.janela.get_at((20, 540))[:3] == antes == (20, 170, 60)


def test_cache_das_bordas_reusa_superficies_e_libera_tamanhos_anteriores():
    import gc
    import weakref

    jogo = Jogo()
    jogo.config["aspecto"] = "PREENCHE"
    jogo.fade = 0
    jogo.janela = pygame.Surface((2560, 1080))
    jogo._apresentar()
    fundo = jogo._fundo_preenche
    superficie_escalada = jogo._superficie_escalada
    for _ in range(4):
        jogo._apresentar()
    assert jogo._fundo_preenche is fundo
    assert jogo._superficie_escalada is superficie_escalada
    jogo.config["estilo_visual"] = "COMIC"
    assert jogo._obter_fundo_preenche((2560, 1080)) is fundo

    referencia_antiga = weakref.ref(fundo)
    jogo.janela = pygame.Surface((1920, 1080))
    jogo._apresentar()
    assert jogo._fundo_preenche is not fundo
    del fundo
    gc.collect()
    assert referencia_antiga() is None


def test_redimensionar_e_alternar_tela_cheia_recria_cache_uma_vez():
    jogo = Jogo()
    jogo.config["aspecto"] = "PREENCHE"
    jogo.fade = 0
    jogo.config["resolucao"] = "1920x1080"
    jogo._liberar_apresentador_gpu = mock.Mock()
    jogo._criar_janela_video = mock.Mock(
        side_effect=lambda tamanho, flags: pygame.Surface(tamanho))

    for tela_cheia in (False, True, False, True):
        jogo.config["tela_cheia"] = tela_cheia
        jogo._aplicar_modo_video()
        janela = jogo.janela
        jogo._apresentar()
        fundo = jogo._fundo_preenche
        for _ in range(3):
            jogo._apresentar()
        assert jogo._fundo_preenche is fundo
        assert jogo.janela is janela


def test_modo_desempenho_troca_escala_somente_apos_atraso_sustentado():
    jogo = Jogo()
    jogo.config["qualidade_grafica"] = "EQUILIBRADA"
    for _ in range(8):
        jogo._atualizar_modo_desempenho(25)
    assert jogo._escala_rapida is True
    for _ in range(90):
        jogo._atualizar_modo_desempenho(8)
    assert jogo._escala_rapida is False


def test_modo_desempenho_reage_rapido_a_quedas_sustentadas():
    jogo = Jogo()
    jogo.config["qualidade_grafica"] = "EQUILIBRADA"
    for _ in range(3):
        jogo._atualizar_modo_desempenho(25)
    assert jogo._escala_rapida is False
    jogo._atualizar_modo_desempenho(25)
    assert jogo._escala_rapida is True


def test_qualidade_alta_nunca_troca_para_escala_pixelada():
    jogo = Jogo()
    jogo.config["qualidade_grafica"] = "ALTA"
    jogo._escala_rapida = True

    for _ in range(30):
        jogo._atualizar_modo_desempenho(25)

    assert jogo._escala_rapida is False
    assert jogo._quadros_lentos == 0


def test_qualidade_visual_e_aplicada_ao_mundo_e_as_particulas():
    jogo = Jogo()
    jogo.config["qualidade_grafica"] = "DESEMPENHO"

    jogo._aplicar_qualidade_grafica()

    assert jogo.cenario.qualidade == "DESEMPENHO"
    assert jogo.particulas.qualidade == "DESEMPENHO"


def test_aplicar_qualidade_alta_restaura_escala_suave_imediatamente():
    jogo = Jogo()
    jogo.config["qualidade_grafica"] = "ALTA"
    jogo._escala_rapida = True
    jogo._quadros_lentos = 4

    jogo._aplicar_qualidade_grafica()

    assert jogo._escala_rapida is False
    assert jogo._quadros_lentos == 0


def test_modo_opengl_tenta_habilitar_vsync():
    janela = pygame.Surface((900, 700))
    with mock.patch("src.runtime.application.core.pygame.display.set_mode",
                    return_value=janela) as set_mode:
        assert Jogo._criar_modo_com_vsync((900, 700), pygame.OPENGL) is janela
    set_mode.assert_called_once_with((900, 700), pygame.OPENGL, vsync=1)


def test_modo_video_usa_resolucao_escolhida_em_tela_cheia():
    jogo = Jogo()
    jogo.config["resolucao"] = "1024x768"
    jogo.config["tela_cheia"] = True
    jogo._criar_janela_video = mock.Mock(return_value=pygame.Surface((1920, 1080)))

    jogo._aplicar_modo_video()

    jogo._criar_janela_video.assert_called_once_with((1024, 768), pygame.FULLSCREEN)


def test_modo_tela_cheia_recusa_resolucao_que_o_monitor_nao_oferece():
    with mock.patch("src.runtime.application.core.pygame.display.list_modes",
                    return_value=[(1920, 1080)]):
        assert Jogo._modo_tela_cheia_disponivel((1280, 720)) is False


def test_inicio_restaura_janela_se_o_modo_salvo_nao_estiver_disponivel():
    config = Configuracoes()
    config["tela_cheia"] = True
    config["resolucao"] = "1920x1080"
    config.salvar = mock.Mock()
    janela = pygame.Surface((1920, 1080))

    with mock.patch.object(Jogo, "_criar_janela_video",
                           side_effect=[pygame.error(), janela]):
        jogo = Jogo(config=config)

    assert jogo.config["tela_cheia"] is False
    assert jogo.config["resolucao"] == "1920x1080"
    config.salvar.assert_called_once()

def test_desenha_estados():
    jogo = novo_jogo()
    jogo.progressao_controller.oferecer_melhorias(2)
    for estado in ("MENU", "JOGANDO", "MELHORIA", "PAUSA", "GAME_OVER", "PREPARANDO"):
        jogo.estado = estado
        jogo._desenhar()
    jogo.estado = "JOGANDO"
    jogo._desenhar_jogo()
    jogo._desenhar_hud()


def test_arsenal_desenha_catalogo_completo():
    jogo = novo_jogo()
    jogo.menu_equipamento = True
    jogo.jogador.armas_desbloqueadas = list(range(len(ARMARIA)))
    jogo.especiais_desbloqueados = ["bomba", "cura", "imortal"]
    jogo._desenhar_jogo()
    jogo._desenhar_carregando()
    jogo._desenhar_game_over()


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
