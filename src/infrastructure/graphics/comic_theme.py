"""Direção de arte e opções do estilo comic; nenhum estado de gameplay."""

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

TINTA = (13, 12, 16)
PAPEL = (229, 211, 167)
AREIA = (86, 77, 64)
SOMBRA = (38, 37, 39)
FERRUGEM = (144, 76, 48)
LARANJA = (255, 151, 42)
CIANO = (64, 226, 230)
CONTORNO = 3
FATOR_SOMBRA = 0.48
FATOR_LUZ = 0.32
NIVEIS = (0, 85, 170, 255)
PASSO_HACHURA = 7
PASSO_HALFTONE = 12
FONTE_COMIC = "Comic.ttf"  # Opcional: arquivo livre fornecido pelo usuário.
FONTE_SISTEMA = "dejavusans,liberationsans,arial"
RARIDADES = MappingProxyType({
    "comum": (239, 234, 217), "incomum": (99, 223, 99),
    "rara": (69, 159, 255), "epica": (196, 101, 244), "lendaria": LARANJA,
})
ELEMENTOS = MappingProxyType({
    "normal": PAPEL, "critico": LARANJA, "plasma": (196, 101, 244),
    "ion": CIANO, "laser": (99, 223, 99), "nova": (255, 93, 43),
})
RARIDADE_ARMAS = ("comum", "incomum", "incomum", "rara", "rara",
                  "epica", "epica", "lendaria", "lendaria")
PALETA_UI = {
    "primaria": LARANJA, "secundaria": CIANO, "terciaria": PAPEL,
    "detalhe": PAPEL, "fundo_painel": SOMBRA,
    "borda_forte": LARANJA, "borda_fraco": FERRUGEM,
}
FUNDOS = ((65, 66, 65), (66, 68, 75), (75, 61, 52),
          (62, 72, 65), (73, 58, 69), (81, 61, 50))


@dataclass(frozen=True)
class OpcoesVisuais:
    """Perfil imutável resolvido a partir das configurações existentes."""

    estilo: str = "COMIC"
    qualidade: str = "MEDIA"
    papel: bool = True
    halftone: bool = True
    hachuras: bool = True
    line_boil: bool = False

    @property
    def ativo(self) -> bool:
        """Indica se os helpers devem usar o desenho comic."""
        return self.estilo == "COMIC"


def carregar_opcoes(config: Mapping[str, Any] | Any) -> OpcoesVisuais:
    """Valida valores sem modificar ou gravar a configuração recebida.

    Args:
        config: Mapeamento ou Configuracoes com acesso por chave.
    """
    def ler(chave: str, padrao: Any) -> Any:
        try:
            return config[chave]
        except (KeyError, TypeError):
            return padrao

    estilo = ler("estilo_visual", "COMIC")
    qualidade = ler("qualidade_comic", "MEDIA")
    if estilo not in ("COMIC", "ORIGINAL"):
        estilo = "COMIC"
    if qualidade not in ("BAIXA", "MEDIA", "ALTA"):
        qualidade = "MEDIA"
    detalhes = qualidade != "BAIXA"
    return OpcoesVisuais(
        estilo, qualidade,
        detalhes and ler("comic_papel", True) is True,
        detalhes and ler("comic_halftone", True) is True,
        detalhes and ler("comic_hachuras", True) is True,
        qualidade == "ALTA" and ler("line_boil", False) is True,
    )


# O contexto dura somente a composição de um quadro, isolando jogos e previews.
_OPCOES = ContextVar("opcoes_comic", default=OpcoesVisuais(estilo="ORIGINAL"))


def opcoes_atuais() -> OpcoesVisuais:
    """Consulta o perfil da composição atual."""
    return _OPCOES.get()


@contextmanager
def usar_visual(config: Mapping[str, Any] | Any) -> Iterator[OpcoesVisuais]:
    """Ativa o estilo durante um desenho e restaura mesmo em caso de erro."""
    opcoes = carregar_opcoes(config)
    token = _OPCOES.set(opcoes)
    try:
        yield opcoes
    finally:
        _OPCOES.reset(token)
