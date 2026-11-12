"""Arsenal responsivo, com cartas, prévia e navegação espacial pela grade."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import pygame

from src.core.constants import FPS
from src.infrastructure.graphics.comic_theme import opcoes_atuais, usar_visual
from src.infrastructure.ui.layout import Layout
from src.runtime.domain.entities.weapons import ARMARIA, Projetil
from src.runtime.infrastructure.graphics.fonts import fonte_texto
from src.runtime.infrastructure.graphics.menu_panels import (
    ACENTO_ORIGINAL,
    BORDA_ORIGINAL,
    FUNDO_ORIGINAL,
    PAINEL_ORIGINAL,
    TEXTO_ORIGINAL,
    linhas_painel,
    painel_menu,
    texto_painel,
)

COLUNAS_ARSENAL = 3
ESPECIAIS = {
    "bomba": {"nome": "BOMBA VORTEX", "descricao": "Dano em uma grande área", "icone": "VX"},
    "intangivel": {"nome": "INTANGIBILIDADE", "descricao": "Atravessa perigos por 3 s",
                   "icone": "I"},
    "cura": {"nome": "REPARO +3", "descricao": "Recupera 3 pontos de vida", "icone": "+3"},
    "imortal": {"nome": "IMORTALIDADE", "descricao": "10 segundos sem receber dano",
                "icone": "10s"},
}


@dataclass(frozen=True)
class GeometriaEquipamento:
    """Áreas visuais do arsenal no mesmo espaço lógico do foco por teclado."""

    painel: pygame.Rect
    cabecalho: pygame.Rect
    armas: tuple[pygame.Rect, ...]
    especiais: tuple[pygame.Rect, ...]
    rotulos: tuple[pygame.Rect, ...]
    detalhe: pygame.Rect
    rodape: pygame.Rect


def geometria_equipamento(layout: Layout, quantidades: tuple[int, int]) -> GeometriaEquipamento:
    """Distribui três colunas e reserva uma prévia lateral sem sobrepor seções."""
    px = layout.px
    painel = pygame.Rect(px(24), px(28), layout.largura - px(48), layout.altura - px(56))
    cabecalho = pygame.Rect(painel.x + px(18), painel.y + px(14), painel.w - px(36), px(58))
    rodape = pygame.Rect(painel.x + px(18), painel.bottom - px(34), painel.w - px(36), px(22))
    detalhe = pygame.Rect(painel.x + round(painel.w * .72), painel.y + px(90),
                         round(painel.w * .28) - px(18),
                         rodape.top - px(14) - (painel.y + px(90)))
    grid_x, grid_w = painel.x + px(18), detalhe.x - px(18) - (painel.x + px(18))
    linhas = [max(1, (n + COLUNAS_ARSENAL - 1) // COLUNAS_ARSENAL) for n in quantidades]
    gap = px(8)
    altura = min(px(72), (detalhe.h - px(26) * 2 - px(14)
                          - gap * (sum(linhas) - 2)) // sum(linhas))
    largura = (grid_w - gap * 2) // COLUNAS_ARSENAL
    y = detalhe.y
    secoes, rotulos = [], []
    for quantidade, fileiras in zip(quantidades, linhas):
        rotulos.append(pygame.Rect(grid_x, y, grid_w, px(22)))
        y += px(26)
        secoes.append(tuple(pygame.Rect(grid_x + (i % 3) * (largura + gap),
                                       y + (i // 3) * (altura + gap), largura, altura)
                            for i in range(quantidade)))
        y += fileiras * altura + (fileiras - 1) * gap + px(14)
    return GeometriaEquipamento(painel, cabecalho, secoes[0], secoes[1],
                                tuple(rotulos), detalhe, rodape)


def mover_selecao_equipamento(linha: int, indice: int, quantidades: tuple[int, int],
                              direcao: tuple[int, int]) -> tuple[int, int]:
    """Move o foco entre fileiras reais, preservando a coluna ao trocar de seção."""
    fileiras = [(grupo, inicio, min(inicio + COLUNAS_ARSENAL, quantidade))
                for grupo, quantidade in enumerate(quantidades)
                for inicio in range(0, quantidade, COLUNAS_ARSENAL)]
    if not fileiras:
        return 0, 0
    if linha not in (0, 1) or not quantidades[linha]:
        linha = fileiras[0][0]
    indice %= quantidades[linha]
    dx, dy = direcao
    if dx:
        return linha, (indice + dx) % quantidades[linha]
    if not dy:
        return linha, indice
    atual = next(i for i, (grupo, inicio, fim) in enumerate(fileiras)
                 if grupo == linha and inicio <= indice < fim)
    grupo, inicio, fim = fileiras[(atual + dy) % len(fileiras)]
    return grupo, min(inicio + indice % COLUNAS_ARSENAL, fim - 1)


def _texto(tela, layout, texto, rect, tamanho=16, titulo=False, cor=TEXTO_ORIGINAL):
    fonte = layout.fonte_titulo(tamanho) if titulo else layout.fonte_texto(tamanho)
    arte = texto_painel(fonte, texto, cor, rect.w, rect.h)
    tela.blit(arte, arte.get_rect(center=rect.center))


@lru_cache(maxsize=48)
def _icone(linha: int, item: Any, tamanho: int, comic: bool) -> pygame.Surface:
    base = pygame.Surface((80, 80), pygame.SRCALPHA)
    with usar_visual({"estilo_visual": "COMIC" if comic else "ORIGINAL"}):
        if linha == 0:
            arma = ARMARIA[item]
            proj = Projetil(40, 48, 0, -arma['vel'], 0, arma['cor'], arma['raio'], arma['tipo'])
            proj.tempo = 5
            proj.desenhar(base)
        else:
            fonte = fonte_texto(34)
            arte = texto_painel(fonte, ESPECIAIS[item]['icone'], TEXTO_ORIGINAL, 60, 60)
            base.blit(arte, arte.get_rect(center=(40, 40)))
    return pygame.transform.smoothscale(base, (tamanho, tamanho))


def desenhar_menu_equipamento(jogo: Any) -> None:
    """Mostra armas e especiais em cartas, com detalhes do item sob o foco."""
    layout, tela = jogo.layout, jogo.tela
    px = layout.px
    tela.blit(jogo._sombra_equipamento, (0, 0))
    listas = (jogo.jogador.armas_desbloqueadas, jogo.especiais_desbloqueados)
    g = geometria_equipamento(layout, tuple(len(itens) for itens in listas))
    tela.blit(painel_menu(g.painel.size, FUNDO_ORIGINAL, BORDA_ORIGINAL, raio=px(16)), g.painel)
    _texto(tela, layout, 'ARSENAL', pygame.Rect(g.cabecalho.x, g.cabecalho.y,
                                             g.cabecalho.w, px(32)), 28, True)
    _texto(tela, layout, 'Escolha sua arma e prepare o próximo especial',
           pygame.Rect(g.cabecalho.x, g.cabecalho.y + px(34), g.cabecalho.w, px(20)), 15)
    equipado = (jogo.jogador.arma_atual, jogo.especial_atual)
    foco = jogo.linha_equipamento
    indice_foco = jogo.indice_equipamento % max(1, len(listas[foco]))
    for grupo, (itens, cartas, titulo) in enumerate(zip(
            listas, (g.armas, g.especiais), ('ARMAS', 'ESPECIAIS'))):
        _texto(tela, layout, f'{titulo}  /  {len(itens):02}', g.rotulos[grupo], 17, True)
        for indice, (item, card) in enumerate(zip(itens, cartas)):
            selecionado = grupo == foco and indice == indice_foco
            borda = ACENTO_ORIGINAL if selecionado else BORDA_ORIGINAL
            tela.blit(painel_menu(card.size, PAINEL_ORIGINAL, borda, raio=px(8)), card)
            icone = _icone(grupo, item, px(36), opcoes_atuais().ativo)
            tela.blit(icone, icone.get_rect(center=(card.x + px(24), card.centery)))
            nome = ARMARIA[item]['nome'] if grupo == 0 else ESPECIAIS[item]['nome']
            area = pygame.Rect(card.x + px(46), card.y + px(8), card.w - px(52), px(25))
            _texto(tela, layout, nome, area, 15, True)
            area.y += px(28)
            area.h = px(18)
            estado = 'EM USO' if item == equipado[grupo] else 'ENTER EQUIPAR' if selecionado else ''
            _texto(tela, layout, ('> ' if selecionado else '') + estado, area, 12,
                   cor=ACENTO_ORIGINAL if selecionado else TEXTO_ORIGINAL)
    _desenhar_detalhe(jogo, g.detalhe, listas[foco], indice_foco, foco, equipado[foco])
    _texto(tela, layout, '←/→ COLUNAS   ↑/↓ FILEIRAS   ENTER EQUIPAR   TAB / ESC FECHAR',
           g.rodape, 14)


def _desenhar_detalhe(jogo, rect, itens, indice, grupo, equipado):
    layout, tela = jogo.layout, jogo.tela
    px = layout.px
    tela.blit(painel_menu(rect.size, PAINEL_ORIGINAL, ACENTO_ORIGINAL, raio=px(10)), rect)
    if not itens:
        _texto(tela, layout, 'Nenhum equipamento disponível', rect, 18)
        return
    item = itens[indice]
    nome = ARMARIA[item]['nome'] if grupo == 0 else ESPECIAIS[item]['nome']
    descricao = ARMARIA[item]['papel'] if grupo == 0 else ESPECIAIS[item]['descricao']
    margem = px(14)
    _texto(tela, layout, nome.upper(), pygame.Rect(rect.x + margem, rect.y + px(12),
           rect.w - margem * 2, px(48)), 23, True)
    tamanho = min(rect.w - margem * 2, px(140))
    icone = _icone(grupo, item, tamanho, opcoes_atuais().ativo)
    tela.blit(icone, icone.get_rect(midtop=(rect.centerx, rect.y + px(70))))
    y = rect.y + px(80) + tamanho
    fonte = layout.fonte_texto(17)
    for linha in linhas_painel(fonte, descricao, rect.w - margem * 2):
        _texto(tela, layout, linha, pygame.Rect(rect.x + margem, y,
               rect.w - margem * 2, px(24)), 17)
        y += px(25)
    y += px(14)
    if grupo == 0:
        arma = ARMARIA[item]
        pausa = max(2, round(arma['cooldown'] * getattr(jogo.jogador, 'multiplicador_cadencia', 1)))
        dados = (f"Dano base / projétil: {arma['dano']}",
                 f"{'Pausa da rajada' if arma['tipo'] == 'metralhadora' else 'Intervalo'}: "
                 f"{pausa / FPS:.2f} s")
    else:
        dados = ('Ativar em combate: E', 'Troque o especial com Enter')
    for dado in dados:
        _texto(tela, layout, dado, pygame.Rect(rect.x + margem, y,
               rect.w - margem * 2, px(24)), 15)
        y += px(28)
    _texto(tela, layout, 'EQUIPADO' if item == equipado else 'ENTER PARA EQUIPAR',
           pygame.Rect(rect.x + margem, rect.bottom - px(46), rect.w - margem * 2, px(30)),
           16, True, ACENTO_ORIGINAL)
