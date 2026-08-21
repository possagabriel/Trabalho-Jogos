"""ProgressionSystem - save/load and progression tracking.

Migrated from game/save_system.py SistemaProgressao.
"""

from __future__ import annotations

import json
import os
import random
from typing import Optional

PASTA_DADOS = (
    os.environ.get("SPACEFURY_DATA_DIR")
    or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "..", "data",
    )
)
ARQUIVO_SAVE = os.path.join(PASTA_DADOS, "save.json")
ARQUIVO_RECORDES = os.path.join(PASTA_DADOS, "records.json")


class ProgressionSystem:
    """Carries and saves player progression (coins, skins, records).

    Migrated from game/save_system.py SistemaProgressao.
    """

    def __init__(self) -> None:
        self.dados: dict = self._carregar()

    def _carregar(self) -> dict:
        try:
            with open(ARQUIVO_SAVE, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if "jogador" not in dados:
                raise ValueError
            return dados
        except (FileNotFoundError, json.JSONDecodeError, ValueError, OSError):
            return self._novo_dados()

    @staticmethod
    def _novo_dados() -> dict:
        return {
            "jogador": {
                "nome": "Jogador",
                "moedas": 0,
                "skins_desbloqueadas": ["padrao"],
                "skin_atual": "padrao",
                "total_pontos": 0,
                "bosses_derrotados": 0,
                "nivel_maximo": 1,
                "cenarios_desbloqueados": [1],
            },
            "estatisticas": {
                "inimigos_derrotados": 0,
                "bosses_derrotados": 0,
                "tiros_disparados": 0,
                "tempo_total": 0,
            },
        }

    @property
    def jogador(self) -> dict:
        return self.dados["jogador"]

    def adicionar_moedas(self, quantidade: int) -> None:
        self.jogador["moedas"] += quantidade

    def adicionar_pontos(self, pontos: int) -> None:
        self.jogador["total_pontos"] += pontos

    def registrar_fim_jogo(
        self,
        nivel: int,
        pontuacao: int,
        moedas_jogo: int,
        tempo_partida: float,
        inimigos_abates: int = 0,
        cenario_atual: int = 1,
        bosses_abates: int = 0,
    ) -> None:
        dados = self.dados
        jog = self.jogador
        jog["nivel_maximo"] = max(jog["nivel_maximo"], nivel)
        jog["total_pontos"] += pontuacao
        jog["moedas"] += moedas_jogo + self._moedas_fim_jogo(cenario_atual, bosses_abates)
        dados["estatisticas"]["inimigos_derrotados"] += inimigos_abates
        dados["estatisticas"]["tempo_total"] += int(tempo_partida)

    def registrar_boss(self) -> None:
        self.jogador["bosses_derrotados"] += 1
        self.dados["estatisticas"]["bosses_derrotados"] += 1

    def desbloquear_cenario(self, cenario_id: int) -> None:
        if cenario_id not in self.jogador["cenarios_desbloqueados"]:
            self.jogador["cenarios_desbloqueados"].append(cenario_id)

    def desbloquear_skin(self, skin_id: str) -> bool:
        if skin_id not in self.jogador["skins_desbloqueadas"]:
            self.jogador["skins_desbloqueadas"].append(skin_id)
            return True
        return False

    def salvar_arquivo(self) -> None:
        self._salvar(ARQUIVO_SAVE, self.dados)

    @staticmethod
    def _moedas_fim_jogo(cenario_atual: int, bosses_abates: int) -> int:
        return 50 * cenario_atual + 100 * bosses_abates

    def sincronizar_loja(
        self,
        moedas: int,
        skins_desbloqueadas: list[str],
        skin_atual: str,
    ) -> None:
        self.jogador["moedas"] = moedas
        self.jogador["skins_desbloqueadas"] = skins_desbloqueadas
        self.jogador["skin_atual"] = skin_atual

    def _salvar(self, arquivo: str, dados: dict) -> None:
        os.makedirs(PASTA_DADOS, exist_ok=True)
        try:
            with open(arquivo, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def existe_save(self) -> bool:
        try:
            with open(ARQUIVO_SAVE, "r", encoding="utf-8") as f:
                dados = json.load(f)
            return "jogador" in dados
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return False

    def resetar_progresso(self) -> None:
        self.dados = self._novo_dados()

    @staticmethod
    def carregar_recordes() -> list[dict]:
        try:
            with open(ARQUIVO_RECORDES, "r", encoding="utf-8") as f:
                dados = json.load(f)
            lista = dados.get("recordes", [])
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return []
        lista.sort(key=lambda r: r.get("pontos", 0), reverse=True)
        return lista

    @staticmethod
    def salvar_recorde(nome: str, pontos: int, nivel: int, skin: str) -> list[dict]:
        registro = {"nome": nome, "pontos": pontos, "nivel": nivel, "skin": skin}
        lista = ProgressionSystem.carregar_recordes()
        lista.append(registro)
        lista.sort(key=lambda r: r.get("pontos", 0), reverse=True)
        lista = lista[:10]
        os.makedirs(PASTA_DADOS, exist_ok=True)
        try:
            with open(ARQUIVO_RECORDES, "w", encoding="utf-8") as f:
                json.dump({"recordes": lista}, f, ensure_ascii=False, indent=2)
        except OSError:
            pass
        return lista

    @staticmethod
    def melhor_pontuacao() -> int:
        lista = ProgressionSystem.carregar_recordes()
        return lista[0]["pontos"] if lista else 0

    @staticmethod
    def sortear_tipo_powerup() -> str:
        return random.choices(
            ["escudo", "vida", "arma", "velocidade", "moedas"],
            [12, 28, 22, 14, 24],
        )[0]
