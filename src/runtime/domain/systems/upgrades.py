"""Catálogo e aplicação dos módulos escolhidos entre setores."""

from __future__ import annotations

import random
from dataclasses import dataclass

from src.runtime.domain.entities.player import Jogador


@dataclass(frozen=True)
class DefinicaoMelhoria:
    """Texto apresentado ao jogador e limite de instalação do módulo."""

    nome: str
    descricao: str
    custo: str = ""
    limite: int | None = None


MELHORIAS = {
    "potencia": DefinicaoMelhoria("MUNIÇÃO PESADA", "+1 de dano em todos os disparos"),
    "cadencia": DefinicaoMelhoria("CICLO ACELERADO", "12% menos intervalo entre tiros"),
    "motor": DefinicaoMelhoria("MOTOR VETORIAL", "+8% de velocidade de movimento"),
    "blindagem": DefinicaoMelhoria("BLINDAGEM", "+1 de vida máxima e reparo imediato"),
    "escudo": DefinicaoMelhoria("ESCUDO DE FENDA", "Recebe um escudo protetor"),
    "especial": DefinicaoMelhoria("REATOR VORTEX", "+25% de carga especial por abate"),
    "reator_instavel": DefinicaoMelhoria(
        "REATOR INSTÁVEL", "+2 dano por disparo", "-1 vida máxima", 2),
    "blindagem_pesada": DefinicaoMelhoria(
        "BLINDAGEM PESADA", "+2 vida máxima e cura", "Esquiva 30% mais lenta", 2),
    "motor_emergencia": DefinicaoMelhoria(
        "MOTOR DE EMERGÊNCIA", "Esquiva 25% mais rápida", "Tiros 20% mais lentos", 2),
}
MELHORIAS_COM_CUSTO = {
    chave: definicao for chave, definicao in MELHORIAS.items() if definicao.custo
}


def sortear_melhorias(jogador: Jogador) -> list[str]:
    """Sorteia duas escolhas comuns e uma de risco, quando disponível."""
    comuns = [chave for chave, definicao in MELHORIAS.items() if not definicao.custo]
    arriscadas = [
        chave for chave, definicao in MELHORIAS_COM_CUSTO.items()
        if (definicao.limite is None
            or jogador.melhorias.get(chave, 0) < definicao.limite)
    ]
    escolhidas = random.sample(comuns, 2)
    terceira = (random.choice(arriscadas) if arriscadas else
                random.choice([chave for chave in comuns if chave not in escolhidas]))
    escolhidas.append(terceira)
    random.shuffle(escolhidas)
    return escolhidas


def aplicar_melhoria(jogador: Jogador, chave: str) -> bool:
    """Instala um módulo válido e aplica benefício e custo uma única vez."""
    definicao = MELHORIAS.get(chave)
    if definicao is None:
        return False
    nivel = jogador.melhorias.get(chave, 0)
    if definicao.limite is not None and nivel >= definicao.limite:
        return False
    jogador.melhorias[chave] = nivel + 1
    if chave == "potencia":
        jogador.bonus_dano += 1
    elif chave == "cadencia":
        jogador.multiplicador_cadencia = max(0.55, jogador.multiplicador_cadencia * 0.88)
    elif chave == "motor":
        jogador.multiplicador_velocidade *= 1.08
    elif chave == "blindagem":
        jogador.max_vida += 1
        jogador.vida = min(jogador.max_vida, jogador.vida + 1)
    elif chave == "escudo":
        jogador.escudo = True
    elif chave == "especial":
        jogador.multiplicador_especial *= 1.25
    elif chave == "reator_instavel":
        jogador.bonus_dano += 2
        jogador.max_vida = max(2, jogador.max_vida - 1)
        jogador.vida = min(jogador.vida, jogador.max_vida)
    elif chave == "blindagem_pesada":
        jogador.max_vida += 2
        jogador.vida = min(jogador.max_vida, jogador.vida + 2)
        jogador.multiplicador_recarga_esquiva *= 1.3
    elif chave == "motor_emergencia":
        jogador.multiplicador_recarga_esquiva *= 0.75
        jogador.multiplicador_cadencia *= 1.2
    return True
