"""Identidade dos capítulos LINEAR; ordem estável para checkpoints legados."""

from collections.abc import Mapping
from typing import Any

FASES_CAMPANHA = (
    ("lealdade", "Lealdade", "fases/lealdade.png"),
    ("funcao", "Função", "fases/funcao.png"),
    ("identidade", "Identidade", "fases/identidade.png"),
    ("silencio", "Silêncio", "fases/silencio.png"),
    ("descarte", "Descarte", "fases/descarte.png"),
    ("plano_divino", "Plano Divino", "imagem-fundo4.png"),
    ("ion", "Cinturão de Íons", "procedural:7"),
    ("arquivo", "Arquivo Estelar", "procedural:8"),
    ("horizonte", "Horizonte Fractal", "procedural:9"),
)


def fases_liberadas(jogador: Mapping[str, Any]) -> tuple[int, ...]:
    """Recupera conquistas permanentes e progresso legado sem modificar o save.

    Args:
        jogador: Dados persistentes do piloto, incluindo a campanha atual.
    """
    total = len(FASES_CAMPANHA)
    ids = {fase[0]: i for i, fase in enumerate(FASES_CAMPANHA, 1)}
    liberadas = {1}

    def incluir(valor: object, concluida: bool = False) -> None:
        ordem = valor if type(valor) is int else ids.get(valor) if isinstance(valor, str) else None
        if ordem is not None and 1 <= ordem <= total:
            liberadas.update(range(1, min(total, ordem + int(concluida)) + 1))

    for chave in ("fases_liberadas", "cenarios_desbloqueados"):
        valores = jogador.get(chave, ())
        if isinstance(valores, (list, tuple)):
            for valor in valores:
                incluir(valor)
    campanha = jogador.get("progresso_campanha", {})
    campanha = campanha if isinstance(campanha, dict) else {}
    concluidas = campanha.get("fases_concluidas", ())
    if isinstance(concluidas, (list, tuple)):
        for valor in concluidas:
            incluir(valor, concluida=True)
    incluir(campanha.get("fase_atual"))
    for nivel in (jogador.get("nivel_maximo", 1), campanha.get("nivel_atual", 1)):
        if type(nivel) is int and nivel > 0:
            incluir(min(total, (nivel - 1) // 5 + 1))
    return tuple(sorted(liberadas))
