"""Fachada de compatibilidade para constantes migradas a :mod:`src.core`.

Codigo novo deve importar de ``src.core.constants``. Este modulo nao possui
estado proprio e preserva apenas os imports relativos do legado durante a
migracao incremental.
"""

from src.core.constants import (ALTURA, AMARELO, AZUL, AZUL_CLARO, BRANCO,
                                CIANO, COOLDOWN_ATAQUE_INIMIGO_MAXIMO,
                                COOLDOWN_ATAQUE_INIMIGO_MINIMO,
                                COMBO_MULTIPLICADOR_ALTO,
                                COMBO_MULTIPLICADOR_MEDIO,
                                DIMENSION_GOLD,
                                DIVISOR_NIVEL_INTERVALO_SPAWN, DOURADO,
                                EstadoJogo, FPS, INCREMENTO_CARREGAMENTO,
                                INDIGO, INTERVALO_SPAWN_BASE,
                                INTERVALO_SPAWN_MINIMO,
                                INVISIBILIDADE_QUADROS, LARANJA, LARGURA,
                                MAXIMO_CENARIOS, NEGRO, NIVEL_BOSS,
                                PISCAR_INVISIBILIDADE_QUADROS, PRATA,
                                QUANTUM_CYAN, RIFT_MAGENTA, ROSA, ROXO,
                                SHIFT_WHITE, TITULO, VERDE, VERDE_CLARO,
                                VERMELHO, VOID_BLACK)
