"""Constantes globais do jogo VOID//SHIFT: tela, FPS, cores e titulo."""

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