#!/usr/bin/env python3
"""Extrai a nave padrao do jogador a partir de images/naves.png.

A folha ``naves.png`` contem varias naves; este script recorta a nave
principal (regiao (258,37)-(398,332), nariz apontando para cima), remove o
fundo escuro por distancia de cor e salva ``images/nave-padrao.png`` com
canal alpha. Usado para regenerar o sprite quando a folha mudar:

    python3 tools/extract_nave_padrao.py
"""

import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Regiao da nave padrao na folha (cand_04 da folha de contato).
# Formato: (x0, y0, x1, y1) inclusive, canto superior esquerdo do recorte.
BBOX = (258, 37, 398, 332)
PADDING = 16            # margem em torno do sprite
LIMIAR_FUNDO = 26.0     # distancia de cor abaixo da qual vira transparente
LIMIAR_NAVE = 46.0      # distancia acima da qual fica opaco
RAIZ_IMAGENS = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "images")


def extrair(origem, destino):
    """Recorta, remove o fundo e salva o sprite com alpha."""
    x0, y0, x1, y1 = BBOX
    pad = PADDING
    im = Image.open(origem).convert("RGB")
    a = np.asarray(im).astype(np.int32)
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(im.width - 1, x1 + pad), min(im.height - 1, y1 + pad)
    crop = a[y0:y1 + 1, x0:x1 + 1]

    ring = np.concatenate([crop[0].reshape(-1, 3), crop[-1].reshape(-1, 3),
                           crop[:, 0].reshape(-1, 3),
                           crop[:, -1].reshape(-1, 3)])
    fundo = np.median(ring, axis=0)
    dist = np.sqrt(((crop - fundo) ** 2).sum(axis=2))
    alpha = np.clip((dist - LIMIAR_FUNDO) /
                    (LIMIAR_NAVE - LIMIAR_FUNDO), 0, 1) * 255

    rgba = np.dstack([crop, alpha.astype(np.uint8)]).astype(np.uint8)
    out = Image.fromarray(rgba, "RGBA")
    out.save(destino, optimize=True)
    print(f"salvo {destino} ({out.size[0]}x{out.size[1]}), "
          f"fundo removido ~{fundo.astype(int)}")


if __name__ == "__main__":
    extrair(os.path.join(RAIZ_IMAGENS, "naves.png"),
            os.path.join(RAIZ_IMAGENS, "nave-padrao.png"))