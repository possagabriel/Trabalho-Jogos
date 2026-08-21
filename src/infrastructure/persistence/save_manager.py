"""SaveManager: JSON persistence for player progress.

Provides a clean interface over the save/records files, isolating file I/O
from the domain logic.

Migrated from game/save_system.py (``SistemaProgressao``) -- the full
progression and records system.
"""

import json
import os
from typing import Any, Dict, List, Optional

# Data directory -- can be overridden via env var for testing.
PASTA_DADOS = (os.environ.get("SPACEFURY_DATA_DIR")
               or os.path.join(os.path.dirname(os.path.dirname(
                   os.path.abspath(__file__))), "data"))
ARQUIVO_SAVE = os.path.join(PASTA_DADOS, "save.json")
ARQUIVO_RECORDES = os.path.join(PASTA_DADOS, "records.json")


def _novo_dados_padrao() -> Dict[str, Any]:
    """Return the default save data structure."""
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


class SaveManager:
    """Handles loading, saving and querying player progression data.

    Usage::

        sm = SaveManager()
        sm.jogador["moedas"] += 50
        sm.salvar()
    """

    def __init__(self, caminho_save: "str | None" = None,
                 caminho_recordes: "str | None" = None):
        self._caminho_save = caminho_save or ARQUIVO_SAVE
        self._caminho_recordes = caminho_recordes or ARQUIVO_RECORDES
        self.dados: Dict[str, Any] = self._carregar()

    # ------------------------------------------------------------------
    # Load / save
    # ------------------------------------------------------------------

    def _carregar(self) -> Dict[str, Any]:
        try:
            with open(self._caminho_save, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if "jogador" not in dados:
                raise ValueError
            return dados
        except (FileNotFoundError, json.JSONDecodeError, ValueError, OSError):
            return _novo_dados_padrao()

    def salvar(self) -> None:
        """Persist the current save data to disk."""
        os.makedirs(os.path.dirname(self._caminho_save), exist_ok=True)
        try:
            with open(self._caminho_save, "w", encoding="utf-8") as f:
                json.dump(self.dados, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Player data
    # ------------------------------------------------------------------

    @property
    def jogador(self) -> Dict[str, Any]:
        return self.dados["jogador"]

    def adicionar_moedas(self, quantidade: int) -> None:
        self.jogador["moedas"] += quantidade

    def adicionar_pontos(self, pontos: int) -> None:
        self.jogador["total_pontos"] += pontos

    # ------------------------------------------------------------------
    # Progression events
    # ------------------------------------------------------------------

    def registrar_fim_jogo(self, nivel_jogador: int, pontuacao: int,
                           moedas_jogo: int, tempo_partida: float,
                           inimigos_abates: int = 0,
                           cenario_atual: int = 1,
                           bosses_abates: int = 0) -> None:
        """Update stats and progression at game end."""
        jog = self.jogador
        jog["nivel_maximo"] = max(jog["nivel_maximo"], nivel_jogador)
        jog["total_pontos"] += pontuacao
        jog["moedas"] += (moedas_jogo +
                          self._moedas_fim_jogo(cenario_atual, bosses_abates))
        self.dados["estatisticas"]["inimigos_derrotados"] += inimigos_abates
        self.dados["estatisticas"]["tempo_total"] += int(tempo_partida)

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

    def _moedas_fim_jogo(self, cenario_atual: int,
                         bosses_abates: int) -> int:
        """End-of-game coin bonus (current scenario + bosses this run)."""
        return 50 * cenario_atual + 100 * bosses_abates

    def sincronizar_loja(self, moedas: int, skins_desbloqueadas: List[str],
                         skin_atual: str) -> None:
        """Copy shop state (coins/skins) into the save."""
        self.jogador["moedas"] = moedas
        self.jogador["skins_desbloqueadas"] = skins_desbloqueadas
        self.jogador["skin_atual"] = skin_atual

    # ------------------------------------------------------------------
    # Save existence / reset
    # ------------------------------------------------------------------

    def existe_save(self) -> bool:
        """Check if a valid save file exists on disk."""
        try:
            with open(self._caminho_save, "r", encoding="utf-8") as f:
                dados = json.load(f)
            return "jogador" in dados
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return False

    def resetar_progresso(self) -> None:
        """Zero the player's progress (keeps the default structure)."""
        self.dados = _novo_dados_padrao()

    # ------------------------------------------------------------------
    # High-scores / records
    # ------------------------------------------------------------------

    def carregar_recordes(self) -> List[Dict[str, Any]]:
        try:
            with open(self._caminho_recordes, "r", encoding="utf-8") as f:
                dados = json.load(f)
            lista = dados.get("recordes", [])
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return []
        lista.sort(key=lambda r: r.get("pontos", 0), reverse=True)
        return lista

    def salvar_recorde(self, nome: str, pontos: int, nivel: int,
                       skin: str) -> List[Dict[str, Any]]:
        registro = {"nome": nome, "pontos": pontos, "nivel": nivel,
                    "skin": skin}
        lista = self.carregar_recordes()
        lista.append(registro)
        lista.sort(key=lambda r: r.get("pontos", 0), reverse=True)
        lista = lista[:10]
        os.makedirs(os.path.dirname(self._caminho_recordes), exist_ok=True)
        try:
            with open(self._caminho_recordes, "w", encoding="utf-8") as f:
                json.dump({"recordes": lista}, f, ensure_ascii=False, indent=2)
        except OSError:
            pass
        return lista

    def melhor_pontuacao(self) -> int:
        lista = self.carregar_recordes()
        return lista[0]["pontos"] if lista else 0
