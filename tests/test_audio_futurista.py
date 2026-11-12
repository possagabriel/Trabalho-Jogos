"""Regressões de áudio audível, identidade das armas e ausência de dispositivo."""

import io
import random
import struct
import wave
from collections import defaultdict
from unittest import mock

import pygame
import pytest

from src.runtime.application.core import Jogo
from src.runtime.domain.entities.player import Jogador
from src.runtime.domain.entities.weapons import ARMARIA
from src.runtime.domain.world.open_world import OpenWorldRuntime
from src.runtime.infrastructure.audio import sounds


def test_wav_converte_amplitude_normalizada_para_pcm() -> None:
    with wave.open(io.BytesIO(sounds._wav_bytes([0, 0.5, -0.5, 2, -2]))) as wav:
        assert wav.getframerate() == sounds.SAMPLE_RATE
        assert struct.unpack('<5h', wav.readframes(5)) == (0, 16383, -16383, 32767, -32767)


def test_todas_armas_tem_timbres_audiveis_distintos() -> None:
    gerenciador = sounds.Sons()
    assert gerenciador.habilitado
    dados = []
    for arma in ARMARIA:
        som = gerenciador._sons[f"tiro_{arma['tipo']}"]
        assert som.get_length() > 0.02
        bruto = som.get_raw()
        assert max(abs(v[0]) for v in struct.iter_unpack('<h', bruto)) > 1000
        dados.append(bruto)
    assert len(set(dados)) == len(ARMARIA)


def test_efeitos_preservam_volume_e_reutilizam_sons() -> None:
    gerenciador = sounds.Sons()
    gerenciador.set_volume_efeitos(0.3)
    for arma in ARMARIA:
        som = gerenciador._sons[f"tiro_{arma['tipo']}"]
        assert som.get_volume() == pytest.approx(0.3, abs=0.01)
        gerenciador.tocar(f"tiro_{arma['tipo']}")
        assert gerenciador._sons[f"tiro_{arma['tipo']}"] is som


def test_tiros_suaves_e_impacto_proprio_sem_pico_estridente() -> None:
    gerenciador = sounds.Sons()
    for arma in ARMARIA:
        dados = sounds._amostras_tiro(arma['tipo'])
        assert max(abs(v) for v in dados) <= 0.13
        assert abs(dados[0]) < 0.001
    impacto = gerenciador._sons['acerto']
    assert 0.07 <= impacto.get_length() <= 0.16
    pcm = [v[0] / 32767 for v in struct.iter_unpack('<h', impacto.get_raw())]
    assert 0.03 < max(abs(v) for v in pcm) <= 0.13
    assert impacto.get_raw() != gerenciador._sons['tiro_padrao'].get_raw()


def test_sem_dispositivo_de_audio_nao_interrompe_jogo() -> None:
    with mock.patch.object(pygame.mixer, 'init', side_effect=pygame.error('sem audio')):
        gerenciador = sounds.Sons()
    gerenciador.tocar('tiro_laser')
    gerenciador.set_volume_efeitos(0.4)
    gerenciador.set_volume_musica(0.4)
    gerenciador.pausar_musica()
    gerenciador.retomar_musica()
    assert not gerenciador.habilitado


def test_trilha_tem_headroom_loop_suave_e_nao_altera_sorteios() -> None:
    sounds.Sons._gerar_musica.cache_clear()
    estado = random.getstate()
    dados = sounds.Sons._gerar_musica()
    assert random.getstate() == estado
    assert 15 < len(dados) / sounds.SAMPLE_RATE < 20
    assert 0.1 < max(abs(v) for v in dados) < 0.8
    assert abs(dados[0]) < 0.001 and abs(dados[-1]) < 0.001
    assert sounds.Sons._gerar_musica() is dados


def test_combate_toca_arma_disparada_e_respeita_cooldown() -> None:
    jogo = Jogo()
    jogo._preparar_jogo()
    jogo.inimigos = []
    jogo.boss = None
    jogo.fila_onda = ['basico'] * 20
    jogo.timer_spawn = -100
    teclas = defaultdict(bool, {pygame.K_SPACE: True})
    with (mock.patch.object(pygame.key, 'get_pressed', return_value=teclas),
          mock.patch.object(jogo, 'posicao_mira', return_value=None),
          mock.patch.object(jogo, '_atualizar_projeteis'),
          mock.patch.object(jogo.sons, 'tocar') as tocar):
        for indice, arma in enumerate(ARMARIA):
            jogo.jogador.arma_atual = indice
            jogo.jogador.cooldown_tiro = 0
            tocar.reset_mock()
            jogo._atualizar_jogando()
            tocar.assert_called_once_with(f"tiro_{arma['tipo']}")
            tocar.reset_mock()
            jogo._atualizar_jogando()
            tocar.assert_not_called()


def test_mundo_aberto_toca_timbre_da_arma() -> None:
    mundo = OpenWorldRuntime()
    jogo = mock.Mock()
    jogo.menu_equipamento = False
    jogo.jogador = Jogador()
    jogo.posicao_mira.return_value = None
    jogo.config = {"dispersao_duplo_graus": 12, "dispersao_espiral_graus": 14}
    teclas = defaultdict(bool, {pygame.K_SPACE: True})
    with (mock.patch.object(mundo, '_place_hostiles_in_world'),
          mock.patch.object(mundo, '_update_world_encounters')):
        for indice, arma in enumerate(ARMARIA):
            jogo.jogador.arma_atual = indice
            jogo.jogador.cooldown_tiro = 0
            jogo.sons.tocar.reset_mock()
            mundo._update_combat(1 / 60, teclas, {}, jogo)
            jogo.sons.tocar.assert_called_once_with(f"tiro_{arma['tipo']}")
