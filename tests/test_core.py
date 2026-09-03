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
os.environ["SPACEFURY_DATA_DIR"] = tempfile.mkdtemp(prefix="spacefury_test_")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import random  # noqa: E402
from unittest import mock  # noqa: E402

import pygame  # noqa: E402

from game.config import ALTURA, EstadoJogo, LARGURA  # noqa: E402
from game.combat_session import SessaoCombate  # noqa: E402
from game.core import Jogo  # noqa: E402
from game.game_over_controller import ControladorGameOver  # noqa: E402
from game.loop_controller import ControladorLoop  # noqa: E402
from game.pause_controller import ControladorPausa  # noqa: E402
from game.render_controller import ControladorRenderizacao  # noqa: E402
from game.enemies import Inimigo, InimigoEspecial  # noqa: E402
from game.powerups import PowerUp  # noqa: E402
from game.weapons import ARMARIA, Projetil  # noqa: E402


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
    assert jogo.estado == "JOGANDO"
    assert jogo.carregamento == 100


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
    assert jogo.novo_recorde is False


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
# Desenho
# ---------------------------------------------------------------------------

def test_desenha_estados():
    jogo = novo_jogo()
    for estado in ("MENU", "JOGANDO", "PAUSA", "GAME_OVER", "PREPARANDO"):
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
