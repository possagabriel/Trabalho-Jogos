"""Mede o percurso visual e o combate com 60 inimigos."""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import tempfile
import time
from unittest.mock import Mock


def _medir(jogo: object, quadros: int, avanco: bool) -> dict[str, float]:
    """Mede atualização visual e composição do mundo após aquecer caches."""
    from src.infrastructure.graphics.comic_theme import usar_visual
    from src.runtime.application.timing import PASSO_FIXO

    amostras = []
    with usar_visual(jogo.config):
        for indice in range(quadros + 12):
            inicio = time.perf_counter()
            if avanco:
                jogo.avanco_controller.atualizar(jogo.cenario, PASSO_FIXO)
            jogo._desenhar_jogo()
            if indice >= 12:
                amostras.append((time.perf_counter() - inicio) * 1000)
    ordenadas = sorted(amostras)
    return {
        "media_ms": round(statistics.mean(amostras), 3),
        "mediana_ms": round(statistics.median(amostras), 3),
        "p95_ms": round(ordenadas[int(0.95 * (len(ordenadas) - 1))], 3),
        "maximo_ms": round(max(amostras), 3),
    }


def main() -> None:
    """Executa um benchmark reproduzível e imprime ambiente e tempos em JSON."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--quadros", type=int, default=120)
    parser.add_argument("--repeticoes", type=int, default=3)
    argumentos = parser.parse_args()
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    with tempfile.TemporaryDirectory(prefix="incarnate_scroll_bench_") as dados:
        os.environ["INCARNATE_DATA_DIR"] = dados
        import pygame

        from src.core.constants import ALTURA, LARGURA
        from src.runtime.application.core import Jogo
        from src.runtime.domain.entities.enemies import Inimigo

        jogo = Jogo(sons=Mock())
        jogo.estado = "JOGANDO"
        jogo.config["avanco_semente"] = 2026
        jogo.avanco_controller.reiniciar(jogo.cenario)
        jogo.inimigos = [
            Inimigo("soldado" if indice % 2 else "scout", 1,
                    x=30 + (indice % 12) * 102,
                    y=45 + (indice // 12) * 105)
            for indice in range(60)
        ]
        jogo.fila_onda = []
        fundo = jogo.cenario.parallax
        if fundo._marcos and fundo._marcos._ativos:
            marco = fundo._marcos._ativos[0]
        elif fundo._marcos and fundo._marcos._habilitado:
            fundo._marcos._relogio = 0.0
            fundo._marcos._spawn(jogo.avanco_controller.modelo.velocidade_base)
            marco = fundo._marcos._ativos[0] if fundo._marcos._ativos else None
        else:
            marco = None
        if marco is not None:
            marco.x, marco.y = LARGURA // 2, ALTURA // 3
        antigo_amostras = []
        novo_amostras = []
        for repeticao in range(max(1, argumentos.repeticoes)):
            for avanco in ((False, True) if repeticao % 2 == 0 else (True, False)):
                jogo.cenario.parallax = fundo if avanco else None
                resultado = _medir(jogo, argumentos.quadros, avanco)
                (novo_amostras if avanco else antigo_amostras).append(resultado)
        jogo.cenario.parallax = fundo
        antigo = {chave: round(statistics.median(amostra[chave]
                  for amostra in antigo_amostras), 3) for chave in antigo_amostras[0]}
        novo = {chave: round(statistics.median(amostra[chave]
                for amostra in novo_amostras), 3) for chave in novo_amostras[0]}
        memoria_marcos = {}
        from src.runtime.domain.world.scenarios import Cenario

        for qualidade in ("BAIXA", "MEDIA", "ALTA"):
            cenario_memoria = Cenario(1)
            cenario_memoria.configurar_avanco(
                qualidade, (0, 1), True, True, jogo.config, 2026)
            bytes_cache = cenario_memoria.parallax.memoria_marcos
            memoria_marcos[qualidade] = {
                "bytes": bytes_cache,
                "mebibytes": round(bytes_cache / (1024 * 1024), 3),
            }
        print(json.dumps({
            "ambiente": {
                "sistema": platform.platform(),
                "processador": platform.processor() or platform.machine(),
                "python": platform.python_version(),
                "pygame": pygame.version.ver,
                "driver_video": pygame.display.get_driver(),
                "resolucao_logica": [LARGURA, ALTURA],
                "estilo_visual": jogo.config["estilo_visual"],
                "qualidade_avanco": jogo.config["avanco_qualidade"],
            },
            "entidades": len(jogo.inimigos) + 1,
            "quadros_medidos": argumentos.quadros,
            "repeticoes": max(1, argumentos.repeticoes),
            "mundo_anterior": antigo,
            "mundo_com_avanco": novo,
            "memoria_cache_marcos": memoria_marcos,
            "amostras_medias_ms": {
                "anterior": [amostra["media_ms"] for amostra in antigo_amostras],
                "com_avanco": [amostra["media_ms"] for amostra in novo_amostras],
            },
        }, ensure_ascii=False, indent=2))
        pygame.quit()


if __name__ == "__main__":
    main()
