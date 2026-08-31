"""Contratos minimos para as APIs publicas do legado.

Estas verificacoes sao intencionalmente estruturais: mantem as assinaturas
documentadas sem acoplar os testes a detalhes de implementacao.
"""

from __future__ import annotations

import inspect
from collections.abc import Iterable

from game.bosses import Boss
from game.combat_controller import ControladorCombate
from game.enemies import Inimigo, InimigoEspecial
from game.particles import MensagemFlutuante, Particula, SistemaParticulas
from game.player import Jogador, SistemaCombo, Skin
from game.powerups import PowerUp
from game.weapons import Projetil


def _assert_api_anotada(classe: type, metodos: Iterable[str]) -> None:
    """Garante tipos de parametros e retorno em cada contrato publico."""
    for nome in metodos:
        assinatura = inspect.signature(getattr(classe, nome))
        assert assinatura.return_annotation is not inspect.Signature.empty, nome
        for parametro in assinatura.parameters.values():
            if parametro.name in {"self", "cls"}:
                continue
            assert parametro.annotation is not inspect.Parameter.empty, (
                f"{classe.__name__}.{nome}({parametro.name})")


def test_entidades_de_gameplay_expoem_contratos_tipados():
    _assert_api_anotada(Projetil, (
        "__init__", "atualizar", "atualizar_teleguiado", "refletir",
        "saiu_da_tela", "desenhar"))
    _assert_api_anotada(PowerUp, ("__init__", "atualizar", "aplicar", "desenhar"))
    _assert_api_anotada(Inimigo, (
        "__init__", "atualizar", "sofrer_dano", "desenhar"))
    _assert_api_anotada(InimigoEspecial, (
        "__init__", "acoes_carregado", "e_feito_ja_atirado",
        "desenhar_barra_carga", "desenhar"))
    _assert_api_anotada(Boss, (
        "__init__", "atualizar", "sofrer_dano", "desenhar"))


def test_jogador_e_componentes_expoem_contratos_tipados():
    _assert_api_anotada(Skin, ("__init__", "desenhar"))
    _assert_api_anotada(SistemaCombo, (
        "__init__", "adicionar_tiro", "get_bonus", "zerar"))
    _assert_api_anotada(Jogador, (
        "__init__", "equipar_skin", "atualizar", "atirar",
        "selecionar_arma", "sofrer_dano", "desenhar"))


def test_entidades_de_efeito_expoem_contratos_tipados():
    _assert_api_anotada(Particula, ("__init__", "atualizar", "desenhar"))
    _assert_api_anotada(SistemaParticulas, (
        "__init__", "explosao", "espiral", "estrela", "pulsacao", "mega",
        "explosao_dupla", "faiscas", "rastro", "chamas", "bolhas",
        "cristais", "relampago", "buraco_negro", "salto_dimensional",
        "espiral_revelacao", "atualizar", "desenhar", "limpar"))
    _assert_api_anotada(MensagemFlutuante, (
        "__init__", "atualizar", "desenhar"))


def test_controlador_de_combate_declara_dependencias_de_suas_operacoes():
    _assert_api_anotada(ControladorCombate, (
        "__init__", "distancia", "explodir_em_area", "efeitos_nova",
        "efeitos_bomba", "explodir_nova", "explodir_bomba",
        "explodir_inimigo", "drop_especial", "projetil_jogador_atinge"))
