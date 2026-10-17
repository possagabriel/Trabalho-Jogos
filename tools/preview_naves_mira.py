"""Gera uma folha de prévia das dez skins em quatro direções da mira."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.infrastructure.graphics.comic_theme import usar_visual
from src.runtime.domain.entities.player import Jogador, SKINS, Skin

RAIZ = Path(__file__).resolve().parents[1]
SAIDA_PADRAO = RAIZ / "images" / "preview_naves_mira.png"
LARGURA_CELULA = 120
ALTURA_CELULA = 96
ANGULOS_PREVIA = (0, 90, 180, 270)


def gerar_previa(saida: Path, estilo: str = "ORIGINAL") -> None:
    """Salva uma grade legível das skins orientadas para quatro lados.

    Args:
        saida: Arquivo PNG de destino.
        estilo: Perfil visual ORIGINAL ou COMIC.
    """
    pygame.init()
    pygame.display.set_mode((1, 1))
    folha = pygame.Surface((LARGURA_CELULA * len(ANGULOS_PREVIA),
                           ALTURA_CELULA * len(SKINS)))
    folha.fill((23, 27, 42))
    jogador = Jogador()
    with usar_visual({"estilo_visual": estilo}):
        for linha, config in enumerate(SKINS):
            jogador.skin = Skin(config)
            for coluna, angulo in enumerate(ANGULOS_PREVIA):
                x = coluna * LARGURA_CELULA
                y = linha * ALTURA_CELULA
                pygame.draw.rect(folha, (56, 62, 82),
                                 (x, y, LARGURA_CELULA, ALTURA_CELULA), 1)
                jogador.x = x + LARGURA_CELULA // 2
                jogador.y = y + ALTURA_CELULA // 2
                jogador.angulo_mira = angulo
                jogador.skin.desenhar(folha, jogador)
    saida.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(folha, str(saida))
    pygame.quit()


def main() -> None:
    """Lê argumentos e gera a folha de sprites para revisão visual."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    parser.add_argument("--estilo", choices=("ORIGINAL", "COMIC"), default="ORIGINAL")
    argumentos = parser.parse_args()
    gerar_previa(argumentos.saida, argumentos.estilo)


if __name__ == "__main__":
    main()
