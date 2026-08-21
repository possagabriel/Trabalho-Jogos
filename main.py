"""VOID//SHIFT — New entry point using the src.core.application Application.

Run with:  python main.py
"""

import os
import sys

# Ensure the project root is on sys.path so ``src`` is importable.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.application import Application  # noqa: E402


if __name__ == "__main__":
    Application().run()
