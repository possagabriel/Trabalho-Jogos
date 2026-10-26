"""Contrato da mira: direção, dispersão e persistência retrocompatível."""

import json
import math
from unittest.mock import MagicMock, patch

import pygame

from src.core import settings
from src.core.constants import EstadoJogo
from src.runtime.application.core import Jogo
from src.runtime.domain.entities.player import Jogador
from src.runtime.domain.systems.aiming import (
    angulo_para_alvo,
    direcao_para_alvo,
    indice_sprite_direcional,
)


def test_direcao_normalizada_atinge_o_alvo() -> None:
    """Um disparo isolado atravessa exatamente o ponto indicado."""
    vx, vy = direcao_para_alvo((100, 200), (160, 120), 10)
    assert math.hypot(vx, vy) == 10
    assert (100 + vx * 10, 200 + vy * 10) == (160, 120)


def test_alvo_sobre_a_origem_mantem_disparo_vertical() -> None:
    assert direcao_para_alvo((50, 50), (50, 50), 8) == (0, -8)


def test_angulo_da_nave_aponta_para_os_quatro_lados() -> None:
    """O nariz da sprite segue a mesma direção do disparo."""
    origem = (100, 100)
    assert angulo_para_alvo(origem, (100, 0)) == 0
    assert angulo_para_alvo(origem, (200, 100)) == 90
    assert angulo_para_alvo(origem, (100, 200)) == 180
    assert angulo_para_alvo(origem, (0, 100)) == 270


def test_indice_direcional_arredonda_e_fecha_o_circulo() -> None:
    assert indice_sprite_direcional(0) == 0
    assert indice_sprite_direcional(90) == 12
    assert indice_sprite_direcional(359) == 0
    assert indice_sprite_direcional(-90) == 36


def test_jogador_guarda_direcao_sem_mudar_hitbox() -> None:
    jogador = Jogador()
    retangulo = jogador.rect.copy()
    jogador.atualizar_mira((jogador.x + 100, jogador.y - 20))
    assert jogador.angulo_mira == 90
    assert jogador.rect == retangulo
    jogador.atualizar_mira(None)
    assert jogador.angulo_mira is None


def test_arma_direcional_mira_no_mouse_e_fallback_vertical() -> None:
    jogador = Jogador()
    alvo = (jogador.x + 80, jogador.y - 20)
    tiro = jogador.atirar(alvo=alvo)[0]
    assert tiro.vel_x > 0
    assert tiro.vel_y == 0
    jogador.cooldown_tiro = 0
    legado = jogador.atirar()[0]
    assert (legado.vel_x, legado.vel_y) == (0, -8)


def test_duplo_e_espiral_distribuem_em_torno_da_mira() -> None:
    jogador = Jogador()
    alvo = (jogador.x, jogador.y - 120)
    jogador.arma_atual = 2
    duplo = jogador.atirar(alvo=alvo, dispersao_duplo_graus=8)
    assert len(duplo) == 2
    assert duplo[0].vel_x < 0 < duplo[1].vel_x
    assert math.isclose(duplo[0].vel_x, -duplo[1].vel_x)
    jogador.cooldown_tiro = 0
    jogador.arma_atual = 5
    espiral = jogador.atirar(alvo=alvo, dispersao_espiral_graus=15)
    assert len(espiral) == 3
    assert any(tiro.vel_x != 0 for tiro in espiral)


def test_ion_segue_mira_horizontal_e_mantem_fallback_vertical() -> None:
    jogador = Jogador()
    jogador.arma_atual = 6
    tiro = jogador.atirar(alvo=(jogador.x + 100, jogador.y))[0]
    assert (tiro.vel_x, tiro.vel_y) == (1, 0)
    assert (tiro.x, tiro.y) == (jogador.x + 20, jogador.y)
    jogador.cooldown_tiro = 0
    vertical = jogador.atirar()[0]
    assert (vertical.vel_x, vertical.vel_y) == (0, -1)
    assert (vertical.x, vertical.y) == (jogador.x, jogador.y - 20)


def test_save_antigo_ativa_mira_por_padrao(tmp_path) -> None:
    caminho = tmp_path / "settings.json"
    caminho.write_text(json.dumps({"tema": "AURORA"}), encoding="utf-8")
    with patch.object(settings, "ARQUIVO_CONFIG", str(caminho)):
        config = settings.Configuracoes()
        assert config["mira_ativa"] is True
        config["mira_ativa"] = False
        assert config.salvar()
        assert settings.Configuracoes()["mira_ativa"] is True  # ajuste por perfil


def test_posicao_da_mira_usa_conversao_da_janela() -> None:
    jogo = Jogo()
    jogo.estado = EstadoJogo.JOGANDO
    with patch.object(jogo.menu, "_pos_logica", return_value=(321, 200)) as converter:
        with patch("pygame.mouse.get_pos", return_value=(642, 400)):
            assert jogo.posicao_mira() == (321, 200)
    converter.assert_called_once_with((642, 400))
    jogo.config["mira_ativa"] = False
    assert jogo.posicao_mira() is None
    jogo.config["mira_ativa"] = True
    jogo.estado = EstadoJogo.PAUSA
    assert jogo.posicao_mira() is None


def test_cursor_do_sistema_so_some_durante_o_gameplay() -> None:
    jogo = Jogo()
    render = jogo.render_controller
    with patch("pygame.mouse.set_visible") as visibilidade:
        jogo.estado = EstadoJogo.JOGANDO
        render.sincronizar_cursor()
        visibilidade.assert_called_with(False)
        jogo.estado = EstadoJogo.PAUSA
        render.sincronizar_cursor()
        visibilidade.assert_called_with(True)
        jogo.estado = EstadoJogo.MENU
        render.sincronizar_cursor()
        visibilidade.assert_called_with(True)


def test_f3_alterna_debug_somente_na_partida() -> None:
    jogo = Jogo()
    jogo.estado = EstadoJogo.JOGANDO
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F3))
    jogo.loop_controller.tratar_eventos()
    assert jogo.debug_ativo is True
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F3))
    jogo.loop_controller.tratar_eventos()
    assert jogo.debug_ativo is False


def test_clique_atira_na_posicao_da_mira_e_aciona_pulso() -> None:
    jogo = Jogo()
    jogo.estado = EstadoJogo.JOGANDO
    jogo.fila_onda = ["soldado"]
    alvo = (jogo.jogador.x + 100, jogo.jogador.y - 20)
    teclas = MagicMock()
    teclas.__getitem__.return_value = False
    with patch("pygame.key.get_pressed", return_value=teclas), \
            patch("pygame.mouse.get_pressed", return_value=(True, False, False)), \
            patch.object(jogo, "posicao_mira", return_value=alvo), \
            patch.object(jogo.jogador, "atualizar"), \
            patch.object(jogo.sons, "tocar"):
        jogo._atualizar_jogando()
    tiros = [proj for proj in jogo.projeteis if proj.origem == "jogador"]
    assert tiros
    assert tiros[0].vel_x > 0
    assert tiros[0].vel_y == 0
    assert jogo.jogador.angulo_mira == 90
    assert jogo.mira.pulso > 0


def test_mira_nao_e_desenhada_em_pausa_ou_menu() -> None:
    jogo = Jogo()
    render = jogo.render_controller
    with patch.object(jogo, "_desenhar_jogo"), \
            patch.object(render, "desenhar_hud"), \
            patch.object(jogo, "_desenhar_pausa"), \
            patch.object(jogo.menu, "desenhar"), \
            patch.object(jogo, "_apresentar"), \
            patch("pygame.display.flip"), \
            patch.object(jogo, "posicao_mira", return_value=(200, 200)), \
            patch.object(jogo.mira, "desenhar") as desenhar_mira:
        jogo.estado = EstadoJogo.JOGANDO
        render.desenhar()
        desenhar_mira.assert_called_once()
        jogo.estado = EstadoJogo.PAUSA
        render.desenhar()
        jogo.estado = EstadoJogo.MENU
        render.desenhar()
        desenhar_mira.assert_called_once()


def test_configuracao_do_menu_alterna_mira_e_persiste() -> None:
    jogo = Jogo()
    menu = jogo.menu
    menu.config_selecao = [tipo for _, tipo in menu._linhas_config()].index("mira_ativa")
    with patch.object(jogo.config, "salvar") as salvar:
        menu._ajustar_config(1)
    assert jogo.config["mira_ativa"] is False
    salvar.assert_called_once()
