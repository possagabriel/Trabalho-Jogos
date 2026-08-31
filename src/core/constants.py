"""Constantes globais do jogo VOID//SHIFT: tela, FPS, cores e limites."""

from __future__ import annotations

from enum import Enum

# ---------------------------------------------------------------------------
# Dimensoes e desempenho
# ---------------------------------------------------------------------------

LARGURA: int = 900
"""Largura logica da superficie de jogo (pixels)."""

ALTURA: int = 700
"""Altura logica da superficie de jogo (pixels)."""

FPS: int = 60
"""Taxa de quadros por segundo alvo."""

TITULO: str = "VOID//SHIFT - Enter the Rift"
"""Titulo exibido na barra da janela."""

# ---------------------------------------------------------------------------
# Paleta oficial VOID//SHIFT
# ---------------------------------------------------------------------------

VOID_BLACK: tuple[int, int, int] = (8, 8, 13)
"""Preto profundo — fundo predominante."""

SHIFT_WHITE: tuple[int, int, int] = (244, 244, 247)
"""Branco de alta legibilidade — textos e elementos importantes."""

RIFT_MAGENTA: tuple[int, int, int] = (255, 23, 107)
"""Magenta da fissura — assinatura visual da marca."""

QUANTUM_CYAN: tuple[int, int, int] = (25, 217, 255)
"""Ciano quantico — HUD, elementos de tecnologia."""

DIMENSION_GOLD: tuple[int, int, int] = (255, 200, 87)
"""Ouro dimensional — bosses, eventos raros e progressao."""

# ---------------------------------------------------------------------------
# Cores derivadas (aliases para uso interno)
# ---------------------------------------------------------------------------

NEGRO: tuple[int, int, int] = VOID_BLACK
BRANCO: tuple[int, int, int] = SHIFT_WHITE
VERDE: tuple[int, int, int] = (0, 255, 100)
VERMELHO: tuple[int, int, int] = (255, 50, 50)
AZUL: tuple[int, int, int] = QUANTUM_CYAN
DOURADO: tuple[int, int, int] = DIMENSION_GOLD
ROXO: tuple[int, int, int] = (150, 50, 200)
LARANJA: tuple[int, int, int] = (255, 150, 0)
CIANO: tuple[int, int, int] = QUANTUM_CYAN
ROSA: tuple[int, int, int] = RIFT_MAGENTA
AZUL_CLARO: tuple[int, int, int] = (200, 220, 255)
AMARELO: tuple[int, int, int] = (255, 240, 60)
VERDE_CLARO: tuple[int, int, int] = (140, 255, 160)
INDIGO: tuple[int, int, int] = (75, 0, 130)
PRATA: tuple[int, int, int] = (192, 200, 220)

# ---------------------------------------------------------------------------
# Limites de progressao
# ---------------------------------------------------------------------------

NIVEL_BOSS: int = 5
"""Quantidade de niveis entre encontros com bosses (modulo)."""

MAXIMO_CENARIOS: int = 6
"""Numero total de cenarios/dimensoes jogaveis."""


class EstadoJogo(str, Enum):
    """Estados do fluxo principal mantidos pela aplicacao e pelas telas."""

    MENU = "MENU"
    CONTINUAR = "CONTINUAR"
    LOJA = "LOJA"
    RECORDES = "RECORDES"
    CONFIG = "CONFIG"
    PREPARANDO = "PREPARANDO"
    JOGANDO = "JOGANDO"
    PAUSA = "PAUSA"
    GAME_OVER = "GAME_OVER"


# Regras de gameplay compartilhadas por entidades e controladores.
INTERVALO_SPAWN_BASE: int = 35
INTERVALO_SPAWN_MINIMO: int = 18
DIVISOR_NIVEL_INTERVALO_SPAWN: int = 3
INCREMENTO_CARREGAMENTO: float = 2.6
COMBO_MULTIPLICADOR_MEDIO: int = 10
COMBO_MULTIPLICADOR_ALTO: int = 20
INVISIBILIDADE_QUADROS: int = 40
PISCAR_INVISIBILIDADE_QUADROS: int = 4
COOLDOWN_ATAQUE_INIMIGO_MINIMO: int = 110
COOLDOWN_ATAQUE_INIMIGO_MAXIMO: int = 170
