"""Contratos puros da rolagem, estados de avanço e configuração antiga."""

import json
from unittest.mock import patch

import pytest

from src.core import settings
from src.runtime.domain.world.scroll import (
    EstadoAvanco,
    ModeloAvanco,
    deslocamento_camada,
    faixas_repetidas,
)


def test_deslocamento_vertical_independe_da_mira() -> None:
    assert deslocamento_camada((0, 1), 120, 0.5, 1 / 60) == (0, 1)
    assert deslocamento_camada((1, 0), 120, 0.5, 1 / 60) == (1, 0)


def test_faixas_repetidas_cobrem_a_tela_sem_buracos() -> None:
    for deslocamento in (0, 1, 719, 720, 721, 10_000):
        faixas = faixas_repetidas(720, deslocamento)
        assert sum(altura for _, _, altura in faixas) == 720
        assert all(altura > 0 for _, _, altura in faixas)
        assert faixas[0][1] == 0
        assert faixas[-1][1] + faixas[-1][2] == 720


def test_frenagem_parada_aceleracao_e_pico() -> None:
    modelo = ModeloAvanco(120, freada=1, aceleracao=1, pico=0.25)
    modelo.boss_entrou()
    assert modelo.estado is EstadoAvanco.FREANDO
    modelo.atualizar(0.5)
    assert 0 < modelo.velocidade < 120
    modelo.atualizar(0.5)
    assert modelo.estado is EstadoAvanco.PARADO
    assert modelo.velocidade == 0
    modelo.boss_derrotado()
    assert modelo.estado is EstadoAvanco.ACELERANDO
    modelo.atualizar(0.75)
    assert modelo.velocidade > 0
    modelo.atualizar(0.25)
    assert modelo.velocidade > 120
    modelo.atualizar(0.25)
    assert modelo.estado is EstadoAvanco.AVANCANDO
    assert modelo.velocidade == 120


def test_boss_derrotado_durante_frenagem_reverte_sem_salto() -> None:
    modelo = ModeloAvanco(100, freada=2, aceleracao=1, pico=0)
    modelo.boss_entrou()
    modelo.atualizar(0.5)
    anterior = modelo.velocidade
    modelo.boss_derrotado()
    assert modelo.velocidade == pytest.approx(anterior)
    modelo.atualizar(0.1)
    assert modelo.velocidade > anterior


def test_pausa_congela_parado_e_transicao() -> None:
    modelo = ModeloAvanco(100, freada=1, aceleracao=1)
    modelo.boss_entrou()
    modelo.atualizar(1)
    assert modelo.estado is EstadoAvanco.PARADO
    modelo.atualizar(10, pausado=True)
    assert modelo.estado is EstadoAvanco.PARADO
    assert modelo.velocidade == 0


def test_troca_dimensao_durante_aceleracao_preserva_estado() -> None:
    modelo = ModeloAvanco(100, freada=1, aceleracao=1)
    modelo.boss_entrou()
    modelo.atualizar(1)
    modelo.boss_derrotado()
    modelo.atualizar(0.2)
    modelo.trocar_dimensao(200, duracao_salto=1, pico_salto=0.4)
    assert modelo.estado is EstadoAvanco.ACELERANDO
    assert modelo.velocidade > 0
    modelo.atualizar(0.2)
    assert modelo.velocidade > 0


def test_miniboss_reduz_ate_metade_e_retorna() -> None:
    modelo = ModeloAvanco(100, freada=1, aceleracao=1, pico=0)
    modelo.miniboss_entrou(0.5)
    modelo.atualizar(1)
    assert modelo.estado is EstadoAvanco.AVANCANDO
    assert modelo.velocidade == pytest.approx(50)
    modelo.miniboss_derrotado()
    modelo.atualizar(1)
    assert modelo.velocidade == pytest.approx(100)


def test_miniboss_a_cem_por_cento_nao_muda_estado_nem_velocidade() -> None:
    modelo = ModeloAvanco(100)
    modelo.miniboss_entrou(1)
    modelo.atualizar(2)
    assert modelo.estado is EstadoAvanco.AVANCANDO
    assert modelo.velocidade == 100


def test_config_antiga_recebe_padrao_e_preserva_valores(tmp_path) -> None:
    caminho = tmp_path / "settings.json"
    caminho.write_text(json.dumps({"tema": "AURORA"}), encoding="utf-8")
    with patch.object(settings, "ARQUIVO_CONFIG", str(caminho)):
        config = settings.Configuracoes()
        assert config["tema"] == "AURORA"
        assert config["avanco_direcao"] == [0, 1]
        assert config["avanco_qualidade"] == "MEDIA"
        assert config["avanco_miniboss_percentual"] == pytest.approx(0.5)
        assert config["avanco_desvio_parado"] > 0
        assert config["avanco_marcos"] is True
        assert config["avanco_evolucao_paleta"] is True
        assert config["avanco_ritmo_variavel"] is True
        assert config["avanco_semente"] is None
        assert config["avanco_marco_tamanho_max"] == 420


def test_config_avanco_mescla_dimensoes_e_limita_valores(tmp_path) -> None:
    caminho = tmp_path / "settings.json"
    caminho.write_text(json.dumps({
        "avanco_direcao": [1, 0],
        "avanco_qualidade": "ALTA",
        "avanco_velocidades": {"3": 188},
        "avanco_miniboss_percentual": 2,
        "avanco_miniboss_tipos": {"eco": -1},
    }), encoding="utf-8")
    with patch.object(settings, "ARQUIVO_CONFIG", str(caminho)):
        config = settings.Configuracoes()
    assert config["avanco_direcao"] == [1, 0]
    assert config["avanco_qualidade"] == "ALTA"
    assert config["avanco_velocidades"]["3"] == 188
    assert len(config["avanco_velocidades"]) == 6
    assert config["avanco_miniboss_percentual"] == 1
    assert config["avanco_miniboss_tipos"]["eco"] == 0


def test_config_percurso_limita_tamanho_e_ritmo(tmp_path) -> None:
    caminho = tmp_path / "settings.json"
    caminho.write_text(json.dumps({
        "avanco_marcos": False,
        "avanco_evolucao_paleta": "false",
        "avanco_ritmo_variavel": True,
        "avanco_semente": 9.5,
        "avanco_marco_tamanho_max": 5000,
        "avanco_ritmo_variacao": 0.9,
    }), encoding="utf-8")
    with patch.object(settings, "ARQUIVO_CONFIG", str(caminho)):
        config = settings.Configuracoes()

    assert config["avanco_marcos"] is False
    assert config["avanco_evolucao_paleta"] is False
    assert config["avanco_ritmo_variavel"] is True
    assert config["avanco_semente"] is None
    assert config["avanco_marco_tamanho_max"] == 1024
    assert config["avanco_ritmo_variacao"] == 0.2
