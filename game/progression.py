"""Dados e máquinas de estado da campanha INCARNATE.

O módulo não depende de pygame: pode ser usado pelas telas, pelo combate e
por ferramentas de conteúdo. Textos narrativos ficam separados dos estados.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


FASES = [
    {"id": 1, "nome": "PROTOCOLO 01", "fundo": "fundo-vermelho.png", "deterioracao": 1},
    {"id": 2, "nome": "PROTOCOLO 02", "fundo": "imagem-fundo3.png", "deterioracao": 2},
    {"id": 3, "nome": "PROTOCOLO 03", "fundo": "imagem-fundo4.png", "deterioracao": 2},
    {"id": 4, "nome": "PROTOCOLO 04", "fundo": "imagem-fundo5.png", "deterioracao": 3},
    {"id": 5, "nome": "PROTOCOLO 05", "fundo": "Fundo-roxo.png", "deterioracao": 4},
]

FRAGMENTOS: Dict[int, List[str]] = {
    1: ["fragmento_01_a", "fragmento_01_b"],
    2: ["fragmento_02_a", "fragmento_02_b"],
    3: ["fragmento_03_a", "fragmento_03_b"],
    4: ["fragmento_04_a", "fragmento_04_b"],
    5: ["fragmento_05_a", "fragmento_05_b"],
}


class EstadoSubBoss(str, Enum):
    IDLE = "idle"
    ATAQUE = "ataque"
    DERROTADO = "derrotado"


class EstadoBoss(str, Enum):
    FASE_1 = "fase_1"
    FASE_2 = "fase_2"
    DERROTADO = "derrotado"


@dataclass
class MaquinaSubBoss:
    fase: int
    estado: EstadoSubBoss = EstadoSubBoss.IDLE
    padrao: int = 0
    hp: float = 1
    hp_max: float = 1
    ataques_por_fase: List[dict] = field(default_factory=list)

    def atualizar(self, hp: Optional[float] = None) -> EstadoSubBoss:
        if hp is not None:
            self.hp = max(0, hp)
        if self.hp <= 0:
            self.estado = EstadoSubBoss.DERROTADO
        elif self.estado == EstadoSubBoss.IDLE:
            self.estado = EstadoSubBoss.ATAQUE
        return self.estado

    def sofrer_dano(self, dano: float) -> bool:
        self.atualizar(self.hp - dano)
        return self.estado == EstadoSubBoss.DERROTADO

    @property
    def ataque_atual(self) -> dict:
        if not self.ataques_por_fase:
            return {}
        return self.ataques_por_fase[self.padrao % len(self.ataques_por_fase)]


@dataclass
class MaquinaBoss:
    hp: float
    hp_max: float
    estado: EstadoBoss = EstadoBoss.FASE_1
    transicao: bool = False

    def sofrer_dano(self, dano: float) -> bool:
        self.hp = max(0, self.hp - dano)
        if self.hp <= 0:
            self.estado = EstadoBoss.DERROTADO
        elif self.estado == EstadoBoss.FASE_1 and self.hp <= self.hp_max * .5:
            self.estado = EstadoBoss.FASE_2
            self.transicao = True
        return self.estado == EstadoBoss.DERROTADO


class ProgressaoFases:
    def __init__(self, concluidas=None):
        self.concluidas = set(concluidas or [])

    def status(self, fase: int) -> str:
        if fase in self.concluidas:
            return "concluida"
        if fase == 1 or fase - 1 in self.concluidas:
            return "disponivel"
        return "bloqueada"

    def disponivel(self, fase: int) -> bool:
        return self.status(fase) != "bloqueada"

    def concluir(self, fase: int) -> bool:
        if not self.disponivel(fase):
            return False
        self.concluidas.add(fase)
        return True


class Codex:
    def __init__(self, fragmentos=None):
        self.fragmentos = set(fragmentos or [])

    def coletar(self, fragmento: str) -> None:
        self.fragmentos.add(fragmento)

    def revelado(self, fase: int) -> bool:
        return bool(self.fragmentos.intersection(FRAGMENTOS.get(fase, [])))

    def protocolo(self, fase: int) -> dict:
        dados = FASES[fase - 1]
        return {**dados, "status": "revelado" if self.revelado(fase) else "oculto",
                "fragmentos": [f for f in FRAGMENTOS.get(fase, [])
                               if f in self.fragmentos]}


FALAS_DERROTA = {
    "HEXAGONO": "A geometria... não sustenta mais o protocolo.",
    "LOSANGO": "O sinal atravessou a camada final.",
    "ESTRELA": "A luz residual foi transferida.",
    "PENTAGONO": "A contenção falhou. Continue.",
    "ANEIS": "O ciclo foi interrompido.",
    "ANEIS DOURADO": "Substituto... aguardando você.",
}


def novo_progresso() -> dict:
    return {"fases_concluidas": [], "subbosses_derrotados": [],
            "bosses_derrotados": [], "fragmentos": [], "decisao_final": None,
            "ending": None}
