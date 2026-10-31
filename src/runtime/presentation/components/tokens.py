"""Tokens visuais do kit de UI, resolvidos por estilo e tema.

Os valores estruturais usam "design px" (base 900x700) e devem ser
convertidos pelos componentes com ``Layout.px``. As cores nunca são
hardcoded nas telas: ORIGINAL usa superfícies sóbrias com acento do tema e COMIC
usa a paleta de papel e tinta.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.core.constants import BRANCO, VOID_BLACK
from src.infrastructure.graphics.comic_theme import (
    AREIA,
    CIANO,
    LARANJA,
    PAPEL,
    SOMBRA,
    TINTA,
    opcoes_atuais,
)
from src.infrastructure.graphics.theme import (
    DEFAULT_TEMA,
    MENU_COR_TEXTO,
    MENU_COR_TEXTO_DESABILITADO,
    MENU_COR_TEXTO_SECUNDARIO,
    TEMAS_CORES,
)
from src.runtime.infrastructure.graphics.menu_panels import (
    BORDA_SOBRIA,
    FOCO_SOBRIO,
    FUNDO_SOBRIO,
    PAINEL_SOBRIO,
    TEXTO_SOBRIO,
)

ESTILO_ORIGINAL = "ORIGINAL"
ESTILO_COMIC = "COMIC"


@dataclass(frozen=True)
class EspacamentoTokens:
    """Escala de espaçamento em design px."""

    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 18
    xl: int = 24
    xxl: int = 32


@dataclass(frozen=True)
class TipografiaTokens:
    """Tamanhos de referência em design px."""

    titulo_tela: int = 38
    titulo_painel: int = 24
    subtitulo: int = 18
    corpo: int = 20
    valor: int = 22
    legenda: int = 18


@dataclass(frozen=True)
class SuperficieTokens:
    """Cores e medidas de painéis, linhas e estados."""

    estilo: str
    fundo: tuple
    fundo_cabecalho: tuple
    fundo_linha: tuple
    fundo_destaque: tuple
    borda: tuple
    borda_forte: tuple
    texto: tuple
    texto_secundario: tuple
    texto_desabilitado: tuple
    destaque: tuple
    destaque_secundario: tuple
    sombra: tuple
    raio: int
    raio_pequeno: int
    espessura: int
    alpha: int
    glow: int


@dataclass(frozen=True)
class BotaoTokens:
    """Medidas e cores de botões."""

    altura: int
    raio: int
    preenchimento: int
    fundo: tuple
    fundo_hover: tuple
    borda: tuple
    borda_hover: tuple
    texto: tuple
    texto_desabilitado: tuple
    glow: int


@dataclass(frozen=True)
class UITokens:
    """Conjunto completo consumido pelos componentes."""

    estilo: str
    espacamento: EspacamentoTokens
    tipografia: TipografiaTokens
    superficie: SuperficieTokens
    botao: BotaoTokens
    altura_lista: int = 42
    espaco_lista: int = 5
    largura_barra: int = 6


def _tema_original(nome_tema: str | None) -> dict:
    chave = (nome_tema or DEFAULT_TEMA).upper()
    return TEMAS_CORES.get(chave, TEMAS_CORES[DEFAULT_TEMA])


def tokens_para(estilo: str, nome_tema: str | None = None) -> UITokens:
    """Resolve tokens para um estilo explícito.

    Args:
        estilo: ``ORIGINAL`` ou ``COMIC``.
        nome_tema: Tema de cor usado apenas no estilo ORIGINAL.
    """
    if estilo.upper() == ESTILO_COMIC:
        return _tokens_comic()
    return _tokens_original(_tema_original(nome_tema))


def tokens_atuais(nome_tema: str | None = None) -> UITokens:
    """Resolve tokens a partir do contexto visual da composição."""
    return tokens_para(opcoes_atuais().estilo, nome_tema)


def _tokens_original(tema: dict) -> UITokens:
    return UITokens(
        estilo=ESTILO_ORIGINAL,
        espacamento=EspacamentoTokens(),
        tipografia=TipografiaTokens(),
        superficie=SuperficieTokens(
            estilo=ESTILO_ORIGINAL,
            fundo=PAINEL_SOBRIO,
            fundo_cabecalho=FUNDO_SOBRIO,
            fundo_linha=PAINEL_SOBRIO,
            fundo_destaque=FOCO_SOBRIO,
            borda=BORDA_SOBRIA,
            borda_forte=TEXTO_SOBRIO,
            texto=MENU_COR_TEXTO,
            texto_secundario=MENU_COR_TEXTO_SECUNDARIO,
            texto_desabilitado=MENU_COR_TEXTO_DESABILITADO,
            destaque=TEXTO_SOBRIO,
            destaque_secundario=tuple(round(a * 0.85 + b * 0.15)
                                      for a, b in zip(TEXTO_SOBRIO, tema["primaria"])),
            sombra=VOID_BLACK,
            raio=4,
            raio_pequeno=4,
            espessura=1,
            alpha=245,
            glow=0,
        ),
        botao=BotaoTokens(
            altura=46,
            raio=4,
            preenchimento=18,
            fundo=PAINEL_SOBRIO,
            fundo_hover=FOCO_SOBRIO,
            borda=BORDA_SOBRIA,
            borda_hover=BRANCO,
            texto=BRANCO,
            texto_desabilitado=MENU_COR_TEXTO_DESABILITADO,
            glow=0,
        ),
    )


def _tokens_comic() -> UITokens:
    return UITokens(
        estilo=ESTILO_COMIC,
        espacamento=EspacamentoTokens(),
        tipografia=TipografiaTokens(),
        superficie=SuperficieTokens(
            estilo=ESTILO_COMIC,
            fundo=PAPEL,
            fundo_cabecalho=(244, 232, 200),
            fundo_linha=(244, 232, 200),
            fundo_destaque=(255, 205, 120),
            borda=TINTA,
            borda_forte=LARANJA,
            texto=TINTA,
            texto_secundario=AREIA,
            texto_desabilitado=SOMBRA,
            destaque=LARANJA,
            destaque_secundario=CIANO,
            sombra=SOMBRA,
            raio=16,
            raio_pequeno=10,
            espessura=4,
            alpha=255,
            glow=0,
        ),
        botao=BotaoTokens(
            altura=46,
            raio=16,
            preenchimento=18,
            fundo=(244, 232, 200),
            fundo_hover=LARANJA,
            borda=TINTA,
            borda_hover=TINTA,
            texto=TINTA,
            texto_desabilitado=SOMBRA,
            glow=0,
        ),
    )
