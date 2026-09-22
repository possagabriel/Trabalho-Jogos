"""Silhuetas e telegráficos cel-shaded, sem alterar as regras do encontro."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.core.constants import BRANCO, CIANO, VERMELHO, VOID_BLACK
from src.infrastructure.ui.layout import Layout
from src.runtime.domain.entities.minibosses.states import Ataque, Aviso
from src.runtime.infrastructure.graphics.cel_shading import (
    circulo_com_contorno,
    poligono_com_contorno,
)
from src.runtime.infrastructure.graphics.geometry import poligono
from src.runtime.infrastructure.graphics.smooth import (
    desenhar_circulo,
    desenhar_glow,
    desenhar_poligono,
    linha_suave,
    retangulo_suave,
)
from src.runtime.presentation.ui import desenhar_texto

if TYPE_CHECKING:
    from src.runtime.domain.entities.minibosses.base import Miniboss


def desenhar_miniboss(tela: pygame.Surface, boss: Miniboss) -> None:
    """Desenha os mesmos núcleos/zonas que as colisões consultam."""
    cor = BRANCO if boss.flash > 0 else boss.cor
    for zona in boss.zonas:
        ativo = isinstance(boss.estado, Ataque)
        retangulo_suave(tela, VERMELHO if ativo else boss.cor, zona,
                       raio_canto=0, espessura=5 if ativo else 2)
        if not ativo:
            # Marcas descontínuas indicam contagem; preenchimento não esconde tiros.
            for fracao in (0.2, 0.4, 0.6, 0.8):
                x = zona.left + zona.width * fracao
                linha_suave(tela, boss.cor, (x, zona.top), (x, zona.top + 8), 2)
        desenhar_texto(tela, "PERIGO" if ativo else "SAIA DA ZONA",
                       zona.center, VERMELHO if ativo else boss.cor, 16)
    destino = boss.estrategia.destino
    if destino is not None and isinstance(boss.estado, Aviso):
        desenhar_circulo(tela, boss.cor, destino, boss.raio + 8, espessura=3)
        desenhar_texto(tela, "SALTO", destino, BRANCO, 18)
    centro = (round(boss.x), round(boss.y))
    pontos = poligono(centro, boss.raio, boss.cfg["lados"], boss.angulo)
    desenhar_poligono(tela, VOID_BLACK, [(x + 4, y + 6) for x, y in pontos])
    poligono_com_contorno(tela, cor, pontos, espessura_contorno=4)
    desenhar_circulo(tela, BRANCO, (centro[0] - 7, centro[1] - 8), 4)
    protegido = boss.estrategia.dano(boss, 1) == 0
    if protegido:
        desenhar_circulo(tela, CIANO, centro, boss.raio + 7, espessura=3)
    for rect in boss.estrategia.pontos_fracos(boss):
        linha_suave(tela, boss.cor, centro, rect.center, 3)
        circulo_com_contorno(tela, BRANCO, rect.center, rect.width // 2,
                            espessura_contorno=3)
    if boss.inverte_controles:
        desenhar_glow(tela, boss.cor, centro, boss.raio * 1.6, 0.5)
    layout = Layout(*tela.get_size())
    aviso = "ENTRANDO" if boss.entrando else boss.estado.rotulo
    if protegido and not boss.entrando:
        aviso += " / BLINDADO"
    if boss.inverte_controles:
        aviso = "CONTROLES INVERTIDOS"
    texto = f"{aviso}  {boss.estado.restante:.1f}s"
    desenhar_texto(tela, texto, (layout.x(0.5), layout.y(0.13)), boss.cor, layout.px(16))
    desenhar_texto(tela, boss.cfg["dica"], (layout.x(0.5), layout.y(0.17)),
                   BRANCO, layout.px(15))
