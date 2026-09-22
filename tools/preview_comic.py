"""Cena reproduzível para screenshots e custo de renderização por efeito.

Uso: python tools/preview_comic.py --save /tmp/comic.png --benchmark
"""

from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("INCARNATE_DATA_DIR", tempfile.mkdtemp(prefix="comic_preview_"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame  # noqa: E402

from src.core.constants import EstadoJogo  # noqa: E402
from src.infrastructure.graphics.comic_theme import usar_visual  # noqa: E402
from src.runtime.application.core import Jogo  # noqa: E402
from src.runtime.domain.entities.bosses import Boss  # noqa: E402
from src.runtime.domain.entities.enemies import TIPOS, Inimigo  # noqa: E402
from src.runtime.domain.entities.powerups import PowerUp  # noqa: E402
from src.runtime.domain.entities.weapons import ARMARIA, Projetil  # noqa: E402
from src.runtime.domain.world.particles import Particula  # noqa: E402
from src.runtime.presentation.damage_feedback import NumeroDano  # noqa: E402


def preparar_cena(estilo: str, qualidade: str) -> Jogo:
    """Cria cena de carga fixa sem gravar progresso do usuário."""
    random.seed(413)
    jogo = Jogo()
    jogo._preparar_jogo()
    jogo.estado = EstadoJogo.JOGANDO
    jogo.config["estilo_visual"] = estilo
    jogo.config["qualidade_comic"] = qualidade
    jogo.config["qualidade_grafica"] = "EQUILIBRADA"
    jogo._aplicar_qualidade_grafica()
    jogo.jogador.invencivel = 0
    jogo.inimigos = [Inimigo(tipo, 8, x=170 + (i % 10) * 95 + random.randrange(-20, 20),
                                   y=220 + (i // 10) * 86 + random.randrange(-25, 25))
                     for i, tipo in enumerate(list(TIPOS) * 2)]
    jogo.boss = Boss(5, jogo.cenario)
    jogo.boss.x, jogo.boss.y, jogo.boss.entrando = 640, 180, False
    jogo.projeteis = [Projetil(190 + (i % 20) * 47, 315 + (i // 20) * 28,
                              0, -8, 1, ARMARIA[i % 9]["cor"], 4,
                              tipo="laser" if i % 3 else "padrao") for i in range(80)]
    jogo.powerups = [PowerUp(tipo, 330 + i * 135, 530)
                    for i, tipo in enumerate(("vida", "arma", "escudo", "moedas"))]
    jogo.particulas.particulas = [Particula(random.gauss(420, 23), random.gauss(470, 16),
                                           (255, 151, 42), (0, 0), 3, 30)
                                 for i in range(180)]
    jogo.mensagens = [NumeroDano("12!", 430, 418, (255, 151, 42)),
                      NumeroDano("5", 790, 280, (64, 226, 230))]
    return jogo


def medir(acao: Callable[[], None], repeticoes: int = 120) -> dict[str, float]:
    """Retorna mediana e percentil 95 em milissegundos após aquecimento."""
    for _ in range(10):
        acao()
    tempos = []
    for _ in range(repeticoes):
        inicio = time.perf_counter()
        acao()
        tempos.append((time.perf_counter() - inicio) * 1000)
    return {"mediana_ms": round(statistics.median(tempos), 3),
            "p95_ms": round(sorted(tempos)[int(len(tempos) * .95)], 3)}


def main() -> None:
    """Gera preview e relatório local; SDL dummy não mede latência de monitor."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save", type=Path)
    parser.add_argument("--benchmark", action="store_true")
    parser.add_argument("--menu", action="store_true")
    parser.add_argument("--style", default="COMIC", choices=("COMIC", "ORIGINAL"))
    parser.add_argument("--quality", default="MEDIA", choices=("BAIXA", "MEDIA", "ALTA"))
    args = parser.parse_args()
    inicio = time.perf_counter()
    jogo = preparar_cena(args.style, args.quality)
    with usar_visual(jogo.config):
        jogo._desenhar_jogo()
        jogo._desenhar_hud()
        if args.menu:
            jogo.menu.entrada_t = 10
            jogo.menu.alpha_entrada = 255
            jogo.menu.desenhar(jogo.tela)
        if args.save:
            args.save.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(jogo.tela, str(args.save))
        carga = round((time.perf_counter() - inicio) * 1000, 2)
        if args.benchmark:
            def quadro() -> None:
                jogo._desenhar_jogo()
                jogo._desenhar_hud()
                jogo._apresentar()
                pygame.display.flip()

            relatorio = {"estilo": args.style, "qualidade": args.quality,
                         "logica": jogo.tela.get_size(), "janela": jogo.janela.get_size(),
                         "carga_e_primeiro_quadro_ms": carga,
                         "inimigos": len(jogo.inimigos), "projeteis": len(jogo.projeteis),
                         "particulas": len(jogo.particulas.particulas),
                         "fundo": medir(lambda: jogo.cenario.desenhar(jogo.tela)),
                         "sprites_e_efeitos": medir(jogo._desenhar_jogo),
                         "hud": medir(jogo._desenhar_hud),
                         "particulas_isoladas": medir(lambda: jogo.particulas.desenhar(jogo.tela)),
                         "apresentacao": medir(jogo._apresentar),
                         "quadro_completo_render": medir(quadro)}
            def loop_real() -> None:
                # Mantém a captura ativa; inimigos e projéteis seguem o update real.
                jogo.jogador.invencivel = 3
                jogo._atualizar_jogando()
                quadro()

            relatorio["loop_com_atualizacao_120_quadros"] = medir(loop_real)
            print(json.dumps(relatorio, indent=2))
    pygame.quit()


if __name__ == "__main__":
    main()
