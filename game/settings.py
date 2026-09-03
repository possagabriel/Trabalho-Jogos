"""Alias temporario para as configuracoes canônicas em :mod:`src.core`.

O alias de modulo mantém compatibilidade inclusive para ferramentas e testes
que ajustam ``ARQUIVO_CONFIG`` durante a transição.
"""

import sys

from src.core import settings as _settings

sys.modules[__name__] = _settings
