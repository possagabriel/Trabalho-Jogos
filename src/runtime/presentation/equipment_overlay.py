"""Overlay do arsenal exibido durante uma partida."""

from __future__ import annotations

from typing import Any

import pygame

from src.core.constants import ALTURA, BRANCO, DIMENSION_GOLD, LARGURA, VOID_BLACK
from src.infrastructure.graphics.theme import tema_atual
from src.runtime.domain.entities.weapons import ARMARIA
from src.runtime.infrastructure.graphics.smooth import (
    desenhar_glow,
    desenhar_painel_cartoon,
    retangulo_suave,
)
from src.runtime.presentation.ui import desenhar_cantos, desenhar_texto

ESPECIAIS = {
    "bomba": {"nome": "BOMBA VORTEX", "descricao": "Dano em uma grande area"},
    "cura": {"nome": "REPARO +3", "descricao": "Recupera 3 pontos de vida"},
    "imortal": {"nome": "IMORTALIDADE", "descricao": "10 segundos sem receber dano"},
}


def desenhar_menu_equipamento(jogo: Any) -> None:
    """Desenha o arsenal em formato de terminal tático aberto por TAB."""
    jogo.tela.blit(jogo._sombra_equipamento, (0, 0))
    painel = pygame.Rect(60, 70, LARGURA - 120, ALTURA - 140)
    tema = tema_atual(jogo.config["tema"])
    desenhar_painel_cartoon(
        jogo.tela,
        tema["primaria"],
        painel,
        cor_fundo=(8, 14, 30),
        raio_canto=24,
        espessura_borda=5,
        alpha=248,
        glow_raio=28,
    )
    desenhar_cantos(jogo.tela, tema["secundaria"], painel, tamanho=18)

    cabecalho = pygame.Rect(painel.x + 20, painel.y + 18, painel.w - 40, 64)
    retangulo_suave(jogo.tela, (16, 28, 54), cabecalho, 12)
    retangulo_suave(
        jogo.tela,
        tema["secundaria"],
        cabecalho,
        12,
        1,
        glow_cor=tema["secundaria"],
        glow_raio=12,
    )
    desenhar_glow(
        jogo.tela,
        tema["secundaria"],
        (cabecalho.x + 31, cabecalho.centery),
        19,
        0.9,
    )
    pygame.draw.circle(
        jogo.tela, tema["secundaria"], (cabecalho.x + 31, cabecalho.centery), 6
    )
    desenhar_texto(
        jogo.tela,
        "ARSENAL",
        (cabecalho.x + 56, cabecalho.y + 17),
        BRANCO,
        31,
        "esquerda",
        jogo.fontes,
    )
    desenhar_texto(
        jogo.tela,
        "EQUIPAMENTO // SELEÇÃO TÁTICA",
        (cabecalho.x + 58, cabecalho.y + 45),
        (145, 170, 215),
        14,
        "esquerda",
        jogo.fontes,
    )
    desenhar_texto(
        jogo.tela,
        "TAB  FECHAR",
        (cabecalho.right - 18, cabecalho.centery),
        tema["secundaria"],
        15,
        "direita",
        jogo.fontes,
    )

    linhas = [
        ("ARMAS", jogo.jogador.armas_desbloqueadas, jogo.jogador.arma_atual),
        ("ESPECIAIS", jogo.especiais_desbloqueados, jogo.especial_atual),
    ]
    for linha, (titulo, itens, equipado) in enumerate(linhas):
        _desenhar_linha(jogo, painel, tema, linha, titulo, itens, equipado)

    rodape = pygame.Rect(painel.x + 20, painel.bottom - 44, painel.w - 40, 25)
    retangulo_suave(jogo.tela, (14, 24, 47), rodape, 6)
    desenhar_texto(
        jogo.tela,
        "SETAS / WASD  NAVEGAR     ENTER / ESPAÇO  EQUIPAR",
        rodape.center,
        (165, 183, 222),
        14,
        "centro",
        jogo.fontes,
    )


def _desenhar_linha(
    jogo: Any,
    painel: pygame.Rect,
    tema: dict[str, tuple[int, int, int]],
    linha: int,
    titulo: str,
    itens: list[Any],
    equipado: Any,
) -> None:
    y = painel.y + (104 if linha == 0 else 358)
    cor = tema["secundaria"] if linha == jogo.linha_equipamento else (125, 145, 188)
    desenhar_texto(
        jogo.tela, f"0{linha + 1} // {titulo}", (painel.x + 28, y), cor, 19,
        "esquerda", jogo.fontes,
    )
    linha_y = y + 25
    pygame.draw.line(
        jogo.tela, cor, (painel.x + 28, linha_y), (painel.right - 28, linha_y), 1
    )
    for indice, item in enumerate(itens):
        _desenhar_item(
            jogo, painel, tema, linha, indice, item, len(itens), equipado, cor, y
        )


def _desenhar_item(
    jogo: Any,
    painel: pygame.Rect,
    tema: dict[str, tuple[int, int, int]],
    linha: int,
    indice: int,
    item: Any,
    quantidade_itens: int,
    equipado: Any,
    cor: tuple[int, int, int],
    y: int,
) -> None:
    coluna, fileira = indice % 3, indice // 3
    x = painel.x + 27 + coluna * 244
    item_y = y + 40 + fileira * 70
    card = pygame.Rect(x, item_y, 226, 58)
    selecionado = (
        linha == jogo.linha_equipamento
        and indice == jogo.indice_equipamento % max(1, quantidade_itens)
    )
    if linha == 0:
        arma = ARMARIA[item]
        nome, detalhe = arma["nome"], arma["papel"].upper()
        numero = f"{item + 1:02d}"
    else:
        especial = ESPECIAIS[item]
        nome, detalhe = especial["nome"], especial["descricao"].upper()
        numero = f"0{indice + 1}"
    equipado_agora = item == equipado
    fundo = (28, 38, 68) if selecionado else (13, 23, 45)
    borda = (
        DIMENSION_GOLD if selecionado else cor if equipado_agora else (58, 77, 116)
    )
    retangulo_suave(jogo.tela, fundo, card, 9)
    retangulo_suave(
        jogo.tela,
        borda,
        card,
        9,
        2 if selecionado else 1,
        glow_cor=borda if selecionado else None,
        glow_raio=10 if selecionado else 0,
    )
    numero_surf = jogo.fontes[22].render(numero, True, borda)
    jogo.tela.blit(numero_surf, (card.x + 10, card.y + 7))
    desenhar_texto(
        jogo.tela, nome, (card.x + 42, card.y + 8), BRANCO, 17, "esquerda",
        jogo.fontes,
    )
    desenhar_texto(
        jogo.tela, detalhe, (card.x + 42, card.y + 31), (148, 166, 205), 12,
        "esquerda", jogo.fontes,
    )
    if equipado_agora:
        badge = pygame.Rect(card.right - 52, card.y + 8, 42, 16)
        retangulo_suave(jogo.tela, tema["primaria"], badge, 5)
        desenhar_texto(
            jogo.tela, "USO", badge.center, VOID_BLACK, 10, "centro", jogo.fontes
        )
