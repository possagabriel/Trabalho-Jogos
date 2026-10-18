"""Sistema de progressao e salvamento em JSON."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

from src.shared.persistence import carregar_json_resiliente, salvar_json_atomico
from src.shared.user_data import diretorio_dados

if TYPE_CHECKING:
    from src.domain.systems.profile_service import ProfileService

PASTA_DADOS = diretorio_dados()
ARQUIVO_SAVE = os.path.join(PASTA_DADOS, "save.json")
ARQUIVO_RECORDES = os.path.join(PASTA_DADOS, "records.json")
VERSAO_SAVE = 2


class SistemaProgressao:
    """Carrega e salva o progresso do jogador (moedas, skins, recordes)."""

    def __init__(self):
        self.dados = self._carregar()

    def _carregar(self):
        try:
            dados = carregar_json_resiliente(ARQUIVO_SAVE)
            if not isinstance(dados, dict) or not isinstance(dados.get("jogador"), dict):
                raise ValueError
            migrado = self._mesclar_padrao(self._novo_dados(), dados)
            migrado["versao"] = VERSAO_SAVE
            return migrado
        except (FileNotFoundError, json.JSONDecodeError, ValueError, OSError):
            return self._novo_dados()

    def _novo_dados(self):
        return {
            "versao": VERSAO_SAVE,
            "jogador": {
                "nome": "Jogador",
                "moedas": 0,
                "skins_desbloqueadas": ["padrao"],
                "skin_atual": "padrao",
                "total_pontos": 0,
                "bosses_derrotados": 0,
                "minibosses_derrotados": 0,
                "nivel_maximo": 1,
                "cenarios_desbloqueados": [1],
                "progresso_campanha": {
                    "fases_concluidas": [], "subbosses_derrotados": [],
                    "bosses_derrotados": [], "fragmentos": [],
                    "indice_fases": {}, "decisao_final": None,
                    "ending": None, "fase_atual": "lealdade",
                    "nivel_atual": 1, "cenas_vistas": [],
                },
            },
            "estatisticas": {
                "minibosses_derrotados": 0,
                "minibosses_por_tipo": {},
                "inimigos_derrotados": 0,
                "bosses_derrotados": 0,
                "tiros_disparados": 0,
                "tempo_total": 0,
            },
        }

    @property
    def jogador(self):
        return self.dados["jogador"]

    @property
    def campanha(self):
        """Estado persistente da campanha, incluindo fases e codex."""
        return self.jogador.setdefault("progresso_campanha", {})

    @property
    def cenas_vistas(self) -> list[str]:
        """IDs únicos de cenas concluídas ou puladas em save antigo ou atual."""
        atual = self.campanha.get("cenas_vistas", [])
        if not isinstance(atual, list):
            atual = []
        atual = list(dict.fromkeys(item for item in atual if isinstance(item, str)))
        self.campanha["cenas_vistas"] = atual
        return atual

    def marcar_cena_vista(self, identificador: str) -> None:
        """Persiste uma cena apenas após conclusão explícita."""
        if identificador not in self.cenas_vistas:
            self.campanha["cenas_vistas"].append(identificador)
            self.salvar_arquivo()

    @staticmethod
    def _mesclar_padrao(padrao, salvo):
        """Completa saves antigos sem descartar campos desconhecidos."""
        if isinstance(padrao, dict) and not isinstance(salvo, dict):
            return padrao
        if not isinstance(padrao, dict):
            return salvo
        resultado = {
            chave: SistemaProgressao._mesclar_padrao(valor, salvo[chave])
            if chave in salvo else valor
            for chave, valor in padrao.items()
        }
        resultado.update({chave: valor for chave, valor in salvo.items()
                          if chave not in resultado})
        return resultado

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

    def registrar_miniboss(self, chave: str) -> None:
        """Registra derrota separada dos bosses e da progressão de dimensões."""
        self.jogador["minibosses_derrotados"] += 1
        estatisticas = self.dados["estatisticas"]
        estatisticas["minibosses_derrotados"] += 1
        contagens = estatisticas["minibosses_por_tipo"]
        contagens[chave] = contagens.get(chave, 0) + 1

    def resetar_fases(self):
        """Inicia campanha preservando memórias já desbloqueadas no perfil."""
        vistas = list(self.cenas_vistas)
        self.jogador["progresso_campanha"] = {
            "fases_concluidas": [], "subbosses_derrotados": [],
            "bosses_derrotados": [], "fragmentos": [], "indice_fases": {},
            "decisao_final": None, "ending": None, "fase_atual": "lealdade",
            "nivel_atual": 1, "cenas_vistas": vistas,
        }
        self.jogador["nivel_maximo"] = 1
        self.jogador["cenarios_desbloqueados"] = [1]
        self.salvar_arquivo()

    def registrar_checkpoint(self, nivel: int) -> None:
        """Guarda a fase e o nivel que devem ser retomados no Lobby."""
        nivel = max(1, int(nivel))
        fases = ["lealdade", "funcao", "identidade", "silencio", "descarte"]
        indice = min((nivel - 1) // 5, len(fases) - 1)
        self.campanha["fase_atual"] = fases[indice]
        self.campanha["nivel_atual"] = nivel

    def registrar_fase_concluida(self, nivel_boss: int) -> None:
        """Marca a fase do boss como concluida e libera a proxima no Lobby."""
        ordem = max(1, (int(nivel_boss) - 1) // 5 + 1)
        concluidas = self.campanha.setdefault("fases_concluidas", [])
        if ordem not in concluidas:
            concluidas.append(ordem)
        self.registrar_checkpoint(int(nivel_boss) + 1)

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

    def exportar_progresso(self, caminho):
        """Exporta um save portátil para outro sistema operacional."""
        return salvar_json_atomico(caminho, self.dados, criar_backup=False)

    def importar_progresso(self, caminho):
        """Importa um save válido sem substituir o atual em caso de erro."""
        try:
            dados = carregar_json_resiliente(caminho)
            if not isinstance(dados, dict) or not isinstance(dados.get("jogador"), dict):
                return False
            migrado = self._mesclar_padrao(self._novo_dados(), dados)
            migrado["versao"] = VERSAO_SAVE
        except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
            return False
        anterior = self.dados
        self.dados = migrado
        if self.salvar_arquivo():
            return True
        self.dados = anterior
        return False

    def _moedas_fim_jogo(self, cenario_atual, bosses_abates):
        """Bonus de moedas ao fim do jogo (cenario atual + bosses da partida)."""
        return 50 * cenario_atual + 100 * bosses_abates

    def sincronizar_loja(self, loja):
        """Copiar o estado da loja (moedas/skins) para o save."""
        self.jogador["moedas"] = loja.moedas
        self.jogador["skins_desbloqueadas"] = loja.lista_desbloqueadas()
        self.jogador["skin_atual"] = loja.skin_atual

    def _salvar(self, arquivo, dados):
        return salvar_json_atomico(arquivo, dados)

    def existe_save(self):
        """Verifica se existe um save valido em disco."""
        try:
            dados = carregar_json_resiliente(ARQUIVO_SAVE)
            return "jogador" in dados
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return False

    def resetar_progresso(self):
        """Zera o progresso do jogador (mantem a estrutura padrao)."""
        self.dados = self._novo_dados()

    @staticmethod
    def carregar_recordes():
        try:
            dados = carregar_json_resiliente(ARQUIVO_RECORDES)
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
        if not salvar_json_atomico(ARQUIVO_RECORDES, {"recordes": lista}):
            return False
        return lista

    @staticmethod
    def melhor_pontuacao():
        lista = SistemaProgressao.carregar_recordes()
        return lista[0]["pontos"] if lista else 0


class ProgressoPerfil(SistemaProgressao):
    """Adapta o contrato de progresso existente ao perfil ativo."""

    def __init__(self, service: ProfileService) -> None:
        self.service = service
        self.dados = self._novo_dados()
        self.carregar_ativo()

    def carregar_ativo(self) -> None:
        """Troca o estado em memória pelo do perfil selecionado."""
        profile = self.service.active
        if profile is None:
            self.dados = self._novo_dados()
            return
        saved = profile.progress.get("legacy", {})
        self.dados = self._mesclar_padrao(self._novo_dados(), saved)
        jog = self.jogador
        progress = profile.progress
        jog["nome"] = profile.name
        for old, new in (("moedas", "moedas"), ("skins_desbloqueadas", "skins_desbloqueadas"),
                         ("skin_atual", "skin_atual"), ("nivel_maximo", "nivel_maximo"),
                         ("total_pontos", "total_pontos")):
            jog[old] = progress[new]
        self.campanha["cenas_vistas"] = list(progress["cenas_vistas"])

    def resetar_progresso(self) -> None:
        """Reinicia somente o progresso do perfil selecionado."""
        from src.domain.profiles import initial_progress

        if self.service.active:
            self.service.active.progress = initial_progress()
        self.dados = self._novo_dados()

    def salvar_arquivo(self) -> bool:
        """Persiste progresso no perfil; não grava save.json legado."""
        if self.service.active is None:
            return False
        from src.domain.profiles import MAX_MONEY

        jog = self.jogador
        money = jog.get("moedas")
        if type(money) is not int or not 0 <= money <= MAX_MONEY:
            self.service.dirty = True
            self.service.save_error = True
            return False
        progress = self.service.active.progress
        progress.update({
            "moedas": jog["moedas"],
            "skins_desbloqueadas": list(jog["skins_desbloqueadas"]),
            "skin_atual": jog["skin_atual"],
            "nivel_maximo": jog["nivel_maximo"],
            "total_pontos": jog["total_pontos"],
            "dimensao_maxima": max(jog.get("cenarios_desbloqueados", [1]) or [1]),
            "cenas_vistas": list(self.cenas_vistas),
            "memorias_desbloqueadas": list(self.cenas_vistas),
            "tempo_total": self.dados["estatisticas"].get("tempo_total", 0),
            "inimigos_derrotados": self.dados["estatisticas"].get("inimigos_derrotados", 0),
            "legacy": self.dados,
        })
        return self.service._save()

    def existe_save(self) -> bool:
        """Perfil ativo equivale ao save selecionado."""
        return self.service.active is not None

    def registrar_recorde(self, nome: str, pontos: int, nivel: int,
                         skin: str) -> list[dict]:
        """Mantém recordes exclusivamente no perfil ativo."""
        progress = self.service.active.progress if self.service.active else self.dados.setdefault(
            "_recordes_em_memoria", {"recordes": [], "recorde_pontos": 0})
        records = progress["recordes"]
        records.append({"nome": nome, "pontos": pontos, "nivel": nivel, "skin": skin})
        records.sort(key=lambda row: row.get("pontos", 0), reverse=True)
        del records[10:]
        progress["recorde_pontos"] = max(progress["recorde_pontos"], pontos)
        if self.service.active:
            self.service._save()
        return records

    def carregar_recordes_perfil(self) -> list[dict]:
        """Devolve recordes somente do perfil ativo."""
        return (self.service.active.progress["recordes"] if self.service.active else
                self.dados.get("_recordes_em_memoria", {}).get("recordes", []))

    def melhor_pontuacao_perfil(self) -> int:
        """Devolve recorde pessoal."""
        return (self.service.active.progress["recorde_pontos"] if self.service.active else
                self.dados.get("_recordes_em_memoria", {}).get("recorde_pontos", 0))
