"""Balanceamento dos protocolos corporativos; tempos em segundos de simulação."""

from src.core.constants import ALTURA, AZUL, CIANO, DOURADO, LARANJA, ROSA, ROXO, VERDE

SPAWN = {"modo": "ondas", "intervalo": 3, "seed": None}
PADRAO = {
    "raio": 32, "nivel": 1, "escala_vida": 0.035,
    "mov": "centro", "ataques": [], "alvo_y": ALTURA * 0.22,
    "efeito": "explosao", "part_qtd": 20,
    "aviso": 1.2, "ativo": 1.8, "recuperacao": 2.5,
    "velocidade_entrada": 150, "velocidade_tiro": 4,
    "dimensoes": (1, 2, 3, 4, 5, 6),
}

CATALOGO = {
    "bastiao": {
        **PADRAO, "nome": "BASTIÃO // FIREWALL", "vida": 22, "peso": 10,
        "cor": CIANO, "lados": 6, "pontos": 180, "moedas": 25,
        "drop": "escudo", "vida_nucleo": 3,
        "dica": "Destrua os dois núcleos laterais; depois ataque o centro.",
    },
    "espectro": {
        **PADRAO, "nome": "ESPECTRO // BACKDOOR", "vida": 20, "peso": 5,
        "cor": ROXO, "lados": 4, "pontos": 220, "moedas": 30,
        "drop": "arma", "dimensoes": (2, 3, 4, 5, 6), "ativo": 1.0,
        "dica": "Saia da marca de salto e ataque quando ele retornar ao topo.",
    },
    "matriz": {
        **PADRAO, "nome": "MATRIZ // FORK", "vida": 26, "peso": 9,
        "cor": VERDE, "lados": 5, "pontos": 200, "moedas": 25,
        "drop": "vida", "limite_lacaios": 3,
        "dica": "Elimine as cópias; o núcleo recebe dano dobrado sem escolta.",
    },
    "censor": {
        **PADRAO, "nome": "CENSOR // OVERRIDE", "vida": 18, "peso": 4,
        "cor": ROSA, "lados": 3, "pontos": 240, "moedas": 35,
        "drop": "escudo", "dimensoes": (3, 4, 5, 6), "ativo": 2.0,
        "dica": "Movimento invertido durante o pulso; disparo e pausa preservados.",
    },
    "cartografo": {
        **PADRAO, "nome": "CARTÓGRAFO // QUARENTENA", "vida": 24, "peso": 8,
        "cor": LARANJA, "lados": 4, "pontos": 210, "moedas": 30,
        "drop": "vida", "aviso": 1.6, "raio_zona": 52,
        "dica": "Saia das zonas tracejadas antes da ativação.",
    },
    "eco": {
        **PADRAO, "nome": "ECO // MIRROR", "vida": 20, "peso": 6,
        "cor": AZUL, "lados": 6, "pontos": 230, "moedas": 35,
        "drop": "arma", "dimensoes": (2, 3, 4, 5, 6), "limite_copia": 5,
        "dica": "O último disparo alimenta a cópia; ofereça tiros simples e desvie.",
    },
    "cronista": {
        **PADRAO, "nome": "CRONISTA // CLOCK", "vida": 16, "peso": 3,
        "cor": DOURADO, "lados": 8, "pontos": 260, "moedas": 40,
        "drop": "arma", "aviso": 1.0, "ativo": 2.0, "recuperacao": 3.0,
        "dica": "Blindado durante a carga e a rajada; ataque na recuperação.",
    },
}
