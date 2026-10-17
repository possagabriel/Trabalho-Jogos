"""Catálogo validado e sequenciador puro de cenas narrativas."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

LOGGER = logging.getLogger(__name__)
TIPOS_PASSO = frozenset({
    "fala", "espera", "fade", "shake", "glitch", "retrato", "som", "musica", "titulo",
})
TIPOS_TEMPORIZADOS = frozenset({"espera", "fade", "shake", "glitch", "titulo"})


@dataclass(frozen=True)
class Cena:
    """Cena imutável identificada por um gatilho de gameplay."""

    id: str
    gatilho: str
    passos: tuple[dict[str, Any], ...]
    nome: str = ""


@dataclass(frozen=True)
class CatalogoCenas:
    """Índices de cenas e personagens prontos para consulta segura."""

    cenas: dict[str, Cena]
    personagens: dict[str, dict[str, str]]

    def cena(self, identificador: str) -> Cena | None:
        """Retorna uma cena conhecida ou None."""
        return self.cenas.get(identificador)

    def por_gatilho(self, gatilho: str) -> Cena | None:
        """Retorna a primeira cena do gatilho solicitado."""
        return next((cena for cena in self.cenas.values() if cena.gatilho == gatilho), None)


def _passo_valido(passo: Any, personagens: dict[str, dict[str, str]]) -> bool:
    if not isinstance(passo, dict) or passo.get("tipo") not in TIPOS_PASSO:
        return False
    tipo = passo["tipo"]
    if tipo == "fala":
        return (passo.get("personagem") in personagens
                and isinstance(passo.get("texto"), str) and bool(passo["texto"]))
    if tipo in TIPOS_TEMPORIZADOS:
        return isinstance(passo.get("duracao"), (int, float)) and passo["duracao"] >= 0
    if tipo == "retrato":
        return passo.get("personagem") in personagens and isinstance(passo.get("icone"), str)
    if tipo in ("som", "musica"):
        return isinstance(passo.get("acao"), str)
    return True


def carregar_catalogo(dados: Any) -> CatalogoCenas:
    """Valida dados externos e ignora cenas incorretas com aviso no log."""
    if not isinstance(dados, dict):
        LOGGER.warning("Catálogo de cenas inválido: raiz não é objeto")
        return CatalogoCenas({}, {})
    brutos = dados.get("personagens", {})
    personagens = {
        chave: valor for chave, valor in brutos.items()
        if isinstance(chave, str) and isinstance(valor, dict)
        and isinstance(valor.get("nome"), str) and isinstance(valor.get("retrato"), str)
    } if isinstance(brutos, dict) else {}
    cenas: dict[str, Cena] = {}
    entradas = dados.get("cenas", [])
    if not isinstance(entradas, list):
        LOGGER.warning("Catálogo de cenas inválido: cenas não é lista")
        return CatalogoCenas({}, personagens)
    for bruto in entradas:
        if not isinstance(bruto, dict):
            LOGGER.warning("Cena inválida: registro não é objeto")
            continue
        identificador = bruto.get("id")
        gatilho = bruto.get("gatilho")
        passos = bruto.get("passos")
        if (not isinstance(identificador, str) or not identificador
                or not isinstance(gatilho, str) or not gatilho
                or not isinstance(passos, list) or not passos
                or identificador in cenas):
            LOGGER.warning("Cena inválida ou duplicada: %r", identificador)
            continue
        invalidos = [p for p in passos if not _passo_valido(p, personagens)]
        if invalidos:
            LOGGER.warning("Cena %s ignorada: passo ou personagem ausente %r",
                           identificador, invalidos[0])
            continue
        nome = bruto.get("nome", identificador)
        cenas[identificador] = Cena(
            identificador, gatilho, tuple(passos),
            nome if isinstance(nome, str) else identificador,
        )
    return CatalogoCenas(cenas, personagens)


def ler_catalogo(caminho: str | Path) -> CatalogoCenas:
    """Lê JSON UTF-8 sem propagar falhas de arquivo ou dados."""
    try:
        with Path(caminho).open(encoding="utf-8") as arquivo:
            return carregar_catalogo(json.load(arquivo))
    except (OSError, ValueError, TypeError) as erro:
        LOGGER.warning("Não foi possível carregar roteiro %s: %s", caminho, erro)
        return CatalogoCenas({}, {})


class SequenciadorCena:
    """Executa passos por tempo fixo, sem conhecer Pygame ou o save."""

    def __init__(
        self, velocidade: float = 42,
        ao_concluir: Callable[[str], None] | None = None,
        ao_entrar: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.velocidade = max(1.0, float(velocidade))
        self.ao_concluir = ao_concluir
        self.ao_entrar = ao_entrar
        self.cena: Cena | None = None
        self.indice = 0
        self.tempo = 0.0
        self.pausado = False

    @property
    def ativo(self) -> bool:
        """Indica se existe uma cena em execução."""
        return self.cena is not None

    @property
    def passo(self) -> dict[str, Any] | None:
        """Retorna o passo atual, se houver."""
        return self.cena.passos[self.indice] if self.cena is not None else None

    @property
    def texto_visivel(self) -> str:
        """Revela a fala segundo a velocidade configurada."""
        passo = self.passo
        if passo is None or passo["tipo"] != "fala":
            return ""
        return passo["texto"][:int(self.tempo * self.velocidade)]

    def iniciar(self, cena: Cena) -> None:
        """Começa uma cena sem marcar persistência."""
        self.cena = cena
        self.indice = 0
        self.tempo = 0.0
        self.pausado = False
        self._entrar()

    def _entrar(self) -> None:
        while self.cena is not None:
            passo = self.passo
            if self.ao_entrar is not None:
                self.ao_entrar(passo)
            if passo["tipo"] not in ("retrato", "som", "musica"):
                break
            atual = self.cena
            self._proximo()
            if self.cena is not atual:
                return

    def _proximo(self) -> None:
        if self.cena is None:
            return
        self.indice += 1
        self.tempo = 0.0
        if self.indice >= len(self.cena.passos):
            self._finalizar(True)

    def atualizar(self, dt: float) -> None:
        """Atualiza o passo; pausa e tempo não positivo não avançam."""
        if not self.ativo or self.pausado or dt <= 0:
            return
        passo = self.passo
        self.tempo += dt
        if passo["tipo"] in TIPOS_TEMPORIZADOS and self.tempo >= passo["duracao"]:
            atual = self.cena
            self._proximo()
            if self.cena is atual:
                self._entrar()

    def confirmar(self) -> None:
        """Completa a fala atual ou segue ao próximo passo."""
        if not self.ativo or self.pausado:
            return
        passo = self.passo
        if passo["tipo"] == "fala" and self.texto_visivel != passo["texto"]:
            self.tempo = len(passo["texto"]) / self.velocidade
            return
        atual = self.cena
        self._proximo()
        if self.cena is atual:
            self._entrar()

    def pular(self) -> None:
        """Encerra intencionalmente e registra a cena como vista."""
        self._finalizar(True)

    def interromper(self) -> None:
        """Descarta uma cena interrompida sem marcar como vista."""
        self._finalizar(False)

    def _finalizar(self, concluida: bool) -> None:
        cena = self.cena
        self.cena = None
        if concluida and cena is not None and self.ao_concluir is not None:
            self.ao_concluir(cena.id)
