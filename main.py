"""VOID//SHIFT - Enter the Rift.

Ponto de entrada do jogo. Execute com:  python main.py
"""

import os
import sys

# Garante que o pacote game seja importavel mesmo rodando de outras pastas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.core import Jogo  # noqa: E402


if __name__ == "__main__":
    Jogo().executar()