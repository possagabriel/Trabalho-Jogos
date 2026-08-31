"""Sistema de progressao e salvamento em JSON."""

import json
import logging
import os

PASTA_DADOS = (os.environ.get("SPACEFURY_DATA_DIR")
               or os.path.join(os.path.dirname(os.path.dirname(
                   os.path.abspath(__file__))), "data"))
ARQUIVO_SAVE = os.path.join(PASTA_DADOS, "save.json")
ARQUIVO_RECORDES = os.path.join(PASTA_DADOS, "records.json")
LOGGER = logging.getLogger(__name__)


class SistemaProgressao:
    """Carrega e salva o progresso do jogador (moedas, skins, recordes)."""

    def __init__(self):
        self.dados = self._carregar()

    def _carregar(self):
        try:
            with open(ARQUIVO_SAVE, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if "jogador" not in dados:
                raise ValueError
            return dados
        except (FileNotFoundError, json.JSONDecodeError, ValueError, OSError):
            return self._novo_dados()

    def _novo_dados(self):
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
    def jogador(self):
        return self.dados["jogador"]

    def adicionar_moedas(self, quantidade):
        self.jogador["moedas"] += quantidade

    def adicionar_pontos(self, pontos):
        self.jogador["total_pontos"] += pontos

    def registrar_fim_jogo(self, jogador, tempo_partida, inimigos_abates=0,
                           cenario_atual=1, bosses_abates=0):
        """Atualiza estatisticas e progresso ao fim de uma partida."""
        dados = self.dados
        jog = self.jogador
        jog["nivel_maximo"] = max(jog["nivel_maximo"], jogador.nivel)
        jog["total_pontos"] += jogador.pontuacao
        jog["moedas"] += (jogador.moedas_jogo +
                          self._moedas_fim_jogo(cenario_atual, bosses_abates))
        dados["estatisticas"]["inimigos_derrotados"] += inimigos_abates
        dados["estatisticas"]["tempo_total"] += int(tempo_partida)

    def registrar_boss(self):
        self.jogador["bosses_derrotados"] += 1
        self.dados["estatisticas"]["bosses_derrotados"] += 1

    def desbloquear_cenario(self, cenario_id):
        if cenario_id not in self.jogador["cenarios_desbloqueados"]:
            self.jogador["cenarios_desbloqueados"].append(cenario_id)

    def desbloquear_skin(self, skin_id):
        if skin_id not in self.jogador["skins_desbloqueadas"]:
            self.jogador["skins_desbloqueadas"].append(skin_id)
            return True
        return False

    def salvar_arquivo(self):
        """Grava o save atual em disco."""
        return self._salvar(ARQUIVO_SAVE, self.dados)

    def _moedas_fim_jogo(self, cenario_atual, bosses_abates):
        """Bonus de moedas ao fim do jogo (cenario atual + bosses da partida)."""
        return 50 * cenario_atual + 100 * bosses_abates

    def sincronizar_loja(self, loja):
        """Copiar o estado da loja (moedas/skins) para o save."""
        self.jogador["moedas"] = loja.moedas
        self.jogador["skins_desbloqueadas"] = loja.lista_desbloqueadas()
        self.jogador["skin_atual"] = loja.skin_atual

    def _salvar(self, arquivo, dados):
        os.makedirs(PASTA_DADOS, exist_ok=True)
        try:
            with open(arquivo, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
        except OSError as erro:
            LOGGER.warning("Nao foi possivel salvar progresso em %s: %s", arquivo, erro)
            return False
        return True

    def existe_save(self):
        """Verifica se existe um save valido em disco."""
        try:
            with open(ARQUIVO_SAVE, "r", encoding="utf-8") as f:
                dados = json.load(f)
            return "jogador" in dados
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return False

    def resetar_progresso(self):
        """Zera o progresso do jogador (mantem a estrutura padrao)."""
        self.dados = self._novo_dados()

    @staticmethod
    def carregar_recordes():
        try:
            with open(ARQUIVO_RECORDES, "r", encoding="utf-8") as f:
                dados = json.load(f)
            lista = dados.get("recordes", [])
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return []
        lista.sort(key=lambda r: r.get("pontos", 0), reverse=True)
        return lista

    @staticmethod
    def salvar_recorde(nome, pontos, nivel, skin):
        registro = {"nome": nome, "pontos": pontos, "nivel": nivel,
                    "skin": skin}
        lista = SistemaProgressao.carregar_recordes()
        lista.append(registro)
        lista.sort(key=lambda r: r.get("pontos", 0), reverse=True)
        lista = lista[:10]
        os.makedirs(PASTA_DADOS, exist_ok=True)
        try:
            with open(ARQUIVO_RECORDES, "w", encoding="utf-8") as f:
                json.dump({"recordes": lista}, f, ensure_ascii=False, indent=2)
        except OSError as erro:
            LOGGER.warning("Nao foi possivel salvar recordes: %s", erro)
            return False
        return lista

    @staticmethod
    def melhor_pontuacao():
        lista = SistemaProgressao.carregar_recordes()
        return lista[0]["pontos"] if lista else 0
