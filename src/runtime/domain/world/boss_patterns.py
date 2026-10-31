"""Rotas independentes do jogador e padrões anunciados dos bosses do mundo aberto."""

import math


def posicao_patrulha(centro: tuple[float, float], tempo: float,
                     dimensao: int, fase: int) -> tuple[float, float]:
    """Percorre uma arena ampla sem usar a posição da nave como destino."""
    raio = 420 + dimensao * 30 + fase * 35
    direcao = -1 if dimensao % 2 else 1
    angulo = tempo * direcao * (0.32 + fase * 0.04)
    return (centro[0] + math.cos(angulo) * raio,
            centro[1] + math.sin(angulo * 1.3) * raio * 0.8)


def descricao_padrao(dimensao: int) -> str:
    """Explica a ação de esquiva própria de cada dimensão."""
    return (
        "LEQUE // SAIA DA LINHA", "CRUZ // USE AS DIAGONAIS",
        "ANEL // BUSQUE A ABERTURA", "PINÇA // PASSE PELO CENTRO",
        "ESPIRAL // MUDE DE FAIXA", "COROA // BUSQUE O CORREDOR",
    )[(dimensao - 1) % 6]


def angulos_ataque(dimensao: int, fase: int, mira: float) -> tuple[float, ...]:
    """Retorna exatamente as direções mostradas no aviso anterior ao disparo."""
    fase = max(1, min(3, fase))
    quantidade = 1 + fase * 2
    if dimensao == 1:
        return tuple(mira + (i - quantidade // 2) * 0.18 for i in range(quantidade))
    if dimensao == 2:
        return tuple(mira + math.pi / 4 + i * math.pi / 2 + desvio
                     for i in range(4) for desvio in ((0.0,) if fase == 1 else (-0.12, 0.12)))
    if dimensao in (3, 6):
        total = (14 if dimensao == 6 else 10) + fase * 2
        return tuple(mira + i * math.tau / total for i in range(2, total - 1))
    if dimensao == 4:
        return tuple(mira + lado * (0.3 + i * 0.16)
                     for lado in (-1, 1) for i in range(fase + 1))
    return tuple(mira + i * math.tau / (5 + fase) for i in range(5 + fase))
