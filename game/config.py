"""Constantes globais do jogo VOID//SHIFT: tela, FPS, cores e regras."""

from enum import Enum

LARGURA = 900
ALTURA = 700
FPS = 60
TITULO = "VOID//SHIFT - Enter the Rift"

# Paleta oficial da marca VOID//SHIFT
VOID_BLACK = (8, 8, 13)        # fundo predominante
SHIFT_WHITE = (244, 244, 247)  # textos e elementos importantes
RIFT_MAGENTA = (255, 23, 107)  # assinatura visual
QUANTUM_CYAN = (25, 217, 255)  # HUD e tecnologia
DIMENSION_GOLD = (255, 200, 87)  # bosses, eventos raros e progressao

# Cores base (aliased para a paleta da marca onde possivel)
NEGRO = VOID_BLACK
BRANCO = SHIFT_WHITE
VERDE = (0, 255, 100)
VERMELHO = (255, 50, 50)
AZUL = QUANTUM_CYAN
DOURADO = DIMENSION_GOLD
ROXO = (150, 50, 200)
LARANJA = (255, 150, 0)
CIANO = QUANTUM_CYAN
ROSA = RIFT_MAGENTA
AZUL_CLARO = (200, 220, 255)
AMARELO = (255, 240, 60)
VERDE_CLARO = (140, 255, 160)
INDIGO = (75, 0, 130)
PRATA = (192, 200, 220)

# Limites de progressao
NIVEL_BOSS = 5          # a cada 5 niveis aparece um boss
MAXIMO_CENARIOS = 6     # numero total de cenarios


class EstadoJogo(str, Enum):
    """Estados possiveis do fluxo principal do jogo legado.

    Herdar de ``str`` preserva a compatibilidade com saves, menus e codigo
    externo que ainda compara o estado com seu nome textual.
    """

    MENU = "MENU"
    CONTINUAR = "CONTINUAR"
    LOJA = "LOJA"
    RECORDES = "RECORDES"
    CONFIG = "CONFIG"
    PREPARANDO = "PREPARANDO"
    JOGANDO = "JOGANDO"
    PAUSA = "PAUSA"
    GAME_OVER = "GAME_OVER"


# Regras de gameplay antes espalhadas em ``core.py``, ``player.py`` e
# ``enemies.py``. Mantidas aqui para tornar o balanceamento rastreavel.
INTERVALO_SPAWN_BASE = 35
INTERVALO_SPAWN_MINIMO = 18
DIVISOR_NIVEL_INTERVALO_SPAWN = 3
INCREMENTO_CARREGAMENTO = 2.6
COMBO_MULTIPLICADOR_MEDIO = 10
COMBO_MULTIPLICADOR_ALTO = 20
INVISIBILIDADE_QUADROS = 40
PISCAR_INVISIBILIDADE_QUADROS = 4
COOLDOWN_ATAQUE_INIMIGO_MINIMO = 110
COOLDOWN_ATAQUE_INIMIGO_MAXIMO = 170
